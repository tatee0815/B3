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
            self.show_prompt = False # Tắt chữ khi đã mở
            
            # 1. Lưu Checkpoint
            player.checkpoint_pos = (float(self.rect.x), float(self.rect.y - 20))
            print(f"Đã lưu Checkpoint tại rương {self.unlock_skill}!")

            # 2. Mở khóa kỹ năng
            progress = self.game.player_progress
            if self.unlock_skill:
                if self.unlock_skill == "double_jump":
                    progress["double_jump"] = True
                elif self.unlock_skill not in progress.get("unlocked_skills", []):
                    progress.setdefault("unlocked_skills", []).append(self.unlock_skill)
                print(f">>> ĐÃ MỞ KHÓA KỸ NĂNG: {self.unlock_skill.upper()}!")

    def update(self, delta_time, level):
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

        # Trổ tài vẽ chữ "Nhấn E" lơ lửng trên rương
        if self.show_prompt and not self.opened:
            font = self.game.font
            if font:
                text = "Nhấn E"
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