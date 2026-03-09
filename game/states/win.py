"""
State Win - Cứu được công chúa
"""

import sdl2
from game.constants import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT


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
        renderer.clear(COLORS["black"])
        # self.game.font.render(renderer, "CỨU ĐƯỢC CÔNG CHÚA!", (SCREEN_WIDTH//2, 180), align="center", color=COLORS["yellow"])
        # self.game.font.render(renderer, "Cảm ơn bạn đã chơi!", (SCREEN_WIDTH//2, 300), align="center")