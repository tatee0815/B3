import sdl2
from game.constants import COLORS
from game.entities.base import Entity

class Button(Entity):
    def __init__(self, game, x, y, gate_id, w=32, h=16):
        super().__init__(game, x, y, w, h)
        self.gate_id = gate_id
        self.pressed = False
        self.color = COLORS["yellow"]
        self.z_index = 2

    def on_interact(self, player):
        if not self.pressed:
            self.pressed = True
            # Kích hoạt gate tương ứng
            level = self.game.states["playing"].level
            for gate in level.gates:
                if gate.gate_id == self.gate_id:
                    gate.open()
            self.color = COLORS["green"]

    def update(self, delta_time, level):
        # Kiểm tra va chạm với player để tự động kích hoạt (nếu muốn)
        player = level.game.player
        if player and not self.pressed and self.collides_with(player):
            self.on_interact(player)

    def render(self, renderer, camera):
        draw_rect = sdl2.SDL_Rect(
            int(self.rect.x - camera.x),
            int(self.rect.y - camera.y),
            self.rect.w, self.rect.h
        )
        sdl2.SDL_SetRenderDrawColor(renderer, *self.color, 255)
        sdl2.SDL_RenderFillRect(renderer, draw_rect)