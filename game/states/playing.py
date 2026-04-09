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
                if self.game.game_mode == "single" or self.game.network.is_host:
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

    def handle_network(self, packet):
        if not packet:
            return
        if packet.get("type") == "game_sync":
            if self.remote_player:
                self.remote_player.rect.x = packet["x"]
                self.remote_player.rect.y = packet["y"]
                self.remote_player.state = packet["state"]
                self.remote_player.facing_right = packet["facing"]
                self.remote_player.hp = packet["hp"]
                self.remote_player.mana = packet["mana"]
                self.remote_player.gold = packet["gold"]
        elif packet.get("type") == "chest_opened":
            chest_id = packet["chest_id"]
            for entity in self.level.entities:
                if hasattr(entity, "rect") and f"{entity.rect.x}_{entity.rect.y}" == chest_id:
                    entity.opened = True
                    break
        elif packet.get("type") == "level_change":
            new_level = packet["level"]
            self.game.player_progress["current_level"] = new_level
            self.is_initialized = False
            self.on_enter()
        elif packet.get("type") == "portal_ready":
            self.remote_at_portal = packet.get("ready", False)
        elif packet.get("type") == "full_state":
            self.level.entities.clear()
            self.level.enemies.clear()

            for e in packet["entities"]:
                etype = e["type"]
                x, y = e["x"], e["y"]

                # spawn lại đúng object
                if etype == "goblin":
                    from game.entities.enemy import Goblin
                    enemy = Goblin(self.game, x, y)
                    self.level.entities.append(enemy)
                    self.level.enemies.append(enemy)

                elif etype == "coin":
                    from game.entities.collectible import Coin
                    self.level.entities.append(Coin(self.game, x, y))

    def update(self, delta_time):
        if not self.player or not self.level:
            return

        for entity in self.level.entities:
            if isinstance(entity, EndPortal):
                if self.local_player and sdl2.SDL_HasIntersection(self.local_player.rect, entity.rect):
                    self.local_at_portal = True
                    break

        self.level.update(delta_time)
        self.level.update_entities(delta_time)
        self.player.update(delta_time, self.level)

        self.local_at_portal = False

        for entity in self.level.entities:
            if isinstance(entity, EndPortal):
                if sdl2.SDL_HasIntersection(self.player.rect, entity.rect):
                    self.local_at_portal = True
                    print("🔥 PLAYER TOUCHING PORTAL")
                    break

        # ================= SINGLE MODE =================
        if self.game.game_mode == "single":
            if self.local_at_portal:
                print("✅ LEVEL COMPLETE (SINGLE)")
                self.level.is_completed = True

        # ================= MULTIPLAYER =================
        if self.game.game_mode == "multi":
            # 1. Gửi tín hiệu của mình đi (Giữ nguyên code send_data của bạn)
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
                self.game.network.send_data(sync_data)

            # 2. Nhận tín hiệu từ máy kia về
            packets = self.game.network.get_packets()
            for p in packets:
                if p.get("type") == "game_sync" and self.remote_player:
                    # Cập nhật tọa độ và animation của đối phương
                    self.remote_player.rect.x = p.get("x", self.remote_player.rect.x)
                    self.remote_player.rect.y = p.get("y", self.remote_player.rect.y)
                    self.remote_player.state = p.get("state", "idle")
                    self.remote_player.facing_right = p.get("facing", True)
                    self.remote_player.hp = p.get("hp", self.remote_player.hp)
                    
                elif p.get("type") == "portal_ready":
                    self.remote_at_portal = p.get("ready", False)

            # --- SYNC PORTAL ---
            if self.local_at_portal != self.last_local_portal_state:
                self.last_local_portal_state = self.local_at_portal
                self.game.network.send_data({
                    "type": "portal_ready",
                    "ready": self.local_at_portal
                })

            # --- CHECK WIN ---
            if not self.multi_completed and self.local_at_portal and self.remote_at_portal:
                print("✅ BOTH PLAYERS AT PORTAL")
                self.multi_completed = True
                self.complete_level_multi()

        elif self.level.check_win(self.player):
            self.complete_level_single()

        # Xử lý va chạm platform
        if hasattr(self.level, 'platforms'):
            for plat in self.level.platforms:
                if hasattr(plat, 'resolve_collision'):
                    plat.resolve_collision(self.player, delta_time)

        # Va chạm player - enemy
        for enemy in self.level.enemies[:]:
            if enemy.alive and sdl2.SDL_HasIntersection(self.player.rect, enemy.rect):
                knock_dir = -1 if self.player.rect.x < enemy.rect.x else 1
                self.player.take_damage(enemy.damage, knock_dir)
                if sdl2.SDL_HasIntersection(self.player.rect, enemy.rect):
                    player_left = self.player.rect.x
                    player_right = self.player.rect.x + self.player.rect.w
                    player_center_x = self.player.rect.x + self.player.rect.w // 2
                    enemy_left = enemy.rect.x
                    enemy_right = enemy.rect.x + enemy.rect.w
                    enemy_center_x = enemy.rect.x + enemy.rect.w // 2
                    if player_center_x < enemy_center_x:
                        overlap = player_right - enemy_left
                        self.player.rect.x -= overlap
                    else:
                        overlap = enemy_right - player_left
                        self.player.rect.x += overlap
                    self.player.pos_x = float(self.player.rect.x)
                    if (self.player.facing_right and player_center_x < enemy_center_x) or \
                       (not self.player.facing_right and player_center_x > enemy_center_x):
                        self.player.vel_x = 0

        # Camera
        if hasattr(self.game, 'camera'):
            self.game.camera.update(self.player)

        # Projectile va chạm enemy
        projectiles = [e for e in self.level.entities if isinstance(e, Projectile)]
        for proj in projectiles[:]:
            if not proj.alive:
                continue
            for enemy in self.level.enemies:
                if enemy.alive and sdl2.SDL_HasIntersection(proj.rect, enemy.rect):
                    enemy.take_damage(proj.damage)
                    enemy.vel_x = proj.direction * 5.0
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
        # Lưu tiến trình cho cả hai người (thực tế chỉ cần lưu của host, client sẽ nhận level_change)
        self.game.player_progress["players"]["knight"]["coin"] = self.local_player.gold if self.game.network.is_host else self.remote_player.gold
        self.game.player_progress["players"]["princess"]["coin"] = self.remote_player.gold if self.game.network.is_host else self.local_player.gold
        # (tương tự có thể lưu lives, hp, mana... nhưng tạm bỏ qua)
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