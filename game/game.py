"""
game.py - Class Game chính: quản lý toàn bộ vòng đời game
- Chuyển đổi states (menu → playing → pause → win)
- Quản lý camera, HUD, progress
- Xử lý event chung (pause, fullscreen)
"""

import sdl2
import sdl2.ext

from game.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS_TARGET,
    KEY_BINDINGS_DEFAULT, COLORS, PLAYER_MAX_HP, MAX_LIVES,
    MANA_MAX
)
from game.utils.camera import Camera
from game.utils.save import save_game, load_game
from game.states.menu import MenuState
from game.states.playing import PlayingState
from game.states.pause import PauseState
from game.states.win import WinState
from game.ui.hud import HUD


class Game:
    def __init__(self, window, renderer):
        self.window = window
        self.renderer = renderer

        # Kích thước hiện tại của cửa sổ (cập nhật khi resize)
        self.current_width = SCREEN_WIDTH
        self.current_height = SCREEN_HEIGHT

        # Scale factor (dùng để scale nội dung)
        self.scale_x = 1.0
        self.scale_y = 1.0

        # Scale riêng cho HUD/font (giữ nhỏ hơn hoặc cố định)
        self.hud_scale = 1.0

        # Trạng thái game hiện tại
        self.current_state = None
        self.states = {}

        # Thời gian & delta
        self.running = True
        self.delta_time = 0.0
        self.game_time = 0.0  # thời gian chơi tổng (giây)

        # Progress người chơi (unlock skill, lives, deaths...)
        self.player_progress = {
            "current_level": "level1_forest",
            "unlocked_skills": ["melee"],  # ban đầu chỉ có chém kiếm
            "double_jump": False,
            "skill_a_upgraded": False,
            "total_deaths": 0,
            "high_score": 0
        }

        # Load progress từ save (nếu có)
        self.player_progress = load_game(self.player_progress)

        # Lives & deaths (quản lý riêng cho dễ reset)
        self.lives = MAX_LIVES

        # Camera chung (follow player)
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)

        # HUD (HP, mana, vàng, lives, deaths, timer)
        self.hud = HUD(self)

        # Khởi tạo tất cả states
        self._init_states()

        # Bắt đầu từ menu
        self.change_state("menu")

    def _init_states(self):
        """Khởi tạo các trạng thái game"""
        self.states["menu"] = MenuState(self)
        self.states["playing"] = PlayingState(self)
        self.states["pause"] = PauseState(self)
        self.states["win"] = WinState(self)

    def change_state(self, state_name, **kwargs):
        """Chuyển đổi trạng thái game"""
        if state_name not in self.states:
            print(f"State '{state_name}' không tồn tại!")
            return

        # Cleanup state cũ
        if self.current_state:
            self.current_state.on_exit()

        self.current_state = self.states[state_name]
        self.current_state.on_enter(**kwargs)
        print(f"Chuyển sang state: {state_name}")

    def handle_events(self):
        """Xử lý event chung cho toàn game"""
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                self.running = False

            elif event.type == sdl2.SDL_KEYDOWN:
                key = event.key.keysym.sym

                # Pause chung (ESC)
                if key == KEY_BINDINGS_DEFAULT["pause"]:
                    if self.current_state.name == "playing":
                        self.change_state("pause")
                    elif self.current_state.name == "pause":
                        self.change_state("playing")

                # Fullscreen toggle (F11)
                elif key == sdl2.SDLK_F11:
                    flags = self.window.get_flags()
                    if flags & sdl2.SDL_WINDOW_FULLSCREEN:
                        self.window.set_fullscreen(False)
                    else:
                        self.window.set_fullscreen(True)

            elif event.type == sdl2.SDL_WINDOWEVENT:
                if event.window.event == sdl2.SDL_WINDOWEVENT_RESIZED:
                    # Cửa sổ thay đổi kích thước
                    new_width = event.window.data1
                    new_height = event.window.data2

                    # Cập nhật kích thước hiện tại
                    self.current_width = new_width
                    self.current_height = new_height

                    # Cập nhật scale (so với kích thước gốc)
                    self.scale_x = new_width / SCREEN_WIDTH
                    self.scale_y = new_height / SCREEN_HEIGHT

                    # Scale HUD/font: giữ gần 1.0 (hoặc scale nhẹ theo min để không quá to)
                    min_scale = min(self.scale_x, self.scale_y)

                    # Cập nhật camera nếu có
                    if hasattr(self.camera, 'width'):
                        self.camera.width = new_width
                        self.camera.height = new_height

            # Chuyển event cho state hiện tại xử lý
            if self.current_state:
                self.current_state.handle_event(event)

    def update(self, delta_time):
        self.delta_time = delta_time
        self.game_time += delta_time

        if self.current_state:
            self.current_state.update(delta_time)

        # Cập nhật camera nếu đang chơi
        if self.current_state.name == "playing":
            player = self.states["playing"].player
            if player:
                self.camera.update(player)

    def render(self):
        # Set scale theo kích thước cửa sổ hiện tại
        sdl2.SDL_RenderSetScale(self.renderer, self.scale_x, self.scale_y)

        # Low-level: set màu đen và clear màn hình
        sdl2.SDL_SetRenderDrawColor(self.renderer, 0, 0, 0, 255)
        sdl2.SDL_RenderClear(self.renderer)

        # Render state hiện tại (cũng cần low-level)
        if self.current_state:
            self.current_state.render(self.renderer)

        # HUD nếu đang chơi
        if self.current_state.name == "playing":
            self.hud.render(self.renderer)

        sdl2.SDL_RenderSetScale(self.renderer, self.hud_scale, self.hud_scale)
        
        # Low-level: present (hiển thị lên màn hình)
        sdl2.SDL_RenderPresent(self.renderer)

    def run(self):
        """Vòng lặp game chính"""
        clock = sdl2.SDL_GetTicks()

        while self.running:
            new_clock = sdl2.SDL_GetTicks()
            delta_ms = new_clock - clock
            clock = new_clock

            # Giới hạn FPS (~60fps)
            if delta_ms < 1000 // FPS_TARGET:
                sdl2.SDL_Delay((1000 // FPS_TARGET) - delta_ms)
                delta_ms = 1000 // FPS_TARGET

            delta_time = delta_ms / 1000.0

            self.handle_events()
            self.update(delta_time)
            self.render()

        # Cleanup khi thoát
        self.on_quit()

    def on_quit(self):
        """Cleanup khi thoát game"""
        print("Game đang thoát... Lưu tiến độ.")
        save_game(self.player_progress)

        # Giải phóng tài nguyên nếu có cache
        # Ví dụ: self.font.close() nếu dùng font