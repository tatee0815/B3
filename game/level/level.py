# -*- coding: utf-8 -*-
import sdl2
import json
import os
from game.constants import TILE_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT, GRAVITY
from game.entities.enemy import Goblin, Skeleton, FireBat, BossShadowKing

class Level:
    def __init__(self, game):
        self.game = game
        self.renderer = game.renderer
        
        self.name = ""
        self.width = 0 
        self.height = 0
        self.tile_size = 32  # THÊM DÒNG NÀY: Mặc định là 32
        self.pixel_width = 0    
        self.pixel_height = 0   
        self.entities = []
        self.entities_data = []
        self.enemies = []
        self.platforms = []
        self.tiles = []  
        self.bg_color = (0, 0, 0, 255)
        self.start_position = (100, 100)
        self.gravity = GRAVITY

    def load_from_json(self, filename):
        """Đọc file JSON từ game/level/levels/"""
        path = os.path.join("game", "level", "levels", filename)
        if not filename.endswith(".json"):
            path += ".json"
        
        if not os.path.exists(path):
            print(f"[Level] Lỗi: Không thấy file tại {path}")
            return False

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                # Nạp tile_size từ file JSON, nếu không có thì dùng hằng số TILE_SIZE
                self.tile_size = data.get("tile_size", TILE_SIZE)
                
                self.width = data["width"]
                self.height = data["height"]
                self.tiles = data["tiles"]
                self.bg_color = data.get("bg_color", [0, 0, 0, 255])

                self.entities_data = data.get("entities", [])

                # Sử dụng self.tile_size để tính toán
                self.pixel_width = self.width * self.tile_size
                self.pixel_height = self.height * self.tile_size
                
                if "start_position" in data:
                    self.start_position = (data["start_position"]["x"], data["start_position"]["y"])
                return True
        except Exception as e:
            print(f"[Level] Lỗi JSON: {e}")
            return False

    def handle_collision(self, player):
        """Xử lý va chạm với kiểm tra biên an toàn (Tránh IndexError)"""
        player.on_ground = False
        p = player.rect
        
        # Tính toán các ô gạch xung quanh và giới hạn trong phạm vi mảng
        start_col = max(0, p.x // TILE_SIZE)
        end_col = min(self.width - 1, (p.x + p.w) // TILE_SIZE)
        start_row = max(0, p.y // TILE_SIZE)
        end_row = min(self.height - 1, (p.y + p.h) // TILE_SIZE)

        for row in range(start_row, end_row + 1):
            for col in range(start_col, end_col + 1):
                tile_id = self.tiles[row][col]
                if tile_id == 1 or tile_id == 2:
                    tile_rect = sdl2.SDL_Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    if sdl2.SDL_HasIntersection(p, tile_rect):
                        self._resolve_collision(player, tile_rect)
                elif tile_id == 3: # Đụng trúng Lava
                    tile_rect = sdl2.SDL_Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    if sdl2.SDL_HasIntersection(p, tile_rect):
                        if player.invincible_time <= 0:
                            player.take_damage(20, -1 if player.vel_x > 0 else 1)

    def _resolve_collision(self, player, tile):
        p = player.rect
        
        # 1. Tính độ lún
        overlap_x = min(p.x + p.w, tile.x + tile.w) - max(p.x, tile.x)
        overlap_y = min(p.y + p.h, tile.y + tile.h) - max(p.y, tile.y)

        # 2. Xác định trục va chạm chính
        if overlap_x < overlap_y:
            # VA CHẠM NGANG (Tường)
            if p.x + p.w / 2 < tile.x + tile.w / 2: # Chạm tường bên phải
                p.x -= overlap_x
            else: # Chạm tường bên trái
                p.x += overlap_x
            player.pos_x = float(p.x)
            
            # Dừng dash nếu đâm tường
            if hasattr(player, 'is_dashing') and player.is_dashing:
                player.is_dashing = False
                player.vel_x = 0
        else:
            # VA CHẠM DỌC (Sàn/Trần)
            if p.y + p.h / 2 < tile.y + tile.h / 2: # Đứng trên sàn
                p.y -= overlap_y
                player.vel_y = 0
                player.on_ground = True # Bật nhảy được là nhờ dòng này!
            else: # Đụng trần
                p.y += overlap_y
                player.vel_y = 0
            player.pos_y = float(p.y)

    def render(self, renderer, camera):
        """Vẽ map với kiểm tra biên an toàn để tránh IndexError"""
        # Chuyển đổi tọa độ camera sang số nguyên
        camera_x = int(camera.x)
        camera_y = int(camera.y)

        # 1. Vẽ màu nền
        sdl2.SDL_SetRenderDrawColor(renderer, *self.bg_color)
        # (Giả sử bạn có logic clear screen ở đây hoặc trong game.py)

        # 2. Tính toán phạm vi tile cần vẽ (Culling)
        # Đảm bảo start không nhỏ hơn 0 và end không lớn hơn kích thước map
        start_col = max(0, camera_x // TILE_SIZE)
        end_col = min(self.width, (camera_x + SCREEN_WIDTH) // TILE_SIZE + 2)
        
        start_row = max(0, camera_y // TILE_SIZE)
        end_row = min(self.height, (camera_y + SCREEN_HEIGHT) // TILE_SIZE + 2)

        # 3. Vẽ gạch với kiểm tra lỗi mảng
        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                # KIỂM TRA AN TOÀN TRƯỚC KHI TRUY CẬP MẢNG
                if 0 <= row < len(self.tiles) and 0 <= col < len(self.tiles[row]):
                    tile_id = self.tiles[row][col]
                    
                    if tile_id > 0:
                        dst_rect = sdl2.SDL_Rect(
                            col * TILE_SIZE - camera_x,
                            row * TILE_SIZE - camera_y,
                            TILE_SIZE, TILE_SIZE
                        )
                        
                        # Vẽ dựa trên ID
                        if tile_id == 1: # Đất cứng
                            sdl2.SDL_SetRenderDrawColor(renderer, 100, 70, 50, 255)
                            sdl2.SDL_RenderFillRect(renderer, dst_rect)
                        elif tile_id == 2: # Nền tảng
                            sdl2.SDL_SetRenderDrawColor(renderer, 150, 150, 150, 255)
                            sdl2.SDL_RenderFillRect(renderer, dst_rect)
                        elif tile_id == 3: # Dung nham (LAVA)
                            sdl2.SDL_SetRenderDrawColor(renderer, 255, 69, 0, 255) # Màu đỏ cam rực
                            sdl2.SDL_RenderFillRect(renderer, dst_rect)
        self.render_entities(renderer, camera)

    def get_spawn_position(self):
        return self.start_position

    def check_win(self, player):
        return player.rect.x > (self.pixel_width - 100)
    
    def spawn_all_entities(self, game):
        """Khởi tạo tất cả thực thể từ dữ liệu JSON"""
        self.entities.clear()
        self.enemies.clear() # Xóa danh sách quái cũ
        self.platforms = []
        
        for e in self.entities_data:
            etype = e.get("type")
            x, y = e.get("x"), e.get("y")
            
            # --- Xử lý các loại Quái vật ---
            if etype == "goblin":
                goblin = Goblin(game, e["x"], e["y"])
                goblin.type = "goblin" # Để playing.py nhận diện được
                self.entities.append(goblin)
                self.enemies.append(goblin)
                
            elif etype == "skeleton":
                skeleton = Skeleton(game, e["x"], e["y"])
                skeleton.type = "skeleton" # Để playing.py nhận diện được
                self.entities.append(skeleton)
                self.enemies.append(skeleton)

            elif etype in ("fire_bat", "firebat"):
                fire_bat = FireBat(game, e["x"], e["y"])
                fire_bat.type = "fire_bat" # Để playing.py nhận diện được
                self.entities.append(fire_bat)
                self.enemies.append(fire_bat)

            # --- Xử lý các loại Vật phẩm / Platform ---
            elif etype == "platform":
                from game.objects.platform import Platform
                plat = Platform(game, x, y, e.get("w", 128), e.get("h", 32))
                self.entities.append(plat)
                # Phải có dòng này để vòng lặp ở bước 2 tìm thấy platform để vẽ
                if not hasattr(self, 'platforms'): self.platforms = []
                self.platforms.append(plat)

            elif etype == "moving_platform":
                from game.objects.platform import MovingPlatform
                # Thêm tốc độ và hướng từ JSON
                m_plat = MovingPlatform(game, x, y, e.get("w", 128), e.get("h", 20), 
                                        speed=e.get("speed", 2.0))
                self.entities.append(m_plat)
                self.platforms.append(m_plat)
                
            elif etype == "coin":
                from game.entities.collectible import Coin
                self.entities.append(Coin(game, x, y, e.get("value", 5)))
                
            elif etype == "mana":
                from game.entities.collectible import ManaBottle
                mana = ManaBottle(game, x, y, e.get("value", 25))
                self.entities.append(mana)

            elif etype == "checkpoint":
                from game.objects.checkpoint import Checkpoint
                cp = Checkpoint(game, x, y)
                self.entities.append(cp)
                
            # Projectile sẽ được thêm động trong skill_a_fire()
    
    def spawn_enemy(self, enemy_type: str, x: int, y: int):
        """
        Spawn một quái vật tại vị trí (x, y) bất kỳ lúc nào.
        Trả về đối tượng enemy để có thể thao tác thêm (ví dụ: set HP, velocity...).
        """
        from game.entities.enemy import Goblin, Skeleton, FireBat, BossShadowKing
        
        enemy = None
        etype = enemy_type.lower()
        
        if etype == "goblin":
            enemy = Goblin(self.game, x, y)
            enemy.type = "goblin"
        elif etype == "skeleton":
            enemy = Skeleton(self.game, x, y)
            enemy.type = "skeleton"
        elif etype in ("fire_bat", "firebat"):
            enemy = FireBat(self.game, x, y)
            enemy.type = "fire_bat"
        elif etype in ("boss", "shadow_king", "boss_shadow_king"):
            enemy = BossShadowKing(self.game, x, y)
            enemy.type = "boss"
        else:
            print(f"[Level] ❌ Không hỗ trợ spawn enemy loại: {enemy_type}")
            return None
        
        # Thêm vào danh sách quản lý (đã fix bug goblin không vào enemies)
        self.entities.append(enemy)
        if hasattr(self, 'enemies') and enemy not in self.enemies:
            self.enemies.append(enemy)
        
        print(f"[Level] Đã spawn {enemy_type} tại ({x}, {y})")
        return enemy
    
    def spawn_enemies(self, enemies_list: list):
        """
        Spawn nhiều quái cùng lúc (dùng cho wave, khu vực nguy hiểm...).
        Ví dụ: spawn_enemies([("goblin", 1400, 900), ("skeleton", 1550, 900)])
        """
        spawned = []
        for etype, x, y in enemies_list:
            enemy = self.spawn_enemy(etype, x, y)
            if enemy:
                spawned.append(enemy)
        return spawned
    
    def is_solid_at(self, x, y):
        """Kiểm tra có gạch đặc không (cho quái patrol)"""
        col = int(x // TILE_SIZE)
        row = int(y // TILE_SIZE)
        if 0 <= row < len(self.tiles) and 0 <= col < len(self.tiles[row]):
            tile_id = self.tiles[row][col]
            return tile_id in [1, 2]
        return False

    def update_entities(self, delta_time):
        # 1. Update Platform trước (Để logic cưỡi platform mượt hơn)
        for plat in self.platforms:
            plat.update(delta_time)

        # 2. Update các thực thể khác
        from game.objects.checkpoint import Checkpoint # Import để check loại

        for entity in self.entities[:]:
            if hasattr(entity, 'alive') and not entity.alive:
                continue
            
            # --- ĐOẠN FIX CHO CHECKPOINT ---
            if isinstance(entity, Checkpoint):
                # Vì file checkpoint.py của fen nhận player, ta lấy player từ state playing
                player = self.game.states["playing"].player
                if player:
                    entity.update(player) 
            # -------------------------------
            
            elif hasattr(entity, 'update'):
                # Các thực thể khác như Enemy, Coin, Mana vẫn dùng delta_time và level
                entity.update(delta_time, self)

    def render_entities(self, renderer, camera):
        """Vẽ tất cả entities (quái sẽ hiện ở đây)"""
        for entity in self.entities:
            if hasattr(entity, 'alive') and not entity.alive:
                continue
            if hasattr(entity, 'render'):
                entity.render(renderer, camera)