# -*- coding: utf-8 -*-
import sdl2
import json
import os
from game.constants import TILE_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT, GRAVITY

class Level:
    def __init__(self, game):
        self.game = game
        self.renderer = game.renderer
        
        self.name = ""
        self.width = 0          # Số lượng tile ngang
        self.height = 0         # Số lượng tile dọc
        self.pixel_width = 0    
        self.pixel_height = 0   
        self.entities = []       # Các thực thể trong level (nếu có)
        self.entities_data = []  # Dữ liệu thô từ JSON để khởi tạo thực thể sau này
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
                self.width = data["width"]
                self.height = data["height"]
                self.tiles = data["tiles"]
                self.pixel_width = self.width * TILE_SIZE
                self.pixel_height = self.height * TILE_SIZE
                
                self.entities_data = data.get("entities", [])
                self.entities = []  # sẽ spawn sau

                sp = data.get("start_position", {"x": 100, "y": 100})
                self.start_position = (sp["x"], sp["y"])
                self.bg_color = tuple(data.get("bg_color", [30, 30, 30, 255]))
                self.gravity = data.get("gravity", GRAVITY)
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
                if self.tiles[row][col] == 1:
                    tile_rect = sdl2.SDL_Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    if sdl2.SDL_HasIntersection(p, tile_rect):
                        self._resolve_collision(player, tile_rect)

    def _resolve_collision(self, player, tile):
        p = player.rect
        
        # TÍNH TOÁN SAI LỆCH (Overlap)
        overlap_x = min(p.x + p.w, tile.x + tile.w) - max(p.x, tile.x)
        overlap_y = min(p.y + p.h, tile.y + tile.h) - max(p.y, tile.y)

        # Ưu tiên xử lý va chạm theo trục có độ lún nhỏ hơn (giảm thiểu kẹt biên)
        if overlap_x > overlap_y:
            # Va chạm dọc (Y)
            if player.vel_y > 0 and p.y < tile.y: # Rơi xuống
                p.y = tile.y - p.h
                player.pos_y = float(p.y)
                player.vel_y = 0
                player.on_ground = True
            elif player.vel_y < 0 and p.y > tile.y: # Nhảy đụng trần
                p.y = tile.y + tile.h
                player.pos_y = float(p.y)
                player.vel_y = 0
        else:
            # Va chạm ngang (X) - Chỉ xử lý khi player thực sự đang di chuyển ngang
            if player.vel_x > 0 and p.x < tile.x: # Chạm tường phải
                p.x = tile.x - p.w
                player.pos_x = float(p.x)
            elif player.vel_x < 0 and p.x > tile.x: # Chạm tường trái
                p.x = tile.x + tile.w
                player.pos_x = float(p.x)

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

    def get_spawn_position(self):
        return self.start_position

    def check_win(self, player):
        return player.rect.x > (self.pixel_width - 100)
    
    def spawn_all_entities(self, game):
        """Tạo các entity từ dữ liệu JSON (gọi sau khi load level)"""
        self.entities.clear()
        
        for e in self.entities_data:
            etype = e.get("type")
            
            if etype == "player_spawn":
                continue  # đã xử lý riêng trong PlayingState
                
            elif etype == "goblin":
                from game.entities.enemy import Goblin  # bạn sẽ tạo file này sau
                goblin = Goblin(game, e["x"], e["y"])
                self.entities.append(goblin)
                
            elif etype == "platform":
                from game.objects.platform import Platform
                plat = Platform(game, e["x"], e["y"], e.get("w", 128), e.get("h", 32))
                self.entities.append(plat)
                
            elif etype == "oneway_platform":
                from game.objects.platform import OneWayPlatform
                plat = OneWayPlatform(game, e["x"], e["y"], e.get("w", 96), e.get("h", 32))
                self.entities.append(plat)
                
            elif etype == "breakable":
                from game.objects.breakable import BreakableBox
                brk = BreakableBox(game, e["x"], e["y"])
                self.entities.append(brk)
                
            elif etype == "coin":
                from game.entities.collectible import Coin
                coin = Coin(game, e["x"], e["y"], e.get("value", 5))
                self.entities.append(coin)
                
            elif etype == "heart":
                from game.entities.collectible import Heart
                heart = Heart(game, e["x"], e["y"])
                self.entities.append(heart)
                
            elif etype == "checkpoint":
                from game.objects.checkpoint import Checkpoint
                cp = Checkpoint(game, e["x"], e["y"])
                self.entities.append(cp)
                
            elif etype == "mana":
                from game.entities.collectible import ManaBottle
                mana = ManaBottle(game, e["x"], e["y"], e.get("value", 25))
                self.entities.append(mana)
                
            # Projectile sẽ được thêm động trong skill_a_fire()