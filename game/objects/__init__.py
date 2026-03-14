"""
Package objects - Các đối tượng tĩnh / tương tác trong level
Không có AI di chuyển phức tạp như enemy
"""

from .platform import Platform, OneWayPlatform, MovingPlatform
from .breakable import BreakableBox
from game.entities.collectible import Heart, Coin, ManaBottle  # import từ entities nếu tách riêng
from .checkpoint import Checkpoint
from .chest import Chest

__all__ = [
    "Platform",
    "OneWayPlatform",
    "MovingPlatform",
    "BreakableBox",
    "Heart", "Coin", "ManaBottle",
    "Checkpoint",
    "Chest",
]