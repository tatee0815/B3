# -*- coding: utf-8 -*-
import sdl2
from sdl2 import sdlimage as sdlimage
import sdl2.sdlttf as ttf
import random
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

class MenuState:
    def __init__(self, game):
        self.game = game
        self.name = "menu"
        self.options = ["Tiếp tục","Bắt đầu mới", "Cài đặt", "Thoát game"]
        self.selected = 0

        # Assets & Textures
        self.bg_texture = None
        self.title_tex = None
        self.title_rect = sdl2.SDL_Rect(0, 0, 0, 0)
        self.opt_textures = []
        self.hint_tex = None
        self.hint_rect = sdl2.SDL_Rect(0, 0, 0, 0)

        # Effects
        self.particles = []
        self.particle_timer = 0.0
        self.assets_loaded = False

    def on_enter(self, **kwargs):
        self.selected = 0
        self.particles.clear()
        if not self.assets_loaded:
            self._init_assets()
            self.assets_loaded = True

    def _init_assets(self):
        """Khởi tạo toàn bộ tài nguyên, dọn dẹp rác bộ nhớ"""
        renderer = self.game.renderer

        # 1. Load Background
        bg_path = "assets/backgrounds/menu_bg.png"
        surf = sdlimage.IMG_Load(bg_path.encode('utf-8'))
        if surf:
            self.bg_texture = sdl2.SDL_CreateTextureFromSurface(renderer, surf)
            self.bg_width = surf.contents.w
            self.bg_height = surf.contents.h
            sdl2.SDL_FreeSurface(surf)
        
        # 2. Render Tiêu đề (Chống tràn)
        if hasattr(self.game, 'title_font') and self.game.title_font:
            t_surf = ttf.TTF_RenderUTF8_Blended(self.game.title_font, "HIỆP SĨ KIẾM HUYỀN THOẠI".encode('utf-8'), sdl2.SDL_Color(255, 215, 0))
            if t_surf:
                self.title_tex = sdl2.SDL_CreateTextureFromSurface(renderer, t_surf)
                tw, th = t_surf.contents.w, t_surf.contents.h
                max_w = int(SCREEN_WIDTH * 0.8)
                if tw > max_w:
                    th = int(th * (max_w / tw))
                    tw = max_w
                self.title_rect = sdl2.SDL_Rect(SCREEN_WIDTH//2 - tw//2, 60, tw, th)
                sdl2.SDL_FreeSurface(t_surf)

        # 3. Render Options
        self.opt_textures = []
        if hasattr(self.game, 'font') and self.game.font:
            for opt in self.options:
                o_surf = ttf.TTF_RenderUTF8_Blended(self.game.font, opt.encode('utf-8'), sdl2.SDL_Color(255, 255, 255))
                if o_surf:
                    tex = sdl2.SDL_CreateTextureFromSurface(self.game.renderer, o_surf)
                    self.opt_textures.append((tex, o_surf.contents.w, o_surf.contents.h))
                    sdl2.SDL_FreeSurface(o_surf)

            # 5. Render Hint (Sửa lỗi chữ bị dồn ở góc)
            h_str = "UP / DOWN : Chọn  |  Z : Xác nhận  |  ESC : Thoát"
            h_surf = ttf.TTF_RenderUTF8_Blended(self.game.font, h_str.encode('utf-8'), sdl2.SDL_Color(220, 220, 220))
            if h_surf:
                self.hint_tex = sdl2.SDL_CreateTextureFromSurface(renderer, h_surf)
                hw, hh = h_surf.contents.w, h_surf.contents.h
                # Căn giữa chính xác ở cạnh dưới
                self.hint_rect = sdl2.SDL_Rect(SCREEN_WIDTH//2 - hw//2, SCREEN_HEIGHT - 65, hw, hh)
                sdl2.SDL_FreeSurface(h_surf)

    def update(self, delta_time):
        self.particle_timer += delta_time
        if self.particle_timer > 0.1:
            self.particle_timer = 0.0
            px = self.title_rect.x + random.randint(0, self.title_rect.w)
            py = self.title_rect.y + random.randint(0, self.title_rect.h)
            self.particles.append(Particle(px, py))

        for p in self.particles[:]:
            p.x += p.vx
            p.y += p.vy
            p.life -= delta_time
            p.alpha = int(max(0, 255 * (p.life / 2.5)))
            if p.life <= 0: self.particles.remove(p)

    def handle_event(self, event):
        if event.type == sdl2.SDL_KEYDOWN:
            scancode = event.key.keysym.scancode
            
            # Chỉ nhận phím mũi tên Lên/Xuống
            if scancode == sdl2.SDL_SCANCODE_UP:
                self.selected = (self.selected - 1) % len(self.options)
                AudioManager.play_sfx("choice")
            elif scancode == sdl2.SDL_SCANCODE_DOWN:
                self.selected = (self.selected + 1) % len(self.options)
                AudioManager.play_sfx("choice")
            
            # Phím xác nhận (Z, Enter hoặc Space)
            elif scancode in (sdl2.SDL_SCANCODE_RETURN, sdl2.SDL_SCANCODE_Z, sdl2.SDL_SCANCODE_SPACE):
                self._handle_selection()
                AudioManager.play_sfx("select")
            
            # Phím thoát nhanh
            elif scancode == sdl2.SDL_SCANCODE_ESCAPE:
                self.game.running = False

    def _handle_selection(self):
        choice = self.options[self.selected]
        
        if choice == "Tiếp tục":
            # Kiểm tra nếu có file save thì mới vào game luôn, không thì vào intro
            self.game.change_state("playing", menu_continue=True)
            
        elif choice == "Bắt đầu mới":
            # Buộc PlayingState phải load lại map và reset Player về vị trí spawn gốc
            self.game.reset_progress()  # Đảm bảo reset lại progress nếu có
            self.game.change_state("intro")
            
        elif choice == "Cài đặt":
            self.game.change_state("setting")
            
        elif choice == "Thoát game":
            self.game.running = False

    def render(self, renderer):
        sdl2.SDL_SetRenderDrawBlendMode(renderer, sdl2.SDL_BLENDMODE_NONE)

        # 1. Background (Fill toàn màn hình)
        if self.bg_texture:
            scale = max(SCREEN_WIDTH / self.bg_width, SCREEN_HEIGHT / self.bg_height)
            nw, nh = int(self.bg_width * scale), int(self.bg_height * scale)
            dst = sdl2.SDL_Rect((SCREEN_WIDTH - nw)//2, (SCREEN_HEIGHT - nh)//2, nw, nh)
            sdl2.SDL_RenderCopy(renderer, self.bg_texture, None, dst)

        # 2. Particles
        for p in self.particles:
            sdl2.SDL_SetRenderDrawColor(renderer, 255, 255, 180, p.alpha)
            sdl2.SDL_RenderFillRect(renderer, sdl2.SDL_Rect(int(p.x), int(p.y), p.size, p.size))

        # 3. Tiêu đề
        if self.title_tex:
            sdl2.SDL_RenderCopy(renderer, self.title_tex, None, self.title_rect)
        
        sdl2.SDL_SetRenderDrawBlendMode(renderer, sdl2.SDL_BLENDMODE_BLEND)

        # 4. Menu Options
        start_y = SCREEN_HEIGHT // 2 - 100
        gap = 95
        for i, (tex, tw, th) in enumerate(self.opt_textures):
            is_sel = (i == self.selected)
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
            
            # Vẽ chữ căn giữa Box
            sdl2.SDL_RenderCopy(renderer, tex, None, sdl2.SDL_Rect(bx + (bw-tw)//2, by + (bh-th)//2, tw, th))

        # 5. Hint (Vẽ duy nhất một lần ở trung tâm dưới)
        if self.hint_tex:
            sdl2.SDL_RenderCopy(renderer, self.hint_tex, None, self.hint_rect)

    def on_exit(self): pass