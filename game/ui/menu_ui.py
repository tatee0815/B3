"""
Menu UI - Các phần tử giao diện cho menu và setting
Hiện tại triển khai đơn giản (text + highlight selected)
Sau này có thể mở rộng thành buttons thật (rect clickable)
"""

import sdl2
from game.constants import SCREEN_WIDTH, SCREEN_HEIGHT, COLORS, KEY_BINDINGS_DEFAULT


class MenuUI:
    def __init__(self, game):
        self.game = game
        self.options = ["Chơi ngay", "Cài đặt", "Thoát game"]
        self.selected = 0

    def handle_input(self, event):
        if event.type == sdl2.SDL_KEYDOWN:
            key = event.key.keysym.sym
            
            if key == sdl2.SDLK_UP or key == sdl2.SDLK_w:
                self.selected = (self.selected - 1) % len(self.options)
            elif key == sdl2.SDLK_DOWN or key == sdl2.SDLK_s:
                self.selected = (self.selected + 1) % len(self.options)
            elif key == sdl2.SDLK_RETURN or key == sdl2.SDLK_z or key == sdl2.SDLK_SPACE:
                self._select_option()

    def _select_option(self):
        choice = self.options[self.selected]
        if choice == "Chơi ngay":
            self.game.change_state("playing")
        elif choice == "Cài đặt":
            self.game.change_state("setting")  # sau này thêm state setting
        elif choice == "Thoát game":
            self.game.running = False

    def render(self, renderer):
        renderer.fill(COLORS["black"])
        
        title_y = 100
        # Tiêu đề lớn
        # self.game.font.render(renderer, "HIỆP SĨ KIẾM HUYỀN THOẠI", (SCREEN_WIDTH//2, title_y),
        #                       color=COLORS["yellow"], size=48, align="center")

        # Các lựa chọn
        y_offset = 220
        for i, option in enumerate(self.options):
            color = COLORS["yellow"] if i == self.selected else COLORS["white"]
            # self.game.font.render(renderer, option, (SCREEN_WIDTH//2, y_offset),
            #                       color=color, size=32, align="center")
            y_offset += 60
        
        # Hướng dẫn
        hint_y = SCREEN_HEIGHT - 100
        # self.game.font.render(renderer, "↑ ↓ : Chọn    ENTER / Z : Xác nhận    ESC : Quay lại",
        #                       (SCREEN_WIDTH//2, hint_y), color=COLORS["gray"], align="center")


class SettingUI:
    """UI cho phần Cài đặt (âm lượng, phím, fullscreen)"""
    def __init__(self, game):
        self.game = game
        self.options = ["Âm lượng nhạc", "Âm lượng hiệu ứng", "Fullscreen", "Quay lại"]
        self.selected = 0
        
        # Giá trị tạm (sẽ load từ settings.json sau)
        self.music_volume = 70
        self.sfx_volume = 90
        self.fullscreen = False

    def handle_input(self, event):
        if event.type == sdl2.SDL_KEYDOWN:
            key = event.key.keysym.sym
            
            if key == sdl2.SDLK_UP or key == sdl2.SDLK_w:
                self.selected = (self.selected - 1) % len(self.options)
            elif key == sdl2.SDLK_DOWN or key == sdl2.SDLK_s:
                self.selected = (self.selected + 1) % len(self.options)
            elif key == sdl2.SDLK_LEFT or key == sdl2.SDLK_a:
                self._adjust_value(-10)
            elif key == sdl2.SDLK_RIGHT or key == sdl2.SDLK_d:
                self._adjust_value(10)
            elif key == sdl2.SDLK_RETURN or key == sdl2.SDLK_z:
                self._select_option()

    def _adjust_value(self, delta):
        if self.selected == 0:  # nhạc
            self.music_volume = max(0, min(100, self.music_volume + delta))
        elif self.selected == 1:  # sfx
            self.sfx_volume = max(0, min(100, self.sfx_volume + delta))
        elif self.selected == 2:  # fullscreen
            self.fullscreen = not self.fullscreen
            # Áp dụng ngay
            flags = self.game.window.get_flags()
            if self.fullscreen:
                self.game.window.set_fullscreen(True)
            else:
                self.game.window.set_fullscreen(False)

    def _select_option(self):
        if self.selected == 3:  # Quay lại
            self.game.change_state("menu")

    def render(self, renderer):
        renderer.fill(COLORS["dark_gray"])
        
        # Tiêu đề
        # self.game.font.render(renderer, "CÀI ĐẶT", (SCREEN_WIDTH//2, 100), color=COLORS["white"], size=40, align="center")
        
        y_offset = 180
        for i, option in enumerate(self.options):
            color = COLORS["yellow"] if i == self.selected else COLORS["white"]
            text = option
            if i == 0:
                text += f": {self.music_volume}%"
            elif i == 1:
                text += f": {self.sfx_volume}%"
            elif i == 2:
                text += f": {'Bật' if self.fullscreen else 'Tắt'}"
            
            # self.game.font.render(renderer, text, (SCREEN_WIDTH//2, y_offset), color=color, align="center")
            y_offset += 50
        
        # Hướng dẫn
        # self.game.font.render(renderer, "← → : Điều chỉnh    ENTER : Chọn    ESC : Quay lại",
        #                       (SCREEN_WIDTH//2, SCREEN_HEIGHT - 80), color=COLORS["gray"], align="center")