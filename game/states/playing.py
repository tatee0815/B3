"""
State Playing - Trạng thái chơi chính (level, player, enemies, collision...)
"""

from game.constants import GRAVITY


class PlayingState:
    def __init__(self, game):
        self.game = game
        self.name = "playing"

        self.player = None
        self.level = None
        self.hud = self.game.hud

    def on_enter(self, **kwargs):
        print("Bắt đầu chơi level:", self.game.player_progress["current_level"])

        # Load level từ json (sẽ implement loader sau)
        from game.level.loader import load_level_from_json
        level_name = kwargs.get("level", self.game.player_progress["current_level"])
        self.level = load_level_from_json(level_name, self.game)

        # Khởi tạo player
        from game.entities.player import Player
        self.player = Player(self.game)

        # Spawn tại vị trí checkpoint hoặc start
        spawn_pos = self.level.get_spawn_position()
        self.player.rect.x = spawn_pos[0]
        self.player.rect.y = spawn_pos[1]
        self.player.hp = 3  # ví dụ

        self.game.camera.reset()

    def on_exit(self):
        print("Thoát playing state")

    def handle_event(self, event):
        if self.player:
            self.player.handle_input(event)

    def update(self, delta_time):
        if not self.player or not self.level:
            return

        # Update player
        self.player.update(delta_time, self.level)

        # Update entities khác
        for entity in self.level.entities:
            if hasattr(entity, "update"):
                entity.update(delta_time)

        # Update platforms di chuyển (nếu có)
        for plat in self.level.platforms:
            if hasattr(plat, "update"):
                plat.update(delta_time, self.level)

        # Check thắng level
        if self.level.check_win(self.player):
            self.game.change_state("win")

        # Check chết (đã xử lý trong player hoặc level)
        # ...

    def render(self, renderer):
        # Low-level: vẽ nền level (ví dụ màu xanh lá cho rừng)
        sdl2.SDL_SetRenderDrawColor(renderer, 80, 140, 60, 255)
        sdl2.SDL_RenderClear(renderer)

        # Render level (tiles, platforms, entities)
        if self.level:
            self.level.render(renderer, self.game.camera)

        # Render player
        if self.player:
            self.player.render(renderer, self.game.camera)

        # HUD sẽ được render ở cấp Game sau state