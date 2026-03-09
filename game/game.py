"""
Class Game chính - Quản lý toàn bộ game loop, states, và tài nguyên chung
"""

import sys
import sdl2
import sdl2.ext

from game.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS_TARGET,
    KEY_BINDINGS_DEFAULT, COLORS
)
from game.utils.assets import load_texture, load_sound
from game.utils.camera import Camera
from game.states.menu import MenuState
from game.states.playing import PlayingState
from game.states.pause import PauseState
from game.states.game_over import GameOverState
from game.states.win import WinState
from game.ui.hud import HUD


class Game:
    def __init__(self, window):
        self.window = window
        self.renderer = window.get_renderer()
        
        # Trạng thái game hiện tại
        self.current_state = None
        self.states = {}
        
        # Tài nguyên chung (có thể cache ở đây hoặc dùng assets.py)
        self.font = None  # sẽ load sau
        self.sounds = {}  # cache sound
        self.textures = {}  # cache texture nếu cần
        
        # Biến game toàn cục
        self.running = True
        self.paused = False
        self.game_time = 0.0          # thời gian chơi (giây)
        self.delta_time = 0.0         # thời gian frame (giây)

        # === THAY ĐỔI MỚI: Lives & Deaths ===
        self.lives = PLAYER_START_LIVES
        self.deaths = PLAYER_START_DEATHS
        
        # Player & progress (có thể lưu/load sau)
        self.player_progress = {
            "current_level": "level1_forest",
            "unlocked_skills": ["melee"],
            "double_jump": False,
            "skill_a_upgraded": False,
            "high_score": 0,
            "total_deaths": 0          # lưu vĩnh viễn số lần chết
        }
        
        # Camera chung (dùng trong playing state)
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # HUD (hiển thị HP, mana, vàng, timer...)
        self.hud = HUD(self)
        
        # Khởi tạo các state
        self._init_states()
        
        # Bắt đầu từ menu
        self.change_state("menu")
        
        # Load font chung (nếu dùng text rendering)
        # self.font = sdl2.ext.FontManager(FONT_PIXEL, size=16)

    def _init_states(self):
        """Khởi tạo tất cả các state"""
        self.states["menu"] = MenuState(self)
        self.states["playing"] = PlayingState(self)
        self.states["pause"] = PauseState(self)
        self.states["game_over"] = GameOverState(self)
        self.states["win"] = WinState(self)

    def change_state(self, state_name, **kwargs):
        """Chuyển đổi giữa các state"""
        if state_name not in self.states:
            print(f"State '{state_name}' không tồn tại!")
            return
        
        # Gọi cleanup của state cũ nếu có
        if self.current_state:
            self.current_state.on_exit()
        
        self.current_state = self.states[state_name]
        self.current_state.on_enter(**kwargs)

    def handle_events(self):
        """Xử lý event chung (quit, pause, fullscreen...)"""
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                self.running = False
            
            elif event.type == sdl2.SDL_KEYDOWN:
                key = event.key.keysym.sym
                
                # Phím pause chung (ESC)
                if key == KEY_BINDINGS_DEFAULT["pause"]:
                    if self.current_state.name == "playing":
                        self.change_state("pause")
                    elif self.current_state.name == "pause":
                        self.change_state("playing")
                
                # Fullscreen toggle (F11 ví dụ)
                elif key == sdl2.SDLK_F11:
                    flags = self.window.get_flags()
                    if flags & sdl2.SDL_WINDOW_FULLSCREEN:
                        self.window.set_fullscreen(False)
                    else:
                        self.window.set_fullscreen(True)
            
            # Chuyển event cho state hiện tại xử lý
            if self.current_state:
                self.current_state.handle_event(event)

    def update(self, delta_time):
        """Cập nhật logic game"""
        self.delta_time = delta_time
        self.game_time += delta_time
        
        if self.current_state:
            self.current_state.update(delta_time)
        
        # Cập nhật camera nếu đang chơi
        if self.current_state.name == "playing":
            self.camera.update(self.states["playing"].player)

    def render(self):
        """Vẽ toàn bộ frame"""
        self.renderer.clear(COLORS["black"])
        
        if self.current_state:
            self.current_state.render(self.renderer)
        
        # HUD chỉ vẽ khi đang chơi
        if self.current_state.name == "playing":
            self.hud.render(self.renderer)
        
        self.renderer.present()

    def run(self):
        """Vòng lặp game chính"""
        clock = sdl2.SDL_GetTicks()
        
        while self.running:
            new_clock = sdl2.SDL_GetTicks()
            delta_ms = new_clock - clock
            clock = new_clock
            
            # Giới hạn FPS
            if delta_ms < 1000 // FPS_TARGET:
                sdl2.SDL_Delay((1000 // FPS_TARGET) - delta_ms)
                delta_ms = 1000 // FPS_TARGET
            
            delta_time = delta_ms / 1000.0  # chuyển sang giây
            
            self.handle_events()
            self.update(delta_time)
            self.render()
        
        # Cleanup khi thoát
        self.on_quit()

    def on_quit(self):
        """Cleanup tài nguyên khi thoát game"""
        print("Game đang thoát...")
        # Lưu progress nếu cần
        # save_game(self.player_progress)
        
        # Giải phóng sound/texture nếu cache ở đây
        for sound in self.sounds.values():
            sdl2.mixer.Mix_FreeChunk(sound)
        self.sounds.clear()