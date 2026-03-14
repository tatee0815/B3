"""
Các đối tượng thu thập (collectible) - item nhặt được từ thùng hoặc rơi từ quái
"""

import math
import sdl2
from game.constants import TILE_SIZE, COLORS
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
        self.z_index = 2
        self.collected = False  # đã được nhặt chưa

        self.draw_y = float(y)
        
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

    def render(self, renderer, camera):
        # Dùng draw_y thay vì rect.y để tạo hiệu ứng bob 
        draw_x = int(self.rect.x - camera.x)
        draw_y = int(self.draw_y - camera.y) # Dùng draw_y thay vì rect.y
        
        draw_rect = sdl2.SDL_Rect(draw_x, draw_y, self.rect.w, self.rect.h)
        sdl2.SDL_SetRenderDrawColor(renderer, *self.color)
        sdl2.SDL_RenderFillRect(renderer, draw_rect)


# ────────────────────────────────────────────────


class Heart(Collectible):
    """Hồi máu cho Player"""
    def __init__(self, game, x, y):
        super().__init__(game, x, y, w=22, h=20)
        self.color = (255, 50, 50, 255) # Màu đỏ
        self.z_index = 2

    def on_collect(self, player):
        from game.constants import PLAYER_MAX_HP

        if self.collected: return  # tránh collect nhiều lần
        self.collected = True

        if player.hp < PLAYER_MAX_HP:
            player.hp += 1
            print(f"Nhặt tim! HP hiện tại: {player.hp}")
        else:
            print("HP đã đầy!")

class Coin(Collectible):
    """Thu thập vàng"""

    def __init__(self, game, x, y, value=1):
        super().__init__(game, x, y, w=20, h=20)
        self.value = value
        self.color = COLORS["yellow"]  
        self.particle_color = (255, 240, 100, 255)
        self.bob_amplitude = 5.0
        self.bob_frequency = 4.0  # lắc nhanh hơn tí

    def on_collect(self, player):
        if self.collected: return  # tránh collect nhiều lần
        self.collected = True
        player.gold += self.value
        print(f"+{self.value} vàng → {player.gold}")
        self.kill()  # loại bỏ khỏi game sau khi nhặt

class ManaBottle(Collectible):
    """Hồi mana"""

    def __init__(self, game, x, y, value=25):
        super().__init__(game, x, y, w=24, h=28)
        self.value = value
        self.color = COLORS["mana_bar"]
        self.particle_color = (120, 220, 255, 255)

    def on_collect(self, player):
        if self.collected: return  # tránh collect nhiều lần
        self.collected = True
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