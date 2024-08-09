import numpy as np
from typing import List, Optional

from rlbot.flat import *
from .physics_object import PhysicsObject
from .player_data import PlayerData


class GameState:
    def __init__(self, game_info: FieldInfo):
        self.game_type: int = 0  # TODO: perhaps update this according to match settings
        self.blue_score = 0
        self.orange_score = 0
        self.last_touch: Optional[int] = -1
        
        self.players: List[PlayerData] = []
        self._on_ground_ticks = np.zeros(64)
        self._air_time_since_jump = np.zeros(64)
        self.has_jumped = [False] * 10

        self.ball: PhysicsObject = PhysicsObject()
        self.inverted_ball: PhysicsObject = PhysicsObject()

        # List of "booleans" (1 or 0)
        self.boost_pads: np.ndarray = np.zeros(len(game_info.boost_pads), dtype=np.float32)
        self.inverted_boost_pads: np.ndarray = np.zeros_like(self.boost_pads, dtype=np.float32)

    def decode(self, packet: GameTickPacket, ticks_elapsed=1, tick_skip=8):
        self.blue_score = packet.teams[0].score
        self.orange_score = packet.teams[1].score

        for i, pad in enumerate(packet.boost_pad_states):
            self.boost_pads[i] = pad.is_active
        self.inverted_boost_pads[:] = self.boost_pads[::-1]

        self.ball.decode_ball_data(packet.balls[0].physics)
        self.inverted_ball.invert(self.ball)

        self.players = []
        latest_touch = packet.balls[0].latest_touch
        for i, car in enumerate(packet.players):
            player = self._decode_player(car, i, ticks_elapsed)
            if latest_touch.game_seconds > 0 and i == latest_touch.player_index and packet.game_info.seconds_elapsed - latest_touch.game_seconds < tick_skip / 120:
                player.ball_touched = True
            
            self.players.append(player)
        
        if latest_touch.game_seconds > 0:
            self.last_touch = latest_touch.player_index
        

    def _decode_player(self, player_info: PlayerInfo, index: int, ticks_elapsed: int) -> PlayerData:
        player_data = PlayerData()

        player_data.car_data.decode_car_data(player_info.physics)
        player_data.inverted_car_data.invert(player_data.car_data)

        if player_info.air_state == AirState.OnGround:
            self._on_ground_ticks[index] = 0
            self._air_time_since_jump[index] = 0
            self.has_jumped[index] = False
        else:
            self._on_ground_ticks[index] += ticks_elapsed

            if player_info.air_state == AirState.Jumping:
                self._air_time_since_jump[index] = 0
                self.has_jumped[index] = True
            elif player_info.air_state in {
                AirState.DoubleJumping,
                AirState.Dodging,
            }:
                self._air_time_since_jump[index] = 150
            else:
                self._air_time_since_jump[index] += ticks_elapsed

        player_data.car_id = index
        player_data.team_num = player_info.team
        player_data.match_goals = player_info.score_info.goals
        player_data.match_saves = player_info.score_info.saves
        player_data.match_shots = player_info.score_info.shots
        player_data.match_demolishes = player_info.score_info.demolitions
        if player_data.boost_amount < player_info.boost / 100: # This isn't perfect but with decent fps it'll work
            if player_data.boost_pickups == -1:
                player_data.boost_pickups = 1
            else:
                player_data.boost_pickups += 1
        player_data.is_demoed = player_info.demolished_timeout > 0
        player_data.on_ground = player_info.air_state == AirState.OnGround or self._on_ground_ticks[index] <= 6
        player_data.ball_touched = False
        player_data.has_jump = not self.has_jumped
        player_data.has_flip = self._air_time_since_jump[index] < 150
        player_data.boost_amount = player_info.boost / 100

        return player_data
