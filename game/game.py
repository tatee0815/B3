"""
game.py - Class Game chính 
"""

import sdl2
import sdl2.ext
import sdl2.sdlttf as ttf
from game.utils.network import NetworkManager

from game.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS_TARGET,
    KEY_BINDINGS_DEFAULT, COLORS, PLAYER_MAX_HP, MAX_LIVES,
    MANA_MAX
)
from game.utils.assets import AudioManager
from game.utils.camera import Camera
from game.utils.save import save_game, load_game, get_save_value
from game.states.menu import MenuState
from game.states.setting import SettingState
from game.states.playing import PlayingState
from game.states.pause import PauseState
from game.states.win import WinState
from game.states.cutsence import CutsceneState
from game.ui.hud import HUD
from game.states.game_over import GameOverState
from game.states.lobby import LobbyState


class Game:
    def __init__(self, window, renderer):
        sdl2.SDL_SetHint(sdl2.SDL_HINT_RENDER_SCALE_QUALITY, b"1")
        
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

        self.player = None

        # Progress người chơi
        self.player_progress = {
            "current_level": "level1_village",
            "unlocked_skills": ["melee"],
            "double_jump": False,
            "skill_a_upgraded": False,
            "total_deaths": 0,
            "high_score": 0,
            "play_time": 0.0,
            "opened_chests": [],
            "checkpoint": None,
            "coin": 0,
            "lives": MAX_LIVES
        }
        self.game_mode = "single"  # "single" hoặc "multiplayer"
        self.network = NetworkManager()

        self.player_progress = load_game(self.player_progress)

        # Đảm bảo các key cần thiết tồn tại
        if "play_time" not in self.player_progress:
            self.player_progress["play_time"] = 0.0

        # Đảm bảo cấu trúc players (cho multiplayer)
        if "players" not in self.player_progress:
            # Chuyển đổi từ cấu trúc cũ (single player) sang mới
            self.player_progress["players"] = {
                "knight": {
                    "unlocked_skills": self.player_progress.get("unlocked_skills", ["melee"]),
                    "double_jump": self.player_progress.get("double_jump", False),
                    "skill_a_upgraded": self.player_progress.get("skill_a_upgraded", False),
                    "coin": self.player_progress.get("coin", 0),
                    "lives": self.player_progress.get("lives", MAX_LIVES),
                    "hp": self.player_progress.get("hp", PLAYER_MAX_HP),
                    "mana": self.player_progress.get("mana", 50),
                    "checkpoint": self.player_progress.get("checkpoint"),
                    "opened_chests": self.player_progress.get("opened_chests", [])
                },
                "princess": {
                    "unlocked_skills": ["melee"],
                    "double_jump": False,
                    "skill_a_upgraded": False,
                    "coin": 0,
                    "lives": MAX_LIVES,
                    "hp": PLAYER_MAX_HP,
                    "mana": 50,
                    "checkpoint": None,
                    "opened_chests": []
                }
            }
        self.lives = self.player_progress.get("lives", MAX_LIVES)

        self.setup()

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
        self.slowmo_timer = 0.0
        self.slowmo_factor = 1.0

        # Âm thanh
        AudioManager.init()
        st = self.states["setting"]
        AudioManager.set_volumes(st.music_volume, st.sfx_volume)
        AudioManager.play_bgm()

    def setup(self):
        from game.entities.player import Player
        from game.entities.princess import Princess
        
        # Đảm bảo cấu trúc players tồn tại (phòng khi load game cũ thiếu)
        if "players" not in self.player_progress:
            self.player_progress["players"] = {
                "knight": {
                    "unlocked_skills": ["melee"],
                    "double_jump": False,
                    "skill_a_upgraded": False,
                    "coin": 0,
                    "lives": MAX_LIVES,
                    "hp": PLAYER_MAX_HP,
                    "mana": 50,
                    "checkpoint": None,
                    "opened_chests": []
                },
                "princess": {
                    "unlocked_skills": ["melee"],
                    "double_jump": False,
                    "skill_a_upgraded": False,
                    "coin": 0,
                    "lives": MAX_LIVES,
                    "hp": PLAYER_MAX_HP,
                    "mana": 50,
                    "checkpoint": None,
                    "opened_chests": []
                }
            }
            # Copy dữ liệu cũ nếu có
            if "coin" in self.player_progress:
                self.player_progress["players"]["knight"]["coin"] = self.player_progress["coin"]
            if "lives" in self.player_progress:
                self.player_progress["players"]["knight"]["lives"] = self.player_progress["lives"]
            if "checkpoint" in self.player_progress:
                self.player_progress["players"]["knight"]["checkpoint"] = self.player_progress["checkpoint"]
            if "opened_chests" in self.player_progress:
                self.player_progress["players"]["knight"]["opened_chests"] = self.player_progress["opened_chests"]
            if "unlocked_skills" in self.player_progress:
                self.player_progress["players"]["knight"]["unlocked_skills"] = self.player_progress["unlocked_skills"]
            if "double_jump" in self.player_progress:
                self.player_progress["players"]["knight"]["double_jump"] = self.player_progress["double_jump"]
        
        if self.game_mode == "multi" and not self.network.is_host:
            self.player = Princess(self)
            self.player.progress = self.player_progress["players"]["princess"]
        else:
            self.player = Player(self)
            self.player.progress = self.player_progress["players"]["knight"]
        self.player.game = self
        
        # Đồng bộ self.lives với player hiện tại
        self.lives = self.player.progress.get("lives", MAX_LIVES)

    def get_save_filename(self):
        """Trả về tên file tương ứng với chế độ chơi hiện tại"""
        return "save_sp.json" if self.game_mode == "single" else "save_mp.json"

    def save_current_game(self):
        """Hàm bọc (wrapper) để các state gọi lưu game nhanh"""
        filename = self.get_save_filename()
        # Nếu là chơi mạng, lưu thêm port vào progress để lần sau 'Tiếp tục' tự mở lại
        if self.game_mode == "multi" and self.network.is_host:
            self.player_progress["last_port"] = self.network.sock.getsockname()[1]
            
        save_game(self.player_progress, filename)

    def load_selected_game(self):
        """Hàm bọc để nạp đúng file save"""
        filename = self.get_save_filename()
        self.player_progress = load_game(self.player_progress, filename)

    def load_port_from_save(self, filename="save_mp.json"):
        """Dùng cho LobbyState khi nhấn 'Tiếp tục' ở chế độ 2 người"""
        return get_save_value(filename, "last_port", 5555) # Mặc định 5555 nếu không thấy

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
        self.states["game_over"] = GameOverState(self)
        self.states["win"] = WinState(self)
        self.states["intro"] = CutsceneState(self, mode = "intro")
        self.states["outro"] = CutsceneState(self, mode = "outro")
        self.states["fail"] = CutsceneState(self, mode="fail")
        self.states["lobby"] = LobbyState(self)
        
    def change_state(self, state_name, **kwargs):
        if state_name not in self.states:
            print(f"State '{state_name}' không tồn tại!")
            return

        if self.current_state:
            self.current_state.on_exit()

        if state_name == "intro" and "mode" in kwargs:
            self.states[state_name] = CutsceneState(self, mode=kwargs["mode"])

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
        self.last_time = sdl2.timer.SDL_GetTicks()

    def set_resolution(self, width, height):
        """Thay đổi kích thước cửa sổ và cập nhật scale"""
        self.current_width = width
        self.current_height = height
        
        # 1. Đổi kích thước cửa sổ thật
        sdl2.SDL_SetWindowSize(self.window, width, height)
        # 2. Căn giữa cửa sổ ra giữa màn hình máy tính
        sdl2.SDL_SetWindowPosition(self.window, sdl2.SDL_WINDOWPOS_CENTERED, sdl2.SDL_WINDOWPOS_CENTERED)
        
        # 3. Tính lại Scale dựa trên kích thước gốc (1280x720)
        self.scale_x = self.current_width / self.logical_width
        self.scale_y = self.current_height / self.logical_height
        
        # 4. Camera LUÔN giữ kích thước Logical
        self.camera.width = self.logical_width
        self.camera.height = self.logical_height

    def handle_events(self):
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                self.running = False
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
        if self.slowmo_timer > 0:
            self.slowmo_timer -= delta_time
            effective_delta = delta_time * self.slowmo_factor
            if self.slowmo_timer <= 0:
                self.slowmo_factor = 1.0
        else:
            effective_delta = delta_time

        self.delta_time = effective_delta
        self.game_time += effective_delta

        # --- LẮNG NGHE MẠNG MỖI FRAME ---
        incoming_data = self.network.get_packets()
        if incoming_data and hasattr(self.current_state, "handle_network"):
            self.current_state.handle_network(incoming_data)

        if self.current_state:
            self.current_state.update(effective_delta)

        if self.current_state.name == "playing":
            if "play_time" in self.player_progress:
                self.player_progress["play_time"] += effective_delta
            else:
                # Nếu chưa có (do save cũ hoặc reset không đầy đủ) thì tạo mới
                self.player_progress["play_time"] = effective_delta
            player = self.states["playing"].player
            if player:
                self.camera.update(player)
                
    def reset_progress(self):
        # Giữ lại cấu trúc multiplayer nếu có
        if self.game_mode == "multi":
            self.player_progress = {
                "current_level": "level1_village",
                "play_time": 0.0,
                "players": {
                    "knight": {
                        "unlocked_skills": ["melee"],
                        "double_jump": False,
                        "skill_a_upgraded": False,
                        "coin": 0,
                        "lives": MAX_LIVES,
                        "hp": PLAYER_MAX_HP,
                        "mana": 50,
                        "checkpoint": None,
                        "opened_chests": []
                    },
                    "princess": {
                        "unlocked_skills": ["melee"],
                        "double_jump": False,
                        "skill_a_upgraded": False,
                        "coin": 0,
                        "lives": MAX_LIVES,
                        "hp": PLAYER_MAX_HP,
                        "mana": 50,
                        "checkpoint": None,
                        "opened_chests": []
                    }
                }
            }
        else:
            self.player_progress = {
                "current_level": "level1_village",
                "unlocked_skills": ["melee"],
                "double_jump": False,
                "skill_a_upgraded": False,
                "total_deaths": 0,
                "high_score": 0,
                "play_time": 0.0,
                "opened_chests": [],
                "checkpoint": None,
                "coin": 0,
                "lives": MAX_LIVES
            }
        if self.player:
            self.lives = self.player.progress.get("lives", MAX_LIVES)
        if self.player:
            self.setup()
        if "playing" in self.states:
            self.states["playing"].is_initialized = False

    def render(self):
        sdl2.SDL_SetRenderDrawColor(self.renderer, 0, 0, 0, 255)
        sdl2.SDL_RenderClear(self.renderer)

        sdl2.SDL_RenderSetScale(self.renderer, self.scale_x, self.scale_y)

        # Xử lý Render đặc biệt cho Pause (vẽ Playing làm nền)
        if self.current_state.name == "pause":
            self.states["playing"].render(self.renderer) # Vẽ game đang chơi bên dưới
            # sdl2.SDL_RenderSetScale(self.renderer, 1.0, 1.0)
            self.states["pause"].render(self.renderer)
        else:
            self.current_state.render(self.renderer)

            # Vẽ HUD riêng nếu đang chơi
            if self.current_state.name == "playing":
                self.hud.render(self.renderer)

        sdl2.SDL_RenderPresent(self.renderer)

    def run(self):
        clock = sdl2.SDL_GetTicks()
        while self.running:
            sdl2.SDL_Delay(10)
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

    def trigger_slowmo(self, duration=3.5, strength=0.35):
        """Kích hoạt slow-motion toàn game"""
        self.slowmo_timer = duration
        self.slowmo_factor = strength

    def on_quit(self):
        self.save_current_game()
        if self.current_state.name == "playing":
            if self.player and hasattr(self.player, 'checkpoint_pos'):
                # Lưu checkpoint vào đúng progress của player
                if hasattr(self.player, 'progress'):
                    self.player.progress["checkpoint"] = self.player.checkpoint_pos
                else:
                    self.player_progress["checkpoint"] = self.player.checkpoint_pos
        save_game(self.player_progress)