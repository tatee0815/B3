import sdl2
import os
from game.entities.projectile import Projectile
from game.level.level import Level

class PlayingState:
    def __init__(self, game):
        self.game = game
        self.name = "playing"
        self.player = None
        self.level = Level(self.game) # Khởi tạo instance Level
        self.is_initialized = False

    def on_enter(self, **kwargs):
        force_reset = kwargs.get("reset", False)
        menu_continue = kwargs.get("menu_continue", False)
        from_intro = kwargs.get("from_intro", False)
        
        # Nếu chọn "Bắt đầu mới" hoặc chưa khởi tạo, tiến hành nạp lại từ đầu
        if from_intro or not self.is_initialized or force_reset:
            
            if force_reset:
                self.game.reset_progress()
            
            level_name = self.game.player_progress["current_level"]
            
            if self.level.load_from_json(level_name):
                from game.entities.player import Player
                self.player = Player(self.game)
                
                # Spawn tại vị trí gốc của level (KHÔNG dùng checkpoint)
                spawn_pos = self.level.get_spawn_position()
                self.player.rect.x, self.player.rect.y = spawn_pos
                self.player.pos_x, self.player.pos_y = float(spawn_pos[0]), float(spawn_pos[1])
                self.player.vel_x = 0
                self.player.vel_y = 0
                
                self.level.spawn_all_entities(self.game)
                self.is_initialized = True

                # Đảm bảo checkpoint bị xóa khi đi qua Intro (tránh lặp lỗi cũ)
                self.game.player_progress["checkpoint"] = None

                # Camera reset ngay
                if hasattr(self.game, 'camera'):
                    self.game.camera.reset()
            return   # ← Kết thúc block để tránh chạy code phía dưới

        # === TIẾP TỤC TỪ MENU (có checkpoint) ===
        if menu_continue and self.player and self.game.player_progress.get("checkpoint") is not None:
            checkpoint_pos = self.game.player_progress["checkpoint"]
            self.player.respawn(checkpoint_pos)
            self.player.checkpoint_pos = checkpoint_pos
            if hasattr(self.game, 'camera'):
                self.game.camera.reset()
            return

        # === Camera điều chỉnh bình thường (trường hợp khác) ===
        if self.is_initialized and not force_reset and not menu_continue:
            if hasattr(self.game, 'camera'):
                self.game.camera.x = self.player.rect.x - self.game.camera.width // 2
                self.game.camera.y = self.player.rect.y - self.game.camera.height // 2
                self.game.camera.update(self.player)
        
    def update(self, delta_time):
        if not self.player or not self.level:
            return

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
                
                # Enemy bật lùi nhẹ
                enemy.direction *= -1
                enemy.vel_x = -knock_dir * 4.0
                enemy.pos_x += enemy.vel_x * 5  # đẩy xa thêm tí cho đẹp

        # 6. Camera bám player
        if hasattr(self.game, 'camera'):
            self.game.camera.update(self.player)

        # 7. Kiểm tra thắng level
        if self.level.check_win(self.player):
            current_lv = self.game.player_progress.get("current_level", "level1_forest")
            
            # Sync progress trước khi chuyển
            self.game.player_progress["coin"] = self.player.gold
            self.game.player_progress["lives"] = self.game.lives
            self.game.player_progress["checkpoint"] = None  # ← XÓA CHECKPOINT CŨ KHI CHUYỂN LEVEL

            if current_lv == "level1_forest":
                print(">>> Chuyển sang Level 2: Hang Đá Lửa")
                self.game.player_progress["current_level"] = "level2_lava"
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