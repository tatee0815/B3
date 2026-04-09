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
            return

        # 3. Va chạm với quái
        for i, enemy in enumerate(level.enemies):
            if enemy.alive and sdl2.SDL_HasIntersection(self.rect, enemy.rect):
                enemy.take_damage(self.damage, self.direction)
                
                # GỬI TÍN HIỆU VỀ HOST NẾU LÀ CLIENT
                if self.game.game_mode == "multi" and not self.game.network.is_host:
                    self.game.network.send_data({
                        "type": "hit_enemy",
                        "enemy_idx": i,
                        "damage": self.damage,
                        "k_dir": self.direction
                    })
                
                self.die()
                break

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
        
        # Thêm hiệu ứng phát sáng cho chưởng (nhiều lớp màu)
        # Lớp ngoài (Mờ hơn)
        sdl2.SDL_SetRenderDrawBlendMode(renderer, sdl2.SDL_BLENDMODE_BLEND)
        outer_rect = sdl2.SDL_Rect(draw_x - 2, draw_y - 2, self.rect.w + 4, self.rect.h + 4)
        sdl2.SDL_SetRenderDrawColor(renderer, 0, 100, 255, 150) # Xanh dương đậm mờ
        sdl2.SDL_RenderFillRect(renderer, outer_rect)
        
        # Lớp lõi (Rực rỡ)
        sdl2.SDL_SetRenderDrawColor(renderer, 0, 255, 255, 255) # Cyan rực rỡ
        sdl2.SDL_RenderFillRect(renderer, draw_rect)
        
        # Viền trắng để làm nổi bật
        sdl2.SDL_SetRenderDrawColor(renderer, 255, 255, 255, 200)
        sdl2.SDL_RenderDrawRect(renderer, draw_rect)
        
        sdl2.SDL_SetRenderDrawBlendMode(renderer, sdl2.SDL_BLENDMODE_NONE)
        
        # Vẽ hitbox nếu bật Debug mode (truy cập qua game)
        if self.game.states["playing"].player and self.game.states["playing"].player.debug_mode:
            sdl2.SDL_SetRenderDrawColor(renderer, 255, 0, 0, 255) # Màu đỏ debug
            sdl2.SDL_RenderDrawRect(renderer, draw_rect)