"""
Các đối tượng thu thập (collectible) - item nhặt được từ thùng hoặc rơi từ quái
"""

import math
import random
import sdl2
from game.constants import COLORS, PLAYER_MAX_HP
from game.utils.assets import AssetManager
from .base import Entity

PLAYER_COLLECT_QUOTES = {
    "heart": ["Hồi phục nào!", "Cảm thấy khỏe hơn rồi.", "Hú hồn!", "Tim nè!", "Vẫn còn trụ được."],
    "coin": ["Vàng kìa!", "Giàu to rồi!", "Lụm lúa!", "Thêm chút tiền tiêu vặt.", "Keng keng!"],
    "mana": ["Năng lượng tràn trề!", "Phép thuật lên ngôi.", "Mana đây rồi!", "Tiếp thêm sức mạnh."]
}

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
        
        # Tạo ID duy nhất dựa trên vị trí để lưu trạng thái đã nhặt
        self.item_id = f"{self.__class__.__name__}_{int(x)}_{int(y)}"

        if "collected_items" in self.game.player_progress:
            if self.item_id in self.game.player_progress["collected_items"]:
                self.alive = False 
                return

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

    def _mark_as_collected(self):
        """Hỗ trợ lưu ID vào danh sách đã nhặt"""
        if "collected_items" not in self.game.player_progress:
            self.game.player_progress["collected_items"] = []
        
        if self.item_id not in self.game.player_progress["collected_items"]:
            self.game.player_progress["collected_items"].append(self.item_id)
        
        # Lưu file ngay lập tức để tránh crash mất dữ liệu
        from game.utils.save import save_game
        save_game(self.game.player_progress)

    def update(self, delta_time, level=None):
        if not self.alive: return
        super().update(delta_time, level)

        # Animation lơ lửng (không ảnh hưởng collision)
        self.bob_timer += delta_time
        offset_y = math.sin(self.bob_timer * self.bob_frequency) * self.bob_amplitude
        self.draw_y = self.rect.y + offset_y  # chỉ dùng khi render, không thay đổi rect

        # Check collision với player (xử lý ở playing state hoặc đây)
        player = self.game.player
        if player and self.collides_with(player):
            self.on_collect(player)

    def render(self, renderer, camera):
        if not self.alive: return
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
        if not self.alive: return
        self.color = (255, 50, 50, 255) # Màu đỏ
        self.z_index = 2

    def on_collect(self, player):
        if self.collected: return  # tránh collect nhiều lần
        self.collected = True
        self._mark_as_collected()
        player.hp = min(player.hp + 1, PLAYER_MAX_HP)
        if hasattr(player, 'show_speech'):
            player.show_speech(random.choice(PLAYER_COLLECT_QUOTES["heart"]))
        self.kill()  # loại bỏ khỏi game sau khi nhặt

class Coin(Collectible):
    """Thu thập vàng"""

    def __init__(self, game, x, y, value=1):
        super().__init__(game, x, y, w=20, h=20)
        if not self.alive: return
        self.value = value
        self.color = COLORS["yellow"]  
        self.particle_color = (255, 240, 100, 255)
        self.bob_amplitude = 5.0
        self.bob_frequency = 4.0  # lắc nhanh hơn tí

    def on_collect(self, player):
        if self.collected: return  # tránh collect nhiều lần
        self.collected = True
        self._mark_as_collected()
        player.add_gold(self.value)
        if hasattr(player, 'show_speech'):
            player.show_speech(random.choice(PLAYER_COLLECT_QUOTES["coin"]))
        self.kill()  # loại bỏ khỏi game sau khi nhặt

class ManaBottle(Collectible):
    """Hồi mana"""

    def __init__(self, game, x, y, value=25):
        super().__init__(game, x, y, w=24, h=28)
        if not self.alive: return
        self.value = value
        self.color = COLORS["mana_bar"]
        self.particle_color = (120, 220, 255, 255)

    def on_collect(self, player):
        if self.collected: return  # tránh collect nhiều lần
        self.collected = True
        self._mark_as_collected()
        player.mana = min(player.mana + self.value, 100)
        if hasattr(player, 'show_speech'):
            player.show_speech(random.choice(PLAYER_COLLECT_QUOTES["mana"]))
        self.kill()  # loại bỏ khỏi game sau khi nhặt

