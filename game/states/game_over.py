"""
State Game Over
"""

import sdl2
from game.constants import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT


class GameOverState:
    def __init__(self, game):
        self.game = game
        self.name = "game_over"

    def on_enter(self, **kwargs):
        print("Game Over!")

    def handle_event(self, event):
        if event.type == sdl2.SDL_KEYDOWN:
            if event.key.keysym.sym in (sdl2.SDLK_RETURN, sdl2.SDLK_z, sdl2.SDLK_SPACE):
                # Restart level hoặc về menu
                self.game.change_state("playing")

    def update(self, delta_time):
        pass

    def render(self, renderer):
        renderer.clear(COLORS["dark_gray"])
        # self.game.font.render(renderer, "GAME OVER", (SCREEN_WIDTH//2, 200), align="center", color=COLORS["red"])
        # self.game.font.render(renderer, "Nhấn ENTER để chơi lại", (SCREEN_WIDTH//2, 350), align="center")