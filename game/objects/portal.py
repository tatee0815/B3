import sdl2
import math
from game.entities.base import Entity
from game.constants import COLORS

class EndPortal(Entity):
    def __init__(self, game, x, y):
        super().__init__(game, x, y, 64, 64)
        self.z_index = 0 # Nằm dưới Player
        self.color = COLORS.get("purple", (180, 60, 220, 255))
        self.timer = 0.0

    def update(self, delta_time, level=None):
        # ❌ KHÔNG xử lý collision ở đây nữa
        self.timer += delta_time

    def render(self, renderer, camera):
        # Tạo hiệu ứng portal phình to / thu nhỏ nhẹ nhàng
        scale = 1.0 + 0.1 * math.sin(self.timer * 4.0)
        draw_w = int(self.rect.w * scale)
        draw_h = int(self.rect.h * scale)
        
        # Giữ portal căn giữa
        offset_x = (draw_w - self.rect.w) // 2
        offset_y = (draw_h - self.rect.h) // 2

        draw_rect = sdl2.SDL_Rect(
            int(self.rect.x - camera.x - offset_x),
            int(self.rect.y - camera.y - offset_y),
            draw_w, draw_h
        )
        
        sdl2.SDL_SetRenderDrawColor(renderer, *self.color)
        sdl2.SDL_RenderFillRect(renderer, draw_rect)
        
        # Vẽ lõi portal màu đen
        inner_rect = sdl2.SDL_Rect(
            int(self.rect.x - camera.x + 16),
            int(self.rect.y - camera.y + 16),
            32, 32
        )
        sdl2.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255)
        sdl2.SDL_RenderFillRect(renderer, inner_rect)