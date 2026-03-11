"""
Hiệp Sĩ Kiếm Huyền Thoại: Giải Cứu Công Chúa
Mini platformer 2D side-scrolling (~5-10 phút chơi) dùng PySDL2
"""

# Phiên bản game (có thể hiển thị ở menu hoặc title bar)
__version__ = "0.1.0-dev"

# Tên game chính thức (dùng cho window title, save file, v.v.)
GAME_TITLE = "Hiệp Sĩ Kiếm Huyền Thoại: Giải Cứu Công Chúa"
GAME_SHORT_TITLE = "Knight Quest"

# Import các hằng số quan trọng (dễ dùng ở mọi nơi)
from .constants import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FPS_TARGET,
    GRAVITY,
    PLAYER_SPEED,
    JUMP_FORCE,
    MANA_MAX,
    MANA_PER_KILL,
    MANA_PER_BOTTLE,
    KEY_BINDINGS_DEFAULT,
    COLORS,
)

# Import các class chính (cho phép import kiểu: from game import Player, Level)
from .entities.base import Entity
from .entities.player import Player
from .entities.enemy import Enemy, Goblin, Skeleton, FireBat, BossShadowKing
from .entities.projectile import Projectile
from .entities.npc import NPC

from .objects.platform import Platform, MovingPlatform, OneWayPlatform
from .objects.breakable import BreakableBox
from game.entities.collectible import Collectible, Heart, Coin, ManaBottle
from .objects.checkpoint import Checkpoint

from .level.level import Level

from .game import Game
from .states.playing import PlayingState

from .ui.hud import HUD

# Tiện ích thường dùng
from .utils.assets import load_texture, load_sound
from .utils.collision import check_collision, resolve_collision
from .utils.camera import Camera
from .utils.save import save_game, load_game

# (Tùy chọn) Nếu muốn export một alias ngắn gọn cho class Game chính
KnightQuestGame = Game