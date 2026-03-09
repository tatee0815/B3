# -*- coding: utf-8 -*-
import sdl2
import sdl2.sdlttf as ttf
from game.constants import (
    PLAYER_MAX_HP, MANA_MAX,
    MAX_LIVES, COLORS
)

class HUD:
    def __init__(self, game):
        self.game = game
        self.font = None
        self._load_font()

        # Cấu hình Scale
        self.ref_w = 1280  # Độ phân giải tham chiếu chuẩn
        self.ref_h = 720
        self.padding = 20

        # Cache để tối ưu hiệu năng (không tạo lại texture mỗi frame)
        self.cache = {
            "gold": {"val": None, "tex": None, "w": 0, "h": 0},
            "mana_text": {"val": None, "tex": None, "w": 0, "h": 0},
            "timer": {"val": None, "tex": None, "w": 0, "h": 0},
            "lives": {"val": None, "tex": None, "w": 0, "h": 0}
        }

    def _load_font(self):
        """Khởi tạo font hỗ trợ tiếng Việt"""
        if ttf.TTF_WasInit() == 0:
            ttf.TTF_Init()
        
        # Đảm bảo bạn có file font này trong thư mục assets/fonts/
        font_path = "assets/fonts/unifont.ttf" 
        self.font = ttf.TTF_OpenFont(font_path.encode(), 22)
        if not self.font:
            print(f"HUD Warning: Không tìm thấy font tại {font_path}, dùng font mặc định.")

    def _get_cached_text(self, renderer, text, color, key):
        """Chỉ render lại text thành texture khi nội dung thay đổi"""
        if self.cache[key]["val"] == text:
            return self.cache[key]["tex"], self.cache[key]["w"], self.cache[key]["h"]

        # Giải phóng texture cũ
        if self.cache[key]["tex"]:
            sdl2.SDL_DestroyTexture(self.cache[key]["tex"])

        if not self.font:
            return None, 0, 0

        surf = ttf.TTF_RenderUTF8_Blended(self.font, text.encode('utf-8'), color)
        if not surf:
            return None, 0, 0
            
        tex = sdl2.SDL_CreateTextureFromSurface(renderer, surf)
        w, h = surf.contents.w, surf.contents.h
        
        self.cache[key] = {"val": text, "tex": tex, "w": w, "h": h}
        sdl2.SDL_FreeSurface(surf)
        return tex, w, h

    def render(self, renderer):
        player = self.game.states["playing"].player
        if not player:
            return

        # 1. Tính toán tỉ lệ Scale thông minh (Clamping)
        curr_w = self.game.window_width 
        curr_h = self.game.window_height
        raw_scale = min(curr_w / self.ref_w, curr_h / self.ref_h)
        # Giới hạn HUD không quá bé (<0.8) hoặc quá to (>1.4)
        hud_scale = max(0.8, min(raw_scale, 1.4))
        
        padding = int(self.padding * hud_scale)

        # 2. HP BAR (Góc trên trái)
        heart_size = int(28 * hud_scale)
        for i in range(PLAYER_MAX_HP):
            # Vẽ bóng đổ cho tim (tạo hiệu ứng nổi)
            shadow_rect = sdl2.SDL_Rect(padding + i * int(35 * hud_scale) + 2, padding + 2, heart_size, heart_size)
            sdl2.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 100)
            sdl2.SDL_RenderFillRect(renderer, shadow_rect)

            # Vẽ tim chính
            color = COLORS["red"] if i < player.hp else (60, 60, 60, 255)
            rect = sdl2.SDL_Rect(padding + i * int(35 * hud_scale), padding, heart_size, heart_size)
            sdl2.SDL_SetRenderDrawColor(renderer, *color)
            sdl2.SDL_RenderFillRect(renderer, rect)

        # 3. MANA BAR (Góc trên phải)
        bar_w, bar_h = int(180 * hud_scale), int(14 * hud_scale)
        mana_x = curr_w - bar_w - padding
        mana_y = padding

        # Nền thanh mana (có độ trong suốt)
        sdl2.SDL_SetRenderDrawColor(renderer, 20, 20, 40, 180)
        sdl2.SDL_RenderFillRect(renderer, sdl2.SDL_Rect(mana_x - 4, mana_y - 4, bar_w + 8, bar_h + 8))
        
        # Mana hiện tại
        mana_ratio = max(0, min(1, player.mana / MANA_MAX))
        sdl2.SDL_SetRenderDrawColor(renderer, 0, 120, 255, 255)
        sdl2.SDL_RenderFillRect(renderer, sdl2.SDL_Rect(mana_x, mana_y, int(bar_w * mana_ratio), bar_h))

        # Text Mana (Số) ngay dưới thanh
        mana_str = f"{int(player.mana)}/{MANA_MAX}"
        m_tex, mw, mh = self._get_cached_text(renderer, mana_str, sdl2.SDL_Color(200, 230, 255), "mana_text")
        if m_tex:
            sdl2.SDL_RenderCopy(renderer, m_tex, None, sdl2.SDL_Rect(mana_x + bar_w - mw, mana_y + bar_h + 5, mw, mh))

        # 4. THÔNG TIN DƯỚI CÙNG (Floating Bottom)
        # Vàng (Góc dưới trái)
        gold_str = f"💰 Vàng: {player.gold}"
        g_tex, gw, gh = self._get_cached_text(renderer, gold_str, sdl2.SDL_Color(255, 215, 0), "gold")
        if g_tex:
            sdl2.SDL_RenderCopy(renderer, g_tex, None, sdl2.SDL_Rect(padding, curr_h - gh - padding, gw, gh))

        # Timer (Chính giữa trên cùng)
        time_str = f"⏱ {int(self.game.game_time)}s"
        t_tex, tw, th = self._get_cached_text(renderer, time_str, sdl2.SDL_Color(255, 255, 255), "timer")
        if t_tex:
            sdl2.SDL_RenderCopy(renderer, t_tex, None, sdl2.SDL_Rect((curr_w - tw)//2, padding, tw, th))

        # Mạng (Góc dưới phải)
        lives_str = f"Mạng: {self.game.lives} | Chết: {self.game.player_progress['total_deaths']}"
        l_tex, lw, lh = self._get_cached_text(renderer, lives_str, sdl2.SDL_Color(255, 100, 100), "lives")
        if l_tex:
            sdl2.SDL_RenderCopy(renderer, l_tex, None, sdl2.SDL_Rect(curr_w - lw - padding, curr_h - lh - padding, lw, lh))

    def __del__(self):
        """Dọn dẹp tài nguyên khi object bị hủy"""
        for key in self.cache:
            if self.cache[key]["tex"]:
                sdl2.SDL_DestroyTexture(self.cache[key]["tex"])
        if self.font:
            ttf.TTF_CloseFont(self.font)