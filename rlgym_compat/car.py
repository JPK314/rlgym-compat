from collections import deque
from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np
from rlbot.flat import AirState, BoxShape, GamePacket, PlayerInfo, Vector3

from .common_values import (
    BLUE_TEAM,
    BREAKOUT,
    DOMINUS,
    DOUBLEJUMP_MAX_DELAY,
    FLIP_TORQUE_TIME,
    HYBRID,
    JUMP_RESET_TIME_PAD,
    MERC,
    MIN_BOOST_TIME,
    MIN_JUMP_TIME,
    OCTANE,
    ORANGE_TEAM,
    PLANK,
    POWERSLIDE_FALL_RATE,
    POWERSLIDE_RISE_RATE,
    TICK_TIME,
    TICKS_PER_SECOND,
)
from .extra_info import ExtraPlayerInfo
from .physics_object import PhysicsObject
from .utils import compare_hitbox_shape, create_default_init


@dataclass(init=False)
class Car:
    # Misc Data
    team_num: int  # the team of this car, constants in common_values.py
    hitbox_type: int  # the hitbox of this car, constants in common_values.py
    ball_touches: int  # number of ball touches since last state was sent
    bump_victim_id: Optional[
        int
    ]  # The agent ID of the car you had car contact with if any

    # Actual State
    demo_respawn_timer: float  # time, in seconds, until respawn, or 0 if alive (in [0,3] unless changed in mutator config)
    wheels_with_contact: Tuple[
        bool, bool, bool, bool
    ]  # front_left, front_right, back_left, back_right
    supersonic_time: float  # time, in seconds, since car entered supersonic state (reset to 0 when exited supersonic state) (in [0, infinity) but only relevant values are in [0,1] (1 comes from SUPERSONIC_MAINTAIN_MAX_TIME in RLConst.h))
    boost_amount: float  # (in [0,100])
    boost_active_time: float  # time, in seconds, since car started pressing boost (reset to 0 when boosting stops) (in [0, infinity) but only relevant values are in [0,0.1] (0.1 comes from BOOST_MIN_TIME in RLConst.h))
    handbrake: float  # indicates the magnitude of the handbrake, which ramps up and down when handbrake is pressed/released (in [0,1])

    # Jump Stuff
    is_jumping: bool  # whether the car is currently jumping (you gain a little extra velocity while holding jump)
    has_jumped: bool  # whether the car has jumped since last time it was on ground
    is_holding_jump: bool  # whether you pressed jump last tick or not
    jump_time: float  # time, in seconds, since jump was pressed while car was on ground, clamped to 0.2 (reset to 0 when car presses jump while on ground) (in [0,0.2] (0.2 comes from JUMP_MAX_TIME in RLConst.h))

    # Flip Stuff
    has_flipped: bool  # whether the car has flipped since last time it was on ground
    has_double_jumped: (
        bool  # whether the car has double jumped since last time it was on ground
    )
    air_time_since_jump: float  # time, in seconds, since a jump off ground ended (reset to 0 when car is on ground or has not jumped or is jumping) (in [0, infinity) but only relevant values are in [0,1.25] (1.25 comes from DOUBLEJUMP_MAX_DELAY in RLConst.h))
    flip_time: float  # time, in seconds, since flip (or stall) was initiated (reset to 0 when car is on ground) (in [0, infinity) but only relevant values are in [0, 0.95] (0.95 comes from FLIP_TORQUE_TIME + FLIP_PITCHLOCK_EXTRA_TIME in RLConst.h))
    flip_torque: (
        np.ndarray
    )  # torque applied to the car for the duration of the flip (in [0,1])

    # AutoFlip Stuff - What helps you recover from turtling
    is_autoflipping: bool  # changes to false after max autoflip time
    autoflip_timer: float  # time, in seconds, until autoflip force ends (in [0,0.4] (0.4 comes from CAR_AUTOFLIP_TIME in RLConst.h))
    autoflip_direction: float  # 1 or -1, determines roll direction

    # Physics
    physics: PhysicsObject
    _inverted_physics: PhysicsObject  # Cache for inverted physics

    # RLBot Compat specific fields
    _next_action_tick_duration: int
    _ball_touch_ticks: deque[bool]  # history for past _tick_skip ticks
    _prev_air_state: int
    _game_seconds: int
    _cur_tick: int

    __slots__ = tuple(__annotations__)

    exec(create_default_init(__slots__))

    @property
    def is_blue(self) -> bool:
        return self.team_num == BLUE_TEAM

    @property
    def is_orange(self) -> bool:
        return self.team_num == ORANGE_TEAM

    @property
    def is_demoed(self) -> bool:
        return self.demo_respawn_timer > 0

    @property
    def is_boosting(self) -> bool:
        return self.boost_active_time > 0

    @property
    def is_supersonic(self) -> bool:
        return self.supersonic_time > 0

    @property
    def on_ground(self) -> bool:
        return sum(self.wheels_with_contact) >= 3

    @on_ground.setter
    def on_ground(self, value: bool):
        self.wheels_with_contact = (value, value, value, value)

    @property
    def has_flip(self) -> bool:
        return (
            not self.has_double_jumped
            and not self.has_flipped
            and self.air_time_since_jump < DOUBLEJUMP_MAX_DELAY
        )

    @property
    def can_flip(self) -> bool:
        return not self.on_ground and not self.is_holding_jump and self.has_flip

    @property
    def is_flipping(self) -> bool:
        return self.has_flipped and self.flip_time < FLIP_TORQUE_TIME

    @is_flipping.setter
    def is_flipping(self, value: bool):
        if value:
            self.has_flipped = True
            if self.flip_time >= FLIP_TORQUE_TIME:
                self.flip_time = 0
        else:
            self.flip_time = FLIP_TORQUE_TIME

    @property
    def had_car_contact(self) -> bool:
        return self.bump_victim_id is not None

    @property
    def inverted_physics(self) -> PhysicsObject:
        if self._inverted_physics is None:
            self._inverted_physics = self.physics.inverted()
        return self._inverted_physics

    # Octane: hitbox=BoxShape(length=118.00738, width=84.19941, height=36.159073), hitbox_offset=Vector3(x=13.87566, y=0, z=20.754988)
    # Dominus: hitbox=BoxShape(length=127.92678, width=83.27995, height=31.3), hitbox_offset=Vector3(x=9, y=0, z=15.75)
    # Batmobile: hitbox=BoxShape(length=128.81978, width=84.670364, height=29.394402), hitbox_offset=Vector3(x=9.008572, y=0, z=12.0942)
    # Breakout: hitbox=BoxShape(length=131.49236, width=80.521, height=30.3), hitbox_offset=Vector3(x=12.5, y=0, z=11.75)
    # Venom: hitbox=BoxShape(length=127.01919, width=82.18787, height=34.159073), hitbox_offset=Vector3(x=13.87566, y=0, z=20.754988)
    # Merc: hitbox=BoxShape(length=120.72023, width=76.71031, height=41.659073), hitbox_offset=Vector3(x=11.37566, y=0, z=21.504988)

    @staticmethod
    def detect_hitbox(hitbox_shape: BoxShape, hitbox_offset: Vector3):
        if compare_hitbox_shape(hitbox_shape, 118.00738, 84.19941, 36.159073):
            return OCTANE
        if compare_hitbox_shape(hitbox_shape, 127.92678, 83.27995, 31.3):
            return DOMINUS
        if compare_hitbox_shape(hitbox_shape, 128.81978, 84.670364, 29.394402):
            return PLANK
        if compare_hitbox_shape(hitbox_shape, 131.49236, 80.521, 30.3):
            return BREAKOUT
        if compare_hitbox_shape(hitbox_shape, 127.01919, 82.18787, 34.159073):
            return HYBRID
        if compare_hitbox_shape(hitbox_shape, 120.72023, 76.71031, 41.659073):
            return MERC
        return OCTANE

    @staticmethod
    def create_compat_car(
        packet: GamePacket, player_index: int, action_tick_duration: int
    ):
        player_info = packet.players[player_index]
        car = Car()
        car.team_num = BLUE_TEAM if player_info.team == 0 else ORANGE_TEAM
        car.hitbox_type = Car.detect_hitbox(
            player_info.hitbox, player_info.hitbox_offset
        )
        car.ball_touches = 0
        car.bump_victim_id = None
        car.demo_respawn_timer = 0
        car.on_ground = player_info.air_state == AirState.OnGround
        car.supersonic_time = 0
        car.boost_amount = player_info.boost / 100
        car.boost_active_time = 0
        car.handbrake = 0
        car.has_jumped = player_info.has_jumped
        car.is_holding_jump = player_info.last_input.jump
        car.is_jumping = False
        car.jump_time = 0
        car.has_flipped = player_info.has_dodged
        car.has_double_jumped = player_info.has_double_jumped
        if player_info.dodge_timeout == -1:
            car.air_time_since_jump = 0
        else:
            car.air_time_since_jump = DOUBLEJUMP_MAX_DELAY - player_info.dodge_timeout
        car.flip_time = player_info.dodge_elapsed
        car.flip_torque = np.array(
            [-player_info.dodge_dir.y, player_info.dodge_dir.x, 0]
        )
        car.is_autoflipping = False
        car.autoflip_timer = 0
        car.autoflip_direction = 0
        car.physics = PhysicsObject.create_compat_physics_object()
        car._prev_air_state = int(player_info.air_state)
        car._game_seconds = packet.match_info.seconds_elapsed
        car._cur_tick = packet.match_info.frame_num
        return car

    def reset_ball_touches(self):
        self.ball_touches = 0

    def update(
        self,
        player_info: PlayerInfo,
        game_tick: int,
        extra_player_info: Optional[ExtraPlayerInfo] = None,
    ):
        # Assuming hitbox_type and team_num can't change without updating spawn id (and therefore creating new compat car)
        ticks_elapsed = game_tick - self._cur_tick
        self._cur_tick = game_tick
        time_elapsed = TICK_TIME * ticks_elapsed
        self._game_seconds += time_elapsed

        if player_info.latest_touch is not None:
            ticks_since_touch = int(
                round(
                    (self._game_seconds - player_info.latest_touch.game_seconds)
                    * TICKS_PER_SECOND
                )
            )
            if ticks_since_touch < ticks_elapsed:
                self.ball_touches += 1
        self.demo_respawn_timer = (
            0
            if player_info.demolished_timeout == -1
            else player_info.demolished_timeout
        )
        if player_info.is_supersonic:
            self.supersonic_time += time_elapsed
        else:
            self.supersonic_time = 0
        self.boost_amount = player_info.boost / 100
        # Taken from rocket sim
        if self.boost_active_time > 0:
            if (
                not player_info.last_input.boost
                and self.boost_active_time >= MIN_BOOST_TIME
            ):
                self.boost_active_time = 0
            else:
                self.boost_active_time += time_elapsed
        else:
            if player_info.last_input.boost:
                self.boost_active_time = time_elapsed

        if player_info.last_input.handbrake:
            self.handbrake += POWERSLIDE_RISE_RATE * time_elapsed
        else:
            self.handbrake -= POWERSLIDE_FALL_RATE * time_elapsed
        self.handbrake = min(1, max(0, self.handbrake))

        self.is_holding_jump = player_info.last_input.jump

        self.has_jumped = player_info.has_jumped
        self.has_double_jumped = player_info.has_double_jumped
        self.has_flipped = player_info.has_dodged
        self.flip_time = player_info.dodge_elapsed
        self.flip_torque[0] = -player_info.dodge_dir.y
        self.flip_torque[1] = player_info.dodge_dir.x
        if self.has_jumped or self.is_jumping:
            self.jump_time += TICK_TIME * ticks_elapsed
        if player_info.dodge_timeout == -1:
            self.air_time_since_jump = 0
        else:
            self.air_time_since_jump = DOUBLEJUMP_MAX_DELAY - player_info.dodge_timeout

        match player_info.air_state:
            case AirState.OnGround:
                self.on_ground = True
                self.is_jumping = False
                self.air_time_since_jump = 0
            case AirState.Jumping:
                if self._prev_air_state == int(AirState.OnGround):
                    self.jump_time = 0
                # After pressing jump, it usually takes 6 ticks to leave the ground. This is the only air state where we are uncertain if we are on the ground or not.
                self.on_ground = self.jump_time <= 6 * TICK_TIME
                self.is_jumping = True
            case AirState.InAir:
                self.on_ground = False
                self.is_jumping = False
            case AirState.Dodging:
                self.on_ground = False
                self.is_jumping = False
            case AirState.DoubleJumping:
                self.on_ground = False
                self.is_jumping = False

        self.physics.update(player_info.physics)
        self._inverted_physics = self.physics.inverted()

        # Override with extra info if available
        if extra_player_info is not None:
            if extra_player_info.wheels_with_contact is not None:
                self.wheels_with_contact = extra_player_info.wheels_with_contact
            if extra_player_info.handbrake is not None:
                self.handbrake = extra_player_info.handbrake
            if extra_player_info.ball_touches is not None:
                self.ball_touches = extra_player_info.ball_touches
            if (
                extra_player_info.car_contact_id is not None
                and extra_player_info.car_contact_cooldown_timer is not None
            ):
                self.bump_victim_id = (
                    extra_player_info.car_contact_id
                    if extra_player_info.car_contact_cooldown_timer > 0
                    else None
                )
            if extra_player_info.is_autoflipping is not None:
                self.is_autoflipping = extra_player_info.is_autoflipping
            if extra_player_info.autoflip_timer is not None:
                self.autoflip_timer = extra_player_info.autoflip_timer
            if extra_player_info.autoflip_direction is not None:
                self.autoflip_direction = extra_player_info.autoflip_direction

        self._prev_air_state = int(player_info.air_state)
