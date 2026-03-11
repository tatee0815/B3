import sdl2
from .base import Entity
from game.constants import TILE_SIZE

class Projectile(Entity):
    def __init__(self, game, x, y, direction):
        # Kích thước luồng sáng là 24x16
        super().__init__(game, x, y, 24, 16)
        self.speed = 8.0
        self.direction = direction
        self.damage = 25
        self.distance_traveled = 0
        self.max_distance = 400  # Bay xa 400 pixel rồi biến mất
        self.alive = True

    def update(self, delta_time, level):
        if not self.alive: return

        # Di chuyển theo hướng
        move_step = self.speed * self.direction * delta_time * 60
        self.pos_x += move_step
        self.rect.x = int(self.pos_x)
        self.distance_traveled += abs(move_step)

        # 1. Biến mất nếu bay quá xa
        if self.distance_traveled > self.max_distance:
            self.die()

        # 2. Biến mất nếu chạm tường (Tile 1)
        if level.is_solid_at(self.rect.x + (self.rect.w if self.direction > 0 else 0), self.rect.y + 8):
            self.die()

    def die(self):
        self.alive = False
        # Xóa khỏi danh sách thực thể để giải phóng bộ nhớ
        level = self.game.states["playing"].level
        if self in level.entities:
            level.entities.remove(self)

    def render(self, renderer, camera):
        if not self.alive: return
        draw_x = int(self.rect.x - camera.x)
        draw_y = int(self.rect.y - camera.y)
        draw_rect = sdl2.SDL_Rect(draw_x, draw_y, self.rect.w, self.rect.h)
        
        # Luồng sáng màu xanh cyan rực rỡ
        sdl2.SDL_SetRenderDrawColor(renderer, 0, 255, 255, 255)
        sdl2.SDL_RenderFillRect(renderer, draw_rect)