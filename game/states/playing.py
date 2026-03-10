import sdl2
import os
from game.level.level import Level

class PlayingState:
    def __init__(self, game):
        self.game = game
        self.name = "playing"
        self.player = None
        self.level = Level(self.game) # Khởi tạo instance Level

    def on_enter(self, **kwargs):
        level_name = kwargs.get("level", self.game.player_progress.get("current_level", "level1_forest"))
        print(f"[PlayingState] Nạp: {level_name}")

        if self.level.load_from_json(level_name):
            from game.entities.player import Player
            self.player = Player(self.game)

            # Đặt player tại vị trí bắt đầu của map
            spawn_pos = self.level.get_spawn_position()
            self.player.rect.x = spawn_pos[0]
            self.player.rect.y = spawn_pos[1]

            self.level.spawn_all_entities(self.game)
            
            if hasattr(self.game, 'camera'):
                self.game.camera.reset()
        else:
            print("Lỗi nạp dữ liệu màn chơi!")

    def update(self, delta_time):
        if not self.player or not self.level:
            return

        # Player update xử lý di chuyển và va chạm thông qua level.handle_collision
        self.player.update(delta_time, self.level)
        
        # Camera bám theo player
        if hasattr(self.game, 'camera'):
            self.game.camera.update(self.player)

        if self.level.check_win(self.player):
            self.game.change_state("win")

    def render(self, renderer):
        # Clear screen với màu nền của level
        sdl2.SDL_SetRenderDrawColor(renderer, *self.level.bg_color)
        sdl2.SDL_RenderClear(renderer)
        
        if self.level:
            self.level.render(renderer, self.game.camera)
        if self.player:
            self.player.render(renderer, self.game.camera)

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

    def on_exit(self):
        print("Thoát PlayingState")