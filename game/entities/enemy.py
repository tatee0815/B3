import sdl2
from .base import Entity
from game.constants import GRAVITY, TILE_SIZE

MANA_PER_KILL = 5

class Enemy(Entity):
    def __init__(self, game, x, y, hp=30, damage=10):
        super().__init__(game, x, y, 32, 32)
        self.hp = hp
        self.damage = damage
        self.patrol_speed = 1.5
        self.direction = 1
        self.color = (255, 0, 0, 255)
        self.alive = True
        
        # === PHYSICS ===
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.on_ground = False
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.rect.x = x
        self.rect.y = y
        
        self.is_flying = False  # ← Quan trọng: mặc định là quái đi bộ

    def update(self, delta_time, level):
        if not self.alive: return

        playing_state = self.game.states.get("playing")
        player = playing_state.player if playing_state else None

        # === LOGIC AI NÂNG CAO ===
        should_chase = False
        if player:
            dist_x = player.rect.x - self.rect.x
            dist_y = player.rect.y - self.rect.y
            distance = (dist_x**2 + dist_y**2)**0.5

            # Tầm nhìn (Quái bay nhìn xa hơn)
            view_dist = 400 if self.is_flying else 250
            # Khoảng cách để quái "mất dấu" (Hủy chase)
            lose_dist = view_dist + 150 

            # Kiểm tra điều kiện bắt đầu đuổi: Trong tầm mắt + Nhìn thấy trực tiếp
            if distance < view_dist:
                if self._has_line_of_sight(player, level):
                    should_chase = True
            
            # Duy trì truy đuổi: Nếu đang đuổi mà player chưa chạy quá xa (lose_dist)
            elif distance < lose_dist and getattr(self, 'is_chasing', False):
                should_chase = True

        if should_chase:
            self.is_chasing = True
            self._chase_player(player)
        else:
            self.is_chasing = False
            if self.is_flying: self.vel_y = 0 # Quái bay ngừng bay lên/xuống khi mất dấu
            self._patrol_ai(level)

        # === VẬT LÝ ===
        # Trọng lực chỉ cho quái đi bộ
        if not self.is_flying:
            self.vel_y += GRAVITY * delta_time * 60
        
        # Di chuyển Y và X (Giữ nguyên logic resolve_collision của bạn)
        self.pos_y += self.vel_y * delta_time * 60
        self.rect.y = int(self.pos_y)
        self._resolve_collision(level, is_y=True)

        # Tốc độ x1.5 khi đang đuổi theo
        current_speed = self.patrol_speed * 1.5 if getattr(self, 'is_chasing', False) else self.patrol_speed
        self.vel_x = current_speed * self.direction
        
        self.pos_x += self.vel_x * delta_time * 60
        self.rect.x = int(self.pos_x)
        self._resolve_collision(level, is_y=False)

    def _has_line_of_sight(self, player, level):
        """Kiểm tra xem có tường (tile == 1) giữa Quái và Player không"""
        # Tự tính toán center x và center y
        x1 = self.rect.x + (self.rect.w // 2)
        y1 = self.rect.y + (self.rect.h // 2)
        
        x2 = player.rect.x + (player.rect.w // 2)
        y2 = player.rect.y + (player.rect.h // 2)
        
        # Kiểm tra 5 điểm dọc theo đường thẳng nối quái và người chơi
        for i in range(1, 6):
            check_x = x1 + (x2 - x1) * (i / 5)
            check_y = y1 + (y2 - y1) * (i / 5)
            if level.is_solid_at(check_x, check_y):
                return False # Có tường chắn
        return True
    
    def _chase_player(self, player):
        """Đuổi theo Player: X cho mọi loại, Y chỉ cho quái bay"""
        # Hướng X
        self.direction = 1 if player.rect.x > self.rect.x else -1

        # Hướng Y (Chỉ dành cho FireBat hoặc quái bay)
        if self.is_flying:
            y_diff = player.rect.y - self.rect.y
            if abs(y_diff) > 10: # Chỉ di chuyển nếu lệch quá 10 pixel
                self.vel_y = self.patrol_speed * (1 if y_diff > 0 else -1)
            else:
                self.vel_y = 0

    def _resolve_collision(self, level, is_y: bool):
        start_col = max(0, self.rect.x // TILE_SIZE)
        end_col = min(level.width - 1, (self.rect.x + self.rect.w) // TILE_SIZE)
        start_row = max(0, self.rect.y // TILE_SIZE)
        end_row = min(level.height - 1, (self.rect.y + self.rect.h) // TILE_SIZE)

        for row in range(start_row, end_row + 1):
            for col in range(start_col, end_col + 1):
                if level.tiles[row][col] == 1:
                    tile = sdl2.SDL_Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    if sdl2.SDL_HasIntersection(self.rect, tile):
                        if is_y and not self.is_flying:
                            if self.vel_y > 0 and self.rect.y < tile.y:
                                self.rect.y = tile.y - self.rect.h
                                self.pos_y = float(self.rect.y)
                                self.vel_y = 0
                                self.on_ground = True
                            elif self.vel_y < 0 and self.rect.y > tile.y:
                                self.rect.y = tile.y + tile.h
                                self.pos_y = float(self.rect.y)
                                self.vel_y = 0
                        else:
                            # Va chạm ngang → quay đầu
                            if self.vel_x > 0 and self.rect.x < tile.x:
                                self.rect.x = tile.x - self.rect.w
                                self.pos_x = float(self.rect.x)
                                self.direction *= -1
                            elif self.vel_x < 0 and self.rect.x > tile.x:
                                self.rect.x = tile.x + tile.w
                                self.pos_x = float(self.rect.x)
                                self.direction *= -1

    def _patrol_ai(self, level):
        if self.rect.x <= 0 or (self.rect.x + self.rect.w) >= level.pixel_width:
            self.direction *= -1
            return
    
        ahead_x = self.rect.x + (self.rect.w if self.direction > 0 else 0) + (self.direction * 15)
        ahead_y = self.rect.y + 16
        if level.is_solid_at(ahead_x, ahead_y):
            self.direction *= -1
            return

        # Chỉ kiểm tra vực nếu là quái đi bộ
        if not self.is_flying:
            ledge_x = self.rect.x + (self.rect.w // 2) + (self.rect.w * self.direction)
            ledge_y = self.rect.y + self.rect.h + 8
            if not level.is_solid_at(ledge_x, ledge_y):
                self.direction *= -1

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.die()

    def die(self):
        self.alive = False
        playing_state = self.game.states.get("playing")
        if playing_state and playing_state.player:
            player = playing_state.player
            player.mana = min(player.mana + MANA_PER_KILL, 100)
            player.gold += 5
        
        level = self.game.states["playing"].level
        if self in level.entities:
            level.entities.remove(self)
        if hasattr(level, "enemies") and self in level.enemies:
            level.enemies.remove(self)

    def render(self, renderer, camera):
        if not self.alive:
            return
        draw_x = int(self.rect.x - camera.x)
        draw_y = int(self.rect.y - camera.y)
        draw_rect = sdl2.SDL_Rect(draw_x, draw_y, self.rect.w, self.rect.h)
        sdl2.SDL_SetRenderDrawColor(renderer, *self.color)
        sdl2.SDL_RenderFillRect(renderer, draw_rect)


# ==================== CÁC CLASS CON (GIỮ NGUYÊN + CHỈ THÊM 1 DÒNG CHO FIREBAT) ====================
class Goblin(Enemy):
    def __init__(self, game, x, y):
        super().__init__(game, x, y, hp=25, damage=1)
        self.patrol_speed = 1.2
        self.color = (50, 200, 50, 255)


class Skeleton(Enemy):
    def __init__(self, game, x, y):
        super().__init__(game, x, y, hp=40, damage=1)
        self.patrol_speed = 0.8
        self.color = (200, 200, 200, 255)


class FireBat(Enemy):
    def __init__(self, game, x, y):
        super().__init__(game, x, y, hp=20, damage=1)
        self.patrol_speed = 2.5
        self.color = (255, 100, 0, 255)
        self.is_flying = True   # ← DÒNG QUAN TRỌNG: khiến FireBat bay được!


class BossShadowKing(Enemy):
    def __init__(self, game, x, y):
        super().__init__(game, x, y, hp=150, damage=1)
        self.rect.w, self.rect.h = 64, 64
        self.patrol_speed = 0.5
        self.color = (100, 0, 150, 255)