"""
game.py - Class Game chính (đã fix scale + resize mượt)
"""

import sdl2
import sdl2.ext
import sdl2.sdlttf as ttf

from game.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS_TARGET,
    KEY_BINDINGS_DEFAULT, COLORS, PLAYER_MAX_HP, MAX_LIVES,
    MANA_MAX
)
from game.utils.camera import Camera
from game.utils.save import save_game, load_game
from game.states.menu import MenuState
from game.states.setting import SettingState
from game.states.playing import PlayingState
from game.states.pause import PauseState
from game.states.win import WinState
from game.ui.hud import HUD


class Game:
    def __init__(self, window, renderer):
        self.window = window
        self.renderer = renderer

        # Kích thước gốc (không thay đổi)
        self.logical_width = SCREEN_WIDTH
        self.logical_height = SCREEN_HEIGHT

        # Kích thước thực tế của cửa sổ (cập nhật khi resize)
        self.current_width = SCREEN_WIDTH
        self.current_height = SCREEN_HEIGHT

        # Scale chính cho nội dung game (menu, level, background)
        self.scale_x = 1.0
        self.scale_y = 1.0

        # Scale riêng cho HUD (giữ nhỏ hơn để dễ đọc)
        self.hud_scale = 1.0

        # Khởi tạo Font
        self._init_fonts()

        # Trạng thái game
        self.current_state = None
        self.states = {}

        self.is_paused = False
        self.last_time = sdl2.timer.SDL_GetTicks()

        # Progress người chơi
        self.player_progress = {
            "current_level": "level1_forest",
            "unlocked_skills": ["melee"],
            "double_jump": False,
            "skill_a_upgraded": False,
            "total_deaths": 0,
            "high_score": 0
        }
        self.player_progress = load_game(self.player_progress)
        self.lives = MAX_LIVES

        self.reset_progress()

        # Camera & HUD
        self.camera = Camera(self, SCREEN_WIDTH, SCREEN_HEIGHT)
        self.hud = HUD(self)

        # Khởi tạo states
        self._init_states()
        self.change_state("menu")

        self.is_paused = False

        # Thời gian
        self.running = True
        self.delta_time = 0.0
        self.game_time = 0.0

    def _init_fonts(self):
        """Khởi tạo thư viện và nạp font hệ thống"""
        if ttf.TTF_Init() == -1:
            print("Không thể khởi tạo SDL_ttf")
            return

        font_path = "assets/fonts/UTM-Netmuc-KT.ttf"
        self.font = ttf.TTF_OpenFont(font_path.encode(), 30)
        self.title_font = ttf.TTF_OpenFont(font_path.encode(), 70)

        if not self.font or not self.title_font:
            print(f"Cảnh báo: Không tìm thấy file font tại {font_path}")

    def _init_states(self):
        self.states["menu"] = MenuState(self)
        self.states["setting"] = SettingState(self)
        self.states["playing"] = PlayingState(self)
        self.states["pause"] = PauseState(self)
        self.states["win"] = WinState(self)

    def change_state(self, state_name, **kwargs):
        if state_name not in self.states:
            print(f"State '{state_name}' không tồn tại!")
            return

        if self.current_state:
            self.current_state.on_exit()

        self.current_state = self.states[state_name]
        self.current_state.on_enter(**kwargs)

    def toggle_pause(self):
        """Bật/Tắt trạng thái tạm dừng mà không làm mất tiến trình"""
        if self.current_state.name == "playing":
            self.is_paused = True
            self.current_state = self.states["pause"]
            self.current_state.on_enter()
        elif self.current_state.name == "pause":
            self.resume_game()

    def resume_game(self):
        """Quay lại trạng thái chơi mà không gọi on_enter của PlayingState"""
        self.is_paused = False
        self.current_state = self.states["playing"]

    def handle_events(self):
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                self.running = False
            elif event.type == sdl2.SDL_WINDOWEVENT:
                if event.window.event == sdl2.SDL_WINDOWEVENT_RESIZED:
                    # Cập nhật kích thước thực tế chính xác từ sự kiện
                    self.current_width = event.window.data1
                    self.current_height = event.window.data2
                    
                    # Tính toán scale chỉ để các state dùng nếu cần, 
                    # không áp dụng vào SDL_RenderSetScale nữa
                    self.scale_x = self.current_width / SCREEN_WIDTH
                    self.scale_y = self.current_height / SCREEN_HEIGHT
                    
                    # Cập nhật camera theo kích thước thực
                    self.camera.width = self.current_width
                    self.camera.height = self.current_height

            if event.type == sdl2.SDL_KEYDOWN:
                if event.key.keysym.scancode == sdl2.SDL_SCANCODE_ESCAPE:
                    if self.current_state.name == "playing":
                        self.toggle_pause()
                        continue

            if self.current_state:
                if hasattr(self.current_state, "handle_event"):
                    self.current_state.handle_event(event)
                elif hasattr(self.current_state, "handle_input"):
                    self.current_state.handle_input(event)

    def update(self, delta_time):
        self.delta_time = delta_time
        self.game_time += delta_time

        if self.current_state:
            self.current_state.update(delta_time)

        if self.current_state.name == "playing":
            player = self.states["playing"].player
            if player:
                self.camera.update(player)
                
    def reset_progress(self):
        self.player_progress = {
            "current_level": "level1_forest",
            "hp": PLAYER_MAX_HP,
            "mana": MANA_MAX,
            "gold": 0,
            "double_jump": False,
            "total_deaths": 0,
            "unlocked_skills": []
        }
        # Nếu bạn có hệ thống lives (mạng)
        self.lives = MAX_LIVES

    def render(self):
        sdl2.SDL_SetRenderDrawColor(self.renderer, 0, 0, 0, 255)
        sdl2.SDL_RenderClear(self.renderer)

        # Xử lý Render đặc biệt cho Pause (vẽ Playing làm nền)
        if self.current_state.name == "pause":
            sdl2.SDL_RenderSetScale(self.renderer, self.scale_x, self.scale_y)
            self.states["playing"].render(self.renderer) # Vẽ game đang chơi bên dưới
            
            sdl2.SDL_RenderSetScale(self.renderer, 1.0, 1.0) # Reset để vẽ Pause đè lên toàn màn hình
            self.states["pause"].render(self.renderer)
        else:
            # Render thông thường cho các state khác
            sdl2.SDL_RenderSetScale(self.renderer, self.scale_x, self.scale_y)
            self.current_state.render(self.renderer)

            # Vẽ HUD riêng nếu đang chơi
            if self.current_state.name == "playing":
                sdl2.SDL_RenderSetScale(self.renderer, self.hud_scale, self.hud_scale)
                self.hud.render(self.renderer)

        sdl2.SDL_RenderPresent(self.renderer)

    def run(self):
        clock = sdl2.SDL_GetTicks()
        while self.running:
            new_clock = sdl2.SDL_GetTicks()
            delta_ms = new_clock - clock
            clock = new_clock

            if delta_ms < 1000 // FPS_TARGET:
                sdl2.SDL_Delay((1000 // FPS_TARGET) - delta_ms)
                delta_ms = 1000 // FPS_TARGET

            delta_time = delta_ms / 1000.0

            self.handle_events()
            self.update(delta_time)
            self.render()

        self.on_quit()

    def on_quit(self):
        print("Game đang thoát... Lưu tiến độ.")
        save_game(self.player_progress)