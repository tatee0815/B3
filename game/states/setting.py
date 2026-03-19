# -*- coding: utf-8 -*-
import sdl2
import sdl2.sdlttf as ttf
from game.utils.assets import AudioManager
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
            "Độ phân giải",
            "Âm lượng nhạc",
            "Âm lượng hiệu ứng",
            "Tùy chỉnh phím",
            "Quay lại"
        ]

        # Danh sách các độ phân giải hỗ trợ
        self.resolutions = [(1280, 720), (1600, 900), (1920, 1080)]
        self.res_index = 0

        self.music_volume = 70
        self.sfx_volume = 85

        self.key_names = ["Trái", "Phải", "Nhảy", "Chém", "Kỹ năng", "Lướt", "Tạm dừng", "Tương tác"]
        self.key_list = ["left", "right", "jump", "attack", "skill", "dash", "pause", "interact"]

        self._load_settings()

    def _load_settings(self):
        path = "config/settings.json"
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.music_volume = data.get("music_volume", 70)
                    self.sfx_volume = data.get("sfx_volume", 85)
                    
                    if "controls" in data:
                        saved_controls = data["controls"]
                        for k in self.key_list:
                            if k in saved_controls:
                                # Gán giá trị số nguyên từ JSON vào KEY_BINDINGS_DEFAULT
                                KEY_BINDINGS_DEFAULT[k] = int(saved_controls[k])
            except : pass

        res = self.resolutions[self.res_index]
        self.game.set_resolution(res[0], res[1])

    def _save_settings(self):
        os.makedirs("config", exist_ok=True)
        # Tạo bản sao của controls nhưng đảm bảo giá trị là số nguyên
        controls_to_save = {}
        for k, v in KEY_BINDINGS_DEFAULT.items():
            controls_to_save[k] = int(v) # Ép kiểu về số nguyên để lưu JSON chuẩn

        data = {
            "res_index": self.res_index,
            "music_volume": self.music_volume,
            "sfx_volume": self.sfx_volume,
            "controls": controls_to_save
        }
        with open("config/settings.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def handle_event(self, event):
        if event.type != sdl2.SDL_KEYDOWN: return
        scancode = event.key.keysym.scancode

        # 1. TRẠNG THÁI "remap": Đang chờ nhấn phím mới để gán
        if self.mode == "remap":
            if scancode != sdl2.SDL_SCANCODE_ESCAPE:
                # Gán phím mới dựa trên scancode
                from game.constants import KEY_BINDINGS_DEFAULT
                KEY_BINDINGS_DEFAULT[self.key_list[self.remap_index]] = scancode
                self._save_settings()
            self.mode = "sub_menu" # Xong thì quay lại danh sách phím
            return

        # 2. ĐIỀU HƯỚNG TRONG "sub_menu" (Tùy chỉnh phím)
        if self.mode == "sub_menu":
            # Chỉ nhận phím mũi tên Lên/Xuống để duyệt danh sách theo thứ tự
            if scancode == sdl2.SDL_SCANCODE_UP:
                # Nếu đang ở vị trí 0 (Trái), nhảy xuống cuối là vị trí 8 (Mặc định)
                self.selected = (self.selected - 1) % 9
                    
            elif scancode == sdl2.SDL_SCANCODE_DOWN:
                # Duyệt từ trên xuống dưới, hết Mặc định sẽ quay lại Trái
                self.selected = (self.selected + 1) % 9

        # 3. ĐIỀU HƯỚNG TRONG "main" (Menu Cài đặt chính)
        else: # self.mode == "main"
            if scancode == sdl2.SDL_SCANCODE_UP:
                self.selected = (self.selected - 1) % len(self.options)
                AudioManager.play_sfx("choice")
            elif scancode == sdl2.SDL_SCANCODE_DOWN:
                self.selected = (self.selected + 1) % len(self.options)
                AudioManager.play_sfx("choice")
            elif scancode == sdl2.SDL_SCANCODE_LEFT:
                self._adjust_value(-1) # Giảm âm lượng hoặc lùi độ phân giải
            elif scancode == sdl2.SDL_SCANCODE_RIGHT:
                self._adjust_value(1)  # Tăng âm lượng hoặc tiến độ phân giải

        # 4. XỬ LÝ CHỌN (Xác nhận dùng Enter, Z hoặc Space)
        if scancode in (sdl2.SDL_SCANCODE_RETURN, sdl2.SDL_SCANCODE_Z, sdl2.SDL_SCANCODE_SPACE):
            AudioManager.play_sfx("select")
            if self.mode == "main":
                if self.selected == 3: # Chọn mục "Tùy chỉnh phím"
                    self.mode = "sub_menu"
                    self.selected = 0 
                elif self.selected == 4: # Nút "Quay lại" trong menu chính
                    self.game.change_state("menu")
            elif self.mode == "sub_menu":
                if self.selected == 8: # Chọn nút "Mặc định"
                    self._reset_keys_only()
                else:
                    self.remap_index = self.selected
                    self.mode = "remap"

        # 5. XỬ LÝ QUAY LẠI (Phím ESC)
        elif scancode == sdl2.SDL_SCANCODE_ESCAPE:
            AudioManager.play_sfx("choice")
            if self.mode == "sub_menu":
                self.mode = "main"
                self.selected = 3  # Quay về đúng mục "Tùy chỉnh phím" ở menu chính
            else:
                self.game.change_state("menu")

    def _reset_keys_only(self):
        # Định nghĩa lại các phím gốc bằng SCANCODE
        defaults = {
            "left": sdl2.SDL_SCANCODE_LEFT,
            "right": sdl2.SDL_SCANCODE_RIGHT,
            "jump": sdl2.SDL_SCANCODE_Z,
            "attack": sdl2.SDL_SCANCODE_X,
            "skill": sdl2.SDL_SCANCODE_A,
            "dash": sdl2.SDL_SCANCODE_C,
            "pause": sdl2.SDL_SCANCODE_P,
            "interact": sdl2.SDL_SCANCODE_UP,
        }
        for k, v in defaults.items():
            KEY_BINDINGS_DEFAULT[k] = v
        
        self._save_settings()

    def _adjust_value(self, delta):
        # Chọn độ phân giải (Bấm trái/phải sẽ áp dụng màn hình ngay lập tức)
        if self.selected == 0: 
            if delta > 0: self.res_index = (self.res_index + 1) % len(self.resolutions)
            else: self.res_index = (self.res_index - 1) % len(self.resolutions)
            
            res = self.resolutions[self.res_index]
            self.game.set_resolution(res[0], res[1])
            
        elif self.selected == 1: 
            amt = delta * 5 # Tăng/giảm 5%
            self.music_volume = max(0, min(100, self.music_volume + amt))
            AudioManager.set_volumes(self.music_volume, self.sfx_volume)
        elif self.selected == 2: 
            amt = delta * 5
            self.sfx_volume = max(0, min(100, self.sfx_volume + amt))
            AudioManager.set_volumes(self.music_volume, self.sfx_volume)
            AudioManager.play_sfx("choice")

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
        self.draw_text(title_text, SCREEN_WIDTH // 2, 60, (255, 215, 0), use_title_font=True)

        # 5. Vẽ nội dung tùy theo chế độ (Mode)
        if self.mode == "main":
            self._render_main_menu(renderer)
        else:
            self._render_key_config(renderer)

        # 6. Hướng dẫn sử dụng ở dưới cùng
        hint = "LEFT/RIGHT/UP/DOWN : Điều chỉnh   ENTER : Chọn   ESC : Quay lại" if self.mode == "main" else "NHẤN PHÍM MỚI ĐỂ GÁN (ESC để hủy)"
        self.draw_text(hint, SCREEN_WIDTH // 2, SCREEN_HEIGHT - 65, (180, 180, 180))

    def _render_main_menu(self, renderer):
        """Vẽ menu cài đặt chính 1 cột dọc"""
        y = 150
        for i, opt in enumerate(self.options):
            is_sel = (i == self.selected)
            rect = sdl2.SDL_Rect(SCREEN_WIDTH // 2 - 220, y, 440, 70)
            
            # Màu sắc nút (Vàng khi chọn, Đen mờ khi không chọn)
            if is_sel:
                sdl2.SDL_SetRenderDrawColor(renderer, 255, 215, 0, 255)
                text_color = (0, 0, 0)
            else:
                sdl2.SDL_SetRenderDrawColor(renderer, 20, 20, 20, 160)
                text_color = (255, 255, 255)

            sdl2.SDL_RenderFillRect(renderer, rect)

            # Hiển thị giá trị cụ thể cho âm lượng
            display_text = opt
            if i == 0: 
                res = self.resolutions[self.res_index]
                display_text += f": {res[0]}x{res[1]}"
            if i == 1: display_text += f": {self.music_volume}%"
            elif i == 2: display_text += f": {self.sfx_volume}%"

            self.draw_text(display_text, SCREEN_WIDTH // 2, y + 18, text_color)
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
        
        is_sel_default = (self.selected == 8)
        self._draw_option_box(renderer, default_btn_x, default_btn_y, default_btn_w, 60, 7, is_sel_default, is_default_btn=True)

    def _draw_option_box(self, renderer, x, y, w, h, index, is_sel, is_default_btn=False):
        """Hàm phụ trợ để vẽ các ô lựa chọn"""
        rect = sdl2.SDL_Rect(x, y, w, h)
        
        if is_sel:
            # Màu vàng rực cho lựa chọn (Bỏ nhấp nháy theo yêu cầu trước)
            sdl2.SDL_SetRenderDrawColor(renderer, 255, 200, 0, 255)
            text_color = (0, 0, 0)
        else:
            sdl2.SDL_SetRenderDrawColor(renderer, 20, 20, 20, 180)
            text_color = (255, 255, 255)
            
        sdl2.SDL_RenderFillRect(renderer, rect)

        # Nội dung văn bản
        if is_default_btn:
            display_text = "Mặc định"
        else:
            name = self.key_names[index]
            scancode = KEY_BINDINGS_DEFAULT[self.key_list[index]]

            if self.mode == "remap" and index == self.remap_index:
                val_str = "< Chờ... >"
            else:
                val_str = sdl2.SDL_GetScancodeName(scancode).decode('utf-8')
            
            display_text = f"{name}: {val_str}"

        self.draw_text(display_text, x + w // 2, y + h // 2, text_color)

    def draw_text(self, text, x, y, color=(255, 255, 255), use_title_font=False):
        """Sử dụng font từ game.py và vẽ căn giữa tại x, y"""
        font = self.game.title_font if use_title_font else self.game.font
        if not font: return

        sdl_color = sdl2.SDL_Color(color[0], color[1], color[2], 255)
        surface = ttf.TTF_RenderUTF8_Blended(font, text.encode('utf-8'), sdl_color)
        if not surface: return

        # Chuyển surface thành texture để vẽ (Dùng self.game.renderer cho chắc chắn)
        renderer = self.game.renderer 
        texture = sdl2.SDL_CreateTextureFromSurface(renderer, surface)
        
        if texture:
            w, h = surface.contents.w, surface.contents.h
            # Tạo khung hình chữ nhật căn giữa tại x, y
            rect = sdl2.SDL_Rect(x - w // 2, y - h // 2, w, h)
            sdl2.SDL_RenderCopy(renderer, texture, None, rect)
            sdl2.SDL_DestroyTexture(texture)

        sdl2.SDL_FreeSurface(surface)

    def on_enter(self, **kwargs): 
        self.selected_index = 0
        self.waiting_for_key = False

    def on_exit(self): self._save_settings()