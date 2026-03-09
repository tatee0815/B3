"""
HUD - Heads-Up Display: hiển thị thông tin realtime khi chơi
"""

import sdl2
import sdl2.ext
from game.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    PLAYER_MAX_HP, MANA_MAX,
    MAX_LIVES, COLORS
)


class HUD:
    def __init__(self, game):
        self.game = game
        
        # Cache một số texture nếu dùng icon (sau này load từ assets)
        self.heart_full = None   # sẽ load icon tim
        self.heart_empty = None
        self.coin_icon = None
        
        # Font fallback (sẽ dùng sdl2.ext.FontManager sau khi có font)
        # tạm thời dùng text đơn giản (sau này thay bằng font pixel)

    def render(self, renderer):
        player = self.game.states["playing"].player
        if not player:
            return
        
        # Vị trí HUD (góc trên trái và phải)
        padding = 20
        
        # --- Trái: HP (tim) ---
        heart_x = padding
        heart_y = padding
        for i in range(PLAYER_MAX_HP):
            color = COLORS["red"] if i < player.hp else COLORS["gray"]
            # Icon tim fallback (vuông nhỏ)
            renderer.fill(color, (heart_x + i*40, heart_y, 32, 32))
            # Sau này: renderer.copy(self.heart_full if i < player.hp else self.heart_empty, ...)

        # --- Phải: Mana bar ---
        mana_x = SCREEN_WIDTH - padding - 200
        mana_y = padding
        # Thanh nền
        renderer.fill(COLORS["mana_empty"], (mana_x, mana_y, 200, 20))
        # Thanh mana hiện tại
        mana_width = int((player.mana / MANA_MAX) * 200)
        renderer.fill(COLORS["mana_bar"], (mana_x, mana_y, mana_width, 20))
        
        # Text mana (số)
        mana_text = f"Mana: {int(player.mana)}/{MANA_MAX}"
        # self.game.font.render(renderer, mana_text, (mana_x, mana_y + 30), color=COLORS["white"])

        # --- Dưới: Vàng, Lives, Deaths ---
        bottom_y = SCREEN_HEIGHT - padding - 40
        
        gold_text = f"Vàng: {player.gold}"
        # self.game.font.render(renderer, gold_text, (padding, bottom_y), color=COLORS["yellow"])

        lives_text = f"Mạng: {self.game.lives}/{MAX_LIVES}"
        # self.game.font.render(renderer, lives_text, (padding + 150, bottom_y), color=COLORS["white"])

        deaths_text = f"Chết: {self.game.player_progress['total_deaths']}"
        # self.game.font.render(renderer, deaths_text, (padding + 300, bottom_y), color=COLORS["red"])

        # Timer (thời gian chơi hoặc countdown nếu có)
        timer_text = f"Thời gian: {int(self.game.game_time)}s"
        # self.game.font.render(renderer, timer_text, (SCREEN_WIDTH // 2 - 80, padding), color=COLORS["white"])

        # Skill icon / cooldown (nếu muốn mở rộng)
        # Ví dụ: icon skill A ở góc phải dưới