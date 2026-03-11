import sdl2
import os
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
            print("[PlayingState] Đang tiến hành RESET màn chơi...")
            
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
                print("[PlayingState] Tiếp tục từ Menu: Respawn về Checkpoint.")
                self.player.respawn(self.player.checkpoint_pos)
                # Reset camera để tránh bị giật hình
                if hasattr(self.game, 'camera'):
                    self.game.camera.reset()
            return

        if self.is_initialized and not force_reset:
            print("[PlayingState] Tiếp tục tại vị trí hiện tại.")
            return # Thoát hàm sớm để không chạy logic respawn bên dưới

        # Reset camera để nhìn vào nhân vật ở vị trí mới
        

    def update(self, delta_time):
        if not self.player or not self.level:
            return

        # Player update xử lý di chuyển và va chạm thông qua level.handle_collision
        self.player.update(delta_time, self.level)
        
        # Camera bám theo player
        if hasattr(self.game, 'camera'):
            self.game.camera.update(self.player)

        if self.level.check_win(self.player):
            self.is_initialized = False
            self.game.change_state("win")

        # if hasattr(self, 'test_checkpoint') and self.player:
        #     self.test_checkpoint.update(self.player)

    def render(self, renderer):
        # Clear screen với màu nền của level
        sdl2.SDL_SetRenderDrawColor(renderer, *self.level.bg_color)
        sdl2.SDL_RenderClear(renderer)
        
        if self.level:
            self.level.render(renderer, self.game.camera)
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