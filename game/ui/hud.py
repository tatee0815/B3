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
        self.current_font_size = 0
        self._load_font()

    def _load_font(self):
        # Tính toán font size dựa trên scale thực tế của cửa sổ
        base_size = 22
        target_size = int(base_size * self.game.scale_y)
        
        # Chỉ load lại nếu size thay đổi
        if target_size != self.current_font_size:
            font_path = "assets/fonts/UTM-Netmuc-KT.ttf"
            if self.font: ttf.TTF_CloseFont(self.font)
            self.font = ttf.TTF_OpenFont(font_path.encode(), target_size)
            self.current_font_size = target_size

    def render(self, renderer):
        player = self.game.states["playing"].player
        if not player: return
        
        self._load_font()

        # Tắt scale để vẽ 1:1
        sdl2.SDL_RenderSetScale(renderer, 1.0, 1.0)
        
        sx, sy = self.game.scale_x, self.game.scale_y
        p = int(20 * sx) 

        # --- Vẽ HP (Tim) ---
        heart_size = int(34 * sy)
        for i in range(PLAYER_MAX_HP):
            color = COLORS["red"] if i < player.hp else COLORS["gray"]
            sdl2.SDL_SetRenderDrawColor(renderer, *color)
            # Quan trọng: Ép kiểu int cho toàn bộ đối số trong SDL_Rect
            rect = sdl2.SDL_Rect(int(p + i * (42 * sx)), int(p), heart_size, heart_size)
            sdl2.SDL_RenderFillRect(renderer, rect)

        # --- Vẽ Mana Bar ---
        bar_w, bar_h = int(200 * sx), int(15 * sy)
        mana_x, mana_y = p, int(p + heart_size + (10 * sy))
        
        sdl2.SDL_SetRenderDrawColor(renderer, *COLORS["mana_empty"])
        sdl2.SDL_RenderFillRect(renderer, sdl2.SDL_Rect(mana_x, mana_y, bar_w, bar_h))
        
        if player.mana > 0:
            current_mana_w = int(bar_w * (int(player.mana) / MANA_MAX))
            sdl2.SDL_SetRenderDrawColor(renderer, *COLORS["mana_bar"])
            sdl2.SDL_RenderFillRect(renderer, sdl2.SDL_Rect(mana_x, mana_y, current_mana_w, bar_h))

        # --- Vẽ Text ở dưới ---
        # Sử dụng current_height thực tế để tính vị trí
        bottom_y = int(self.game.current_height - p - (45 * sy))

        self._draw_text(renderer, f"Vàng: {player.gold}", p, bottom_y, (255, 215, 0))
        self._draw_text(renderer, f"Mạng: {self.game.lives}/{MAX_LIVES}", int(p + (180 * sx)), bottom_y, (255, 255, 255))
        self._draw_text(renderer, f"Chết: {self.game.player_progress['total_deaths']}", int(p + 380 * sx), bottom_y, (220, 60, 60))

        
        # Bật lại scale cũ
        sdl2.SDL_RenderSetScale(renderer, self.game.scale_x, self.game.scale_y)

    def _draw_text(self, renderer, text, x, y, color):
        if not self.font: return
        sdl_color = sdl2.SDL_Color(color[0], color[1], color[2], 255)
        surf = ttf.TTF_RenderUTF8_Blended(self.font, text.encode('utf-8'), sdl_color)
        if surf:
            tex = sdl2.SDL_CreateTextureFromSurface(renderer, surf)
            tw, th = surf.contents.w, surf.contents.h
            # Tọa độ x, y truyền vào cũng phải là int
            sdl2.SDL_RenderCopy(renderer, tex, None, sdl2.SDL_Rect(int(x), int(y), int(tw), int(th)))
            sdl2.SDL_DestroyTexture(tex)
            sdl2.SDL_FreeSurface(surf)