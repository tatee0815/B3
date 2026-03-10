# -*- coding: utf-8 -*-
import sdl2
import sdl2.sdlttf as ttf
import json
import os
from game.constants import SCREEN_WIDTH, SCREEN_HEIGHT, KEY_BINDINGS_DEFAULT

class SettingState:
    def __init__(self, game):
        self.game = game
        self.name = "setting"
        self.mode = "main"          # "main" hoặc "remap"
        self.selected = 0
        self.remap_index = -1       

        self.options = [
            "Âm lượng nhạc",
            "Âm lượng hiệu ứng",
            "Tùy chỉnh phím",
            "Quay lại"
        ]

        self.music_volume = 70
        self.sfx_volume = 85

        self.key_names = ["Trái", "Phải", "Nhảy", "Chém", "Skill", "Lướt", "Tạm dừng"]
        self.key_list = ["left", "right", "jump", "attack", "skill", "dash", "pause"]

        self._load_settings()
        self._init_assets()

    def _init_assets(self):
        font_path = "assets/fonts/UTM-Netmuc-KT.ttf"
        # Đồng bộ cỡ chữ với menu (30 cho nội dung, 70 cho tiêu đề)
        self.font = ttf.TTF_OpenFont(font_path.encode(), 30)
        self.title_font = ttf.TTF_OpenFont(font_path.encode(), 70)

    def _load_settings(self):
        path = "config/settings.json"
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.music_volume = data.get("music_volume", 70)
                    self.sfx_volume = data.get("sfx_volume", 85)
                    if "controls" in data:
                        for k, v in data["controls"].items():
                            if k in KEY_BINDINGS_DEFAULT:
                                KEY_BINDINGS_DEFAULT[k] = getattr(sdl2, v) if isinstance(v, str) else v
            except: pass

    def _save_settings(self):
        os.makedirs("config", exist_ok=True)
        # Chuyển đổi SDL Key thành string để lưu JSON an toàn
        controls = {k: sdl2.SDL_GetKeyName(v).decode('utf-8') for k, v in KEY_BINDINGS_DEFAULT.items()}
        data = {
            "music_volume": self.music_volume,
            "sfx_volume": self.sfx_volume,
            "controls": controls
        }
        with open("config/settings.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def handle_event(self, event):
        if event.type != sdl2.SDL_KEYDOWN: return
        key = event.key.keysym.sym

        # TRẠNG THÁI 3: Đang chờ nhấn phím mới để gán
        if self.mode == "remap":
            if key != sdl2.SDLK_ESCAPE:
                KEY_BINDINGS_DEFAULT[self.key_list[self.remap_index]] = key
                self._save_settings()
            self.mode = "sub_menu" # Xong thì quay lại danh sách phím
            return

        # ĐIỀU HƯỚNG CHUNG (Dùng cho cả Main và Sub_menu)
        if self.mode == "sub_menu":
            if key in (sdl2.SDLK_UP, sdl2.SDLK_w):
                if self.selected == 7: # Từ Mặc định lên lại
                    self.selected = 6  # Lên phím Chém (hoặc 6 nếu muốn lên cột 2)
                else:
                    self.selected = (self.selected - 1) % 8
                    
            elif key in (sdl2.SDLK_DOWN, sdl2.SDLK_s):
                # LOGIC YÊU CẦU: Từ phím Chém (index 3) bấm DOWN xuống Mặc định (index 7)
                if self.selected == 3: 
                    self.selected = 7
                # Nếu từ phím cuối cột 2 (index 6 - Tạm dừng) bấm DOWN cũng xuống Mặc định
                elif self.selected == 6:
                    self.selected = 7
                elif self.selected == 7:
                    self.selected = 0 # Từ Mặc định về đầu danh sách
                else:
                    self.selected = (self.selected + 1) % 8

            elif key in (sdl2.SDLK_LEFT, sdl2.SDLK_a):
                if 4 <= self.selected <= 6: # Đang ở cột 2
                    self.selected -= 4      # Nhảy sang cột 1
                elif self.selected == 7:    # Đang ở Mặc định
                    self.selected = 3       # Nhảy lên phím cuối cột 1
                    
            elif key in (sdl2.SDLK_RIGHT, sdl2.SDLK_d):
                if 0 <= self.selected <= 2: # Đang ở cột 1 (trừ phím Chém vì đối diện nó là trống)
                    self.selected += 4      # Nhảy sang cột 2
                elif self.selected == 7:    # Đang ở Mặc định
                    self.selected = 6       # Nhảy lên phím cuối cột 2
        else:
            # Điều hướng menu chính (Dọc)
            if key in (sdl2.SDLK_UP, sdl2.SDLK_w):
                self.selected = (self.selected - 1) % len(self.options)
            elif key in (sdl2.SDLK_DOWN, sdl2.SDLK_s):
                self.selected = (self.selected + 1) % len(self.options)

        # XỬ LÝ CHỌN (ENTER / Z)
        if key in (sdl2.SDLK_RETURN, sdl2.SDLK_z, sdl2.SDLK_SPACE):
            if self.mode == "main":
                if self.selected == 2: # Chọn Tùy chỉnh phím
                    self.mode = "sub_menu"
                    self.remap_index = 0
                    self.selected = 0 # Reset vị trí chọn cho danh sách phím
                elif self.selected == 3: # Quay lại
                    self.game.change_state("menu")
            elif self.mode == "sub_menu":
                if self.selected == 7:
                    self._reset_keys_only()
                else:
                    self.remap_index = self.selected
                    self.mode = "remap"

        # XỬ LÝ QUAY LẠI (ESC)
        elif key == sdl2.SDLK_ESCAPE:
            if self.mode == "sub_menu":
                self.mode = "main"
                self.selected = 3 # Quay lại đúng mục Tùy chỉnh phím
            else:
                self.game.change_state("menu")

        # THAY ĐỔI GIÁ TRỊ (Chỉ ở Main)
        if self.mode == "main":
            if key in (sdl2.SDLK_LEFT, sdl2.SDLK_a):
                self._adjust_value(-5)
            elif key in (sdl2.SDLK_RIGHT, sdl2.SDLK_d):
                self._adjust_value(5)

    def _reset_keys_only(self):
        # Định nghĩa lại các phím gốc
        defaults = {
            "left": sdl2.SDLK_LEFT,
            "right": sdl2.SDLK_RIGHT,
            "jump": sdl2.SDLK_z,
            "attack": sdl2.SDLK_x,
            "skill": sdl2.SDLK_a,
            "dash": sdl2.SDLK_c,
            "pause": sdl2.SDLK_p
        }
        for k, v in defaults.items():
            KEY_BINDINGS_DEFAULT[k] = v
        
        self._save_settings()
        print("Đã khôi phục phím mặc định")

    def _adjust_value(self, delta):
        if self.selected == 0: self.music_volume = max(0, min(100, self.music_volume + delta))
        elif self.selected == 1: self.sfx_volume = max(0, min(100, self.sfx_volume + delta))

    def _select_option(self):
        if self.selected == 2:
            self.mode = "remap"
            self.remap_index = 0
        elif self.selected == 3:
            self.game.change_state("menu")

    def update(self, delta_time): pass

    def render(self, renderer):
        # 1. Reset trạng thái renderer để tránh lỗi chồng lấn màu sắc
        sdl2.SDL_SetRenderDrawBlendMode(renderer, sdl2.SDL_BLENDMODE_NONE)
        sdl2.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255)
        sdl2.SDL_RenderClear(renderer)

        # 2. Vẽ Background từ MenuState
        if self.game.states["menu"].bg_texture:
            dst = sdl2.SDL_Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
            sdl2.SDL_RenderCopy(renderer, self.game.states["menu"].bg_texture, None, dst)

        # 3. Overlay tối (Dùng BlendMode để tạo độ mờ)
        sdl2.SDL_SetRenderDrawBlendMode(renderer, sdl2.SDL_BLENDMODE_BLEND)
        sdl2.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 190)
        sdl2.SDL_RenderFillRect(renderer, sdl2.SDL_Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))

        # 4. Vẽ Tiêu đề
        title_text = "CÀI ĐẶT" if self.mode == "main" else "TÙY CHỈNH PHÍM"
        self._draw_text(renderer, title_text, SCREEN_WIDTH // 2, 60, self.title_font, sdl2.SDL_Color(255, 215, 0, 255))

        # 5. Vẽ nội dung tùy theo chế độ (Mode)
        if self.mode == "main":
            self._render_main_menu(renderer)
        else:
            self._render_key_config(renderer)

        # 6. Hướng dẫn sử dụng ở dưới cùng
        hint = "LEFT/RIGHT/UP/DOWN : Điều chỉnh   ENTER : Chọn   ESC : Quay lại" if self.mode == "main" else "NHẤN PHÍM MỚI ĐỂ GÁN (ESC để hủy)"
        self._draw_text(renderer, hint, SCREEN_WIDTH // 2, SCREEN_HEIGHT - 65, self.font, sdl2.SDL_Color(180, 180, 180, 255))

    def _render_main_menu(self, renderer):
        """Vẽ menu cài đặt chính 1 cột dọc"""
        y = 180
        for i, opt in enumerate(self.options):
            is_sel = (i == self.selected)
            rect = sdl2.SDL_Rect(SCREEN_WIDTH // 2 - 220, y, 440, 70)
            
            # Màu sắc nút (Vàng khi chọn, Đen mờ khi không chọn)
            if is_sel:
                sdl2.SDL_SetRenderDrawColor(renderer, 255, 215, 0, 255)
                text_color = sdl2.SDL_Color(0, 0, 0, 255)
            else:
                sdl2.SDL_SetRenderDrawColor(renderer, 20, 20, 20, 160)
                text_color = sdl2.SDL_Color(255, 255, 255, 255)
            
            sdl2.SDL_RenderFillRect(renderer, rect)

            # Hiển thị giá trị cụ thể cho âm lượng
            display_text = opt
            if i == 0: display_text += f": {self.music_volume}%"
            elif i == 1: display_text += f": {self.sfx_volume}%"

            self._draw_text(renderer, display_text, SCREEN_WIDTH // 2, y + 18, self.font, text_color)
            y += 85

    def _render_key_config(self, renderer):
        """Vẽ danh sách phím 2 cột và nút Mặc định ở giữa dưới"""
        start_y = 170
        col_w = 360
        gap_x = 50
        gap_y = 75
        
        # 1. Vẽ 7 phím chính theo 2 cột (4 hàng)
        total_w_2col = (col_w * 2) + gap_x
        start_x_2col = (SCREEN_WIDTH - total_w_2col) // 2

        for i in range(len(self.key_names)):
            col = 0 if i < 4 else 1
            row = i % 4
            bx = start_x_2col + (col * (col_w + gap_x))
            by = start_y + (row * gap_y)
            
            is_sel = (i == self.selected)
            self._draw_option_box(renderer, bx, by, col_w, 60, i, is_sel)

        # 2. Vẽ nút "Mặc định" nằm ở giữa, bên dưới các phím
        # Vị trí i = 7
        default_btn_w = 300
        default_btn_x = (SCREEN_WIDTH - default_btn_w) // 2
        default_btn_y = start_y + (4 * gap_y) # Nằm ở hàng thứ 5
        
        is_sel_default = (self.selected == 7)
        self._draw_option_box(renderer, default_btn_x, default_btn_y, default_btn_w, 60, 7, is_sel_default, is_default_btn=True)

    def _draw_option_box(self, renderer, x, y, w, h, index, is_sel, is_default_btn=False):
        """Hàm phụ trợ để vẽ các ô lựa chọn"""
        rect = sdl2.SDL_Rect(x, y, w, h)
        
        if is_sel:
            # Màu vàng rực cho lựa chọn (Bỏ nhấp nháy theo yêu cầu trước)
            sdl2.SDL_SetRenderDrawColor(renderer, 255, 200, 0, 255)
            text_color = sdl2.SDL_Color(0, 0, 0, 255)
        else:
            sdl2.SDL_SetRenderDrawColor(renderer, 20, 20, 20, 180)
            text_color = sdl2.SDL_Color(255, 255, 255, 255)
            
        sdl2.SDL_RenderFillRect(renderer, rect)

        # Nội dung văn bản
        if is_default_btn:
            display_text = "Mặc định"
        else:
            name = self.key_names[index]
            key_code = KEY_BINDINGS_DEFAULT[self.key_list[index]]
            val_str = "< Chờ... >" if (self.mode == "remap" and index == self.remap_index) else sdl2.SDL_GetKeyName(key_code).decode('utf-8')
            display_text = f"{name}: {val_str}"

        self._draw_text(renderer, display_text, x + w // 2, y + 15, self.font, text_color)

    def _draw_text(self, renderer, text, x, y, font, color):
        """Hàm hỗ trợ vẽ chữ căn giữa"""
        surf = ttf.TTF_RenderUTF8_Blended(font, text.encode('utf-8'), color)
        if surf:
            tex = sdl2.SDL_CreateTextureFromSurface(renderer, surf)
            tw, th = surf.contents.w, surf.contents.h
            sdl2.SDL_RenderCopy(renderer, tex, None, sdl2.SDL_Rect(x - tw // 2, y, tw, th))
            sdl2.SDL_DestroyTexture(tex)
            sdl2.SDL_FreeSurface(surf)

    def on_enter(self, **kwargs): self.selected = 0
    def on_exit(self): self._save_settings()