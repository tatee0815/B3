import sdl2
import sdl2.sdlimage as sdlimage
from game.constants import SCREEN_WIDTH, SCREEN_HEIGHT

class CutsceneState:
    def __init__(self, game, mode="intro"):
        self.game = game
        self.mode = mode  # "intro", "outro", hoặc "fail"
        self.name = mode
        self.timer = 0.0
        self.duration = 25.0
        self.scroll_speed = 60.0 

        self.bg_texture = None
        self.bg_width = 0
        self.bg_height = 0
        self._load_background()

        # Biến để điều khiển độ mờ background
        self.bg_alpha = 255  # bắt đầu hoàn toàn rõ
        self.fade_start_time = 3.0       # bắt đầu mờ sau 3 giây
        self.fade_duration = 2.5         # mất 2.5 giây để mờ hoàn toàn
        self.target_alpha = 100          # độ mờ cuối cùng (có thể chỉnh 80–120)
        
        if self.mode == "intro":
            self.title = "HÀNH TRÌNH BẮT ĐẦU"
            self.lines = ["Năm 2036, Vương quốc Huyền Vũ bất ngờ bị bóng tối bao phủ...", "Công chúa Thanh Yên, người mang trong mình sức mạnh thần linh đã bị bắt giữ", "Công chúa là chìa khóa cuối cùng mà chúng cần để hồi sinh quỷ vương", "", "Trước tình cảnh đó, vị anh hùng Rauma đã đứng lên quyết tâm tiêu diệt cái ác", "Sứ mệnh của bạn là giải cứu công chúa và lấy lại ánh sáng cho Vương quốc!"]
            self.next_state = "playing"
        elif self.mode == "outro":
            self.title = "KẾT THÚC BẤT NGỜ"
            self.lines = ["Sau khi đánh bại trùm cuối và giải cứu công chúa", "Cô ấy bất ngờ tấn công bạn từ phía sau", "Hóa ra cô ấy lại là phù thủy Aurora97", "Ả ta dựng lên mọi thứ để loại bỏ anh hùng của thế giới này", "Cảm ơn bạn đã trải nghiệm game!", ""]
            self.next_state = "win"
        else: # mode == "fail"
            self.title = "VƯƠNG QUỐC SỤP ĐỔ"
            self.lines = ["Anh hùng đã ngã xuống...", "Hy vọng cuối cùng của Vương quốc đã tan biến.", "Bóng tối vĩnh viễn bao trùm vương quốc.", "", "Hãy làm lại ở kiếp sau nhé"]
            self.next_state = "game_over"

    def on_enter(self, **kwargs):
        self.timer = 0.0
        self.bg_alpha = 255
        
    def _load_background(self):
        """Load background theo mode (có thể dùng chung hoặc riêng)"""
        renderer = self.game.renderer
        bg_path = None
        
        if self.mode == "intro":
            bg_path = "assets/backgrounds/cutscene_intro.png"
        elif self.mode == "outro":
            bg_path = "assets/backgrounds/cutscene_outro.png"
        else:
            bg_path = "assets/backgrounds/cutscene_fail.png"

        if bg_path:
            surf = sdlimage.IMG_Load(bg_path.encode('utf-8'))
            if surf:
                self.bg_texture = sdl2.SDL_CreateTextureFromSurface(renderer, surf)
                if self.bg_texture:
                    # BẮT BUỘC phải set blend mode NGAY LÚC NÀY
                    sdl2.SDL_SetTextureBlendMode(self.bg_texture, sdl2.SDL_BLENDMODE_BLEND)
                    self.bg_width = surf.contents.w
                    self.bg_height = surf.contents.h
                sdl2.SDL_FreeSurface(surf)
        else:
            print("[WARN] No background path defined for mode:", self.mode)
    
    def on_exit(self):
        # Nếu là kết thúc game hoặc thất bại, reset toàn bộ tiến trình khi thoát cảnh
        if self.mode in ["fail"]:
            self.game.reset_progress()

    def handle_event(self, event):  
        if event.type == sdl2.SDL_KEYDOWN:
            if event.key.keysym.scancode in (sdl2.SDL_SCANCODE_X, sdl2.SDL_SCANCODE_RETURN):
                if self.mode == "intro":
                    self.game.change_state(self.next_state, from_intro=True)
                else:
                    self.game.change_state(self.next_state)

    def update(self, delta_time):
        state = sdl2.SDL_GetKeyboardState(None)
        if state[sdl2.SDL_SCANCODE_Z]:
            self.timer += delta_time * 10
        else:
            self.timer += delta_time

        if self.timer >= self.fade_start_time:
            fade_progress = min(1.0, (self.timer - self.fade_start_time) / self.fade_duration)
            self.bg_alpha = int(255 - (255 - self.target_alpha) * fade_progress)

        if self.timer >= self.duration:
            if self.mode == "intro":                           # <-- THÊM
                self.game.change_state(self.next_state, from_intro=True)
            else:
                self.game.change_state(self.next_state)

    def _draw_big_text(self, renderer, text, x, y, color=(255, 255, 255), scale=1.5):
        if not text or not hasattr(self.game, 'font'): return
        import sdl2.sdlttf as ttf
        rgba = sdl2.SDL_Color(color[0], color[1], color[2], 255)
        surf = ttf.TTF_RenderUTF8_Blended(self.game.font, text.encode('utf-8'), rgba)
        if surf:
            tex = sdl2.SDL_CreateTextureFromSurface(renderer, surf)
            w, h = surf.contents.w, surf.contents.h
            new_w, new_h = int(w * scale), int(h * scale)
            dst = sdl2.SDL_Rect((SCREEN_WIDTH - new_w) // 2, y, new_w, new_h)
            sdl2.SDL_RenderCopy(renderer, tex, None, dst)
            sdl2.SDL_DestroyTexture(tex)
            sdl2.SDL_FreeSurface(surf)

    def render(self, renderer):
        # Tắt blend mode để vẽ background nhanh và sạch (như menu.py)
        sdl2.SDL_SetRenderDrawBlendMode(renderer, sdl2.SDL_BLENDMODE_BLEND)

        # Vẽ background
        if self.bg_texture:
            scale = max(SCREEN_WIDTH / self.bg_width, SCREEN_HEIGHT / self.bg_height)
            nw = int(self.bg_width * scale)
            nh = int(self.bg_height * scale)
            dst = sdl2.SDL_Rect(
                (SCREEN_WIDTH - nw) // 2,
                (SCREEN_HEIGHT - nh) // 2,
                nw,
                nh
            )
            sdl2.SDL_SetTextureAlphaMod(self.bg_texture, self.bg_alpha)
            sdl2.SDL_RenderCopy(renderer, self.bg_texture, None, dst)
        else:
            # Fallback màu nền (đen cho intro/outro, đỏ thẫm cho fail)
            bg_color = (40, 0, 0) if self.mode == "fail" else (0, 0, 0)
            sdl2.SDL_SetRenderDrawColor(renderer, *bg_color, 255)
            sdl2.SDL_RenderClear(renderer)
        
        base_y = SCREEN_HEIGHT - (self.timer * self.scroll_speed) 
        
        # Tiêu đề (Màu vàng cho thắng/intro, màu đỏ tươi cho thất bại)
        title_y = 60
        t_color = (255, 0, 0) if self.mode == "fail" else (255, 215, 0)
        self._draw_big_text(renderer, self.title, 0, title_y, t_color, scale=2.0)
        
        for i, line in enumerate(self.lines):
            line_y = int(base_y + 150 + i * 95)
            if -100 < line_y < SCREEN_HEIGHT + 100:
                self._draw_big_text(renderer, line, 0, line_y, (255, 255, 255), scale=1.2)

        hint_msg = "Giữ [Z]: Đọc nhanh hơn | [X]: Bỏ qua"
        self._draw_big_text(renderer, hint_msg, 0, SCREEN_HEIGHT - 70, (180, 180, 180), scale=1.0)