class Princess(Entity):
    """Công chúa - Thực thể tương tác để kết thúc game"""
    def __init__(self, game, x, y):
        super().__init__(game, x, y, w=48, h=48)
        self.z_index = 3
        
        # Hệ thống Animation
        self.anim_state = "princess_idle"
        self.anim_frame = 0
        self.anim_timer = 0.0
        self.anim_speed = 0.15
        
        # --- MỚI: Timer đổi Sprite ---
        self.state_change_timer = 5.0  # Đếm ngược 5 giây
        
        self.is_rescued = False
        self.bob_timer = 0.0
        self.base_y = float(y)

    def update(self, delta_time, level):
        # 1. Hiệu ứng lơ lửng nhẹ
        self.bob_timer += delta_time * 3
        self.rect.y = int(self.base_y + math.sin(self.bob_timer) * 5)

        # 2. Logic đổi Sprite sau mỗi 5 giây
        self.state_change_timer -= delta_time
        if self.state_change_timer <= 0:
            # Đổi qua lại giữa 2 state
            if self.anim_state == "princess_idle":
                self.anim_state = "princess_special"
            elif self.anim_state == "princess_special":
                self.anim_state = "princess_protection"
            elif self.anim_state == "princess_protection":
                self.anim_state = "princess_walk"
            else:
                self.anim_state = "princess_idle"
            
            # Reset lại timer và frame
            self.state_change_timer = 5.0
            self.anim_frame = 0 

        # 3. Cập nhật Frame Animation hiện tại
        self.anim_timer += delta_time
        config = AssetManager.ANIM_CONFIG.get(self.anim_state)
        if config and self.anim_timer >= self.anim_speed:
            self.anim_timer = 0
            self.anim_frame = (self.anim_frame + 1) % config["frames"]

    def on_interact(self, player):
        """Hàm này được gọi từ player.interact() khi bấm phím E"""
        if self.is_rescued: 
            return
            
        self.is_rescued = True
        self.game.change_state("outro")

    def render(self, renderer, camera):
        texture, srcrect = AssetManager.get_anim_info(self.anim_state, self.anim_frame)
        
        if texture:
            draw_x = int(self.rect.x - camera.x)
            draw_y = int(self.rect.y - camera.y)
            
            # Scale sprite lên 2 lần cho dễ nhìn
            scale = 2.0
            render_w = 48 * scale
            render_h = 48 * scale
            
            # Căn chỉnh sprite để chân Princess chạm đúng đáy hitbox
            dstrect = sdl2.SDL_Rect(
                int(draw_x - (render_w - self.rect.w) // 2),
                int(draw_y - (render_h - self.rect.h)),
                int(render_w),
                int(render_h)
            )
            
            sdl2.SDL_RenderCopy(renderer, texture, srcrect, dstrect)
        
        draw_rect = sdl2.SDL_Rect(
            int(self.rect.x - camera.x),
            int(self.rect.y - camera.y),
            self.rect.w,
            self.rect.h
        )
        # Vẽ gợi ý tương tác khi Player đứng gần
        # Tính khoảng cách đơn giản để hiện chữ
        player = self.game.player
        if player:
            # Tạo một rect tương tác giả lập để kiểm tra xem có nên hiện chữ "E" không
            interact_check = sdl2.SDL_Rect(int(player.rect.x - 20), int(player.rect.y - 20), 
                                          int(player.rect.w + 40), int(player.rect.h + 40))
            
            if sdl2.SDL_HasIntersection(interact_check, self.rect) and not self.is_rescued:
                if hasattr(self.game, 'hud'):
                    # Hiển thị text hướng dẫn ngay trên đầu Công chúa
                    self.game.hud._draw_text(
                        renderer, "Giải Cứu", 
                        draw_rect.x - 30, draw_rect.y - 30, (255, 255, 255)
                    )