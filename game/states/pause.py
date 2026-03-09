"""
State Pause - Màn hình tạm dừng
"""

import sdl2
from game.constants import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT


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
        # Làm mờ nền (tạm thời vẽ overlay đen mờ)
        renderer.fill((0, 0, 0, 120), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # Text PAUSE
        # self.game.font.render(renderer, "PAUSE", (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 60), align="center", color=COLORS["yellow"])
        # self.game.font.render(renderer, "Nhấn ESC để tiếp tục", (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 40), align="center")