import sdl2
import sdl2.sdlimage as sdlimage
from game.constants import SCREEN_WIDTH, SCREEN_HEIGHT

class CutsceneState:
    def __init__(self, game, mode="intro_1p"):
        self.game = game
        self.mode = mode  
        self.name = mode
        self.timer = 0.0
        self.duration = 25.0
        self.scroll_speed = 60.0 
        self.bg_texture = None
        self.bg_width = 0
        self.bg_height = 0
        self.bg_alpha = 255  
        self.fade_start_time = 3.0       
        self.fade_duration = 2.5         
        self.target_alpha = 100          
        
        self.local_ready = False
        self.remote_ready = False
        self.sync_timer = 0.0

        self._setup_content()
        self._load_background()

    def _setup_content(self):
        if self.mode == "intro_1p":
            self.title = "HÀNH TRÌNH BẮT ĐẦU"
            self.lines = ["Năm 2036, Vương quốc Huyền Vũ bất ngờ bị bóng tối bao phủ...", "Công chúa Thanh Yên đã bị bắt giữ để hiến tế", "Trước tình cảnh đó, vị anh hùng Rauma đã đứng lên", "Sứ mệnh của bạn là giải cứu công chúa một mình!"]
            self.next_state = "playing"
        elif self.mode == "intro_2p":
            self.title = "NGHI THỨC ĐẢO NGƯỢC"
            self.lines = ["Công chúa đã hiến tế, nhưng linh hồn vẫn ở lại...", "Thế giới song song đã mở ra kết nối hai người.", "Hãy cùng nhau tìm kiếm cổ vật để đảo ngược định mệnh!"]
            self.next_state = "playing"
        elif self.mode == "outro":
            self.title = "KẾT THÚC BẤT NGỜ"
            self.lines = ["Sau khi đánh bại trùm cuối và giải cứu công chúa", "Hóa ra cô ấy lại là phù thủy Aurora97", "Cảm ơn bạn đã trải nghiệm game!"]
            self.next_state = "win"
        else: # fail
            self.title = "VƯƠNG QUỐC SỤP ĐỔ"
            self.lines = ["Anh hùng đã ngã xuống...", "Hy vọng cuối cùng đã tan biến.", "Hãy làm lại ở kiếp sau nhé"]
            self.next_state = "game_over"

    def on_enter(self, **kwargs):
        self.timer = 0.0
        self.bg_alpha = 255
        self.local_ready = False
        self.remote_ready = False
        self.sync_timer = 0.0
        
    def _load_background(self):
        renderer = self.game.renderer
        bg_path = None
        
        if self.mode == "intro_1p":
            bg_path = "assets/backgrounds/cutscene_intro_1p.png"
        elif self.mode == "intro_2p":
            bg_path = "assets/backgrounds/cutscene_intro_2p.png"
        elif self.mode == "outro":
            bg_path = "assets/backgrounds/cutscene_outro.png"
        else:
            bg_path = "assets/backgrounds/cutscene_fail.png"

        surf = sdlimage.IMG_Load(bg_path.encode('utf-8'))
        if surf:
            self.bg_texture = sdl2.SDL_CreateTextureFromSurface(renderer, surf)
            if self.bg_texture:
                sdl2.SDL_SetTextureBlendMode(self.bg_texture, sdl2.SDL_BLENDMODE_BLEND)
                self.bg_width = surf.contents.w
                self.bg_height = surf.contents.h
            sdl2.SDL_FreeSurface(surf)
    
    def on_exit(self):
        if self.mode in ["fail"]:
            self.game.reset_progress()

    def handle_event(self, event):  
        if event.type == sdl2.SDL_KEYDOWN:
            if event.key.keysym.scancode in (sdl2.SDL_SCANCODE_X, sdl2.SDL_SCANCODE_RETURN):
                self._set_local_ready()

    def _set_local_ready(self):
        if not self.local_ready:
            self.local_ready = True
            if hasattr(self.game, "game_mode") and self.game.game_mode == "multi":
                self.game.network.send_data({"type": "intro_ready", "ready": True})
            else:
                self.game.change_state(self.next_state, from_intro=True)

    def handle_network(self, packets):
        if not (hasattr(self.game, "game_mode") and self.game.game_mode == "multi"):
            return
        for packet in packets:
            ptype = packet.get("type")
            if ptype == "intro_ready":
                self.remote_ready = packet.get("ready", False)
            elif ptype == "game_sync":
                # Đối phương đã vào game rồi, bắt buộc mình cũng phải vào ngay!
                self.remote_ready = True
                self.local_ready = True

    def update(self, delta_time):
        if hasattr(self.game, "game_mode") and self.game.game_mode == "multi":
            if self.local_ready:
                self.sync_timer += delta_time
                if self.sync_timer > 0.3:
                    self.sync_timer = 0.0
                    self.game.network.send_data({"type": "intro_ready", "ready": True})

            if self.local_ready and self.remote_ready:
                self.remote_ready = False # Tránh gọi liên tục
                self.game.change_state(self.next_state, from_intro=True)
                return

        if not self.local_ready:
            state = sdl2.SDL_GetKeyboardState(None)
            self.timer += delta_time * 10 if state[sdl2.SDL_SCANCODE_Z] else delta_time

            if self.timer >= self.fade_start_time:
                fade_progress = min(1.0, (self.timer - self.fade_start_time) / self.fade_duration)
                self.bg_alpha = int(255 - (255 - self.target_alpha) * fade_progress)

            if self.timer >= self.duration:
                self._set_local_ready()

    def _draw_big_text(self, renderer, text, x, y, color=(255, 255, 255), scale=1.5):
        if not text or not hasattr(self.game, 'font'): return
        import sdl2.sdlttf as ttf
        rgba = sdl2.SDL_Color(color[0], color[1], color[2], 255)
        surf = ttf.TTF_RenderUTF8_Blended(self.game.font, text.encode('utf-8'), rgba)
        if surf:
            tex = sdl2.SDL_CreateTextureFromSurface(renderer, surf)
            w, h = surf.contents.w, surf.contents.h
            new_w, new_h = int(w * scale), int(h * scale)
            dst = sdl2.SDL_Rect((SCREEN_WIDTH - new_w) // 2, int(y), new_w, new_h)
            sdl2.SDL_RenderCopy(renderer, tex, None, dst)
            sdl2.SDL_DestroyTexture(tex)
            sdl2.SDL_FreeSurface(surf)

    def render(self, renderer):
        sdl2.SDL_SetRenderDrawBlendMode(renderer, sdl2.SDL_BLENDMODE_BLEND)
        if self.bg_texture:
            scale = max(SCREEN_WIDTH / self.bg_width, SCREEN_HEIGHT / self.bg_height)
            nw, nh = int(self.bg_width * scale), int(self.bg_height * scale)
            dst = sdl2.SDL_Rect((SCREEN_WIDTH - nw) // 2, (SCREEN_HEIGHT - nh) // 2, nw, nh)
            sdl2.SDL_SetTextureAlphaMod(self.bg_texture, self.bg_alpha)
            sdl2.SDL_RenderCopy(renderer, self.bg_texture, None, dst)
        else:
            bg_color = (40, 0, 0) if self.mode == "fail" else (0, 0, 0)
            sdl2.SDL_SetRenderDrawColor(renderer, *bg_color, 255)
            sdl2.SDL_RenderClear(renderer)
        
        base_y = SCREEN_HEIGHT - (self.timer * self.scroll_speed) 
        t_color = (255, 0, 0) if self.mode == "fail" else (255, 215, 0)
        self._draw_big_text(renderer, self.title, 0, 60, t_color, scale=2.0)
        
        for i, line in enumerate(self.lines):
            line_y = base_y + 150 + i * 95
            if -100 < line_y < SCREEN_HEIGHT + 100:
                self._draw_big_text(renderer, line, 0, line_y, (255, 255, 255), scale=1.2)

        if self.local_ready and hasattr(self.game, "game_mode") and self.game.game_mode == "multi":
            self._draw_big_text(renderer, "Đang chờ người chơi kia...", 0, SCREEN_HEIGHT - 35, (0, 255, 0), scale=1.0)
        else:
            self._draw_big_text(renderer, "Giữ [Z]: Đọc nhanh hơn | [X]: Bỏ qua", 0, SCREEN_HEIGHT - 70, (180, 180, 180), scale=1.0)