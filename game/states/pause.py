"""
State Pause - Màn hình tạm dừng
"""

import sdl2
from game.constants import SCREEN_WIDTH, SCREEN_HEIGHT, COLORS


class PauseState:
    def __init__(self, game):
        self.game = game
        self.name = "pause"

    def on_enter(self, **kwargs):
        print("Game tạm dừng")

    def on_exit(self):
        print("Tiếp tục chơi")

    def handle_event(self, event):
        if event.type == sdl2.SDL_KEYDOWN:
            if event.key.keysym.sym == sdl2.SDLK_ESCAPE:
                self.game.change_state("playing")

    def update(self, delta_time):
        pass

    def render(self, renderer):
        # Làm mờ nền (vẽ overlay đen trong suốt)
        sdl2.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 120)  # đen mờ
        overlay_rect = sdl2.SDL_Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        sdl2.SDL_RenderFillRect(renderer, overlay_rect)

        # Text PAUSE (placeholder hình chữ nhật)
        sdl2.SDL_SetRenderDrawColor(renderer, 255, 255, 0, 255)  # vàng
        pause_rect = sdl2.SDL_Rect(SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 - 50, 300, 100)
        sdl2.SDL_RenderFillRect(renderer, pause_rect)

        # Hướng dẫn
        sdl2.SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255)
        hint_rect = sdl2.SDL_Rect(SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT//2 + 80, 400, 40)
        sdl2.SDL_RenderFillRect(renderer, hint_rect)