"""
State Menu chính - Màn hình bắt đầu game
"""

import sdl2
from game.constants import SCREEN_WIDTH, SCREEN_HEIGHT, COLORS, KEY_BINDINGS_DEFAULT


class MenuState:
    def __init__(self, game):
        self.game = game
        self.name = "menu"
        
        # Các lựa chọn menu (có thể mở rộng sau)
        self.options = ["Chơi ngay", "Cài đặt", "Thoát"]
        self.selected = 0

    def on_enter(self, **kwargs):
        print("Vào Menu")
        # Có thể load nhạc nền menu ở đây

    def on_exit(self):
        print("Thoát Menu")

    def handle_event(self, event):
        if event.type == sdl2.SDL_KEYDOWN:
            key = event.key.keysym.sym
            
            if key == sdl2.SDLK_UP or key == sdl2.SDLK_w:
                self.selected = (self.selected - 1) % len(self.options)
            elif key == sdl2.SDLK_DOWN or key == sdl2.SDLK_s:
                self.selected = (self.selected + 1) % len(self.options)
            elif key == sdl2.SDLK_RETURN or key == sdl2.SDLK_z:
                self._handle_selection()

    def _handle_selection(self):
        choice = self.options[self.selected]
        if choice == "Chơi ngay":
            self.game.change_state("playing")
        elif choice == "Cài đặt":
            # Sau này mở state Setting
            pass
        elif choice == "Thoát":
            self.game.running = False

    def update(self, delta_time):
        pass  # menu tĩnh, không cần update nhiều

    def render(self, renderer):
        renderer.clear(COLORS["black"])
        
        # Vẽ tiêu đề game
        # (sau này dùng font + sdl2.ext.renderer.draw_text)
        # tạm thời dùng comment để mô phỏng
        # self.game.font.render(renderer, "HIỆP SĨ KIẾM HUYỀN THOẠI", (SCREEN_WIDTH//2, 120), align="center")
        
        # Vẽ các lựa chọn
        y_offset = 220
        for i, option in enumerate(self.options):
            color = COLORS["yellow"] if i == self.selected else COLORS["white"]
            # self.game.font.render(renderer, option, (SCREEN_WIDTH//2, y_offset), color=color, align="center")
            y_offset += 60
        
        # Hướng dẫn phím
        # self.game.font.render(renderer, "↑ ↓ : Chọn    ENTER : Xác nhận", (SCREEN_WIDTH//2, SCREEN_HEIGHT - 80), align="center")