from typing import Dict, List, Optional

import numpy as np
from rlbot.flat import FieldInfo, GamePacket, MatchConfiguration, MatchPhase

from .common_values import BLUE_TEAM, ORANGE_TEAM, TICKS_PER_SECOND
from .extra_info import ExtraPacketInfo
from .game_state import GameState
from .v1.physics_object import PhysicsObject as V1PhysicsObject
from .v1.player_data import PlayerData as V1PlayerData


class V1GameState:
    def __init__(
        self,
        field_info: FieldInfo,
        match_settings=MatchConfiguration(),
        tick_skip=8,
        standard_map=True,
        sort_players_by_car_id=False,
    ):
        self._game_state = GameState.create_compat_game_state(
            field_info, match_settings, tick_skip, standard_map
        )
        self.game_type = int(match_settings.game_mode)
        self.blue_score = 0
        self.orange_score = 0
        self.last_touch: Optional[int] = -1
        self.players: List[V1PlayerData] = []
        self.ball: V1PhysicsObject = None
        self.inverted_ball: V1PhysicsObject = None
        self.boost_pads: np.ndarray = None
        self.inverted_boost_pads: np.ndarray = None
        self._sort_players_by_car_id = sort_players_by_car_id
        self._boost_pickups: Dict[int, int] = {}
        self._car_ball_touched: Dict[int, bool] = {}
        self._tick_skip = tick_skip

    def _recalculate_fields(self):
        player_id_spectator_id_map = {}
        blue_spectator_id = 1
        for player_id, car in self._game_state.cars.items():
            if car.team_num == BLUE_TEAM:
                player_id_spectator_id_map[player_id] = blue_spectator_id
                blue_spectator_id += 1
        orange_spectator_id = max(5, blue_spectator_id)
        for player_id, car in self._game_state.cars.items():
            if car.team_num == ORANGE_TEAM:
                player_id_spectator_id_map[player_id] = orange_spectator_id
                orange_spectator_id += 1
        for player_data in self.players:
            player_id = player_data.player_id
            player_data.update_from_v2(
                self._game_state.cars[player_id],
                player_id_spectator_id_map[player_id],
                self._boost_pickups[player_id],
                self._car_ball_touched[player_id],
            )
        if self._sort_players_by_car_id:
            self.players.sort(key=lambda p: p.car_id)
        self.ball = V1PhysicsObject.create_from_v2(self._game_state.ball)
        self.inverted_ball = V1PhysicsObject.create_from_v2(
            self._game_state.inverted_ball
        )
        self.boost_pads = (self._game_state.boost_pad_timers == 0).astype(np.float32)
        self.inverted_boost_pads = (
            self._game_state.inverted_boost_pad_timers == 0
        ).astype(np.float32)

    def update(self, packet: GamePacket, extra_info: Optional[ExtraPacketInfo] = None):
        self.blue_score = packet.teams[BLUE_TEAM].score
        self.orange_score = packet.teams[ORANGE_TEAM].score
        (latest_touch_player_idx, latest_touch_player_info) = max(
            enumerate(packet.players),
            key=lambda item: (
                -1
                if item[1].latest_touch is None
                else item[1].latest_touch.game_seconds
            ),
        )
        self.last_touch = (
            -1
            if latest_touch_player_info.latest_touch is None
            else latest_touch_player_idx
        )
        old_boost_amounts = {
            **{p.player_id: p.boost / 100 for p in packet.players},
            **{k: v.boost_amount for (k, v) in self._game_state.cars.items()},
        }
        self._game_state.update(packet, extra_info)
        self.players: List[V1PlayerData] = []
        for player_info in packet.players:
            player_id = player_info.player_id
            if player_id not in self._boost_pickups:
                self._boost_pickups[player_id] = 0
            if player_id not in self._car_ball_touched:
                self._car_ball_touched[player_id] = False
            # We can't use the RLGym v2's car ball touches since those are tracked per action sequence (with some offset based on delay usage) instead of based on tick skip, so calculate them here
            if player_info.latest_touch is not None:
                ticks_since_touch = int(
                    round(
                        (
                            packet.match_info.seconds_elapsed
                            - player_info.latest_touch.game_seconds
                        )
                        * TICKS_PER_SECOND
                    )
                )
                if ticks_since_touch < self._tick_skip:
                    self._car_ball_touched[player_id] = True
            if (
                packet.match_info.match_phase in (MatchPhase.Active, MatchPhase.Kickoff)
                and old_boost_amounts[player_info.player_id] < player_info.boost / 100
            ):  # This isn't perfect but with decent fps it'll work
                self._boost_pickups[player_info.player_id] += 1
            self.players.append(V1PlayerData.create_base(player_info))
        self._recalculate_fields()
