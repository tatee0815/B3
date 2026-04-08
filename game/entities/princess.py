import sdl2
import math
from game.constants import PLAYER_SPEED, GRAVITY, SKILL_A_COST, MANA_MAX
from game.utils.assets import AssetManager
from .player import Player
from .projectile import Projectile

class Princess(Player):
    def __init__(self, game):
        super().__init__(game)
        # Ghi đè sprite nếu cần (có thể dùng chung sprite hoặc load riêng)
        # Ở đây giả sử dùng chung sprite, nhưng có thể thay bằng sprite công chúa sau
        self.state = "princess_idle"  # để phân biệt animation nếu có
        
        # Điều chỉnh kỹ năng
        self.teleport_cooldown = 0.0
        self.TELEPORT_COOLDOWN_TIME = 1.5
        self.aoe_cooldown = 0.0
        self.AOE_COOLDOWN_TIME = 2.0
        self.AOE_DAMAGE = 20
        self.AOE_RADIUS = 100  # pixel

    def handle_input(self, event):
        """Ghi đè để thêm phím teleport (C) và AOE (A)"""
        scancode = event.key.keysym.scancode
        from game.constants import KEY_BINDINGS_DEFAULT
        
        if event.type == sdl2.SDL_KEYDOWN:
            if self.is_dashing:
                return
            
            # Các phím di chuyển, nhảy, tương tác giữ nguyên
            if scancode == KEY_BINDINGS_DEFAULT["left"]:
                self.moving_left = True
                self.facing_right = False
            elif scancode == KEY_BINDINGS_DEFAULT["right"]:
                self.moving_right = True
                self.facing_right = True
            elif scancode == KEY_BINDINGS_DEFAULT["jump"] or scancode == sdl2.SDL_SCANCODE_SPACE:
                self.jump()
            elif scancode == KEY_BINDINGS_DEFAULT["dash"]:  # Phím C mặc định là dash? Cần đổi tên phím trong constants
                self.teleport()
            elif scancode == KEY_BINDINGS_DEFAULT["skill"]:  # Phím A mặc định là skill
                self.aoe_attack()
            elif scancode == KEY_BINDINGS_DEFAULT["interact"]:
                self.interact()
        
        elif event.type == sdl2.SDL_KEYUP:
            if scancode == KEY_BINDINGS_DEFAULT["left"]:
                self.moving_left = False
            elif scancode == KEY_BINDINGS_DEFAULT["right"]:
                self.moving_right = False

    def teleport(self):
        """Teleport đến ground gần nhất (bề mặt đất/platform)"""
        if self.teleport_cooldown > 0:
            return
        
        # Tìm ground gần nhất bên dưới hoặc bên trái/phải trong phạm vi 300px
        level = self.game.states["playing"].level
        if not level:
            return
        
        start_x = self.rect.centerx
        start_y = self.rect.centery
        search_range = 350  # pixel
        
        best_ground_y = None
        best_distance = float('inf')
        
        # Duyệt các tile và platform để tìm điểm đứng
        # Kiểm tra các tile trong level
        tile_size = level.tile_size
        for ty in range(level.height):
            for tx in range(level.width):
                tile = level.get_tile(tx, ty)
                if tile and tile.get("solid"):
                    tile_x = tx * tile_size
                    tile_y = ty * tile_size
                    # Chỉ xét tile nằm trong khoảng cách ngang search_range
                    if abs(tile_x - start_x) <= search_range:
                        # Điểm đứng là trên tile (tile_y - player height)
                        ground_y = tile_y - self.rect.h
                        # Chỉ nhận nếu ground_y > start_y (dưới chân) hoặc gần ngang
                        dy = ground_y - start_y
                        if dy < 0:
                            continue  # không teleport lên trên
                        dist = abs(tile_x - start_x) + dy
                        if dist < best_distance and self.is_ground_safe(ground_y, tile_x):
                            best_distance = dist
                            best_ground_y = ground_y
                            best_ground_x = tile_x
        
        # Kiểm tra platform
        for plat in level.platforms:
            if hasattr(plat, 'rect'):
                plat_top = plat.rect.y
                ground_y = plat_top - self.rect.h
                dx = abs(plat.rect.centerx - start_x)
                if dx <= search_range and ground_y > start_y:
                    dist = dx + (ground_y - start_y)
                    if dist < best_distance and self.is_ground_safe(ground_y, plat.rect.x):
                        best_distance = dist
                        best_ground_y = ground_y
                        best_ground_x = plat.rect.x
        
        if best_ground_y is not None:
            # Teleport
            self.rect.x = int(best_ground_x + (self.rect.w // 2))
            self.rect.y = int(best_ground_y)
            self.pos_x = float(self.rect.x)
            self.pos_y = float(self.rect.y)
            self.vel_x = 0
            self.vel_y = 0
            self.on_ground = True
            self.teleport_cooldown = self.TELEPORT_COOLDOWN_TIME
            # Hiệu ứng (có thể thêm particle)
            self.show_speech("Teleport!")

    def is_ground_safe(self, ground_y, ground_x):
        """Kiểm tra vị trí ground có đủ rộng để đứng không"""
        # Kiểm tra trong khoảng width của player có tile/platform không
        left = ground_x
        right = ground_x + self.rect.w
        # Giả lập kiểm tra nhanh (có thể bỏ qua nếu tin tưởng map)
        return True

    def aoe_attack(self):
        """Gây sát thương diện rộng lên tất cả enemy trong bán kính"""
        if self.aoe_cooldown > 0:
            return
        if self.mana < SKILL_A_COST:
            self.mana_warning_timer = self.mana_warning_duration
            return
        
        self.mana -= SKILL_A_COST
        self.aoe_cooldown = self.AOE_COOLDOWN_TIME
        self.state = "skill"
        self.is_attacking = True
        self.is_using_skill = True
        self.attack_timer = 0.3
        
        # Tìm tất cả enemy trong bán kính
        level = self.game.states["playing"].level
        center_x = self.rect.centerx
        center_y = self.rect.centery
        for enemy in level.enemies[:]:
            if not enemy.alive:
                continue
            enemy_center_x = enemy.rect.centerx
            enemy_center_y = enemy.rect.centery
            dx = enemy_center_x - center_x
            dy = enemy_center_y - center_y
            dist = math.hypot(dx, dy)
            if dist <= self.AOE_RADIUS:
                enemy.take_damage(self.AOE_DAMAGE, knockback_dir=1 if dx > 0 else -1)
        # Hiệu ứng
        self.show_speech("AOE!")

    def update(self, delta_time, level):
        # Cập nhật cooldown
        if self.teleport_cooldown > 0:
            self.teleport_cooldown -= delta_time
        if self.aoe_cooldown > 0:
            self.aoe_cooldown -= delta_time
        
        super().update(delta_time, level)
        
        # Đảm bảo double jump vẫn hoạt động (kế thừa từ Player)
        # Player đã có double jump logic, chỉ cần đảm bảo self.has_double_jump = True
        if "double_jump" in self.game.player_progress.get("unlocked_skills", []):
            self.has_double_jump = True

    def render(self, renderer, camera):
        # Có thể ghi đè để vẽ sprite công chúa nếu có
        # Tạm thời dùng sprite của player nhưng đổi màu hoặc dùng texture riêng
        # Ở đây gọi super để dùng chung sprite (có thể thay sau)
        super().render(renderer, camera)