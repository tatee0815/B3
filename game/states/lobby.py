import sdl2
import sdl2.sdlttf as ttf
from sdl2 import sdlimage as sdlimage
import random
import socket
import os
from game.constants import SCREEN_WIDTH, SCREEN_HEIGHT
from game.utils.assets import AudioManager

class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-1.0, 1.0)
        self.vy = random.uniform(-2.0, -0.5)
        self.life = random.uniform(1.0, 2.5)
        self.alpha = 255
        self.size = random.randint(2, 4)

class LobbyState:
    def __init__(self, game):
        self.game = game
        self.name = "lobby"
        self.mode_sent = False
        self.sub_state = "select"
        self.ready_to_start = {"me": False, "other": False}
        
        save_path = "save_mp.json"
        self.has_save = os.path.exists(save_path)
        self.selected_index = 0
        self._build_options()
        
        self.host_ip = self.get_local_ip()
        self.room_port = 0
        self.input_text = ""      # lưu mã phòng (Base36) hoặc IP
        self.is_continue = False
        self.connect_error = False
        self.ignore_z_input = False

        # Assets
        self.bg_texture = None
        self.bg_width = self.bg_height = 0
        self.title_tex = None
        self.title_rect = sdl2.SDL_Rect(0, 0, 0, 0)
        self.opt_textures = []
        self.hint_tex = None
        self.hint_rect = sdl2.SDL_Rect(0, 0, 0, 0)
        
        self.particles = []
        self.particle_timer = 0.0
        self.assets_loaded = False
        
        sdl2.SDL_StartTextInput()

    def _build_options(self):
        if self.has_save:
            self.options = ["Tiếp tục", "Tạo mới", "Tham gia", "Quay lại"]
        else:
            self.options = ["Tạo mới", "Tham gia", "Quay lại"]
        if hasattr(self, 'selected_index') and self.selected_index >= len(self.options):
            self.selected_index = 0

    def on_enter(self, **kwargs):
        # Reset network trước khi vào lobby
        if hasattr(self.game.network, 'close'):
            self.game.network.close()
            
        self.sub_state = "select"
        action = kwargs.get("action")
        self.is_continue = kwargs.get("is_continue", False)

        save_path = "save_mp.json"
        self.has_save = os.path.exists(save_path)
        self.selected_index = 0
        self._build_options()
        self.ready_to_start["other"] = False
        self.connect_error = False
        self.ignore_z_input = False
        self.mode_sent = False
        self.particles.clear()

        # TỰ ĐỘNG HÓA DỰA TRÊN MENU
        if action == "host":
            try:
                self.game.network.start_host(port=5555)
                self.sub_state = "waiting"
            except OSError:
                self.connect_error = True
        elif action == "client":
            self.sub_state = "joining"
            self.input_text = ""

        if not self.assets_loaded:
            self._init_assets()
            self.assets_loaded = True
        else:
            self._refresh_menu_textures()
        sdl2.SDL_StartTextInput()

    def _init_assets(self):
        renderer = self.game.renderer
        bg_path = "assets/backgrounds/menu_bg.png"
        surf = sdlimage.IMG_Load(bg_path.encode('utf-8'))
        if surf:
            self.bg_texture = sdl2.SDL_CreateTextureFromSurface(renderer, surf)
            self.bg_width = surf.contents.w
            self.bg_height = surf.contents.h
            sdl2.SDL_FreeSurface(surf)

        if hasattr(self.game, 'title_font') and self.game.title_font:
            t_surf = ttf.TTF_RenderUTF8_Blended(
                self.game.title_font,
                "ĐANG ĐỢI NGƯỜI CHƠI".encode('utf-8'),
                sdl2.SDL_Color(255, 215, 0)
            )
            if t_surf:
                self.title_tex = sdl2.SDL_CreateTextureFromSurface(renderer, t_surf)
                tw, th = t_surf.contents.w, t_surf.contents.h
                max_w = int(SCREEN_WIDTH * 0.8)
                if tw > max_w:
                    th = int(th * (max_w / tw))
                    tw = max_w
                self.title_rect = sdl2.SDL_Rect(SCREEN_WIDTH//2 - tw//2, 60, tw, th)
                sdl2.SDL_FreeSurface(t_surf)

        self._refresh_menu_textures()

        h_str = "UP / DOWN : Chọn  |  Z/ENTER : Xác nhận  |  ESC : Quay lại"
        h_surf = ttf.TTF_RenderUTF8_Blended(
            self.game.font,
            h_str.encode('utf-8'),
            sdl2.SDL_Color(220, 220, 220)
        )
        if h_surf:
            self.hint_tex = sdl2.SDL_CreateTextureFromSurface(renderer, h_surf)
            hw, hh = h_surf.contents.w, h_surf.contents.h
            self.hint_rect = sdl2.SDL_Rect(SCREEN_WIDTH//2 - hw//2, SCREEN_HEIGHT - 65, hw, hh)
            sdl2.SDL_FreeSurface(h_surf)

    def _refresh_menu_textures(self):
        for tex, _, _ in self.opt_textures:
            sdl2.SDL_DestroyTexture(tex)
        self.opt_textures = []
        if hasattr(self.game, 'font') and self.game.font:
            for opt in self.options:
                o_surf = ttf.TTF_RenderUTF8_Blended(
                    self.game.font,
                    opt.encode('utf-8'),
                    sdl2.SDL_Color(255, 255, 255)
                )
                if o_surf:
                    tex = sdl2.SDL_CreateTextureFromSurface(self.game.renderer, o_surf)
                    self.opt_textures.append((tex, o_surf.contents.w, o_surf.contents.h))
                    sdl2.SDL_FreeSurface(o_surf)

    def get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP

    def handle_event(self, event):
        if event.type == sdl2.SDL_KEYDOWN:
            scancode = event.key.keysym.scancode

            if self.sub_state == "select":
                if scancode == sdl2.SDL_SCANCODE_UP:
                    self.selected_index = (self.selected_index - 1) % len(self.options)
                    AudioManager.play_sfx("choice")
                elif scancode == sdl2.SDL_SCANCODE_DOWN:
                    self.selected_index = (self.selected_index + 1) % len(self.options)
                    AudioManager.play_sfx("choice")
                elif scancode in (sdl2.SDL_SCANCODE_RETURN, sdl2.SDL_SCANCODE_Z, sdl2.SDL_SCANCODE_SPACE):
                    selected = self.options[self.selected_index]
                    AudioManager.play_sfx("select")
                    
                    if selected == "Tiếp tục":
                        # Cố định port là 5555, không cần load port random từ save nữa
                        try:
                            self.game.network.start_host(port=5555)
                            self.sub_state = "waiting"
                            self.is_continue = True
                        except OSError:
                            self.connect_error = True
                            
                    elif selected == "Tạo mới":
                        # Khởi tạo máy chủ với port cố định 5555
                        try:
                            self.game.network.start_host(port=5555)
                            self.sub_state = "waiting"
                            self.is_continue = False
                            # RESET SAVE NGAY LẬP TỨC ĐỂ XÓA SNAPSHOT CŨ
                            self.game.reset_progress()
                        except OSError:
                            self.connect_error = True
                            
                    elif selected == "Tham gia":
                        self.sub_state = "joining"
                        self.input_text = ""
                        self.connect_error = False
                        if scancode == sdl2.SDL_SCANCODE_Z:
                            self.ignore_z_input = True
                    elif selected == "Quay lại":
                        self.game.change_state("menu")

            elif self.sub_state == "waiting":
                if scancode == sdl2.SDL_SCANCODE_ESCAPE:
                    self.game.network.close()
                    self.sub_state = "select"
                    AudioManager.play_sfx("choice")

            elif self.sub_state == "joining":
                if scancode == sdl2.SDL_SCANCODE_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                elif scancode == sdl2.SDL_SCANCODE_RETURN:
                    if len(self.input_text) > 0:
                        target_ip = self.game.network.decode_room_code(self.input_text)
                        self.game.network.connect_to_host(target_ip, port=5555)
                        self.sub_state = "connecting"
                        self.connect_error = False
                    else:
                        self.connect_error = True
                elif scancode == sdl2.SDL_SCANCODE_ESCAPE:
                    self.sub_state = "select"
                    AudioManager.play_sfx("choice")

            elif self.sub_state == "connecting":
                if scancode == sdl2.SDL_SCANCODE_ESCAPE:
                    self.game.network.close()
                    self.sub_state = "select"
                    AudioManager.play_sfx("choice")

        elif event.type == sdl2.SDL_TEXTINPUT and self.sub_state == "joining":
            char = event.text.text.decode('utf-8').upper()
            if getattr(self, 'ignore_z_input', False) and char == 'Z':
                self.ignore_z_input = False
                return
            if (char.isalnum() or char == '.') and len(self.input_text) < 15:
                self.input_text += char

    def handle_network(self, packets):
        """packets là một mảng (list) chứa các gói tin gửi về trong frame hiện tại"""
        for packet in packets:
            if packet.get("type") == "ready_to_load":
                self.ready_to_start["other"] = True
            elif packet.get("type") == "game_mode":
                self.is_continue = packet.get("is_continue", False)
                if "world_progress" in packet:
                    self.game.player_progress = packet["world_progress"]
                    print(f"[Lobby] Received world_progress from Host")
                    # LƯU NGAY BẢN BACKUP CHO CLIENT
                    self.game.save_current_game()
                print(f"[Lobby] Received game_mode: continue={self.is_continue}")
            elif packet.get("type") == "rejoin_signal":
                # NHẢY THẲNG VÀO TRẬN ĐANG DIỄN RA
                target_level = packet.get("level", "level1_village")
                self.game.player_progress["current_level"] = target_level
                print(f"[Lobby] Host is already in-game ({target_level}). Rejoining...")
                sdl2.SDL_StopTextInput()
                self.game.load_selected_game() # Nạp lại HP, Coin... từ file save
                self.game.change_state("playing", menu_continue=True)

    def update(self, delta_time):
        self.particle_timer += delta_time
        if self.particle_timer > 0.1 and self.title_tex:
            self.particle_timer = 0.0
            px = self.title_rect.x + random.randint(0, self.title_rect.w)
            py = self.title_rect.y + random.randint(0, self.title_rect.h)
            self.particles.append(Particle(px, py))

        for p in self.particles[:]:
            p.x += p.vx
            p.y += p.vy
            p.life -= delta_time
            p.alpha = int(max(0, 255 * (p.life / 2.5)))
            if p.life <= 0:
                self.particles.remove(p)

        if self.sub_state == "connecting":
            if self.game.network.connected:
                self.sub_state = "waiting"

        if self.game.network.is_host and self.game.network.connected and not self.mode_sent:
            # GỬI THÔNG TIN CHẾ ĐỘ CHƠI VÀ DỮ LIỆU THẾ GIỚI (World State)
            data = {"type": "game_mode", "is_continue": self.is_continue}
            if self.is_continue:
                self.game.load_selected_game() # Nạp save từ file save_mp.json
                data["world_progress"] = self.game.player_progress
            
            self.game.network.send_data(data)
            self.mode_sent = True
            print(f"[Lobby] Host sent game_mode (continue={self.is_continue})")

        if self.game.network.connected:
            self.game.network.send_data({"type": "ready_to_load"})
            if self.ready_to_start["other"]:
                sdl2.SDL_StopTextInput()
                if self.is_continue:
                    # KIỂM TRA XEM CÓ THẬT SỰ LÀ SAVE MỚI TINH KHÔNG (Vừa tạo xong chưa chơi)
                    prog = self.game.player_progress
                    is_fresh = (prog.get("play_time", 0) == 0 and 
                                prog.get("current_level") == "2p_level1_bodystone")
                    
                    if is_fresh:
                        print("[Lobby] Save is fresh. Redirecting to Intro...")
                        self.game.change_state("intro", mode="intro_2p", from_intro=True)
                    else:
                        # Máy Host đã load rồi, Client bây giờ sẽ nhận qua packet handle_network
                        self.game.change_state("playing", menu_continue=True)
                else:
                    self.game.reset_progress()
                    # Cả hai cùng vào intro 2 người
                    self.game.change_state("intro", mode="intro_2p", from_intro=True)

    def _draw_text_simple(self, renderer, text, x, y, color=(255,255,255), center_x=False):
        if not text or not hasattr(self.game, 'font'):
            return
        rgba = sdl2.SDL_Color(color[0], color[1], color[2], 255)
        surf = ttf.TTF_RenderUTF8_Blended(self.game.font, text.encode('utf-8'), rgba)
        if surf:
            tex = sdl2.SDL_CreateTextureFromSurface(renderer, surf)
            w, h = surf.contents.w, surf.contents.h
            if center_x:
                x = (SCREEN_WIDTH - w) // 2
            sdl2.SDL_RenderCopy(renderer, tex, None, sdl2.SDL_Rect(int(x), int(y), w, h))
            sdl2.SDL_DestroyTexture(tex)
            sdl2.SDL_FreeSurface(surf)

    def render(self, renderer):
        if self.bg_texture:
            scale = max(SCREEN_WIDTH / self.bg_width, SCREEN_HEIGHT / self.bg_height)
            nw, nh = int(self.bg_width * scale), int(self.bg_height * scale)
            dst = sdl2.SDL_Rect((SCREEN_WIDTH - nw)//2, (SCREEN_HEIGHT - nh)//2, nw, nh)
            sdl2.SDL_RenderCopy(renderer, self.bg_texture, None, dst)

        for p in self.particles:
            sdl2.SDL_SetRenderDrawColor(renderer, 255, 255, 180, p.alpha)
            sdl2.SDL_RenderFillRect(renderer, sdl2.SDL_Rect(int(p.x), int(p.y), p.size, p.size))

        if self.title_tex:
            sdl2.SDL_RenderCopy(renderer, self.title_tex, None, self.title_rect)

        sdl2.SDL_SetRenderDrawBlendMode(renderer, sdl2.SDL_BLENDMODE_BLEND)

        if self.sub_state == "select":
            start_y = SCREEN_HEIGHT // 2 - 100
            gap = 95
            for i, (tex, tw, th) in enumerate(self.opt_textures):
                is_sel = (i == self.selected_index)
                bx, by = SCREEN_WIDTH//2 - 225, start_y + i * gap
                bw, bh = 450, 75

                if is_sel:
                    sdl2.SDL_SetRenderDrawColor(renderer, 255, 200, 0, 255)
                    sdl2.SDL_RenderFillRect(renderer, sdl2.SDL_Rect(bx, by, bw, bh))
                    sdl2.SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255)
                    sdl2.SDL_RenderDrawRect(renderer, sdl2.SDL_Rect(bx-2, by-2, bw+4, bh+4))
                else:
                    sdl2.SDL_SetRenderDrawColor(renderer, 20, 20, 20, 160)
                    sdl2.SDL_RenderFillRect(renderer, sdl2.SDL_Rect(bx, by, bw, bh))

                sdl2.SDL_RenderCopy(renderer, tex, None, sdl2.SDL_Rect(bx + (bw-tw)//2, by + (bh-th)//2, tw, th))

            if self.hint_tex:
                sdl2.SDL_RenderCopy(renderer, self.hint_tex, None, self.hint_rect)

        elif self.sub_state == "waiting":
            if self.game.network.is_host:
                if not self.game.network.connected:
                    self._draw_text_simple(renderer, "ĐANG TẠO PHÒNG...", 0, 200, (255,215,0), center_x=True)
                    room_code = self.game.network.get_room_code()
                    self._draw_text_simple(renderer, f"Mã phòng: {room_code}", 0, 300, (255,255,255), center_x=True)
                    self._draw_text_simple(renderer, "Nhấn ESC để hủy", 0, 500, (150,150,150), center_x=True)
                else:
                    self._draw_text_simple(renderer, "CÔNG CHÚA ĐÃ KẾT NỐI!", 0, 300, (0,255,0), center_x=True)
                    self._draw_text_simple(renderer, "Đang đồng bộ dữ liệu...", 0, 350, (255,255,255), center_x=True)
            else:  # client
                if not self.game.network.connected:
                    self._draw_text_simple(renderer, "ĐANG KẾT NỐI...", 0, 300, (255,215,0), center_x=True)
                    self._draw_text_simple(renderer, "Chờ phản hồi từ Hiệp sĩ", 0, 350, (255,255,255), center_x=True)
                else:
                    self._draw_text_simple(renderer, "ĐÃ KẾT NỐI!", 0, 300, (0,255,0), center_x=True)
                    self._draw_text_simple(renderer, "Chờ Hiệp sĩ bắt đầu...", 0, 350, (255,255,255), center_x=True)

        elif self.sub_state == "joining":
            self._draw_text_simple(renderer, "THAM GIA PHÒNG", 0, 200, (255, 215, 0), center_x=True)
            self._draw_text_simple(renderer, "Nhập mã phòng (hoặc IP):", 0, 300, (200, 200, 200), center_x=True)
            self._draw_text_simple(renderer, self.input_text + "_", 0, 350, (255, 255, 255), center_x=True)
            self._draw_text_simple(renderer, "ENTER: kết nối | ESC: quay lại", 0, 500, (150,150,150), center_x=True)
            if self.connect_error:
                self._draw_text_simple(renderer, "Mã phòng không hợp lệ!", 0, 450, (255,0,0), center_x=True)

        elif self.sub_state == "connecting":
            self._draw_text_simple(renderer, "ĐANG KẾT NỐI...", 0, 300, (255, 215, 0), center_x=True)
            self._draw_text_simple(renderer, "Chờ phản hồi từ Hiệp sĩ", 0, 350, (255,255,255), center_x=True)

    def on_exit(self):
        sdl2.SDL_StopTextInput()