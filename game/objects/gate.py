import sdl2
from game.constants import COLORS
from game.entities.base import Entity

class Gate(Entity):
    def __init__(self, game, x, y, w, h, gate_id, init_open=False):
        super().__init__(game, x, y, w, h)
        self.gate_id = gate_id
        self.is_open = init_open
        self.solid = not self.is_open
        self.color = COLORS["brown"] if not self.is_open else COLORS["light_gray"]
        self.z_index = 1

    def open(self):
        self.is_open = True
        self.solid = False
        self.color = COLORS["light_gray"]

    def close(self):
        self.is_open = False
        self.solid = True
        self.color = COLORS["brown"]

    def update(self, delta_time, level):
        pass

    def render(self, renderer, camera):
        draw_rect = sdl2.SDL_Rect(
            int(self.rect.x - camera.x),
            int(self.rect.y - camera.y),
            self.rect.w, self.rect.h
        )
        sdl2.SDL_SetRenderDrawColor(renderer, *self.color, 255)
        sdl2.SDL_RenderFillRect(renderer, draw_rect)
        if not self.is_open:
            sdl2.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255)
            sdl2.SDL_RenderDrawRect(renderer, draw_rect)