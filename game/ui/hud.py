"""
HUD hoàn chỉnh - Scale mượt theo cửa sổ, chữ tiếng Việt rõ nét
"""

import sdl2
import sdl2.sdlttf as ttf
from game.constants import PLAYER_MAX_HP, MANA_MAX, MAX_LIVES, COLORS, SCREEN_HEIGHT


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
        if not player: return

        p = 20 # Padding khoảng cách lề

        # ==================== HP (Tim) ====================
        heart_size = 34
        for i in range(PLAYER_MAX_HP):
            color = COLORS["red"] if i < player.hp else COLORS["gray"]
            sdl2.SDL_SetRenderDrawColor(renderer, *color)
            rect = sdl2.SDL_Rect(p + i * 42, p, heart_size, heart_size)
            sdl2.SDL_RenderFillRect(renderer, rect)

        # ==================== Mana (Thanh) ====================
        mana_w = 200
        bar_h = 16
        mana_x = p
        mana_y = p + heart_size + 10

        sdl2.SDL_SetRenderDrawColor(renderer, *COLORS["mana_empty"])
        sdl2.SDL_RenderFillRect(renderer, sdl2.SDL_Rect(mana_x, mana_y, mana_w, bar_h))

        if player.mana > 0:
            current_mana_w = int((player.mana / MANA_MAX) * mana_w)
            sdl2.SDL_SetRenderDrawColor(renderer, *COLORS["mana_bar"])
            sdl2.SDL_RenderFillRect(renderer, sdl2.SDL_Rect(mana_x, mana_y, current_mana_w, bar_h))

        if player.mana_warning_timer > 0:
            surf = ttf.TTF_RenderUTF8_Blended(self.font, "Không đủ Mana!".encode(), sdl2.SDL_Color(255,50,50,255))
            if surf:
                tex = sdl2.SDL_CreateTextureFromSurface(renderer, surf)
                tw, th = surf.contents.w, surf.contents.h
                sdl2.SDL_RenderCopy(renderer, tex, None, sdl2.SDL_Rect(mana_x, mana_y + bar_h + 5, tw, th))
                sdl2.SDL_DestroyTexture(tex)
                sdl2.SDL_FreeSurface(surf)

        # ==================== Dưới cùng: Vàng - Mạng - Chết ====================
        bottom_y = SCREEN_HEIGHT - p - 45

        self._draw_text(renderer, f"Vàng: {player.gold}", p, bottom_y, (255, 215, 0))
        self._draw_text(renderer, f"Mạng: {self.game.lives}/{MAX_LIVES}", p + 180, bottom_y, (255, 255, 255))
        self._draw_text(renderer, f"Chết: {self.game.player_progress['total_deaths']}", p + 380, bottom_y, (220, 60, 60))

    def _draw_text(self, renderer, text, x, y, color):
        if not self.font: return
        sdl_color = sdl2.SDL_Color(color[0], color[1], color[2], 255)
        surf = ttf.TTF_RenderUTF8_Blended(self.font, text.encode(), sdl_color)
        if surf:
            tex = sdl2.SDL_CreateTextureFromSurface(renderer, surf)
            tw, th = surf.contents.w, surf.contents.h
            sdl2.SDL_RenderCopy(renderer, tex, None, sdl2.SDL_Rect(x, y, tw, th))
            sdl2.SDL_DestroyTexture(tex)
            sdl2.SDL_FreeSurface(surf)