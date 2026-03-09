"""
Các loại platform: solid, one-way (chỉ chặn từ dưới lên), moving
"""

import sdl2.ext
from game.constants import TILE_SIZE, GRAVITY
from game.entities.base import Entity  # dùng base để có rect, render


class Platform(Entity):
    """Platform solid thông thường (không di chuyển)"""

    def __init__(self, game, x, y, w=TILE_SIZE, h=TILE_SIZE, tile_id=1):
        super().__init__(game, x, y, w, h)
        self.tile_id = tile_id  # để biết loại tile khi render
        self.color = (100, 180, 80, 255)  # xanh lá fallback
        self.solid = True
        self.one_way = False

    def resolve_collision(self, player):
        """Xử lý va chạm với player (gọi từ level)"""
        if not self.solid:
            return
        
        # Đơn giản: chặn đứng trên
        if player.vel_y > 0 and player.rect.bottom <= self.rect.top + 8:
            player.rect.bottom = self.rect.top
            player.vel_y = 0
            player.on_ground = True


class OneWayPlatform(Platform):
    """Platform chỉ chặn từ dưới lên (nhảy xuyên từ dưới)"""

    def __init__(self, game, x, y, w=TILE_SIZE, h=TILE_SIZE):
        super().__init__(game, x, y, w, h)
        self.one_way = True
        self.color = (120, 200, 100, 180)  # mờ hơn tí

    def resolve_collision(self, player):
        # Chỉ chặn nếu player đang rơi xuống và chân chạm từ trên
        if player.vel_y > 0 and player.rect.bottom <= self.rect.top + 6:
            player.rect.bottom = self.rect.top
            player.vel_y = 0
            player.on_ground = True


class MovingPlatform(Platform):
    """Platform di chuyển ngang hoặc dọc (như thang máy)"""

    def __init__(self, game, x, y, w=TILE_SIZE*3, h=TILE_SIZE, speed=2.0, direction=1):
        super().__init__(game, x, y, w, h)
        self.speed = speed
        self.direction = direction  # 1: phải/xuống, -1: trái/lên
        self.is_horizontal = True   # True: ngang, False: dọc
        self.min_pos = x if self.is_horizontal else y
        self.max_pos = x + 200 if self.is_horizontal else y + 200
        self.color = (180, 100, 60, 255)

    def update(self, delta_time, level=None):
        if self.is_horizontal:
            self.rect.x += self.speed * self.direction * delta_time * 60
            if self.rect.x <= self.min_pos or self.rect.x >= self.max_pos:
                self.direction *= -1
        else:
            self.rect.y += self.speed * self.direction * delta_time * 60
            if self.rect.y <= self.min_pos or self.rect.y >= self.max_pos:
                self.direction *= -1

    def resolve_collision(self, player):
        # Tương tự platform solid, nhưng di chuyển player theo platform
        super().resolve_collision(player)
        if player.on_ground and player.rect.bottom == self.rect.top:
            player.rect.x += self.speed * self.direction * delta_time * 60  # dính theo platform