# -*- coding: utf-8 -*-
import random
import sdl2
import json
import os
import ctypes
import sdl2.sdlttf as ttf
from game.constants import TILE_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT, GRAVITY
from game.entities.enemy import Enemy, Goblin, Skeleton, FireBat
from game.entities.collectible import Coin, Collectible, ManaBottle, Heart, Princess
from game.entities.boss_shadow_king import BossShadowKing
from game.objects.breakable import BreakableBox
from game.objects.platform import Platform, MovingPlatform
from game.utils.assets import AssetManager
from game.objects.button import Button
from game.objects.gate import Gate

class Level:
    def __init__(self, game):
        self.game = game
        self.renderer = game.renderer
        
        self.name = ""
        self.width = 0 
        self.height = 0
        self.tile_size = TILE_SIZE
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
        self.bg_layers = []
        self.is_completed = False
        self.buttons = []
        self.gates = []

        self.title_timer = 0.0
        self.title_duration = 10.0  # 10 giây
        self.display_name = ""      # Tên sẽ hiển thị

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
                self.name = data.get("name", "Unknown Area")
                self.display_name = self.name # Lưu tên để hiển thị
                self.title_timer = self.title_duration
                # Nạp tile_size từ file JSON, nếu không có thì dùng hằng số TILE_SIZE
                self.tile_size = data.get("tile_size", TILE_SIZE)
                
                self.width = data["width"]
                self.height = data["height"]
                self.tiles = data["tiles"]
                self.bg_color = data.get("bg_color", [0, 0, 0, 255])
                # --- NẠP CẤU HÌNH BACKGROUND LAYER ---
                self.bg_layers = []
                bg_config = data.get("backgrounds", [])
                
                for bg in bg_config:
                    layer = BackgroundLayer(
                        self.renderer,
                        bg["texture_key"], # Ví dụ: "sky", "mountain"
                        bg["speed"],       # Ví dụ: 0.1, 0.5
                        bg.get("y_offset", 0), # Mặc định Y = 0
                        bg.get("alpha", 255)
                    )
                    self.bg_layers.append(layer)
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

    def update(self, delta_time):
        if self.title_timer > 0:
            self.title_timer -= delta_time

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

    def resolve_world_collision(self, entity):
        """
        Xử lý va chạm giữa một thực thể bất kỳ (Coin, Thùng, Item) với sàn gạch.
        Giúp chúng không bị rơi xuyên map.
        """
        # 1. Xác định phạm vi các ô gạch xung quanh thực thể
        p = entity.rect
        start_col = max(0, p.x // TILE_SIZE)
        end_col = min(self.width - 1, (p.x + p.w) // TILE_SIZE)
        start_row = max(0, p.y // TILE_SIZE)
        end_row = min(self.height - 1, (p.y + p.h) // TILE_SIZE)

        for row in range(start_row, end_row + 1):
            for col in range(start_col, end_col + 1):
                # Kiểm tra nếu ô gạch là vật thể rắn (ID 1 hoặc 2)
                if 0 <= row < len(self.tiles) and 0 <= col < len(self.tiles[row]):
                    tile_id = self.tiles[row][col]
                    if tile_id in [1, 2]:
                        tile_rect = sdl2.SDL_Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                        
                        if sdl2.SDL_HasIntersection(p, tile_rect):
                            # Chỉ xử lý va chạm từ trên xuống (đứng trên sàn)
                            # để các item rơi xuống và nằm yên trên mặt đất
                            overlap_y = min(p.y + p.h, tile_rect.y + tile_rect.h) - max(p.y, tile_rect.y)
                            overlap_x = min(p.x + p.w, tile_rect.x + tile_rect.w) - max(p.x, tile_rect.x)

                            if overlap_y < overlap_x: # Ưu tiên xử lý trục dọc trước cho việc rơi
                                if p.y + p.h / 2 < tile_rect.y + tile_rect.h / 2: # Chạm mặt trên của gạch
                                    p.y -= overlap_y
                                    if hasattr(entity, 'vel_y'): entity.vel_y = 0
                                    if hasattr(entity, 'on_ground'): entity.on_ground = True
                                    entity.pos_y = float(p.y)

    def render(self, renderer, camera):
        """Vẽ map với kiểm tra biên an toàn để tránh IndexError"""
        # Chuyển đổi tọa độ camera sang số nguyên
        camera_x = int(camera.x)
        camera_y = int(camera.y)

        # 1. VẼ CÁC LỚP BACKGROUND LAYER
        for layer in self.bg_layers:
            # Truyền SCREEN_WIDTH, SCREEN_HEIGHT vào (lấy từ constants)
            layer.render(renderer, camera_x, SCREEN_WIDTH, SCREEN_HEIGHT)

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

        if hasattr(self, 'start_position'):
            spawn_x, spawn_y = self.start_position
            # Vẽ một luồng sáng màu lục lam mờ (Cyan) tại điểm spawn
            spawn_rect = sdl2.SDL_Rect(
                int(spawn_x - camera.x), 
                int(spawn_y - camera.y), 
                self.tile_size, self.tile_size * 2
            )
            sdl2.SDL_SetRenderDrawColor(renderer, 0, 255, 255, 100) # (R, G, B, Alpha)
            # Dùng DrawRect (chỉ viền) hoặc FillRect tùy fen
            sdl2.SDL_RenderDrawRect(renderer, spawn_rect)

        self.render_entities(renderer, camera)

        # 3. Vẽ Tiêu đề Map (Thêm vào cuối hàm render)
        if self.title_timer > 0 and self.display_name:
            font = self.game.font
            if font:
                # Tính toán độ mờ (Alpha) mờ dần khi gần hết thời gian
                alpha = 255
                if self.title_timer < 2.0: # 2 giây cuối sẽ mờ dần
                    alpha = int((self.title_timer / 2.0) * 255)
                
                sdl_color = sdl2.SDL_Color(255, 215, 0, alpha)
                
                # Render chữ
                text_surface = ttf.TTF_RenderUTF8_Blended(font, self.display_name.encode('utf-8'), sdl_color)
                if text_surface:
                    text_texture = sdl2.SDL_CreateTextureFromSurface(renderer, text_surface)
                    tw, th = text_surface.contents.w, text_surface.contents.h
                    
                    # Vị trí: Chính giữa màn hình, cách mép trên 100px
                    dst_rect = sdl2.SDL_Rect(
                        (SCREEN_WIDTH // 2) - (tw // 2),
                        100,
                        tw,
                        th
                    )
                    
                    sdl2.SDL_SetTextureAlphaMod(text_texture, alpha)
                    sdl2.SDL_RenderCopy(renderer, text_texture, None, dst_rect)
                    
                    sdl2.SDL_DestroyTexture(text_texture)
                    sdl2.SDL_FreeSurface(text_surface)

    def get_spawn_position(self):
        return self.start_position

    def check_win(self, player):
        return getattr(self, 'is_completed', False)
    
    def spawn_all_entities(self, game):
        """Khởi tạo tất cả thực thể từ dữ liệu JSON"""
        # --- Đảm bảo Host và Client có chung 1 chuỗi random ---
        random.seed(self.name)
        self.is_completed = False # Reset cờ mỗi khi load map
        self.entities.clear()
        self.enemies.clear() # Xóa danh sách quái cũ
        self.platforms = []
        self.buttons.clear()  
        self.gates.clear()
        
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

            # --- NHÓM PLATFORM ---
            elif "platform" in etype:
                p_w = e.get("w", self.tile_size)
                p_h = e.get("h", self.tile_size)
                if etype == "platform":
                    self.platforms.append(Platform(game, x, y, p_w, p_h))
                elif etype == "moving_platform":
                    p_w = e.get("w", self.tile_size)
                    p_h = e.get("h", self.tile_size)
                    p_speed = e.get("speed", 2.0)
                    # Đọc khoảng cách (distance) và hướng (horizontal)
                    p_dist = e.get("distance", 200)
                    p_horiz = e.get("horizontal", True) # Mặc định là di chuyển ngang
                    
                    self.platforms.append(MovingPlatform(
                        game, x, y, p_w, p_h, 
                        speed=p_speed, 
                        distance=p_dist, 
                        is_horizontal=p_horiz
                    ))
                
            # --- NHÓM ITEM THU THẬP ---
            elif etype == "coin":
                self.entities.append(Coin(game, x, y))
            elif etype == "mana":
                self.entities.append(ManaBottle(game, x, y))
            elif etype == "heart":
                self.entities.append(Heart(game, x, y))
            elif etype == "princess":
                self.entities.append(Princess(self.game, x, y))

            # --- NHÓM VẬT THỂ PHÁ HỦY ---
            elif etype == "breakable":
                box_id = f"box_{int(x)}_{int(y)}"
                broken_list = game.player_progress.get("broken_boxes", [])
                if box_id not in broken_list:
                    self.entities.append(BreakableBox(game, x, y, explosive=e.get("explosive", False)))

            # --- NHÓM CỔNG & CHECKPOINT ---
            elif etype == "eportal":
                from game.objects.portal import EndPortal
                self.entities.append(EndPortal(game, x, y))

            elif etype == "chest":
                from game.objects.chest import Chest
                unlock = e.get("unlock", None)
                
                # 1. Tạo instance rương
                new_chest = Chest(game, x, y, unlock_skill=unlock)
                
                # 2. Tạo ID duy nhất cho rương dựa trên tọa độ
                chest_id = f"{x}_{y}"
                
                # 3. Kiểm tra xem ID này có trong danh sách đã mở chưa
                opened_list = game.player_progress.get("opened_chests", [])
                if chest_id in opened_list:
                    new_chest.opened = True # Đánh dấu đã mở ngay từ đầu
                
                self.entities.append(new_chest)
                
            elif etype == "BossShadowKing":
                boss = BossShadowKing(self.game, e['x'], e['y'])  # vị trí tùy level
                self.entities.append(boss)
                self.enemies.append(boss)

            elif etype == "buttons":
                btn = Button(
                    self.game, x, y,
                    gate_id=e.get("gate_id"),
                    w=e.get("w", 32),
                    h=e.get("h", 16)
                )
                self.buttons.append(btn)
                self.entities.append(btn)

            elif etype == "gates":
                gate = Gate(
                    self.game, x, y,
                    w=e.get("w", 64),
                    h=e.get("h", 32),
                    gate_id=e.get("gate_id")
                )
                self.gates.append(gate)
                self.entities.append(gate)
        
        self.spawn_random_collectibles(count=10, types=[Coin, ManaBottle])
        
        # --- Trả lại random tự do cho các xử lý khác sau này ---
        random.seed()
    
    def spawn_enemy(self, enemy_type: str, x: int, y: int):
        """
        Spawn một quái vật tại vị trí (x, y) bất kỳ lúc nào.
        Trả về đối tượng enemy để có thể thao tác thêm (ví dụ: set HP, velocity...).
        """
        
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
        elif etype in ("BossShadowKing"):
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

    def update_entities(self, delta_time):
        player = self.game.player
        if not player: return

        # 1. UPDATE PLATFORMS TRƯỚC (Rất quan trọng)
        # Truyền 'self' (level) để Platform có thể kéo player đi theo logic dx, dy
        for plat in self.platforms:
            if hasattr(plat, 'update'):
                # Truyền self vào để trong MovingPlatform có thể gọi level.game.states...
                plat.update(delta_time, self) 

        # 2. XỬ LÝ VA CHẠM ĐỨNG LÊN PLATFORM
        # Sau khi bục đã di chuyển và kéo player, ta mới khóa vị trí chân player
        for plat in self.platforms:
            plat.resolve_collision(player)

        # 3. UPDATE VÀ XỬ LÝ CÁC ENTITIES KHÁC
        for entity in self.entities[:]:
            if (hasattr(entity, 'alive') and not entity.alive and 
                not getattr(entity, 'is_dead_body', False)) or \
                (hasattr(entity, 'life_time') and entity.life_time <= 0):
                self.entities.remove(entity)
                continue

            # --- A. UPDATE CHUNG (Trọng lực, vị trí...) ---
            if hasattr(entity, 'update'):
                entity.update(delta_time, self)
            
            # --- B. KIỂM TRA LAVA CHO QUÁI ---
            if isinstance(entity, Enemy) and entity.alive and not entity.is_dead_body:
            # Kiểm tra điểm giữa chân enemy (hoặc có thể kiểm tra nhiều điểm)
                tile_x = (entity.rect.x + entity.rect.w // 2) // self.tile_size  # centerx
                tile_y = (entity.rect.y + entity.rect.h) // self.tile_size # lấy ô ngay dưới chân

                if 0 <= tile_x < self.width and 0 <= tile_y < self.height:
                    if self.tiles[tile_y][tile_x] == 3:   # lava
                        entity.die()
                        continue

            # --- C. CHẶN RƠI CHO ITEM VÀ THÙNG ---
            if isinstance(entity, (Collectible, BreakableBox)):
                # Va chạm với gạch (Tiles)
                self.resolve_world_collision(entity)
                
                # Va chạm với Platforms (Để item rớt lên bục di chuyển được)
                for plat in self.platforms:
                    # Tận dụng hàm resolve_collision có sẵn, 
                    # truyền entity vào thay vì player
                    plat.resolve_collision(entity)

            # --- D. XỬ LÝ RIÊNG BIỆT ---
            if isinstance(entity, Collectible):
                if hasattr(entity, 'alive') and not entity.alive:
                    continue
                if sdl2.SDL_HasIntersection(player.rect, entity.rect):
                    entity.on_collect(player)
                    entity.alive = False
                    if entity in self.entities: self.entities.remove(entity)
                    continue

            elif isinstance(entity, BreakableBox):
                if not entity.broken:
                    self.resolve_solid_collision(player, entity)
                    if player.is_attacking and sdl2.SDL_HasIntersection(player.attack_rect, entity.rect):
                        entity.take_damage(1)
                
                if hasattr(entity, 'update'):
                    entity.update(delta_time, self)

            # --- E. QUÁI VẬT VÀ CÁC THỨ CÒN LẠI ---
            elif hasattr(entity, 'update'):
                # Vì Checkpoint đã xử lý ở mục A, ở đây chỉ còn Enemy/Projectiles...
                entity.update(delta_time, self)

        # --- F. BẢO HIỂM RƠI XUYÊN MAP (CHỐNG BUG) ---
        if player.pos_y > self.pixel_height:
            player.pos_y = float(self.pixel_height - player.rect.h)
            player.rect.y = int(player.pos_y)
            player.vel_y = 0
            player.on_ground = True

        for gate in self.gates:
            if gate.solid and sdl2.SDL_HasIntersection(player.rect, gate.rect):
                # Tính độ chồng lấn
                overlap_x = min(player.rect.x + player.rect.w, gate.rect.x + gate.rect.w) - max(player.rect.x, gate.rect.x)
                overlap_y = min(player.rect.y + player.rect.h, gate.rect.y + gate.rect.h) - max(player.rect.y, gate.rect.y)
                
                # Xác định hướng va chạm chính (ưu tiên dọc)
                if overlap_y < overlap_x:
                    # Va chạm dọc
                    if player.rect.y + player.rect.h / 2 < gate.rect.y + gate.rect.h / 2:
                        # Player ở trên gate (đang rơi xuống)
                        player.rect.y = gate.rect.y - player.rect.h
                        player.pos_y = float(player.rect.y)
                        player.vel_y = 0
                        player.on_ground = True
                    else:
                        # Player ở dưới gate (đụng trần)
                        player.rect.y = gate.rect.y + gate.rect.h
                        player.pos_y = float(player.rect.y)
                        player.vel_y = 0
                else:
                    # Va chạm ngang
                    if player.rect.x + player.rect.w / 2 < gate.rect.x + gate.rect.w / 2:
                        player.rect.x = gate.rect.x - player.rect.w
                    else:
                        player.rect.x = gate.rect.x + gate.rect.w
                    player.pos_x = float(player.rect.x)
                    if player.is_dashing:
                        player.is_dashing = False
                        player.vel_x = 0
    
    def resolve_solid_collision(self, player, obstacle):
        """Xử lý va chạm để Player không đi xuyên qua vật thể rắn (thùng)"""
        if sdl2.SDL_HasIntersection(player.rect, obstacle.rect):
            # Tính toán khoảng cách chồng lấp (overlap)
            overlap_top = (player.rect.y + player.rect.h) - obstacle.rect.y
            overlap_bottom = (obstacle.rect.y + obstacle.rect.h) - player.rect.y
            overlap_left = (player.rect.x + player.rect.w) - obstacle.rect.x
            overlap_right = (obstacle.rect.x + obstacle.rect.w) - player.rect.x

            # Tìm hướng va chạm nhỏ nhất để đẩy player ra
            min_overlap = min(overlap_top, overlap_bottom, overlap_left, overlap_right)

            if min_overlap == overlap_top and player.vel_y > 0:
                player.rect.y -= overlap_top
                player.pos_y = float(player.rect.y)
                player.vel_y = 0
                player.on_ground = True
            elif min_overlap == overlap_bottom and player.vel_y < 0:
                player.rect.y += overlap_bottom
                player.pos_y = float(player.rect.y)
                player.vel_y = 0
            elif min_overlap == overlap_left:
                player.rect.x -= overlap_left
                player.pos_x = float(player.rect.x)
            elif min_overlap == overlap_right:
                player.rect.x += overlap_right
                player.pos_x = float(player.rect.x)

    def is_solid_at(self, x, y):
        # Chuyển tọa độ pixel thành tọa độ tile
        tile_x = int(x // self.tile_size)
        tile_y = int(y // self.tile_size)

        if tile_x < 0 or tile_x >= self.width or tile_y < 0 or tile_y >= self.height:
            return True 

        tile_value = self.tiles[tile_y][tile_x]
        return tile_value >= 1

    def render_entities(self, renderer, camera):
        """Vẽ tất cả entities theo thứ tự Z-Index để đảm bảo tính thống nhất"""
        sorted_entities = sorted(self.entities, key=lambda e: getattr(e, 'z_index', 1))
        
        for entity in sorted_entities:
            if (hasattr(entity, 'alive') and not entity.alive and 
                not getattr(entity, 'is_dead_body', False)):
                continue
            
            if hasattr(entity, 'render'):
                entity.render(renderer, camera)

    def spawn_random_collectibles(self, count=5, types=None):
        """
        Spawn ngẫu nhiên collectible trên mặt đất (tile rắn ID 1 hoặc 2),
        đảm bảo không gian phía trên ô đất là trống (không có tile rắn).
        - count: số lượng item muốn spawn
        - types: list các class collectible (mặc định: [Coin, Heart, ManaBottle])
        Trả về số lượng đã spawn thành công.
        """
        if types is None:
            types = [Coin, Heart, ManaBottle]

        # Thu thập tất cả ô đất (tile rắn) có thể spawn phía trên
        ground_tiles = []
        for row in range(self.height):
            for col in range(self.width):
                if self.tiles[row][col] in (1, 2):
                    ground_tiles.append((col, row))

        if not ground_tiles:
            print("[Level] Không có ô đất nào để spawn collectible!")
            return 0

        spawned = 0
        attempts = 0
        max_attempts = count * 50  # tăng lên để có nhiều cơ hội tìm ô hợp lệ

        while spawned < count and attempts < max_attempts:
            attempts += 1
            col, row = random.choice(ground_tiles)
            item_class = random.choice(types)

            # Kích thước mỗi loại item (dựa trên định nghĩa trong collectible.py)
            if item_class == Coin:
                w, h = 20, 20
            elif item_class == Heart:
                w, h = 22, 20
            elif item_class == ManaBottle:
                w, h = 24, 28
            else:
                w, h = 24, 24  # fallback

            # Tính tọa độ spawn (căn giữa ô và đặt trên mặt đất)
            x = col * self.tile_size + (self.tile_size - w) // 2
            y = row * self.tile_size - h

            # Kiểm tra không vượt ra ngoài map
            if x < 0 or x + w > self.pixel_width or y < 0:
                continue

            # --- KIỂM TRA KHÔNG GIAN PHÍA TRÊN ---
            # Xác định các dòng tile mà item chiếm (từ trên cùng đến ngay trên ô đất)
            top_row = y // self.tile_size
            # Nếu top_row < 0 (item nhô lên trên map) -> bỏ qua
            if top_row < 0:
                continue

            space_ok = True
            # Kiểm tra tất cả các dòng từ top_row đến row-1
            for r in range(top_row, row):
                # Nếu có bất kỳ tile rắn nào (ID >=1) thì không spawn được
                if self.tiles[r][col] >= 1:
                    space_ok = False
                    break

            if not space_ok:
                continue

            # Tạo item và thêm vào danh sách entities
            item = item_class(self.game, x, y)
            self.entities.append(item)
            spawned += 1

        return spawned

class BackgroundLayer:
    def __init__(self, renderer, texture_key, scroll_speed, y_offset=0, alpha=255):
        path = AssetManager.BACKGROUND_ASSETS.get(texture_key)
        if path:
            self.texture = AssetManager.load_texture(path, renderer)
        else:
            print(f"[BG] Warning: Không tìm thấy key {texture_key}!")
            self.texture = None
            
        self.scroll_speed = scroll_speed 
        self.y_offset = y_offset

        self.alpha = alpha
        
        if self.texture:
            # Lấy kích thước ảnh gốc
            w = ctypes.c_int(0)
            h = ctypes.c_int(0)
            sdl2.SDL_QueryTexture(self.texture, None, None, ctypes.byref(w), ctypes.byref(h))
            self.w = w.value
            self.h = h.value
        else:
            self.w = self.h = 0

    def render(self, renderer, camera_x, screen_w, screen_h):
        if not self.texture or self.w <= 0: 
            return
        
        sdl2.SDL_SetTextureAlphaMod(self.texture, self.alpha)

        start_x = int(-camera_x * self.scroll_speed) % self.w
        
        num_tiles = (screen_w // self.w) + 2
        for i in range(-1, num_tiles):
            dstrect = sdl2.SDL_Rect(
                start_x + i * self.w,
                self.y_offset,
                self.w,
                screen_h 
            )
            sdl2.SDL_RenderCopy(renderer, self.texture, None, dstrect)