import sdl2
from game.constants import TILE_SIZE
from game.entities.base import Entity

class Platform(Entity):
    """Platform solid thông thường (không di chuyển)"""
    def __init__(self, game, x, y, w=TILE_SIZE, h=TILE_SIZE, tile_id=1):
        super().__init__(game, x, y, w, h)
        self.color = (100, 180, 80, 255) # Màu xanh lá
        self.solid = True

    def update(self, delta_time, level=None):
        # Ghi đè để đứng yên, không bị trọng lực hút
        pass

    def resolve_collision(self, player, delta_time=None):
        if not self.solid: return
        player_bottom = player.rect.y + player.rect.h
        platform_top = self.rect.y
        
        if player.vel_y > 0 and player_bottom <= platform_top + 15:
            if sdl2.SDL_HasIntersection(player.rect, self.rect):
                player.rect.y = platform_top - player.rect.h
                player.pos_y = float(player.rect.y)
                player.vel_y = 0
                player.on_ground = True

    def render(self, renderer, camera):
        # Tính toán vị trí hiển thị theo camera
        render_x = int(self.rect.x - camera.x)
        render_y = int(self.rect.y - camera.y)
        dst_rect = sdl2.SDL_Rect(render_x, render_y, self.rect.w, self.rect.h)
        
        sdl2.SDL_SetRenderDrawColor(renderer, *self.color)
        sdl2.SDL_RenderFillRect(renderer, dst_rect)
        # Vẽ viền để dễ nhìn bục nhảy
        sdl2.SDL_SetRenderDrawColor(renderer, 255, 255, 255, 150)
        sdl2.SDL_RenderDrawRect(renderer, dst_rect)

class OneWayPlatform(Platform):
    def __init__(self, game, x, y, w=TILE_SIZE, h=TILE_SIZE):
        super().__init__(game, x, y, w, h)
        self.color = (120, 200, 100, 180) # Màu xanh mờ

    def resolve_collision(self, player, delta_time=None):
        player_bottom = player.rect.y + player.rect.h
        if player.vel_y > 0 and player_bottom <= self.rect.y + 6:
            if sdl2.SDL_HasIntersection(player.rect, self.rect):
                player.rect.y = self.rect.y - player.rect.h
                player.pos_y = float(player.rect.y)
                player.vel_y = 0
                player.on_ground = True

class MovingPlatform(Platform):
    def __init__(self, game, x, y, w=TILE_SIZE*3, h=TILE_SIZE, speed=2.0):
        super().__init__(game, x, y, w, h)
        self.speed = speed
        self.direction = 1
        self.is_horizontal = True
        self.min_pos = x
        self.max_pos = x + 200
        self.color = (180, 100, 60, 255) # Màu nâu đỏ

    def update(self, delta_time, level=None):
        # Tự di chuyển trong phạm vi
        move = self.speed * self.direction * delta_time * 60
        if self.is_horizontal:
            self.rect.x += int(move)
            if self.rect.x <= self.min_pos or self.rect.x >= self.max_pos:
                self.direction *= -1