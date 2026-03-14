import sdl2
from game.constants import COLORS

class Checkpoint:
    def __init__(self, game, x, y, w=32, h=64):
        self.game = game
        self.rect = sdl2.SDL_Rect(x, y, w, h)
        self.activated = False

    def update(self, player):
        # Kiểm tra va chạm giữa Player và Checkpoint
        if not self.activated:
            if sdl2.SDL_HasIntersection(self.rect, player.rect):
                self.activated = True
                player.checkpoint_pos = (self.rect.x, self.rect.y - 20)

    def render(self, renderer, camera):
        # Vẽ Checkpoint để test: Màu xanh lam nếu chưa kích hoạt, màu vàng nếu rồi
        color = COLORS["yellow"] if self.activated else COLORS["blue"]
        
        draw_rect = sdl2.SDL_Rect(
            int(self.rect.x - camera.x),
            int(self.rect.y - camera.y),
            self.rect.w,
            self.rect.h
        )
        
        sdl2.SDL_SetRenderDrawColor(renderer, color[0], color[1], color[2], 255)
        sdl2.SDL_RenderFillRect(renderer, draw_rect)