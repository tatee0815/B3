"""
Cột checkpoint - khi chạm thì lưu vị trí respawn
"""

from game.constants import TILE_SIZE
from game.entities.base import Entity


class Checkpoint(Entity):
    """Cột checkpoint (flag)"""

    def __init__(self, game, x, y):
        super().__init__(game, x, y, TILE_SIZE, TILE_SIZE*2)  # cao gấp đôi
        self.color = (60, 180, 60, 255)  # xanh lá
        self.activated = False
        self.activated_color = (220, 220, 60, 255)  # vàng khi active

    def activate(self):
        if self.activated:
            return
        self.activated = True
        print("Checkpoint activated!")
        
        # Lưu vị trí cho player respawn
        level = self.game.states["playing"].level
        level.last_checkpoint = (self.rect.centerx, self.rect.bottom - 48)  # spawn trên cột
        
        # Có thể play sound hoặc animation

    def update(self, delta_time, level=None):
        # Check player chạm
        player = self.game.states["playing"].player
        if player and self.collides_with(player):
            self.activate()

    def render(self, renderer, camera):
        color = self.activated_color if self.activated else self.color
        renderer.fill(color,
                      (self.rect.x - camera.x,
                       self.rect.y - camera.y,
                       self.rect.w, self.rect.h))