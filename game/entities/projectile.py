from .base import Entity
from game.constants import TILE_SIZE


class Projectile(Entity):
    def __init__(self, game, x, y, direction=1):
        super().__init__(game, x, y, 16, 8)
        self.vel_x = 8 * direction
        self.damage = 25
        self.color = (100, 200, 255, 255)  # xanh dương

    def update(self, delta_time, level):
        super().update(delta_time, level)
        
        # Va chạm enemy
        for e in level.entities:
            if isinstance(e, Enemy) and self.collides_with(e):
                e.take_damage(self.damage)
                if self in level.entities:
                    level.entities.remove(self)
                break
        
        # Ra khỏi màn hình → xóa
        if self.rect.x < -50 or self.rect.x > level.width * TILE_SIZE + 50:
            if self in level.entities:
                level.entities.remove(self)