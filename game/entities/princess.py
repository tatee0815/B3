import sdl2
import math
from game.constants import PLAYER_SPEED, GRAVITY, SKILL_A_COST, MANA_MAX, PLAYER_MAX_HP
from game.utils.assets import AssetManager
from .player import Player
from .projectile import Projectile

class Princess(Player):
    def __init__(self, game):
        super().__init__(game)
        self.role = "princess"
        # 1. Xác định progress của người chơi theo role (Multiplayer support)
        if "players" in self.game.player_progress:
            self.progress = self.game.player_progress["players"][self.role]
        else:
            self.progress = self.game.player_progress # Fallback
            
        progress = self.progress
        self.hp = progress.get("hp", PLAYER_MAX_HP)
        self.mana = progress.get("mana", 50)
        self.checkpoint_pos = progress.get("checkpoint", self.checkpoint_pos)
        
        self.state = "idle"
        
        # Điều chỉnh kỹ năng
        self.teleport_cooldown = 0.0
        self.TELEPORT_COOLDOWN_TIME = 1.5
        self.aoe_cooldown = 0.0
        self.AOE_COOLDOWN_TIME = 2.0
        self.AOE_DAMAGE = 20
        self.AOE_RADIUS = 100  # pixel
        
        # Teleport ngắm
        self.is_teleport_aiming = False
        self.teleport_target = None

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
            elif scancode == KEY_BINDINGS_DEFAULT["attack"]:
                if not getattr(self, "is_attack_key_down", False):
                    self.is_attack_key_down = True
                    self.melee_attack()
        
        elif event.type == sdl2.SDL_KEYUP:
            if scancode == KEY_BINDINGS_DEFAULT["left"]:
                self.moving_left = False
            elif scancode == KEY_BINDINGS_DEFAULT["right"]:
                self.moving_right = False
            elif scancode == KEY_BINDINGS_DEFAULT["attack"]:
                self.is_attack_key_down = False

    def calculate_teleport_target(self, level):
        """
        Tìm kiếm vị trí Ground an toàn trong bán kính 250px phía trước mặt (quét 180 độ).
        Ưu tiên các vị trí xa hơn hoặc bục cao.
        """
        start_x = self.rect.x + self.rect.w // 2
        start_y = self.rect.y + self.rect.h // 2
        max_range = 250
        
        best_target = None
        best_score = -99999
        
        # Hướng hiện tại: 1 nếu quay phải, -1 nếu quay trái
        look_dir = 1 if self.facing_right else -1
        
        # Quét theo góc từ -45 đến 45 độ (tổng 90 độ phía trước mặt)
        # Bước quét 5 độ một lần để mịn hơn
        for angle_deg in range(-45, 46, 5):
            # Chuyển độ sang radian và tính vector hướng
            angle_rad = math.radians(angle_deg)
            # Nếu quay trái, ta cộng thêm 180 độ (pi radian)
            if not self.facing_right:
                angle_rad += math.pi
            
            # Quét dọc theo tia từ tâm ra ngoài theo từng nấc 16px (nửa tile)
            for dist in range(32, max_range + 1, 16):
                tx = start_x + math.cos(angle_rad) * dist
                ty = start_y + math.sin(angle_rad) * dist
                
                # Kiểm tra tile tại (tx, ty)
                col, row = int(tx // level.tile_size), int(ty // level.tile_size)
                
                if col < 0 or col >= level.width or row < 0 or row >= level.height:
                    break # Ra khỏi biên map thì dừng tia này
                
                # Nếu tia quét chạm gạch rắn
                is_solid = level.tiles[row][col] == 1 # Chỉ gạch type 1 là tường gạch rắn
                
                if is_solid:
                    # TRƯỜNG HỢP CHẠM TƯỜNG: Dừng quét tia này ngay lập tức để tránh xuyên tường
                    break

                # Kiểm tra nếu là platform hoặc điểm đứng được (tile type 2)
                is_ground = level.tiles[row][col] == 2
                plat_y = None
                for plat in level.platforms:
                    if tx >= plat.rect.x and tx <= plat.rect.x + plat.rect.w:
                        if abs(ty - plat.rect.y) < 16:
                            plat_y = plat.rect.y
                            break
                
                if is_ground or plat_y is not None:
                    # Tìm thấy mặt đất! Xác định cao độ đích (trên mặt đất)
                    ground_y = (row * level.tile_size if is_ground else plat_y)
                    target_y = ground_y - self.rect.h
                    target_x = int(tx - self.rect.w // 2)
                    
                    # KIỂM TRA KHÔNG GIAN CHO NHÂN VẬT (Phải trống 2 ô trên đầu)
                    t_col = int(target_x // level.tile_size)
                    t_row = int(target_y // level.tile_size)
                    
                    space_ok = True
                    if t_row < 0 or t_row >= level.height: space_ok = False
                    else:
                        # Kiểm tra ô chân và ô đầu phải TRỐNG
                        if level.tiles[t_row][t_col] in (1, 2): space_ok = False
                        if t_row > 0 and level.tiles[t_row-1][t_col] in (1, 2): space_ok = False
                    
                    if space_ok:
                        # Tính điểm ưu tiên: xa hơn là tốt
                        score = dist
                        if target_y < start_y - 32: score += 50 # Ưu tiên bục cao
                        
                        if score > best_score:
                            best_score = score
                            best_target = (target_x, int(target_y))
                        
                        # Đã tìm thấy điểm đứng hợp lệ trên tia này, ngừng tiến xa hơn trên chính tia này
                        break
        
        return best_target

    def teleport(self):
        # Kiểm tra mở khóa
        if "teleport" not in self.progress.get("unlocked_skills", []):
            return

        if self.teleport_cooldown > 0:
            return
            
        level = self.game.states["playing"].level
        if not level:
            return
            
        if not self.is_teleport_aiming:
            self.teleport_target = self.calculate_teleport_target(level)
            if self.teleport_target:
                self.is_teleport_aiming = True
        else:
            if self.teleport_target:
                tgt_x, tgt_y = self.teleport_target
                self.rect.x = tgt_x
                self.rect.y = tgt_y
                self.pos_x = float(self.rect.x)
                self.pos_y = float(self.rect.y)
                self.vel_x = 0
                self.vel_y = 0
                self.on_ground = True
                self.teleport_cooldown = self.TELEPORT_COOLDOWN_TIME
                self.show_speech("Teleport!")
            self.is_teleport_aiming = False

    def is_ground_safe(self, ground_y, ground_x):
        """Kiểm tra vị trí ground có đủ rộng để đứng không"""
        # Kiểm tra trong khoảng width của player có tile/platform không
        left = ground_x
        right = ground_x + self.rect.w
        # Giả lập kiểm tra nhanh (có thể bỏ qua nếu tin tưởng map)
        return True

    def melee_attack(self):
        """Ghi đè để dùng hoạt ảnh princess thay vì hero"""
        if self.attack_cooldown_timer <= 0 and not self.is_dashing:
            self.is_attacking = True
            self.is_using_skill = False
            self.attack_timer = self.ATTACK_DURATION
            self.attack_cooldown_timer = self.ATTACK_COOLDOWN
            self.state = "attack"
            self.hit_enemies = []
            self.anim_frame = 0

    def aoe_attack(self, is_sync=False):
        """Gây sát thương diện rộng lên tất cả enemy trong bán kính"""
        if "aoe" not in self.progress.get("unlocked_skills", []):
            return

        if self.aoe_cooldown > 0 and not is_sync:
            return
        if self.mana < SKILL_A_COST and not is_sync:
            self.mana_warning_timer = self.mana_warning_duration
            return
        
        if not is_sync:
            self.mana -= SKILL_A_COST
            self.aoe_cooldown = self.AOE_COOLDOWN_TIME
            
            # GỬI LỆNH QUA MẠNG
            pass

        self.state = "skill"
        self.is_attacking = True
        self.is_using_skill = True
        self.attack_timer = 0.3 # Thời gian hoạt ảnh 
        
        # Tìm tất cả enemy trong bán kính
        level = self.game.states["playing"].level
        center_x = self.rect.x + self.rect.w // 2
        center_y = self.rect.y + self.rect.h // 2
        for enemy in level.enemies[:]:
            if not enemy.alive:
                continue
            enemy_center_x = enemy.rect.x + enemy.rect.w // 2
            enemy_center_y = enemy.rect.y + enemy.rect.h // 2
            dx = enemy_center_x - center_x
            dy = enemy_center_y - center_y
            dist = math.hypot(dx, dy)
            if dist <= self.AOE_RADIUS:
                k_dir = 1 if dx > 0 else -1
                enemy.take_damage(self.AOE_DAMAGE, knockback_dir=k_dir)

                # GỬI TÍN HIỆU VỀ HOST NẾU LÀ CLIENT
                if self.game.game_mode == "multi" and not self.game.network.is_host:
                    # Tìm index của quái (Cần dùng enumerate ở vòng lặp ngoài hoặc .index)
                    try:
                        e_idx = level.enemies.index(enemy)
                        self.game.network.send_data({
                            "type": "hit_enemy",
                            "enemy_idx": e_idx,
                            "damage": self.AOE_DAMAGE,
                            "k_dir": k_dir
                        })
                    except ValueError:
                        pass
        # Hiệu ứng
        self.show_speech("AOE!")

    def update(self, delta_time, level):
        # Cập nhật cooldown
        if self.teleport_cooldown > 0:
            self.teleport_cooldown -= delta_time
        if self.aoe_cooldown > 0:
            self.aoe_cooldown -= delta_time
            
        if self.is_teleport_aiming:
            new_target = self.calculate_teleport_target(level)
            if new_target:
                self.teleport_target = new_target
            else:
                self.is_teleport_aiming = False # Huỷ ngắm nếu không tìm ra chỗ
        
        super().update(delta_time, level)
        
        # Đảm bảo double jump vẫn hoạt động (kế thừa từ Player)
        if self.progress.get("double_jump", False):
            self.has_double_jump = True

    def render(self, renderer, camera):
        # Nếu đang ngắm tele, vẽ bóng mờ trước
        if self.is_teleport_aiming and self.teleport_target:
            tgt_x, tgt_y = self.teleport_target
            # Khởi tạo SDL_BlendMode cho renderer để vẽ hình mờ
            sdl2.SDL_SetRenderDrawBlendMode(renderer, sdl2.SDL_BLENDMODE_BLEND)
            
            # Khung chữ nhật mờ màu xanh dương (Ice Blue)
            draw_rect = sdl2.SDL_Rect(
                int(tgt_x - camera.x),
                int(tgt_y - camera.y),
                self.rect.w, self.rect.h
            )
            sdl2.SDL_SetRenderDrawColor(renderer, 0, 191, 255, 100) # DeepSkyBlue + Alpha 100
            sdl2.SDL_RenderFillRect(renderer, draw_rect)
            
            # Trả lại Blend Mode mặt định (để khỏi lỗi các thứ khác)
            sdl2.SDL_SetRenderDrawBlendMode(renderer, sdl2.SDL_BLENDMODE_NONE)
            
        # 2. Vẽ Hitbox cho Skill A (AOE) khi đang kích hoạt
        if self.is_using_skill and self.state == "skill":
            # Vẽ vòng tròn hoặc khung bao quanh AOE Radius
            sdl2.SDL_SetRenderDrawBlendMode(renderer, sdl2.SDL_BLENDMODE_BLEND)
            
            # Tính tâm nhân vật
            cx = int(self.rect.x + self.rect.w // 2 - camera.x)
            cy = int(self.rect.y + self.rect.h // 2 - camera.y)
            r = self.AOE_RADIUS
            
            # Vẽ một hình vuông mờ bao quanh vùng AOE để hiển thị phạm vi
            aoe_rect = sdl2.SDL_Rect(cx - r, cy - r, r * 2, r * 2)
            sdl2.SDL_SetRenderDrawColor(renderer, 255, 100, 255, 80) # Màu tím nhạt mờ
            sdl2.SDL_RenderFillRect(renderer, aoe_rect)
            
            # Vẽ viền
            sdl2.SDL_SetRenderDrawColor(renderer, 255, 255, 255, 150)
            sdl2.SDL_RenderDrawRect(renderer, aoe_rect)
            
            sdl2.SDL_SetRenderDrawBlendMode(renderer, sdl2.SDL_BLENDMODE_NONE)

        super().render(renderer, camera)