import sdl2
from .base import Entity
from game.constants import GRAVITY, TILE_SIZE, COLORS

MANA_PER_KILL = 5

class Enemy(Entity):
    def __init__(self, game, x, y, hp=30, damage=10):
        super().__init__(game, x, y, 32, 32)
        self.z_index = 3
        self.hp = hp
        self.damage = damage
        self.patrol_speed = 1.5
        self.direction = 1
        self.color = [200, 50, 50, 255]
        self.alive = True
        
        # === STATUS & PHYSICS ===
        self.knockback_timer = 0.0
        self.is_chasing = False
        self.is_flying = False 

    def update(self, delta_time, level):
        if not self.alive: return

        # 1. XỬ LÝ KNOCKBACK (Ưu tiên cao nhất, chặn AI)
        if self.knockback_timer > 0:
            self.knockback_timer -= delta_time
        else:
            # 2. LOGIC AI (Chỉ chạy khi không bị bật lùi)
            playing_state = self.game.states.get("playing")
            player = playing_state.player if playing_state else None
            self._update_ai_state(player, level)

        # 3. VẬT LÝ & TRỌNG LỰC
        if not self.is_flying:
            self.vel_y += GRAVITY * delta_time * 60
            if self.vel_y > 12: self.vel_y = 12

        # 4. THỰC THI DI CHUYỂN & CHECK VA CHẠM (Trục Y trước X sau)
        self.pos_y += self.vel_y * delta_time * 60
        self.rect.y = int(self.pos_y)
        self._resolve_collision(level, is_y=True)

        self.pos_x += self.vel_x * delta_time * 60
        self.rect.x = int(self.pos_x)
        self._resolve_collision(level, is_y=False)

        self.pos_x = max(0, min(self.pos_x, level.pixel_width - self.rect.w))

        # Nếu rơi quá sâu (vượt quá chiều cao của Map)
        if self.pos_y > level.pixel_height:
            if hasattr(self, 'hp'):
                self.hp = 0 # Hiệp sĩ tử trận
            else:
                self.alive = False # Quái biến mất

    def _update_ai_state(self, player, level):
        self.is_chasing = False
        if not player: return

        # 1. Tính toán vị trí tâm
        s_cx, s_cy = self.rect.x + self.rect.w//2, self.rect.y + self.rect.h//2
        p_cx, p_cy = player.rect.x + player.rect.w//2, player.rect.y + player.rect.h//2

        dx, dy = p_cx - s_cx, p_cy - s_cy
        dist_sq = dx**2 + dy**2
        
        view_dist = 400 if self.is_flying else 250
        lose_dist = view_dist + 150

        # 2. KIỂM TRA GÓC NHÌN (Mới)
        # Quái chỉ thấy nếu player ở trong tầm nhìn (ví dụ: lệch Y không quá 100px)
        # Và player phải ở phía trước hướng mặt của quái (direction)
        in_fov = False
        if dist_sq < view_dist**2:
            # Check chiều dọc (không cho quái thấy quá xa phía dưới/trên)
            vertical_limit = 200 if self.is_flying else 80 
            if abs(dy) < vertical_limit:
                # Check hướng mặt: dx và direction phải cùng dấu (cùng bên trái hoặc cùng bên phải)
                if (dx > 0 and self.direction > 0) or (dx < 0 and self.direction < 0):
                    in_fov = True

        # 3. QUYẾT ĐỊNH ĐUỔI
        # Nếu đang trong tầm nhìn + thấy trực tiếp -> Đuổi
        if in_fov and self._has_line_of_sight(player, level):
            self.is_chasing = True
        # Nếu đã đang đuổi rồi thì cho phép "mất dấu" khó hơn (không cần check FOV, chỉ cần distance)
        elif getattr(self, 'is_chasing', False) and dist_sq < lose_dist**2:
            self.is_chasing = True

        # 4. THỰC THI DI CHUYỂN
        if self.is_chasing:
            self.direction = 1 if dx > 0 else -1
            self.vel_x = (self.patrol_speed * 1.5) * self.direction
            if self.is_flying:
                self.vel_y = self.patrol_speed * (1 if dy > 0 else -1) if abs(dy) > 10 else 0
        else:
            if self.is_flying: self.vel_y = 0
            self.vel_x = self.patrol_speed * self.direction
            self._patrol_ai(level)

    def _has_line_of_sight(self, player, level):
        """Check 3 điểm dọc đường nối để xem có tường chắn không"""
        x1 = self.rect.x + (self.rect.w // 2)
        y1 = self.rect.y + (self.rect.h // 2)
        x2 = player.rect.x + (player.rect.w // 2)
        y2 = player.rect.y + (player.rect.h // 2)

        for i in range(1, 4):
            if level.is_solid_at(x1 + (x2 - x1) * (i / 3), y1 + (y2 - y1) * (i / 3)):
                return False
        return True

    def _patrol_ai(self, level):
        """Logic đi tuần cơ bản và quay đầu khi gặp vực/tường"""
        # Check tường phía trước
        ahead_x = self.rect.x + (self.rect.w if self.direction > 0 else 0) + (self.direction * 5)
        if level.is_solid_at(ahead_x, self.rect.y + 5):
            self.direction *= -1
            return

        # Check vực (chỉ quái đi bộ)
        if not self.is_flying:
            ledge_x = self.rect.x + (self.rect.w // 2) + (self.rect.w // 2 * self.direction)
            if not level.is_solid_at(ledge_x, self.rect.y + self.rect.h + 5):
                self.direction *= -1

    def take_damage(self, amount, knockback_dir=0):
        if not self.alive: return
        self.hp -= amount
        if knockback_dir != 0:
            self.knockback_timer = 0.15
            self.vel_x = knockback_dir * 4.0 # Lực đẩy lùi
            self.vel_y = -2.0 # Nảy nhẹ lên cho đẹp
        
        if self.hp <= 0: self.die()

    def die(self):
        self.alive = False
        playing_state = self.game.states.get("playing")
        if not playing_state: return
        playing_state.player.mana = min(100, playing_state.player.mana + MANA_PER_KILL)

        level = playing_state.level
        if self in level.entities:
            level.entities.remove(self)
        if hasattr(level, "enemies") and self in level.enemies:
            level.enemies.remove(self)

    def _resolve_collision(self, level, is_y):
        """Xử lý va chạm để không xuyên tường"""
        # Logic tối giản: Nếu va chạm gạch (id=1), đẩy lùi rect lại
        for row in range(self.rect.y // TILE_SIZE, (self.rect.y + self.rect.h) // TILE_SIZE + 1):
            for col in range(self.rect.x // TILE_SIZE, (self.rect.x + self.rect.w) // TILE_SIZE + 1):
                if 0 <= row < len(level.tiles) and 0 <= col < len(level.tiles[0]):
                    if level.tiles[row][col] == 1:
                        tile_rect = sdl2.SDL_Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                        if sdl2.SDL_HasIntersection(self.rect, tile_rect):
                            if is_y:
                                if self.vel_y > 0: self.rect.y = tile_rect.y - self.rect.h
                                elif self.vel_y < 0: self.rect.y = tile_rect.y + TILE_SIZE
                                self.pos_y = float(self.rect.y)
                                self.vel_y = 0
                            else:
                                if self.vel_x > 0: self.rect.x = tile_rect.x - self.rect.w
                                elif self.vel_x < 0: self.rect.x = tile_rect.x + TILE_SIZE
                                self.pos_x = float(self.rect.x)
                                self.vel_x = 0
                                if self.knockback_timer <= 0: self.direction *= -1

    def render(self, renderer, camera):
        if not self.alive: return
        draw_rect = sdl2.SDL_Rect(int(self.rect.x - camera.x), int(self.rect.y - camera.y), self.rect.w, self.rect.h)
        sdl2.SDL_SetRenderDrawColor(renderer, *self.color)
        sdl2.SDL_RenderFillRect(renderer, draw_rect)

# ==================== CÁC CLASS CON ====================
class Goblin(Enemy):
    def __init__(self, game, x, y):
        super().__init__(game, x, y, hp=25, damage=1)
        self.patrol_speed = 1.2
        self.color = COLORS["green"]

class Skeleton(Enemy):
    def __init__(self, game, x, y):
        super().__init__(game, x, y, hp=40, damage=1)
        self.patrol_speed = 0.8
        self.color = COLORS["white"]

class FireBat(Enemy):
    def __init__(self, game, x, y):
        super().__init__(game, x, y, hp=15, damage=1)
        self.is_flying = True
        self.patrol_speed = 2.0
        self.color = (255, 100, 0, 255)

class BossShadowKing(Enemy):
    def __init__(self, game, x, y):
        super().__init__(game, x, y, hp=150, damage=1)
        self.rect.w, self.rect.h = 64, 64
        self.patrol_speed = 0.5
        self.color = (100, 0, 150, 255)