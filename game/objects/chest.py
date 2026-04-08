import sdl2
import sdl2.sdlttf as ttf
from game.constants import COLORS

class Chest:
    def __init__(self, game, x, y, w=40, h=32, unlock_skill=None):
        self.game = game
        self.rect = sdl2.SDL_Rect(x, y, w, h)
        self.opened = False
        self.unlock_skill = unlock_skill  
        self.z_index = 1
        self.alive = True
        self.show_prompt = False # Cờ hiển thị chữ "Nhấn E"

        self.message_timer = 0.0    
        self.message_duration = 5.0  
        self.unlocked_text = ""

        # Phân biệt màu sắc rương theo Skill
        if self.unlock_skill == "dash":
            self.chest_color = (100, 200, 255) # Xanh lướt (Dash)
        elif self.unlock_skill == "skill_a":
            self.chest_color = (255, 100, 100) # Đỏ (Bắn chưởng)
        elif self.unlock_skill == "double_jump":
            self.chest_color = (100, 255, 100) # Xanh lá (Nhảy kép)
        else:
            self.chest_color = COLORS["orange"] # Mặc định

    def on_interact(self, player):
        if not self.opened:
            self.opened = True
            self.show_prompt = False
            chest_id = f"{self.rect.x}_{self.rect.y}"
            
            # Lấy progress riêng của người chơi (mỗi role có một bảng)
            progress = player.progress if hasattr(player, 'progress') else self.game.player_progress
            
            if "opened_chests" not in progress:
                progress["opened_chests"] = []
            if chest_id not in progress["opened_chests"]:
                progress["opened_chests"].append(chest_id)
                
                # Lưu checkpoint riêng cho player này
                player.checkpoint_pos = (float(self.rect.x), float(self.rect.y - 20))
                progress["checkpoint"] = player.checkpoint_pos
                
                # Mở khóa kỹ năng cho player này
                if self.unlock_skill:
                    if self.unlock_skill == "double_jump":
                        progress["double_jump"] = True
                    elif self.unlock_skill not in progress.get("unlocked_skills", []):
                        progress.setdefault("unlocked_skills", []).append(self.unlock_skill)
                
                self.message_timer = self.message_duration
                skill_names = {
                    "dash": "LƯỚT (C)",
                    "skill_a": "BẮN CHƯỞNG (A)",
                    "double_jump": "NHẢY KÉP (Z)"
                }
                name = skill_names.get(self.unlock_skill, "KỸ NĂNG MỚI")
                self.unlocked_text = f"ĐÃ MỞ KHÓA: {name}!"
                
                # Lưu toàn bộ tiến trình game (cả hai người)
                from game.utils.save import save_game
                save_game(self.game.player_progress)

    def update(self, delta_time, level):
        if self.message_timer > 0:
            self.message_timer -= delta_time

        if not self.opened and level:
            player = level.game.states["playing"].player
            if player:
                # Tính khoảng cách giữa Player và Rương
                dist_x = abs(self.rect.x - player.rect.x)
                dist_y = abs(self.rect.y - player.rect.y)
                
                # Nếu đứng cách rương dưới 60 pixel -> Hiện chữ
                if dist_x < 60 and dist_y < 60:
                    self.show_prompt = True
                else:
                    self.show_prompt = False

    def render(self, renderer, camera):
        color = COLORS["dark_gray"] if self.opened else self.chest_color
        draw_rect = sdl2.SDL_Rect(
            int(self.rect.x - camera.x),
            int(self.rect.y - camera.y),
            self.rect.w,
            self.rect.h
        )
        
        sdl2.SDL_SetRenderDrawColor(renderer, *color, 255)
        sdl2.SDL_RenderFillRect(renderer, draw_rect)
        
        sdl2.SDL_SetRenderDrawColor(renderer, 255, 215, 0, 255)
        sdl2.SDL_RenderDrawRect(renderer, draw_rect)

        # Trổ tài vẽ chữ "Nhấn UP để mở" lơ lửng trên rương
        if self.show_prompt and not self.opened:
            font = self.game.font
            if font:
                text = "Nhấn UP để mở"  # Hướng dẫn tương tác
                sdl_color = sdl2.SDL_Color(255, 255, 255, 255)
                surf = ttf.TTF_RenderUTF8_Blended(font, text.encode('utf-8'), sdl_color)
                if surf:
                    tex = sdl2.SDL_CreateTextureFromSurface(renderer, surf)
                    tw, th = surf.contents.w, surf.contents.h
                    # Đặt chữ nằm chính giữa phía trên rương
                    text_rect = sdl2.SDL_Rect(
                        int(self.rect.x - camera.x + self.rect.w//2 - tw//2), 
                        int(self.rect.y - camera.y - 35), tw, th
                    )
                    sdl2.SDL_RenderCopy(renderer, tex, None, text_rect)
                    sdl2.SDL_DestroyTexture(tex)
                    sdl2.SDL_FreeSurface(surf)

        if self.message_timer > 0 and self.unlocked_text:
            font = self.game.font
            if font:
                # Hiệu ứng bay lên nhẹ và mờ dần
                alpha = int((self.message_timer / self.message_duration) * 255)
                # Màu vàng kim cho trang trọng
                sdl_color = sdl2.SDL_Color(255, 215, 0, alpha) 
                
                surf = ttf.TTF_RenderUTF8_Blended(font, self.unlocked_text.encode('utf-8'), sdl_color)
                if surf:
                    tex = sdl2.SDL_CreateTextureFromSurface(renderer, surf)
                    tw, th = surf.contents.w, surf.contents.h
                    
                    # Vị trí: Trên đầu rương và dịch lên theo thời gian
                    offset_y = (self.message_duration - self.message_timer) * 10
                    tx = int(self.rect.x + self.rect.w//2 - tw//2 - camera.x)
                    ty = int(self.rect.y - 60 - offset_y - camera.y)
                    
                    dst = sdl2.SDL_Rect(tx, ty, tw, th)
                    sdl2.SDL_RenderCopy(renderer, tex, None, dst)
                    
                    sdl2.SDL_DestroyTexture(tex)
                    sdl2.SDL_FreeSurface(surf)