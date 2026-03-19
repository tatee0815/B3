import sdl2
import sdl2.sdlttf as ttf
import sdl2.sdlmixer as mixer
from game.utils.assets import AudioManager

class GameOverState:
    def __init__(self, game):
        self.game = game
        self.name = "game_over"

    def on_enter(self, **kwargs):
        AudioManager.stop_bgm()
        AudioManager.play_sfx("game_over")

    def on_exit(self):
        mixer.Mix_HaltChannel(-1)

    def handle_event(self, event):
        if event.type == sdl2.SDL_KEYDOWN:
            AudioManager.play_bgm()
            if event.key.keysym.sym in (sdl2.SDLK_RETURN, sdl2.SDLK_z, sdl2.SDLK_SPACE):
                # Khi chết hẳn, bấm phím sẽ tự động reset toàn bộ tiến trình và chơi lại
                self.game.change_state("playing", reset=True)
            
            elif event.key.keysym.sym == sdl2.SDLK_ESCAPE:
                self.game.change_state("menu")

    def update(self, delta_time): pass

    def render(self, renderer):
        sdl2.SDL_RenderSetScale(renderer, 1.0, 1.0)
        
        w, h = self.game.current_width, self.game.current_height
        
        # Nền đen xám
        sdl2.SDL_SetRenderDrawColor(renderer, 20, 20, 20, 255)
        sdl2.SDL_RenderClear(renderer)

        self._draw_text(renderer, self.game.title_font, "GAME OVER", w//2, h//2 - 100, (220, 60, 60))
        self._draw_text(renderer, self.game.font, "Công chúa đã bị hiến tế", w//2, h//2 - 50, (200, 200, 200))
        self._draw_text(renderer, self.game.font, "Nhấn ENTER để chơi lại", w//2, h//2 + 50, (200, 200, 200))
        self._draw_text(renderer, self.game.font, "Nhấn ESC để về Menu chính", w//2, h//2 + 100, (150, 150, 150))
        
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