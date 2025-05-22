from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np


@dataclass
class ExtraPlayerInfo:
    wheels_with_contact: Optional[Tuple[bool, bool, bool, bool]]
    handbrake: Optional[float]
    ball_touches: Optional[int]
    car_contact_id: Optional[int]
    car_contact_cooldown_timer: Optional[float]
    is_autoflipping: Optional[bool]
    autoflip_timer: Optional[float]
    autoflip_direction: Optional[float]  # 1 or -1, determines roll direction


@dataclass
class ExtraBallInfo:
    # Net that the heatseeker ball is targeting (0 for none, 1 for orange, -1 for blue)
    heatseeker_target_dir: Optional[int]
    heatseeker_target_speed: Optional[float]
    heatseeker_time_since_hit: Optional[float]


@dataclass
class ExtraPacketInfo:
    players: Optional[List[ExtraPlayerInfo]]
    ball: Optional[ExtraBallInfo]
