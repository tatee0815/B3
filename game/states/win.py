"""
State Win - Cứu được công chúa
"""

import sdl2
from game.constants import SCREEN_WIDTH, SCREEN_HEIGHT, COLORS


class WinState:
    def __init__(self, game):
        self.game = game
        self.name = "win"
        self.timer = 0.0

    def on_enter(self, **kwargs):
        print("YOU WIN!")
        self.timer = 0.0

    def update(self, delta_time):
        self.timer += delta_time
        if self.timer > 5.0:  # tự động về menu sau 5 giây
            self.game.change_state("menu")

    def handle_event(self, event):
        if event.type == sdl2.SDL_KEYDOWN:
            if event.key.keysym.sym in (sdl2.SDLK_RETURN, sdl2.SDLK_z, sdl2.SDLK_ESCAPE):
                self.game.change_state("menu")

    def render(self, renderer):
        # Nền xanh dương thắng lợi
        sdl2.SDL_SetRenderDrawColor(renderer, 60, 100, 220, 255)
        sdl2.SDL_RenderClear(renderer)

        # Text WIN (placeholder)
        sdl2.SDL_SetRenderDrawColor(renderer, 255, 215, 0, 255)  # vàng
        win_rect = sdl2.SDL_Rect(SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT//2 - 100, 400, 200)
        sdl2.SDL_RenderFillRect(renderer, win_rect)

        # Hướng dẫn
        sdl2.SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255)
        hint_rect = sdl2.SDL_Rect(SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT - 100, 400, 40)
        sdl2.SDL_RenderFillRect(renderer, hint_rect)