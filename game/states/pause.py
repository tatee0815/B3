# game/states/pause.py
import sdl2
import sdl2.sdlttf as ttf
from game.constants import SCREEN_WIDTH, SCREEN_HEIGHT, KEY_BINDINGS_DEFAULT

class PauseState:
    def __init__(self, game):
        self.game = game
        self.name = "pause"
        self.renderer = game.renderer
        
        # Menu levels
        self.MENU_MAIN = 0
        self.MENU_SETTINGS = 1
        self.MENU_CONTROLS = 2
        self.current_sub_menu = self.MENU_MAIN
        
        self.main_options = ["Tiếp Tục", "Cài Đặt", "Phím Bấm", "Thoát ra Menu"]
        self.selected_index = 0
        self.volume_music = 70
        self.volume_sfx = 80

    def on_enter(self, **kwargs):
        self.current_sub_menu = self.MENU_MAIN
        self.selected_index = 0

    def on_exit(self): pass

    def update(self, delta_time):
        """Hàm update trống để tránh lỗi AttributeError"""
        pass

    def get_current_options(self):
        if self.current_sub_menu == self.MENU_MAIN:
            return self.main_options
        elif self.current_sub_menu == self.MENU_SETTINGS:
            return [f"Nhạc Nền: {self.volume_music}%", f"Hiệu Ứng: {self.volume_sfx}%", "Quay lại"]
        elif self.current_sub_menu == self.MENU_CONTROLS:
            controls = [f"{k.upper()}: {sdl2.SDL_GetScancodeName(v).decode()}" 
                        for k, v in KEY_BINDINGS_DEFAULT.items()]
            return controls + ["Quay lại"]
        return []

    def handle_event(self, event):
        if event.type == sdl2.SDL_KEYDOWN:
            scancode = event.key.keysym.scancode
            options = self.get_current_options()

            # Bấm ESC để thoát menu tạm dừng hoặc quay lại menu chính của Pause
            if scancode == sdl2.SDL_SCANCODE_ESCAPE:
                if self.current_sub_menu == self.MENU_MAIN:
                    self.game.resume_game() 
                else:
                    self.current_sub_menu = self.MENU_MAIN
                    self.selected_index = 0
                return

            # Chỉ nhận phím mũi tên để di chuyển trong menu
            if scancode == sdl2.SDL_SCANCODE_UP:
                self.selected_index = (self.selected_index - 1) % len(options)
            elif scancode == sdl2.SDL_SCANCODE_DOWN:
                self.selected_index = (self.selected_index + 1) % len(options)
            
            # Phím xác nhận
            elif scancode in (sdl2.SDL_SCANCODE_RETURN, sdl2.SDL_SCANCODE_Z, sdl2.SDL_SCANCODE_SPACE):
                self.process_selection()

            # Điều chỉnh âm lượng (Chỉ dùng mũi tên Trái/Phải)
            if self.current_sub_menu == self.MENU_SETTINGS:
                if scancode == sdl2.SDL_SCANCODE_LEFT: 
                    self.adjust_volume(-5)
                elif scancode == sdl2.SDL_SCANCODE_RIGHT: 
                    self.adjust_volume(5)

    def process_selection(self):
        if self.current_sub_menu == self.MENU_MAIN:
            if self.selected_index == 0: self.game.resume_game()
            elif self.selected_index == 1: self.current_sub_menu = self.MENU_SETTINGS
            elif self.selected_index == 2: self.current_sub_menu = self.MENU_CONTROLS
            elif self.selected_index == 3: self.game.change_state("menu")
        elif self.current_sub_menu in (self.MENU_SETTINGS, self.MENU_CONTROLS):
            if self.selected_index == len(self.get_current_options()) - 1:
                self.current_sub_menu = self.MENU_MAIN
                self.selected_index = 0

    def adjust_volume(self, amount):
        if self.selected_index == 0: self.volume_music = max(0, min(100, self.volume_music + amount))
        elif self.selected_index == 1: self.volume_sfx = max(0, min(100, self.volume_sfx + amount))

    def draw_text(self, text, x, y, color=(255, 255, 255), use_title_font=False):
        """Sử dụng font từ game.py"""
        font = self.game.title_font if use_title_font else self.game.font
        if not font: return

        sdl_color = sdl2.SDL_Color(color[0], color[1], color[2], 255)
        surface = ttf.TTF_RenderUTF8_Blended(font, text.encode('utf-8'), sdl_color)
        if not surface: return

        texture = sdl2.SDL_CreateTextureFromSurface(self.renderer, surface)
        w, h = surface.contents.w, surface.contents.h
        rect = sdl2.SDL_Rect(x - w // 2, y - h // 2, w, h)
        sdl2.SDL_RenderCopy(self.renderer, texture, None, rect)
        
        sdl2.SDL_FreeSurface(surface)
        sdl2.SDL_DestroyTexture(texture)

    def render(self, renderer):
        # 1. Overlay tối (Đồng bộ độ mờ)
        sdl2.SDL_SetRenderDrawBlendMode(renderer, sdl2.SDL_BLENDMODE_BLEND)
        sdl2.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 160)
        sdl2.SDL_RenderFillRect(renderer, sdl2.SDL_Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))

        # 2. Tiêu đề (Đồng bộ font và màu sắc với menu.py)
        title_str = "TẠM DỪNG"
        if self.current_sub_menu == self.MENU_SETTINGS: title_str = "CÀI ĐẶT"
        elif self.current_sub_menu == self.MENU_CONTROLS: title_str = "PHÍM BẤM"
        self.draw_text(title_str, SCREEN_WIDTH // 2, 100, color=(255, 215, 0), use_title_font=True)

        # 3. Vẽ Options theo phong cách Box của Menu
        options = self.get_current_options()

        if self.current_sub_menu == self.MENU_CONTROLS:
            # CHẾ ĐỘ 2 CỘT CHO PHÍM BẤM (Giống SettingState)
            start_y = 200
            col_w = 380
            gap_x = 40
            gap_y = 85
            start_x = (SCREEN_WIDTH - (col_w * 2 + gap_x)) // 2
            
            for i, text in enumerate(options):
                is_sel = (i == self.selected_index)
                
                # Nút "Quay lại" (phần tử cuối) căn giữa ở dưới
                if i == len(options) - 1:
                    bx, by, bw, bh = SCREEN_WIDTH // 2 - 150, start_y + 4 * gap_y, 300, 70
                else:
                    # Chia 2 cột
                    col, row = (0 if i < 4 else 1), (i % 4)
                    bx = start_x + col * (col_w + gap_x)
                    by = start_y + row * gap_y
                    bw, bh = col_w, 70

                # Vẽ Box lựa chọn (Phong cách MenuState)
                if is_sel:
                    sdl2.SDL_SetRenderDrawColor(renderer, 255, 200, 0, 255)
                    text_color = (0, 0, 0)
                else:
                    sdl2.SDL_SetRenderDrawColor(renderer, 20, 20, 20, 160)
                    text_color = (255, 255, 255)
                
                sdl2.SDL_RenderFillRect(renderer, sdl2.SDL_Rect(bx, by, bw, bh))
                self.draw_text(text, bx + bw // 2, by + bh // 2, color=text_color)

        else:
            # CHẾ ĐỘ 1 CỘT CHO MENU CHÍNH (Giống MenuState)
            start_y = SCREEN_HEIGHT // 2 - 100
            gap = 95
            bw, bh = 450, 75
            
            for i, text in enumerate(options):
                is_sel = (i == self.selected_index)
                bx, by = SCREEN_WIDTH // 2 - 225, start_y + i * gap

                if is_sel:
                    sdl2.SDL_SetRenderDrawColor(renderer, 255, 200, 0, 255)
                    text_color = (0, 0, 0)
                else:
                    sdl2.SDL_SetRenderDrawColor(renderer, 20, 20, 20, 160)
                    text_color = (255, 255, 255)
                
                sdl2.SDL_RenderFillRect(renderer, sdl2.SDL_Rect(bx, by, bw, bh))
                self.draw_text(text, SCREEN_WIDTH // 2, by + bh // 2, color=text_color)