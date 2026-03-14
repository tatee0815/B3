"""
Thùng gỗ / thùng nổ - đập bằng kiếm hoặc skill thì vỡ ra item
"""

from game.constants import TILE_SIZE
from game.entities.base import Entity


class BreakableBox(Entity):
    """Thùng có thể phá (gỗ hoặc nổ)"""

    def __init__(self, game, x, y, explosive=False):
        super().__init__(game, x, y, TILE_SIZE, TILE_SIZE)
        self.z_index = 1
        self.explosive = explosive
        self.hp = 1 if not explosive else 2  # thùng nổ chịu 2 hit
        self.color = (180, 120, 60, 255) if not explosive else (200, 80, 40, 255)
        self.broken = False

        # Item có thể rơi ra khi vỡ (random)
        self.possible_drops = ["coin", "heart", "mana"] if not explosive else ["coin", "mana"]

    def take_damage(self, amount=1):
        self.hp -= amount
        if self.hp <= 0:
            self.break_box()

    def break_box(self):
        if self.broken:
            return
        
        self.broken = True
        self.alive = False
        
        # Spawn item ngẫu nhiên (tạo instance Collectible)
        from game.entities.collectible import Coin, Heart, ManaBottle
        import random
        
        center_x = self.rect.x + (self.rect.w // 2)
        center_y = self.rect.y + (self.rect.h // 2)
        
        drop_x = center_x - 12 # Giả định item rộng 24
        drop_y = center_y - 12 # Giả định item cao 24
        
        drop_type = random.choice(self.possible_drops)
        drop = None

        if drop_type == "coin":
            drop = Coin(self.game, drop_x, drop_y, value=5)
        elif drop_type == "heart":
            drop = Heart(self.game, drop_x, drop_y)
        else:
            drop = ManaBottle(self.game, drop_x, drop_y, value=25)
        
        if drop:
            playing_state = self.game.states.get("playing")
            if playing_state and playing_state.level:
                playing_state.level.entities.append(drop)