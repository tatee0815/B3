"""
game.py - Class Game chính (đã fix scale + resize mượt)
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

        # Trạng thái game
        self.current_state = None
        self.states = {}

        # Thời gian
        self.running = True
        self.delta_time = 0.0
        self.game_time = 0.0

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

        # Camera & HUD
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.hud = HUD(self)

        # Khởi tạo states
        self._init_states()
        self.change_state("menu")

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

                if self.current_state:
                    self.current_state.handle_event(event)

    def update(self, delta_time):
        self.delta_time = delta_time
        self.game_time += delta_time

        if self.current_state:
            self.current_state.update(delta_time)

        if self.current_state.name == "playing":
            player = self.states["playing"].player
            if player:
                self.camera.update(player)

    def render(self):
        # Clear màn hình
        sdl2.SDL_SetRenderDrawColor(self.renderer, 0, 0, 0, 255)
        sdl2.SDL_RenderClear(self.renderer)

        # Scale cho nội dung game
        sdl2.SDL_RenderSetScale(self.renderer, self.scale_x, self.scale_y)

        if self.current_state:
            self.current_state.render(self.renderer)

        # Reset scale rồi render HUD (để HUD không bị scale quá mạnh)
        sdl2.SDL_RenderSetScale(self.renderer, self.hud_scale, self.hud_scale)
        if self.current_state.name == "playing":
            self.hud.render(self.renderer)
        sdl2.SDL_RenderSetScale(self.renderer, 1.0, 1.0)   # Reset

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