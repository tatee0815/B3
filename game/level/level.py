"""
Class Level - Đại diện cho một màn chơi
- Load tiles từ json
- Quản lý entities (enemies, collectibles, platforms, breakables...)
- Xử lý collision player vs world
- Checkpoint & spawn point
"""

import sdl2.ext
from game.constants import TILE_SIZE, GRAVITY, COLORS
from game.utils.camera import Camera  # sẽ viết sau


class Level:
    def __init__(self, game, width_tiles=50, height_tiles=20):
        self.game = game
        self.renderer = game.renderer
        
        # Kích thước map (tiles)
        self.width = width_tiles
        self.height = height_tiles
        self.pixel_width = width_tiles * TILE_SIZE
        self.pixel_height = height_tiles * TILE_SIZE
        
        # Tiles: 2D list (0 = air, 1 = solid ground, 2 = one-way, ...)
        self.tiles = [[0 for _ in range(width_tiles)] for _ in range(height_tiles)]
        
        # Entities động & tương tác
        self.entities = []           # enemies, projectiles, collectibles, npcs...
        self.platforms = []          # solid, one-way, moving platforms
        self.breakables = []         # thùng gỗ/nổ
        self.checkpoints = []        # cột checkpoint
        
        # Spawn & checkpoint
        self.start_position = (100, 400)           # pixel
        self.last_checkpoint = None                # (x, y) pixel
        
        # Gravity (có thể khác nhau giữa level nếu muốn)
        self.gravity = GRAVITY
        
        # Background color fallback
        self.bg_color = COLORS["bg_forest"]

    def render(self, renderer, camera):
        # Background
        renderer.fill(self.bg_color, (0, 0, self.game.window.size[0], self.game.window.size[1]))
        
        # Tiles (chỉ render phần trong camera)
        for y in range(max(0, int(camera.y / TILE_SIZE) - 2),
                       min(self.height, int((camera.y + camera.height) / TILE_SIZE) + 2)):
            for x in range(max(0, int(camera.x / TILE_SIZE) - 2),
                           min(self.width, int((camera.x + camera.width) / TILE_SIZE) + 2)):
                tile_id = self.tiles[y][x]
                if tile_id == 0:
                    continue
                
                rect = sdl2.SDL_Rect(
                    int(x * TILE_SIZE - camera.x),
                    int(y * TILE_SIZE - camera.y),
                    TILE_SIZE, TILE_SIZE
                )
                
                if tile_id == 1:
                    renderer.fill((100, 180, 80, 255), rect)  # ground xanh
                elif tile_id == 2:
                    renderer.fill((120, 200, 100, 180), rect)  # one-way mờ
                
                # Sau này dùng texture từ tileset

        # Render platforms, breakables, checkpoints...
        for obj in self.platforms + self.breakables + self.checkpoints:
            if hasattr(obj, "render"):
                obj.render(renderer, camera)

        # Render entities
        for entity in self.entities:
            if hasattr(entity, "render"):
                entity.render(renderer, camera)

    def resolve_player_collision(self, player):
        """Xử lý va chạm player vs tiles + objects"""
        # Tiles collision (đơn giản - chặn đứng trên)
        player_x = player.rect.x
        player_y = player.rect.y
        
        # Dự đoán vị trí mới
        new_rect = player.rect.copy()
        new_rect.x += int(player.vel_x)
        new_rect.y += int(player.vel_y)

        # Check tiles
        for y in range(int(new_rect.y / TILE_SIZE), int((new_rect.y + new_rect.h) / TILE_SIZE) + 1):
            for x in range(int(new_rect.x / TILE_SIZE), int((new_rect.x + new_rect.w) / TILE_SIZE) + 1):
                if 0 <= x < self.width and 0 <= y < self.height:
                    if self.tiles[y][x] == 1:  # solid
                        # Chặn ngang
                        if player.vel_x > 0 and new_rect.right > x * TILE_SIZE:
                            new_rect.right = x * TILE_SIZE
                            player.vel_x = 0
                        elif player.vel_x < 0 and new_rect.left < (x+1) * TILE_SIZE:
                            new_rect.left = (x+1) * TILE_SIZE
                            player.vel_x = 0
                        
                        # Chặn dọc (chủ yếu rơi xuống)
                        if player.vel_y > 0 and new_rect.bottom > y * TILE_SIZE:
                            new_rect.bottom = y * TILE_SIZE
                            player.vel_y = 0
                            player.on_ground = True
        
        # Cập nhật vị trí player sau collision tiles
        player.rect = new_rect
        
        # Collision với platforms, breakables, checkpoints...
        for obj in self.platforms + self.breakables + self.checkpoints:
            if hasattr(obj, "resolve_collision"):
                obj.resolve_collision(player)
            elif hasattr(obj, "collides_with") and obj.collides_with(player):
                if isinstance(obj, self.game.objects.Checkpoint):
                    obj.activate()

    def check_win(self, player):
        """Kiểm tra chạm flag cuối màn (sẽ implement flag trong json)"""
        # Ví dụ: nếu có flag entity, check collision
        # tạm thời giả lập
        return player.rect.x > self.pixel_width - 100

    def get_spawn_position(self):
        """Vị trí spawn khi vào level"""
        return self.start_position

    def get_last_checkpoint_position(self):
        """Vị trí checkpoint gần nhất"""
        return self.last_checkpoint if self.last_checkpoint else self.start_position

    def get_start_position(self):
        return self.start_position