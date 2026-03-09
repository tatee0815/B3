"""
Các đối tượng thu thập (collectible) - item nhặt được từ thùng hoặc rơi từ quái
"""

import math
import sdl2.ext

from game.constants import TILE_SIZE
from .base import Entity


class Collectible(Entity):
    """
    Lớp cơ sở cho mọi item có thể nhặt
    - Lơ lửng nhẹ (bob animation)
    - Tự xoay hoặc nhấp nháy (sau này)
    - Khi player chạm → gọi on_collect(player)
    """

    def __init__(self, game, x, y, w=24, h=24):
        super().__init__(game, x, y, w, h)
        
        # Animation lơ lửng (bob up/down)
        self.bob_timer = 0.0
        self.bob_amplitude = 4.0   # pixel lên xuống
        self.bob_frequency = 3.0   # tốc độ dao động (rad/s)
        
        # Spawn offset để tránh chìm sàn ngay lập tức
        self.rect.y -= 8  # nhấc lên tí khi spawn

        # Có thể override ở subclass
        self.collect_sound = None  # sẽ load từ utils/assets.py sau
        self.particle_color = (255, 255, 255, 255)  # fallback

    def update(self, delta_time, level=None):
        super().update(delta_time, level)
        
        # Animation lơ lửng (không ảnh hưởng collision)
        self.bob_timer += delta_time
        offset_y = math.sin(self.bob_timer * self.bob_frequency) * self.bob_amplitude
        self.draw_y = self.rect.y + offset_y  # chỉ dùng khi render, không thay đổi rect

        # Check collision với player (xử lý ở playing state hoặc đây)
        player = self.game.states["playing"].player
        if player and self.collides_with(player):
            self.on_collect(player)
            self._on_collected()

    def on_collect(self, player):
        """Override ở subclass để áp dụng hiệu ứng"""
        raise NotImplementedError("Phải override on_collect")

    def _on_collected(self):
        """Logic chung khi bị nhặt: xóa khỏi level, play sound/particle"""
        level = self.game.states["playing"].level
        if self in level.entities:
            level.entities.remove(self)
        
        # Play sound (sau này)
        # if self.collect_sound:
        #     sdl2.mixer.Mix_PlayChannel(-1, self.collect_sound, 0)
        
        # Particle giả lập (sau này dùng particle system)
        print(f"Collected {self.__class__.__name__} at ({self.rect.x}, {self.rect.y})")

    def render(self, renderer, camera):
        # Dùng draw_y thay vì rect.y để tạo hiệu ứng bob
        dst_rect = sdl2.SDL_Rect(
            int(self.rect.x - camera.x),
            int(self.draw_y - camera.y),
            self.rect.w,
            self.rect.h
        )
        
        if self.texture:
            renderer.copy(self.texture, dstrect=dst_rect)
        else:
            # Fallback hình chữ nhật + màu
            renderer.fill(self.color, dst_rect)


# ────────────────────────────────────────────────


class Heart(Collectible):
    """Hồi 1 tim (HP)"""

    def __init__(self, game, x, y):
        super().__init__(game, x, y, w=24, h=24)
        self.color = (220, 60, 60, 255)  # đỏ
        self.particle_color = (255, 80, 80, 255)

    def on_collect(self, player):
        player.hp = min(player.hp + 1, player.game.constants.PLAYER_MAX_HP)
        print(f"+1 HP → {player.hp}/{player.game.constants.PLAYER_MAX_HP}")


class Coin(Collectible):
    """Thu thập vàng"""

    def __init__(self, game, x, y, value=1):
        super().__init__(game, x, y, w=20, h=20)
        self.value = value
        self.color = (240, 220, 60, 255)  # vàng
        self.particle_color = (255, 240, 100, 255)
        self.bob_amplitude = 5.0
        self.bob_frequency = 4.0  # lắc nhanh hơn tí

    def on_collect(self, player):
        player.gold += self.value
        print(f"+{self.value} vàng → {player.gold}")


class ManaBottle(Collectible):
    """Hồi mana"""

    def __init__(self, game, x, y, value=25):
        super().__init__(game, x, y, w=24, h=28)
        self.value = value
        self.color = (80, 180, 255, 255)  # xanh dương
        self.particle_color = (120, 220, 255, 255)

    def on_collect(self, player):
        player.mana = min(player.mana + self.value, 100)
        print(f"+{self.value} mana → {player.mana}/100")


# ────────────────────────────────────────────────
# Các loại khác có thể thêm sau (power-up tạm thời)
# ────────────────────────────────────────────────

class PowerUpSword(Collectible):
    """Tăng damage kiếm tạm thời"""

    def __init__(self, game, x, y):
        super().__init__(game, x, y, w=32, h=32)
        self.color = (200, 200, 255, 255)  # tím nhạt

    def on_collect(self, player):
        # Ví dụ: tăng damage 30s
        print("Nhận Power-up Kiếm (damage +50% trong 30 giây)")
        # player.melee_damage_multiplier = 1.5
        # player.powerup_timer = 30.0