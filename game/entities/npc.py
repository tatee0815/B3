from .base import Entity


class NPC(Entity):
    def __init__(self, game, x, y):
        super().__init__(game, x, y, 32, 48)
        self.color = (200, 150, 100, 255)  # màu da

    def interact(self, player):
        # Ví dụ: trao double jump
        player.game.player_progress["double_jump"] = True
        player.has_double_jump = True
        print("Nhận được Double Jump!")