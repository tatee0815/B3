"""
HUD hoàn chỉnh - Scale mượt theo cửa sổ, chữ tiếng Việt rõ nét
"""

import sdl2
import sdl2.sdlttf as ttf
from game.constants import PLAYER_MAX_HP, MANA_MAX, MAX_LIVES, COLORS, SCREEN_HEIGHT


class HUD:
    def __init__(self, game):
        self.game = game
        self.font = None
        self.current_font_size = 0
        self._load_font()
        
        # Minimap properties
        self.minimap_texture = None
        self.last_level_name = ""
        self.minimap_w = 200
        self.minimap_h = 0
        self.minimap_scale = 0.0

    def _load_font(self):
        # Tính toán font size dựa trên scale thực tế của cửa sổ
        base_size = 22
        target_size = int(base_size * self.game.scale_y)
        
        # Chỉ load lại nếu size thay đổi
        if target_size != self.current_font_size:
            font_path = "assets/fonts/UTM-Netmuc-KT.ttf"
            if self.font: ttf.TTF_CloseFont(self.font)
            self.font = ttf.TTF_OpenFont(font_path.encode(), target_size)
            self.current_font_size = target_size

    def _generate_minimap_terrain(self, renderer, level):
        """Tạo texture tĩnh cho địa hình Minimap để tối ưu hiệu suất"""
        if self.minimap_texture:
            sdl2.SDL_DestroyTexture(self.minimap_texture)
        
        self.minimap_scale = self.minimap_w / level.pixel_width
        self.minimap_h = int(level.pixel_height * self.minimap_scale)
        
        # Tạo texture với quyền truy cập TARGET để có thể vẽ lên nó
        self.minimap_texture = sdl2.SDL_CreateTexture(
            renderer, 
            sdl2.SDL_PIXELFORMAT_RGBA8888, 
            sdl2.SDL_TEXTUREACCESS_TARGET, 
            self.minimap_w, self.minimap_h
        )
        
        # Lưu render target cũ
        old_target = sdl2.SDL_GetRenderTarget(renderer)
        sdl2.SDL_SetRenderTarget(renderer, self.minimap_texture)
        
        # Xóa nền texture (đen mờ)
        sdl2.SDL_SetRenderDrawBlendMode(renderer, sdl2.SDL_BLENDMODE_BLEND)
        sdl2.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 150)
        sdl2.SDL_RenderClear(renderer)
        
        # Vẽ tường (Tiles)
        sdl2.SDL_SetRenderDrawColor(renderer, 100, 100, 100, 255) # Màu xám cho tường
        for y, row in enumerate(level.tiles):
            for x, tile_id in enumerate(row):
                if tile_id == 1: # ID va chạm
                    tx = int(x * level.tile_size * self.minimap_scale)
                    ty = int(y * level.tile_size * self.minimap_scale)
                    tw = max(1, int(level.tile_size * self.minimap_scale))
                    th = max(1, int(level.tile_size * self.minimap_scale))
                    sdl2.SDL_RenderFillRect(renderer, sdl2.SDL_Rect(tx, ty, tw, th))
        
        # Vẽ các platform cố định
        sdl2.SDL_SetRenderDrawColor(renderer, 80, 150, 80, 255)
        for plat in level.platforms:
            if not hasattr(plat, "vel_x") or (plat.vel_x == 0 and plat.vel_y == 0):
                px = int(plat.rect.x * self.minimap_scale)
                py = int(plat.rect.y * self.minimap_scale)
                pw = max(1, int(plat.rect.w * self.minimap_scale))
                ph = max(1, int(plat.rect.h * self.minimap_scale))
                sdl2.SDL_RenderFillRect(renderer, sdl2.SDL_Rect(px, py, pw, ph))

        # Khôi phục render target
        sdl2.SDL_SetRenderTarget(renderer, old_target)
        self.last_level_name = level.name

    def _render_minimap(self, renderer):
        playing_state = self.game.states.get("playing")
        if not playing_state or not playing_state.level:
            return
        
        level = playing_state.level
        if level.name != self.last_level_name:
            self._generate_minimap_terrain(renderer, level)
            
        if not self.minimap_texture:
            return

        # Vị trí đặt Minimap (Góc trên bên phải)
        p = 20
        mx = int(self.game.logical_width - self.minimap_w - p)
        my = p
        
        # 1. Vẽ nền và địa hình đã pre-render
        dst_rect = sdl2.SDL_Rect(mx, my, self.minimap_w, self.minimap_h)
        sdl2.SDL_RenderCopy(renderer, self.minimap_texture, None, dst_rect)
        
        # 2. Vẽ khung viền
        sdl2.SDL_SetRenderDrawColor(renderer, 255, 255, 255, 100)
        sdl2.SDL_RenderDrawRect(renderer, dst_rect)

        # 3. Vẽ các thực thể động
        # - Kẻ thù (Chấm Đỏ)
        sdl2.SDL_SetRenderDrawColor(renderer, 255, 50, 50, 255)
        for enemy in level.enemies:
            if enemy.alive:
                ex = int(mx + enemy.rect.x * self.minimap_scale)
                ey = int(my + enemy.rect.y * self.minimap_scale)
                sdl2.SDL_RenderFillRect(renderer, sdl2.SDL_Rect(ex-1, ey-1, 3, 3))

        # - Rương (Chấm Vàng)
        sdl2.SDL_SetRenderDrawColor(renderer, 255, 215, 0, 255)
        from game.objects.chest import Chest
        for entity in level.entities:
            if isinstance(entity, Chest) and not entity.opened:
                cx = int(mx + entity.rect.x * self.minimap_scale)
                cy = int(my + entity.rect.y * self.minimap_scale)
                sdl2.SDL_RenderFillRect(renderer, sdl2.SDL_Rect(cx-1, cy-1, 3, 3))

        # - Người chơi chính (Chấm Xanh lá) - Vẽ to hơn chút
        player = self.game.player
        if player:
            px = int(mx + player.rect.x * self.minimap_scale)
            py = int(my + player.rect.y * self.minimap_scale)
            sdl2.SDL_SetRenderDrawColor(renderer, 50, 255, 50, 255)
            sdl2.SDL_RenderFillRect(renderer, sdl2.SDL_Rect(px-2, py-2, 5, 5))

        # - Đồng đội (Chấm Hồng/Xanh dương)
        if playing_state.remote_player:
            remote = playing_state.remote_player
            rx = int(mx + remote.rect.x * self.minimap_scale)
            ry = int(my + remote.rect.y * self.minimap_scale)
            # Màu sắc theo vai trò của đối phương
            if remote.role == "princess":
                sdl2.SDL_SetRenderDrawColor(renderer, 255, 100, 200, 255)
            else:
                sdl2.SDL_SetRenderDrawColor(renderer, 100, 200, 255, 255)
            sdl2.SDL_RenderFillRect(renderer, sdl2.SDL_Rect(rx-2, ry-2, 5, 5))

    def render(self, renderer):
        player = self.game.player
        if not player: return
        
        self._load_font()

        # --- Vẽ HUD chính ---
        # Tắt scale để vẽ HUD tỉ lệ 1:1 theo kích thước Logical
        sdl2.SDL_RenderSetScale(renderer, self.game.scale_x, self.game.scale_y)
        
        # Vẽ Minimap
        self._render_minimap(renderer)

        # Trở về vẽ text và bars (tắt scale để vẽ tọa độ pixel chuẩn)
        sdl2.SDL_RenderSetScale(renderer, 1.0, 1.0)
        
        sx, sy = self.game.scale_x, self.game.scale_y
        p = int(20 * sx) 

        # --- Vẽ HP (Tim) ---
        heart_size = int(34 * sy)
        for i in range(PLAYER_MAX_HP):
            color = COLORS["red"] if i < player.hp else COLORS["gray"]
            sdl2.SDL_SetRenderDrawColor(renderer, *color)
            rect = sdl2.SDL_Rect(int(p + i * (42 * sx)), int(p), heart_size, heart_size)
            sdl2.SDL_RenderFillRect(renderer, rect)

        # --- Vẽ Mana Bar ---
        bar_w, bar_h = int(200 * sx), int(15 * sy)
        mana_x, mana_y = p, int(p + heart_size + (10 * sy))
        
        sdl2.SDL_SetRenderDrawColor(renderer, *COLORS["mana_empty"])
        sdl2.SDL_RenderFillRect(renderer, sdl2.SDL_Rect(mana_x, mana_y, bar_w, bar_h))
        
        if player.mana > 0:
            current_mana_w = int(bar_w * (int(player.mana) / MANA_MAX))
            sdl2.SDL_SetRenderDrawColor(renderer, *COLORS["mana_bar"])
            sdl2.SDL_RenderFillRect(renderer, sdl2.SDL_Rect(mana_x, mana_y, current_mana_w, bar_h))

        # --- Vẽ Text ở dưới ---
        bottom_y = int(self.game.current_height - p - (45 * sy))

        self._draw_text(renderer, f"Vàng: {player.gold}", p, bottom_y, (255, 215, 0))
        self._draw_text(renderer, f"Mạng: {player.lives}/{MAX_LIVES}", int(p + (180 * sx)), bottom_y, (255, 255, 255))
        
        # --- Vẽ trạng thái đối phương (Multiplayer) ---
        playing_state = self.game.states.get("playing")
        if playing_state and getattr(playing_state, "remote_player", None):
            remote = playing_state.remote_player
            # Vị trí Top Right - Đẩy sang trái để không đè lên Minimap
            # Minimap thường ở (Width - 200 - 20), nên ta đặt HUD ở khoảng cách xa hơn
            rx = int(self.game.logical_width * sx - p - (450 * sx))
            ry = p
            
            # Tên vai trò
            role_name = "CÔNG CHÚA" if remote.role == "princess" else "HIỆP SĨ"
            self._draw_text(renderer, role_name, rx, ry, (255, 255, 255))
            
            # HP của đối phương (các chấm nhỏ)
            for i in range(PLAYER_MAX_HP):
                color = COLORS["red"] if i < getattr(remote, "hp", 0) else COLORS["gray"]
                sdl2.SDL_SetRenderDrawColor(renderer, *color)
                # Vẽ nhỏ hơn một chút cho Remote
                r_heart_size = int(24 * sy)
                r_rect = sdl2.SDL_Rect(int(rx + i * (30 * sx)), int(ry + (35 * sy)), r_heart_size, r_heart_size)
                sdl2.SDL_RenderFillRect(renderer, r_rect)
            
            # Mạng của đối phương
            r_lives = getattr(remote, "lives", MAX_LIVES)
            self._draw_text(renderer, f"Mạng: {r_lives}", rx, int(ry + (70 * sy)), (200, 200, 200))
        
        # Bật lại scale cũ cho các hệ thống khác nếu cần
        sdl2.SDL_RenderSetScale(renderer, self.game.scale_x, self.game.scale_y)

    def _draw_text(self, renderer, text, x, y, color):
        if not self.font: return
        sdl_color = sdl2.SDL_Color(color[0], color[1], color[2], 255)
        surf = ttf.TTF_RenderUTF8_Blended(self.font, text.encode('utf-8'), sdl_color)
        if surf:
            tex = sdl2.SDL_CreateTextureFromSurface(renderer, surf)
            tw, th = surf.contents.w, surf.contents.h
            sdl2.SDL_RenderCopy(renderer, tex, None, sdl2.SDL_Rect(int(x), int(y), int(tw), int(th)))
            sdl2.SDL_DestroyTexture(tex)
            sdl2.SDL_FreeSurface(surf)