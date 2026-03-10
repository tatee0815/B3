"""
HUD hoàn chỉnh - Scale mượt theo cửa sổ, chữ tiếng Việt rõ nét
"""

import sdl2
import sdl2.sdlttf as ttf
from game.constants import PLAYER_MAX_HP, MANA_MAX, MAX_LIVES, COLORS


class HUD:
    def __init__(self, game):
        self.game = game
        self.font = None
        self._load_font()

    def _load_font(self):
        font_path = "assets/fonts/UTM-Netmuc-KT.ttf"          # hoặc font bạn đang dùng
        self.font = ttf.TTF_OpenFont(font_path.encode(), 22)

    def render(self, renderer):
        player = self.game.states["playing"].player
        if not player:
            return

        s = self.game.hud_scale                      # scale HUD động
        p = int(20 * s)                              # padding

        # ==================== HP (tim) ====================
        heart_size = int(34 * s)
        for i in range(PLAYER_MAX_HP):
            color = COLORS["red"] if i < player.hp else COLORS["gray"]
            sdl2.SDL_SetRenderDrawColor(renderer, *color)
            rect = sdl2.SDL_Rect(p + i * int(42 * s), p, heart_size, heart_size)
            sdl2.SDL_RenderFillRect(renderer, rect)

        # ==================== Mana Bar ====================
        mana_x = int(self.game.current_width * s - p - 220 * s)
        mana_y = p
        bar_w = int(200 * s)
        bar_h = int(22 * s)

        # Nền bar
        sdl2.SDL_SetRenderDrawColor(renderer, 40, 60, 100, 180)
        sdl2.SDL_RenderFillRect(renderer, sdl2.SDL_Rect(mana_x, mana_y, bar_w, bar_h))

        # Mana hiện tại
        fill_w = int((player.mana / MANA_MAX) * bar_w)
        sdl2.SDL_SetRenderDrawColor(renderer, 80, 180, 255, 255)
        sdl2.SDL_RenderFillRect(renderer, sdl2.SDL_Rect(mana_x, mana_y, fill_w, bar_h))

        # Text Mana
        if self.font:
            text = f"{int(player.mana)} / {MANA_MAX}"
            surf = ttf.TTF_RenderUTF8_Blended(self.font, text.encode('utf-8'), sdl2.SDL_Color(255,255,255))
            if surf:
                tex = sdl2.SDL_CreateTextureFromSurface(renderer, surf)
                tw, th = surf.contents.w, surf.contents.h
                sdl2.SDL_RenderCopy(renderer, tex, None, sdl2.SDL_Rect(mana_x, mana_y + bar_h + 5, tw, th))
                sdl2.SDL_DestroyTexture(tex)
                sdl2.SDL_FreeSurface(surf)

        # ==================== Dưới cùng: Vàng - Lives - Deaths ====================
        bottom_y = int(self.game.current_height * s - p - 45 * s)

        # Vàng
        gold_text = f"Vàng: {player.gold}"
        self._draw_text(renderer, gold_text, p, bottom_y, (255, 215, 0))

        # Lives
        lives_text = f"Mạng: {self.game.lives}/{MAX_LIVES}"
        self._draw_text(renderer, lives_text, p + 180 * s, bottom_y, (255, 255, 255))

        # Deaths
        deaths_text = f"Chết: {self.game.player_progress['total_deaths']}"
        self._draw_text(renderer, deaths_text, p + 380 * s, bottom_y, (220, 60, 60))

    def _draw_text(self, renderer, text, x, y, color):
        if not self.font:
            return
        surf = ttf.TTF_RenderUTF8_Blended(self.font, text.encode('utf-8'), sdl2.SDL_Color(*color))
        if surf:
            tex = sdl2.SDL_CreateTextureFromSurface(renderer, surf)
            w, h = surf.contents.w, surf.contents.h
            sdl2.SDL_RenderCopy(renderer, tex, None, sdl2.SDL_Rect(int(x), int(y), w, h))
            sdl2.SDL_DestroyTexture(tex)
            sdl2.SDL_FreeSurface(surf)