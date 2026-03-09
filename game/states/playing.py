"""
State Playing - Trạng thái chơi game chính
Đã thay đổi: Không còn Game Over, thay bằng respawn + lives + deaths
"""

from game.constants import (
    GRAVITY, PLAYER_MAX_HP, MAX_LIVES,
    RESPAWN_AT_LEVEL_START_WHEN_NO_LIVES
)


class PlayingState:
    def __init__(self, game):
        self.game = game
        self.name = "playing"
        
        self.player = None
        self.level = None
        self.hud = self.game.hud

    def on_enter(self, **kwargs):
        print(f"Đang chơi level: {self.game.player_progress['current_level']}")
        
        from game.level.loader import load_level_from_json
        level_name = kwargs.get("level", self.game.player_progress["current_level"])
        self.level = load_level_from_json(level_name, self.game)
        
        from game.entities.player import Player
        self.player = Player(self.game)
        
        # Spawn tại vị trí checkpoint hoặc start
        spawn_pos = self.level.get_spawn_position()
        self.player.rect.x = spawn_pos[0]
        self.player.rect.y = spawn_pos[1]
        self.player.hp = PLAYER_MAX_HP

        self.game.camera.reset()

    def handle_event(self, event):
        if self.player:
            self.player.handle_input(event)

    def update(self, delta_time):
        if not self.player or not self.level:
            return

        self.player.update(delta_time, self.level)
        for entity in self.level.entities[:]:  # copy list để tránh lỗi khi remove
            if isinstance(entity, Collectible):
                entity.update(delta_time, self.level)

        # Update các entity khác
        for entity in self.level.entities:
            if hasattr(entity, "update"):
                entity.update(delta_time)

        # === XỬ LÝ KHI CHẾT (LOGIC MỚI) ===
        if self.player.hp <= 0:
            self._handle_player_death()

        # Check thắng level
        if self.level.check_win(self.player):
            self.game.change_state("win")

    def _handle_player_death(self):
        """Xử lý chết: trừ mạng, tăng deaths, respawn"""
        self.game.deaths += 1
        self.game.player_progress["total_deaths"] += 1
        
        self.game.lives -= 1
        print(f"Chết lần {self.game.deaths} | Còn {self.game.lives} mạng")

        if self.game.lives > 0:
            # Còn mạng → respawn tại checkpoint gần nhất
            spawn_pos = self.level.get_last_checkpoint_position()
            self.player.respawn(spawn_pos)          # bạn sẽ viết hàm này trong player.py
            self.player.hp = PLAYER_MAX_HP
        else:
            # Hết mạng → reset 5 mạng và respawn tại đầu level
            self.game.lives = MAX_LIVES
            spawn_pos = self.level.get_start_position()
            self.player.respawn(spawn_pos)
            self.player.hp = PLAYER_MAX_HP
            print("Hết mạng! Đã reset 5 mạng và quay về đầu level.")

    def render(self, renderer):
        self.level.render(renderer, self.game.camera)
        self.player.render(renderer, self.game.camera)
        
        for entity in self.level.entities:
            if hasattr(entity, "render"):
                entity.render(renderer, self.game.camera)