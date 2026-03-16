import sdl2
import sdl2.sdlttf as ttf

class WinState:
    def __init__(self, game):
        self.game = game
        self.name = "win"
        self.timer = 0.0

    def on_enter(self, **kwargs):
        self.timer = 0.0

    def on_exit(self):
        self.game.reset_progress()

    def update(self, delta_time):
        pass

    def handle_event(self, event):
        if event.type == sdl2.SDL_KEYDOWN:
            if event.key.keysym.sym in (sdl2.SDLK_RETURN, sdl2.SDLK_z, sdl2.SDLK_ESCAPE):
                self.game.change_state("menu")

    def render(self, renderer):
        sdl2.SDL_RenderSetScale(renderer, 1.0, 1.0)
        w, h = self.game.current_width, self.game.current_height
        
        sdl2.SDL_SetRenderDrawColor(renderer, 40, 120, 200, 255) # Xanh hy vọng
        sdl2.SDL_RenderClear(renderer)

        self._draw_text(renderer, self.game.title_font, "TRÒ CHƠI KẾT THÚC!", w//2, h//2 - 60, (255, 215, 0))
        self._draw_text(renderer, self.game.font, "Bạn đã hoàn thành trò chơi!", w//2, h//2 + 20, (255, 255, 255))
        self._draw_text(renderer, self.game.font, "Nhấn phím ENTER để về Menu", w//2, h - 100, (200, 255, 200))

        p = self.game.player_progress
        mins = int(p["play_time"] // 60)
        secs = int(p["play_time"] % 60)
        
        # Vẽ các thông số cuối game
        y_offset = h // 2 + 50
        self._draw_text(renderer, self.game.font, f"Vàng thu thập: {p.get('coin', 0)}", w//2, y_offset+ 20, (255, 255, 0))
        self._draw_text(renderer, self.game.font, f"Mạng còn lại: {p.get('lives', 3)}", w//2, y_offset + 60, (0, 255, 0))
        self._draw_text(renderer, self.game.font, f"Thời gian: {mins:02d}:{secs:02d}", w//2, y_offset + 100, (255, 255, 255))

        sdl2.SDL_RenderSetScale(renderer, self.game.scale_x, self.game.scale_y)

    def _draw_text(self, renderer, font, text, x, y, color):
        if not font: return
        sdl_color = sdl2.SDL_Color(*color, 255)
        surf = ttf.TTF_RenderUTF8_Blended(font, text.encode('utf-8'), sdl_color)
        if surf:
            tex = sdl2.SDL_CreateTextureFromSurface(renderer, surf)
            tw, th = surf.contents.w, surf.contents.h
            sdl2.SDL_RenderCopy(renderer, tex, None, sdl2.SDL_Rect(int(x - tw//2), int(y - th//2), tw, th))
            sdl2.SDL_DestroyTexture(tex)
            sdl2.SDL_FreeSurface(surf)