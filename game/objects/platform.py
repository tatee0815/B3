import sdl2
from game.constants import TILE_SIZE, COLORS
from game.entities.base import Entity

class Platform(Entity):
    """Platform solid thông thường (không di chuyển)"""
    def __init__(self, game, x, y, w=TILE_SIZE, h=TILE_SIZE, tile_id=1):
        super().__init__(game, x, y, w, h)
        self.z_index = 0
        self.color = COLORS["plat_green"] # Màu xanh lá
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
        self.color = COLORS["light_green"] # Màu xanh mờ

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
        self.min_pos = float(x)
        self.max_pos = float(x + 200)
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.color = (180, 100, 60, 255) # Màu nâu đỏ

    def update(self, delta_time, level=None):
        # Lưu vị trí cũ để tính độ lệch (displacement)
        old_x = self.pos_x
        old_y = self.pos_y

        # Tính toán di chuyển
        move = self.speed * self.direction * delta_time * 60
        if self.is_horizontal:
            self.pos_x += move
            if self.pos_x <= self.min_pos or self.pos_x >= self.max_pos:
                self.direction *= -1
        
        # Cập nhật Rect (dùng cho va chạm)
        self.rect.x = int(round(self.pos_x))
        self.rect.y = int(round(self.pos_y))

        # TÍNH TOÁN ĐỘ LỆCH THỰC TẾ
        dx = self.pos_x - old_x
        dy = self.pos_y - old_y

        # Kéo Player đi theo nếu đang đứng trên đầu
        if level:
            player = level.game.states["playing"].player
            if self.is_player_on_top(player):
                # Cộng trực tiếp độ lệch vào tọa độ THỰC của player
                player.pos_x += dx
                player.pos_y += dy
                # Cập nhật rect của player ngay lập tức để đồng bộ frame
                player.rect.x = int(round(player.pos_x))
                player.rect.y = int(round(player.pos_y))

    def is_player_on_top(self, player):
        # 1. Player phải đang đứng trên đất (hoặc rơi xuống bục)
        # 2. Chân player phải nằm trong phạm vi bề mặt bục (cho sai số 5-10 pixel)
        within_x = (player.rect.x + player.rect.w > self.rect.x) and (player.rect.x < self.rect.x + self.rect.w)
        # Kiểm tra khoảng cách giữa chân player và đỉnh platform
        is_touching = abs((player.rect.y + player.rect.h) - self.rect.y) < 10
        return within_x and is_touching and player.vel_y >= 0