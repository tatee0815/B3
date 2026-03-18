"""
Thùng gỗ / thùng nổ - đập bằng kiếm hoặc skill thì vỡ ra item
"""

import sdl2
import random
from game.constants import TILE_SIZE
from game.entities.base import Entity


class BreakableBox(Entity):
    """Thùng có thể phá (gỗ hoặc nổ)"""

    def __init__(self, game, x, y, explosive=False):
        super().__init__(game, x, y, TILE_SIZE, TILE_SIZE)
        self.z_index = 1
        self.explosive = explosive
        self.hp = 1 if not explosive else 2  # thùng nổ chịu 2 hit
        self.color = (180, 120, 60, 255) if not explosive else (200, 80, 40, 255)
        self.broken = False

        # --- PHẦN QUAN TRỌNG: ID VÀ TRẠNG THÁI ---
        self.box_id = f"box_{int(x)}_{int(y)}"
        
        # Nếu thùng này đã bị phá ở lần trước (nằm trong file save), thì không cho nó sống lại
        if "broken_boxes" in self.game.player_progress:
            if self.box_id in self.game.player_progress["broken_boxes"]:
                self.alive = False
                self.broken = True
                return

        # Item có thể rơi ra khi vỡ (random)
        self.possible_drops = ["coin", "heart", "mana"] if not explosive else ["coin", "mana"]

    def take_damage(self, amount=1):
        if self.broken: return
        self.hp -= amount
        if self.hp <= 0:
            self.break_box()

    def _mark_as_broken(self):
        """Ghi nhớ vào file save là thùng này đã vỡ"""
        if "broken_boxes" not in self.game.player_progress:
            self.game.player_progress["broken_boxes"] = []
        
        if self.box_id not in self.game.player_progress["broken_boxes"]:
            self.game.player_progress["broken_boxes"].append(self.box_id)
        
        # Lưu game ngay
        from game.utils.save import save_game
        save_game(self.game.player_progress)

    def break_box(self):
        if self.broken:
            return
        
        self.broken = True
        self.alive = False
        self._mark_as_broken() # <--- Lưu lại trạng thái vỡ
        
        # Spawn item ngẫu nhiên (tạo instance Collectible)
        from game.entities.collectible import Coin, Heart, ManaBottle
        
        center_x = self.rect.x + (self.rect.w // 2)
        center_y = self.rect.y + (self.rect.h // 2)
        
        drop_x = center_x - 10 
        drop_y = center_y - 10 
        
        drop_type = random.choice(self.possible_drops)
        drop = None

        if drop_type == "coin":
            drop = Coin(self.game, drop_x, drop_y, value=5)
        elif drop_type == "heart":
            drop = Heart(self.game, drop_x, drop_y)
        else:
            drop = ManaBottle(self.game, drop_x, drop_y, value=25)
        
        if drop and drop.alive: # Chỉ add nếu item đó chưa bị nhặt ở kiếp trước
            playing_state = self.game.states.get("playing")
            if playing_state and playing_state.level:
                playing_state.level.entities.append(drop)

    def render(self, renderer, camera):
        """Hàm vẽ thùng để nó hiện ra màn hình"""
        if not self.alive: return

        draw_rect = sdl2.SDL_Rect(
            int(self.rect.x - camera.x),
            int(self.rect.y - camera.y),
            self.rect.w,
            self.rect.h
        )
        
        # Vẽ khối thùng
        sdl2.SDL_SetRenderDrawColor(renderer, *self.color)
        sdl2.SDL_RenderFillRect(renderer, draw_rect)
        
        # Vẽ thêm cái viền cho đẹp/dễ nhìn
        sdl2.SDL_SetRenderDrawColor(renderer, 50, 30, 10, 255)
        sdl2.SDL_RenderDrawRect(renderer, draw_rect)