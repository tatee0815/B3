import sdl2
from game.entities.projectile import Projectile
from game.level.level import Level
from game.objects.portal import EndPortal

class PlayingState:
    def __init__(self, game):
        self.game = game
        self.name = "playing"
        self.level = Level(self.game)
        self.is_initialized = False
        self.local_player = None
        self.remote_player = None
        self.sync_timer = 0.0
        self.SYNC_INTERVAL = 0.05
        self.local_at_portal = False
        self.remote_at_portal = False
        self.last_local_portal_state = False
        self.last_remote_portal_state = False
        self.multi_completed = False  # tránh gọi nhiều lần

    @property
    def player(self):
        return self.game.player

    def on_enter(self, **kwargs):
        force_reset = kwargs.get("reset", False)
        menu_continue = kwargs.get("menu_continue", False)
        from_intro = kwargs.get("from_intro", False)

        just_loaded_map = False
        self.multi_completed = False

        # --- ĐỒNG BỘ LEVEL CHO MULTIPLAYER ---
        if self.game.game_mode == "multi":
            from game.entities.player import Player
            from game.entities.princess import Princess
            
            if self.game.network.is_host:
                # 1. HOST LÀ MÁY CHỦ -> LUÔN LÀ KNIGHT
                # Đảm bảo local_player là class Player gốc
                if not type(self.game.player) is Player:
                    self.game.player = Player(self.game)
                self.local_player = self.game.player
                self.local_player.role = "knight"
                
                # Remote player (người chơi bên kia) là Princess
                self.remote_player = Princess(self.game)
                
                self.remote_player.is_remote = True
                self.remote_player.target_x = float(self.remote_player.rect.x)
                self.remote_player.target_y = float(self.remote_player.rect.y)
            else:
                # 2. CLIENT LÀ MÁY KHÁCH -> LUÔN LÀ PRINCESS
                # Đảm bảo local_player là class Princess với bộ skill riêng
                if not isinstance(self.game.player, Princess):
                    self.game.player = Princess(self.game)
                self.local_player = self.game.player
                self.local_player.role = "princess"
                
                # Remote player (máy chủ) là Knight
                self.remote_player = Player(self.game)
                self.remote_player.role = "knight"
        else:
            # Chơi đơn
            self.local_player = self.game.player
            self.remote_player = None

        # --- BƯỚC 1: NẠP DỮ LIỆU ---
        if not self.is_initialized or force_reset or from_intro:
            if force_reset or from_intro:
                self.game.reset_progress()

            level_name = self.game.player_progress["current_level"]
            if self.level.load_from_json(level_name):
                # Always spawn entities so both host and client have the map populated
                self.level.spawn_all_entities(self.game)
                self.is_initialized = True
                just_loaded_map = True

        # --- BƯỚC 2: XỬ LÝ VỊ TRÍ NHÂN VẬT & CHECKPOINT ---
        saved_cp = self.game.player_progress.get("checkpoint")

        if from_intro:
            self.game.player_progress["checkpoint"] = None
            spawn_pos = self.level.get_spawn_position()
            self.player.respawn(spawn_pos)
            self.player.checkpoint_pos = spawn_pos
            self.game.player_progress["checkpoint"] = spawn_pos

        elif menu_continue:
            if saved_cp:
                self.player.respawn(saved_cp)
                self.player.checkpoint_pos = saved_cp
            else:
                spawn_pos = self.level.get_spawn_position()
                self.player.respawn(spawn_pos)
                self.player.checkpoint_pos = spawn_pos
                self.game.player_progress["checkpoint"] = spawn_pos

        elif force_reset or just_loaded_map:
            if saved_cp:
                self.player.respawn(saved_cp)
                self.player.checkpoint_pos = saved_cp
            else:
                spawn_pos = self.level.get_spawn_position()
                self.player.respawn(spawn_pos)
                self.player.checkpoint_pos = spawn_pos
                self.game.player_progress["checkpoint"] = spawn_pos

        if hasattr(self.game, 'camera'):
            self.game.camera.update(self.player)

        if self.game.game_mode == "multi" and self.game.network.is_host:
            entities_data = []

            for e in self.level.entities:
                if hasattr(e, "type"):
                    entities_data.append({
                        "type": getattr(e, "type", "unknown"),
                        "x": e.rect.x,
                        "y": e.rect.y
                    })

            self.game.network.send_data({
                "type": "full_state",
                "entities": entities_data
            })

    def handle_network(self, packets):
        if not packets:
            return
            
        for packet in packets:
            ptype = packet.get("type")
            
            if ptype == "game_sync" and self.remote_player:
                # Cập nhật thông số của người chơi kia
                self.remote_player.target_x = float(packet.get("x", self.remote_player.rect.x))
                self.remote_player.target_y = float(packet.get("y", self.remote_player.rect.y))
                self.remote_player.state = packet.get("state", "idle")
                self.remote_player.facing_right = packet.get("facing", True)
                self.remote_player.hp = packet.get("hp", self.remote_player.hp)
                
                # Cập nhật vị trí quái vật từ Host
                if not self.game.network.is_host and "enemies" in packet:
                    for edata in packet["enemies"]:
                        idx = edata.get("i")
                        if idx is not None and idx < len(self.level.enemies):
                            e = self.level.enemies[idx]
                            e.rect.x = edata["x"]
                            e.rect.y = edata["y"]
                            e.pos_x = float(e.rect.x)
                            e.pos_y = float(e.rect.y)
                            e.alive = edata["a"]
                            if hasattr(e, "direction"):
                                e.direction = edata.get("d", e.direction)
                            if hasattr(e, "hp"):
                                e.hp = edata.get("hp", e.hp)
                
            elif ptype == "chest_opened":
                chest_id = packet["chest_id"]
                for entity in self.level.entities:
                    if hasattr(entity, "rect") and f"{entity.rect.x}_{entity.rect.y}" == chest_id:
                        entity.opened = True
                        break
                        
            elif ptype == "level_change":
                new_level = packet["level"]
                self.game.player_progress["current_level"] = new_level
                self.is_initialized = False
                self.on_enter()
                
            elif ptype == "portal_ready":
                self.remote_at_portal = packet.get("ready", False)

    def update(self, delta_time):
        if not self.player or not self.level:
            return

        # 1. Reset cờ portal đầu mỗi frame (để tránh bị kẹt trạng thái)
        self.local_at_portal = False

        # 2. Cập nhật bản thân (Local) và Level
        self.level.update(delta_time)
        self.level.update_entities(delta_time)
        self.player.update(delta_time, self.level)

        # --- 3. LÀM MƯỢT DI CHUYỂN CỦA REMOTE PLAYER (NỘI SUY - LERP) ---
        if self.remote_player and hasattr(self.remote_player, 'target_x'):
            # Di chuyển mượt 30% quãng đường mỗi khung hình
            self.remote_player.pos_x += (self.remote_player.target_x - self.remote_player.pos_x) * 0.3
            self.remote_player.pos_y += (self.remote_player.target_y - self.remote_player.pos_y) * 0.3
            
            # Khóa tọa độ về số nguyên để render chuẩn
            self.remote_player.rect.x = int(self.remote_player.pos_x)
            self.remote_player.rect.y = int(self.remote_player.pos_y)
            
            # Cập nhật frame hoạt ảnh cho Remote Player
            if hasattr(self.remote_player, 'update_animation'):
                self.remote_player.update_animation(delta_time)

        # 4. Kiểm tra va chạm với Portal (Gom lại thành 1 vòng lặp duy nhất)
        from game.objects.portal import EndPortal
        for entity in self.level.entities:
            if isinstance(entity, EndPortal):
                if sdl2.SDL_HasIntersection(self.player.rect, entity.rect):
                    self.local_at_portal = True
                    break

        # ================= KIỂM TRA ĐIỀU KIỆN QUA MÀN =================
        if self.game.game_mode == "single":
            # Chơi đơn: Qua màn nếu chạm Portal HOẶC hoàn thành nhiệm vụ (Princess)
            if self.local_at_portal or self.level.check_win(self.player):
                self.complete_level_single()

        elif self.game.game_mode == "multi":
            packets = self.game.network.get_packets()
            if packets:
                self.handle_network(packets)
            # --- GỬI TÍN HIỆU ĐỒNG BỘ ĐỊNH KỲ ---
            self.sync_timer += delta_time
            if self.sync_timer >= self.SYNC_INTERVAL:
                self.sync_timer = 0.0
                sync_data = {
                    "type": "game_sync",
                    "x": self.local_player.rect.x,
                    "y": self.local_player.rect.y,
                    "state": self.local_player.state,
                    "facing": self.local_player.facing_right,
                    "hp": self.local_player.hp
                }
                
                # Nếu là Host, gửi thêm dữ liệu quái vật để Client đồng bộ chính xác
                if self.game.network.is_host:
                    enemies_sync = []
                    for i, e in enumerate(self.level.enemies):
                        enemies_sync.append({
                            "i": i,
                            "x": e.rect.x,
                            "y": e.rect.y,
                            "a": e.alive,
                            "d": getattr(e, "direction", 1),
                            "hp": getattr(e, "hp", 0)
                        })
                    sync_data["enemies"] = enemies_sync

                self.game.network.send_data(sync_data)

            # --- ĐỒNG BỘ TRẠNG THÁI PORTAL ---
            if self.local_at_portal != self.last_local_portal_state:
                self.last_local_portal_state = self.local_at_portal
                self.game.network.send_data({
                    "type": "portal_ready",
                    "ready": self.local_at_portal
                })

            # --- CHECK WIN MULTIPLAYER (Đợi cả 2 cùng vào portal) ---
            if not self.multi_completed and self.local_at_portal and self.remote_at_portal:
                print("✅ BOTH PLAYERS AT PORTAL")
                self.multi_completed = True
                self.complete_level_multi()

        # ================= VẬT LÝ VÀ VA CHẠM =================
        
        # 1. Xử lý va chạm platform
        if hasattr(self.level, 'platforms'):
            for plat in self.level.platforms:
                if hasattr(plat, 'resolve_collision'):
                    plat.resolve_collision(self.player, delta_time)

        # 2. Va chạm Player - Enemy
        for enemy in self.level.enemies[:]:
            if enemy.alive and sdl2.SDL_HasIntersection(self.player.rect, enemy.rect):
                knock_dir = -1 if self.player.rect.x < enemy.rect.x else 1
                self.player.take_damage(enemy.damage, knock_dir)
                
                # Logic đẩy người chơi ra khỏi quái để tránh bị dính chặt
                if sdl2.SDL_HasIntersection(self.player.rect, enemy.rect):
                    player_left, player_right = self.player.rect.x, self.player.rect.x + self.player.rect.w
                    player_center_x = player_left + self.player.rect.w // 2
                    
                    enemy_left, enemy_right = enemy.rect.x, enemy.rect.x + enemy.rect.w
                    enemy_center_x = enemy_left + enemy.rect.w // 2
                    
                    if player_center_x < enemy_center_x:
                        self.player.rect.x -= (player_right - enemy_left)
                    else:
                        self.player.rect.x += (enemy_right - player_left)
                        
                    self.player.pos_x = float(self.player.rect.x)
                    
                    if (self.player.facing_right and player_center_x < enemy_center_x) or \
                       (not self.player.facing_right and player_center_x > enemy_center_x):
                        self.player.vel_x = 0

        # 3. Cập nhật Camera đi theo người chơi Local
        if hasattr(self.game, 'camera'):
            self.game.camera.update(self.player)

        # 4. Va chạm Projectile (Đạn/Kỹ năng) với Enemy
        from game.entities.projectile import Projectile
        projectiles = [e for e in self.level.entities if isinstance(e, Projectile)]
        for proj in projectiles[:]:
            if not proj.alive:
                continue
            for enemy in self.level.enemies:
                if enemy.alive and sdl2.SDL_HasIntersection(proj.rect, enemy.rect):
                    enemy.take_damage(proj.damage)
                    enemy.vel_x = proj.direction * 5.0 # Đẩy lùi quái nhẹ
                    proj.die()
                    break

    def complete_level_single(self):
        current_lv = self.game.player_progress.get("current_level", "level1_village")
        self.game.player_progress["coin"] = self.player.gold
        self.game.player_progress["lives"] = self.game.lives
        self.game.player_progress["checkpoint"] = None

        if current_lv == "level1_village":
            self.game.player_progress["current_level"] = "level2_valley"
        elif current_lv == "level2_valley":
            self.game.player_progress["current_level"] = "level3_mountain"
        elif current_lv == "level3_mountain":
            self.game.player_progress["current_level"] = "boss_arena"
        else:
            self.game.change_state("win")
            return
        self.is_initialized = False
        self.game.change_state("playing", reset=False)

    def complete_level_multi(self):
        current_lv = self.game.player_progress.get("current_level", "level1_village")
        # Lưu tiến trình: Dùng chung coin
        self.game.player_progress["coin"] = self.game.player_progress.get("coin", 0)
        self.game.player_progress["checkpoint"] = None

        if current_lv == "level1_village":
            new_level = "level2_valley"
        elif current_lv == "level2_valley":
            new_level = "level3_mountain"
        elif current_lv == "level3_mountain":
            new_level = "boss_arena"
        else:
            self.game.change_state("win")
            return

        self.game.player_progress["current_level"] = new_level
        # Gửi gói tin level_change cho client (nếu là host)
        if self.game.network.is_host:
            self.game.network.send_data({"type": "level_change", "level": new_level})
        self.is_initialized = False
        self.game.change_state("playing", reset=False)

    def render(self, renderer):
        sdl2.SDL_SetRenderDrawColor(renderer, *self.level.bg_color)
        sdl2.SDL_RenderClear(renderer)

        if self.level:
            self.level.render(renderer, self.game.camera)
            if hasattr(self.level, 'platforms'):
                for plat in self.level.platforms:
                    plat.render(renderer, self.game.camera)
            self.level.render_entities(renderer, self.game.camera)

        if self.player:
            self.player.render(renderer, self.game.camera)
        if self.remote_player:
            self.remote_player.render(renderer, self.game.camera)

    def handle_event(self, event):
        if event.type == sdl2.SDL_KEYDOWN:
            scancode = event.key.keysym.scancode
            from game.constants import KEY_BINDINGS_DEFAULT
            if scancode == KEY_BINDINGS_DEFAULT["pause"] or scancode == sdl2.SDL_SCANCODE_ESCAPE:
                self.game.change_state("pause")
                return
            if scancode == KEY_BINDINGS_DEFAULT["interact"]:
                if hasattr(self, 'player'):
                    self.player.interact()
                return

        if self.player:
            self.player.handle_input(event)
        self.game.last_time = sdl2.timer.SDL_GetTicks()

    def on_exit(self):
        pass