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

class Princess(Entity):
    """Công chúa - Thực thể tương tác để kết thúc game"""
    def __init__(self, game, x, y):
        # Kích thước 30x48 để trông cao hơn nhân vật một chút
        super().__init__(game, x, y, w=30, h=48)
        self.z_index = 3
        self.color = (255, 105, 180, 255)  # Màu hồng đặc trưng
        
        # Biến để tránh tương tác nhiều lần khi đang chuyển cảnh
        self.is_rescued = False
        
        # Hiệu ứng bay lơ lửng nhẹ (giống các item khác)
        self.bob_timer = 0.0
        self.base_y = float(y)

    def update(self, delta_time, level):
        # Hiệu ứng lơ lửng cho sinh động
        self.bob_timer += delta_time * 3
        self.pos_y = self.base_y + math.sin(self.bob_timer) * 5
        self.rect.y = int(self.pos_y)

    def on_interact(self, player):
        """Hàm này được gọi từ player.interact() khi bấm phím E"""
        if self.is_rescued: 
            return
            
        self.is_rescued = True
        print("Công chúa: 'Cảm ơn hiệp sĩ đã cứu thiếp!'")
        
        # Chuyển trạng thái sang màn hình chiến thắng
        self.game.change_state("win")

    def render(self, renderer, camera):
        draw_rect = sdl2.SDL_Rect(
            int(self.rect.x - camera.x),
            int(self.rect.y - camera.y),
            self.rect.w,
            self.rect.h
        )
        
        # Vẽ Công chúa (Hình khối màu hồng)
        sdl2.SDL_SetRenderDrawColor(renderer, *self.color)
        sdl2.SDL_RenderFillRect(renderer, draw_rect)

        # Vẽ gợi ý tương tác khi Player đứng gần
        # Tính khoảng cách đơn giản để hiện chữ
        playing_state = self.game.states.get("playing")
        if playing_state and playing_state.player:
            player = playing_state.player
            # Tạo một rect tương tác giả lập để kiểm tra xem có nên hiện chữ "E" không
            interact_check = sdl2.SDL_Rect(int(player.rect.x - 20), int(player.rect.y - 20), 
                                          int(player.rect.w + 40), int(player.rect.h + 40))
            
            if sdl2.SDL_HasIntersection(interact_check, self.rect) and not self.is_rescued:
                if hasattr(self.game, 'hud'):
                    # Hiển thị text hướng dẫn ngay trên đầu Công chúa
                    self.game.hud._draw_text(
                        renderer, "Nhấn E để Giải Cứu", 
                        draw_rect.x - 30, draw_rect.y - 30, (255, 255, 255)
                    )