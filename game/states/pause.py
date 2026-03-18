# -*- coding: utf-8 -*-
import sdl2
import sdl2.sdlttf as ttf
from game.constants import SCREEN_WIDTH, SCREEN_HEIGHT, KEY_BINDINGS_DEFAULT

class PauseState:
    def __init__(self, game):
        self.game = game
        self.name = "pause"
        self.mode = "main" # Cấu trúc: "main", "settings_main", "settings_keys", "remap"
        self.selected = 0
        self.remap_index = -1

        self.main_options = ["Tiếp tục", "Cài đặt", "Thoát ra Menu"]
        self.setting_options = [
            "Độ phân giải",
            "Âm lượng nhạc",
            "Âm lượng hiệu ứng",
            "Tùy chỉnh phím",
            "Quay lại"
        ]

    def on_enter(self, **kwargs):
        self.mode = "main"
        self.selected = 0

    def on_exit(self): pass

    def update(self, delta_time): pass

    def handle_event(self, event):
        if event.type != sdl2.SDL_KEYDOWN: return
        scancode = event.key.keysym.scancode
        
        # Lấy trực tiếp State Cài đặt để đồng bộ chung 1 logic
        st = self.game.states["setting"]

        # 1. Chế độ gán phím
        if self.mode == "remap":
            if scancode != sdl2.SDL_SCANCODE_ESCAPE:
                KEY_BINDINGS_DEFAULT[st.key_list[self.remap_index]] = scancode
                st._save_settings()
            self.mode = "settings_keys"
            return

        # 2. Xử lý ESC
        if scancode == sdl2.SDL_SCANCODE_ESCAPE:
            if self.mode == "main": self.game.change_state("playing")
            elif self.mode == "settings_main": 
                self.mode = "main"
                self.selected = 1
            elif self.mode == "settings_keys":
                self.mode = "settings_main"
                self.selected = 3
            return

        # 3. Điều hướng Lên/Xuống/Trái/Phải
        if self.mode == "settings_keys":
            if scancode == sdl2.SDL_SCANCODE_UP: self.selected = (self.selected - 1) % 9
            elif scancode == sdl2.SDL_SCANCODE_DOWN: self.selected = (self.selected + 1) % 9
        else:
            limit = len(self.main_options) if self.mode == "main" else len(self.setting_options)
            if scancode == sdl2.SDL_SCANCODE_UP: self.selected = (self.selected - 1) % limit
            elif scancode == sdl2.SDL_SCANCODE_DOWN: self.selected = (self.selected + 1) % limit
            elif scancode == sdl2.SDL_SCANCODE_LEFT and self.mode == "settings_main": self._adjust_value(-1, st)
            elif scancode == sdl2.SDL_SCANCODE_RIGHT and self.mode == "settings_main": self._adjust_value(1, st)

        # 4. Action / Enter
        if scancode in (sdl2.SDL_SCANCODE_RETURN, sdl2.SDL_SCANCODE_Z, sdl2.SDL_SCANCODE_SPACE):
            if self.mode == "main":
                if self.selected == 0: self.game.change_state("playing")
                elif self.selected == 1:
                    self.mode = "settings_main"
                    self.selected = 0
                elif self.selected == 2: 
                    from game.utils.save import save_game
                    save_game(self.game.player_progress) # Lưu lại trước khi ra Menu
                    self.game.change_state("menu")
            
            elif self.mode == "settings_main":
                if self.selected == 3:
                    self.mode = "settings_keys"
                    self.selected = 0
                elif self.selected == 4:
                    self.mode = "main"
                    self.selected = 1
                    st._save_settings()
            
            elif self.mode == "settings_keys":
                if self.selected == 8: 
                    st._reset_keys_only()
                else:
                    self.remap_index = self.selected
                    self.mode = "remap"

    def _adjust_value(self, delta, st):
        if self.selected == 0: # Phân giải
            if delta > 0: st.res_index = (st.res_index + 1) % len(st.resolutions)
            else: st.res_index = (st.res_index - 1) % len(st.resolutions)
            res = st.resolutions[st.res_index]
            self.game.set_resolution(res[0], res[1])
            st._save_settings()
        elif self.selected == 1: # Nhạc
            st.music_volume = max(0, min(100, st.music_volume + delta * 5))
            st._save_settings()
        elif self.selected == 2: # SFX
            st.sfx_volume = max(0, min(100, st.sfx_volume + delta * 5))
            st._save_settings()

    def render(self, renderer):
        sdl2.SDL_SetRenderDrawBlendMode(renderer, sdl2.SDL_BLENDMODE_BLEND)
        sdl2.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 190)
        sdl2.SDL_RenderFillRect(renderer, sdl2.SDL_Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))

        title = "TẠM DỪNG"
        if self.mode == "settings_main": title = "CÀI ĐẶT"
        elif self.mode in ("settings_keys", "remap"): title = "TÙY CHỈNH PHÍM"
        
        self.draw_text(title, SCREEN_WIDTH // 2, 80, (255, 215, 0), use_title_font=True)

        if self.mode == "main":
            self._render_menu(renderer, self.main_options, y_start=SCREEN_HEIGHT // 2 - 100)
        elif self.mode == "settings_main":
            self._render_settings_main(renderer)
        else:
            self._render_key_config(renderer)

        hint = "LEFT/RIGHT/UP/DOWN : Điều chỉnh   ENTER : Chọn   ESC : Quay lại"
        if self.mode == "remap": hint = "NHẤN PHÍM MỚI ĐỂ GÁN (ESC để hủy)"
        self.draw_text(hint, SCREEN_WIDTH // 2, SCREEN_HEIGHT - 65, (180, 180, 180))

    def _render_menu(self, renderer, options, y_start):
        y = y_start
        for i, opt in enumerate(options):
            is_sel = (i == self.selected)
            rect = sdl2.SDL_Rect(SCREEN_WIDTH // 2 - 200, y, 400, 70)
            if is_sel:
                sdl2.SDL_SetRenderDrawColor(renderer, 255, 215, 0, 255)
                tc = (0, 0, 0)
            else:
                sdl2.SDL_SetRenderDrawColor(renderer, 20, 20, 20, 160)
                tc = (255, 255, 255)
            sdl2.SDL_RenderFillRect(renderer, rect)
            self.draw_text(opt, SCREEN_WIDTH // 2, y + 35, tc) 
            y += 85

    def _render_settings_main(self, renderer):
        st = self.game.states["setting"]
        y = 150
        for i, opt in enumerate(self.setting_options):
            is_sel = (i == self.selected)
            rect = sdl2.SDL_Rect(SCREEN_WIDTH // 2 - 220, y, 440, 70)
            if is_sel:
                sdl2.SDL_SetRenderDrawColor(renderer, 255, 215, 0, 255)
                tc = (0, 0, 0)
            else:
                sdl2.SDL_SetRenderDrawColor(renderer, 20, 20, 20, 160)
                tc = (255, 255, 255)
            sdl2.SDL_RenderFillRect(renderer, rect)

            display_text = opt
            if i == 0:
                res = st.resolutions[st.res_index]
                display_text += f": {res[0]}x{res[1]}"
            elif i == 1: display_text += f": {st.music_volume}%"
            elif i == 2: display_text += f": {st.sfx_volume}%"

            self.draw_text(display_text, SCREEN_WIDTH // 2, y + 35, tc)
            y += 85

    def _render_key_config(self, renderer):
        st = self.game.states["setting"]
        start_y, col_w, gap_x, gap_y = 170, 360, 50, 75
        start_x_2col = (SCREEN_WIDTH - (col_w * 2 + gap_x)) // 2

        for i in range(len(st.key_names)):
            col = 0 if i < 4 else 1
            row = i % 4
            bx = start_x_2col + (col * (col_w + gap_x))
            by = start_y + (row * gap_y)
            is_sel = (i == self.selected)
            self._draw_option_box(renderer, bx, by, col_w, 60, i, is_sel, st)

        default_btn_w = 300
        default_btn_x = (SCREEN_WIDTH - default_btn_w) // 2
        default_btn_y = start_y + (4 * gap_y) 
        
        is_sel_default = (self.selected == 8)
        self._draw_option_box(renderer, default_btn_x, default_btn_y, default_btn_w, 60, 7, is_sel_default, st, is_default_btn=True)

    def _draw_option_box(self, renderer, x, y, w, h, index, is_sel, st, is_default_btn=False):
        rect = sdl2.SDL_Rect(x, y, w, h)
        if is_sel:
            sdl2.SDL_SetRenderDrawColor(renderer, 255, 200, 0, 255)
            text_color = (0, 0, 0)
        else:
            sdl2.SDL_SetRenderDrawColor(renderer, 20, 20, 20, 180)
            text_color = (255, 255, 255)
            
        sdl2.SDL_RenderFillRect(renderer, rect)

        if is_default_btn:
            display_text = "Mặc định"
        else:
            name = st.key_names[index]
            scancode = KEY_BINDINGS_DEFAULT[st.key_list[index]]
            if self.mode == "remap" and index == self.remap_index: val_str = "< Chờ... >"
            else: val_str = sdl2.SDL_GetScancodeName(scancode).decode('utf-8')
            display_text = f"{name}: {val_str}"

        self.draw_text(display_text, x + w // 2, y + h // 2, text_color)

    def draw_text(self, text, x, y, color=(255, 255, 255), use_title_font=False):
        font = self.game.title_font if use_title_font else self.game.font
        if not font: return

        sdl_color = sdl2.SDL_Color(color[0], color[1], color[2], 255)
        surface = ttf.TTF_RenderUTF8_Blended(font, text.encode('utf-8'), sdl_color)
        if not surface: return

        renderer = self.game.renderer 
        texture = sdl2.SDL_CreateTextureFromSurface(renderer, surface)
        if texture:
            w, h = surface.contents.w, surface.contents.h
            rect = sdl2.SDL_Rect(x - w // 2, y - h // 2, w, h)
            sdl2.SDL_RenderCopy(renderer, texture, None, rect)
            sdl2.SDL_DestroyTexture(texture)
        sdl2.SDL_FreeSurface(surface)