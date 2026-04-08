import sdl2
from game.entities.projectile import Projectile
from game.level.level import Level

class PlayingState:
    def __init__(self, game):
        self.game = game
        self.name = "playing"
        self.level = Level(self.game) # Khởi tạo instance Level
        self.is_initialized = False

    @property
    def player(self):
        """Lấy Player từ hệ thống Game chính"""
        return self.game.player

    def on_enter(self, **kwargs):
        force_reset = kwargs.get("reset", False)
        menu_continue = kwargs.get("menu_continue", False)
        from_intro = kwargs.get("from_intro", False)

        just_loaded_map = False

        # --- ĐỒNG BỘ LEVEL CHO MULTIPLAYER ---
        if self.game.game_mode == "multi":
            if self.game.network.is_host:
                lv = self.game.player_progress.get("current_level", "level1_village")
                self.game.network.send_data({"type": "sync_level", "level": lv})
            else:
                # Client chờ nhận level từ Host (Thực tế nên làm qua event, 
                # ở đây tạm gán theo progress chung để tránh lỗi trắng map)
                pass

        # --- BƯỚC 1: NẠP DỮ LIỆU (nếu cần) ---
        if not self.is_initialized or force_reset or from_intro:
            if force_reset or from_intro:
                self.game.reset_progress()

            level_name = self.game.player_progress["current_level"]
            if self.level.load_from_json(level_name):
                self.level.spawn_all_entities(self.game)
                self.is_initialized = True
                just_loaded_map = True

        # --- BƯỚC 2: XỬ LÝ VỊ TRÍ NHÂN VẬT & CHECKPOINT ---
        saved_cp = self.game.player_progress.get("checkpoint")

        if from_intro:
            # Bắt đầu mới: xóa checkpoint, về spawn, lưu spawn làm checkpoint
            self.game.player_progress["checkpoint"] = None
            spawn_pos = self.level.get_spawn_position()
            self.player.respawn(spawn_pos)
            self.player.checkpoint_pos = spawn_pos
            self.game.player_progress["checkpoint"] = spawn_pos

        elif menu_continue:
            # Tiếp tục từ menu: ưu tiên checkpoint, nếu không có thì về spawn và lưu
            if saved_cp:
                self.player.respawn(saved_cp)
                self.player.checkpoint_pos = saved_cp
            else:
                spawn_pos = self.level.get_spawn_position()
                self.player.respawn(spawn_pos)
                self.player.checkpoint_pos = spawn_pos
                self.game.player_progress["checkpoint"] = spawn_pos

        elif force_reset or just_loaded_map:
            # Trường hợp chết/reset trong game hoặc vừa load map (do qua màn)
            if saved_cp:
                # Có checkpoint (do rương hoặc từ trước) -> respawn tại đó
                self.player.respawn(saved_cp)
                self.player.checkpoint_pos = saved_cp
            else:
                # Không có checkpoint (mới qua màn) -> về spawn và lưu
                spawn_pos = self.level.get_spawn_position()
                self.player.respawn(spawn_pos)
                self.player.checkpoint_pos = spawn_pos
                self.game.player_progress["checkpoint"] = spawn_pos

        # --- BƯỚC 3: CẬP NHẬT CAMERA ---
        if hasattr(self.game, 'camera'):
            self.game.camera.update(self.player)
        
    def handle_network(self, packet):
        """Nhận gói tin Level Sync từ Host (Nếu là Client)"""
        if packet.get("type") == "sync_level" and not self.game.network.is_host:
            host_level = packet.get("level")
            if self.game.player_progress["current_level"] != host_level:
                self.game.player_progress["current_level"] = host_level
                self.is_initialized = False 
                self.on_enter() # Reload lại map theo host

    def update(self, delta_time):
        if not self.player or not self.level:
            return

        if self.level:
            self.level.update(delta_time)

        # 1. Update tất cả entities trước (enemy, projectile, moving platform, v.v.)
        self.level.update_entities(delta_time)

        # 2. Update player (di chuyển, gravity, input) – KHÔNG xử lý collision ở đây
        self.player.update(delta_time, self.level)

        # 3. Xử lý va chạm với platform (ưu tiên cao nhất)
        if hasattr(self.level, 'platforms'):
            for plat in self.level.platforms:
                if hasattr(plat, 'resolve_collision'):
                    plat.resolve_collision(self.player, delta_time)

        # 5. Va chạm player - enemy (sau khi vị trí đã ổn định)
        for enemy in self.level.enemies[:]:
            if enemy.alive and sdl2.SDL_HasIntersection(self.player.rect, enemy.rect):
                knock_dir = -1 if self.player.rect.x < enemy.rect.x else 1
                self.player.take_damage(enemy.damage, knock_dir)

                # ---  XỬ LÝ VA CHẠM CỨNG (ĐẨY PLAYER RA, CHẶN DI CHUYỂN) ---
                # Sau khi knockback, kiểm tra lại nếu vẫn còn overlap
                if sdl2.SDL_HasIntersection(self.player.rect, enemy.rect):
                    player_left = self.player.rect.x
                    player_right = self.player.rect.x + self.player.rect.w
                    player_center_x = self.player.rect.x + self.player.rect.w // 2

                    enemy_left = enemy.rect.x
                    enemy_right = enemy.rect.x + enemy.rect.w
                    enemy_center_x = enemy.rect.x + enemy.rect.w // 2

                    # Xác định player đang ở bên trái hay phải enemy
                    if player_center_x < enemy_center_x:
                        # Player bên trái → đẩy player sang trái
                        overlap = player_right - enemy_left
                        self.player.rect.x -= overlap
                    else:
                        # Player bên phải → đẩy player sang phải
                        overlap = enemy_right - player_left
                        self.player.rect.x += overlap

                    self.player.pos_x = float(self.player.rect.x)

                    # Chặn player nếu đang di chuyển về phía enemy
                    if (self.player.facing_right and player_center_x < enemy_center_x) or \
                    (not self.player.facing_right and player_center_x > enemy_center_x):
                        self.player.vel_x = 0

        # 6. Camera bám player
        if hasattr(self.game, 'camera'):
            self.game.camera.update(self.player)

        # 7. Kiểm tra thắng level
        if self.level.check_win(self.player):
            current_lv = self.game.player_progress.get("current_level", "level1_village")
            
            # Sync progress trước khi chuyển
            self.game.player_progress["coin"] = self.player.gold
            self.game.player_progress["lives"] = self.game.lives
            self.game.player_progress["checkpoint"] = None  # ← XÓA CHECKPOINT CŨ KHI CHUYỂN LEVEL

            if current_lv == "level1_village":
                self.game.player_progress["current_level"] = "level2_valley"
                self.is_initialized = False
                self.game.change_state("playing", reset=False)
            elif current_lv == "level2_valley":
                self.game.player_progress["current_level"] = "level3_mountain"
                self.is_initialized = False
                self.game.change_state("playing", reset=False)
            elif current_lv == "level3_mountain":
                self.game.player_progress["current_level"] = "boss_arena"
                self.is_initialized = False
                self.game.change_state("playing", reset=False)
            else:
                self.is_initialized = False
                self.game.change_state("win")

        # 8. Projectile va chạm enemy (để ở cuối cho an toàn)
        projectiles = [e for e in self.level.entities if isinstance(e, Projectile)]
        for proj in projectiles[:]:  # dùng [:] để tránh lỗi modify list khi die
            if not proj.alive: continue
            for enemy in self.level.enemies:
                if enemy.alive and sdl2.SDL_HasIntersection(proj.rect, enemy.rect):
                    enemy.take_damage(proj.damage)
                    enemy.vel_x = proj.direction * 5.0
                    proj.die()
                    break

    def render(self, renderer):
        # Clear screen với màu nền của level
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


        # if hasattr(self, 'test_checkpoint'):
        #     self.test_checkpoint.render(renderer, self.game.camera)

    def handle_event(self, event):
        if event.type == sdl2.SDL_KEYDOWN:
            scancode = event.key.keysym.scancode
            
            # 1. Xử lý Tạm dừng (Dùng Scancode đồng bộ)
            from game.constants import KEY_BINDINGS_DEFAULT
            if scancode == KEY_BINDINGS_DEFAULT["pause"] or scancode == sdl2.SDL_SCANCODE_ESCAPE:
                self.game.change_state("pause")
                return

            # 2. Xử lý Tương tác (Trò chuyện/Mở hòm)
            if scancode == KEY_BINDINGS_DEFAULT["interact"]:
                # Kiểm tra va chạm với Object gần đó
                if hasattr(self, 'player'):
                    self.player.interact() 
                return

        # 3. Chuyển các phím di chuyển/chiến đấu cho Player xử lý
        if self.player:
            self.player.handle_input(event)
        self.game.last_time = sdl2.timer.SDL_GetTicks()

    def on_exit(self):
        pass        