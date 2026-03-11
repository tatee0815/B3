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
        # from game.objects.checkpoint import Checkpoint
        # self.test_checkpoint = Checkpoint(self.game, 500, 350)
        
        # Nếu chọn "Bắt đầu mới" hoặc chưa khởi tạo, tiến hành nạp lại từ đầu
        if not self.is_initialized or force_reset:
            
            # QUAN TRỌNG: Reset dữ liệu trong class Game trước
            if force_reset:
                self.game.reset_progress()
            
            # Sau đó mới nạp Level và Player
            level_name = self.game.player_progress["current_level"]
            
            if self.level.load_from_json(level_name):
                from game.entities.player import Player
                # Khi khởi tạo Player(self.game), nó sẽ đọc HP từ 
                # constants hoặc từ self.game.player_progress đã được reset
                self.player = Player(self.game)
                
                # Reset các thông số vật lý
                spawn_pos = self.level.get_spawn_position()
                self.player.rect.x, self.player.rect.y = spawn_pos
                self.player.pos_x, self.player.pos_y = float(spawn_pos[0]), float(spawn_pos[1])
                self.player.vel_x = 0
                self.player.vel_y = 0
                
                self.level.spawn_all_entities(self.game)
                self.is_initialized = True
            return # Kết thúc hàm sau khi đã xử lý reset hoặc nạp mới
                
        # Nếu là "Tiếp tục" và đã có player, chỉ cần đưa về checkpoint
        if menu_continue:
            if self.player:
                self.player.respawn(self.player.checkpoint_pos)
                # Reset camera để tránh bị giật hình
                if hasattr(self.game, 'camera'):
                    self.game.camera.reset()
            return

        if self.is_initialized and not force_reset:
            if hasattr(self.game, 'camera'):
                # Đặt camera ngay tại tâm player thay vì gọi reset() về 0
                self.game.camera.x = self.player.rect.x - self.game.camera.width // 2
                self.game.camera.y = self.player.rect.y - self.game.camera.height // 2
                # Ràng buộc lại để không vượt biên map ngay từ frame đầu
                self.game.camera.update(self.player)
        

    def update(self, delta_time):
        if not self.player or not self.level:
            return

        # Player update xử lý di chuyển và va chạm thông qua level.handle_collision
        self.player.update(delta_time, self.level)

        self.level.update_entities(delta_time)

        for enemy in self.level.enemies[:]:
            if enemy.alive and sdl2.SDL_HasIntersection(self.player.rect, enemy.rect):
                # Xác định hướng bật lùi
                knock_dir = -1 if self.player.rect.x < enemy.rect.x else 1
                self.player.take_damage(enemy.damage, knock_dir)   # ← Gọi hàm mới
                
                # Quái cũng bật lùi nhẹ (tăng tính chân thực)
                enemy.direction *= -1
                enemy.vel_x = -knock_dir * 4.0
                enemy.pos_x += enemy.vel_x * 5
        
        # Camera bám theo player
        if hasattr(self.game, 'camera'):
            self.game.camera.update(self.player)

        if self.player.is_attacking:
            for enemy in self.level.enemies:
                # Giả sử Enemy có rect và còn sống
                if enemy.alive :
                    if sdl2.SDL_HasIntersection(self.player.attack_rect, enemy.rect):
                        # Gây sát thương cho quái
                        enemy.take_damage(self.player.attack_damage)
                        # Kích hoạt bật lùi cho nhân vật
                        self.player.apply_recoil()

        if self.level.check_win(self.player):
            self.is_initialized = False
            self.game.change_state("win")

        projectiles = [e for e in self.level.entities if isinstance(e, Projectile)]

        for proj in projectiles:
            if not proj.alive: continue
            for enemy in self.level.enemies:
                if enemy.alive and sdl2.SDL_HasIntersection(proj.rect, enemy.rect):
                    # Gây sát thương và đẩy lùi nhẹ quái
                    enemy.take_damage(proj.damage)
                    enemy.vel_x = proj.direction * 5.0
                    
                    # Đạn chạm quái thì tan biến luôn
                    proj.die()
                    break

        # if hasattr(self, 'test_checkpoint') and self.player:
        #     self.test_checkpoint.update(self.player)

    def render(self, renderer):
        # Clear screen với màu nền của level
        sdl2.SDL_SetRenderDrawColor(renderer, *self.level.bg_color)
        sdl2.SDL_RenderClear(renderer)
        
        if self.level:
            self.level.render(renderer, self.game.camera)
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
                # Kiểm tra va chạm với NPC hoặc Object gần đó
                if hasattr(self, 'player'):
                    self.player.interact() # Giả định player có hàm interact()
                return

        # 3. Chuyển các phím di chuyển/chiến đấu cho Player xử lý
        if self.player:
            self.player.handle_input(event)
        self.game.last_time = sdl2.timer.SDL_GetTicks()

    def on_exit(self):
        pass        