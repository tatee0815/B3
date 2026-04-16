import sdl2
import math
from game.constants import PLAYER_SPEED, GRAVITY, SKILL_A_COST, MANA_MAX, PLAYER_MAX_HP
from game.utils.assets import AssetManager
from .player import Player
from .projectile import Projectile
from .enemy import EnemyFireball

class Princess(Player):
    def __init__(self, game):
        super().__init__(game, role="princess")
            
        # Tọa độ checkpoint ban đầu (nếu có lưu)
        self.checkpoint_pos = self.progress.get("checkpoint", self.checkpoint_pos)
        
        self.state = "idle"
        
        # Điều chỉnh kỹ năng
        self.teleport_cooldown = 0.0
        self.TELEPORT_COOLDOWN_TIME = 1.5
        self.aoe_cooldown = 0.0
        self.AOE_COOLDOWN_TIME = 2.0
        self.AOE_DAMAGE = 30
        self.AOE_RADIUS = 100  # pixel
        
        # Teleport ngắm
        self.is_teleport_aiming = False
        self.teleport_target = None
        
        # Hiệu ứng AOE
        self.aoe_visual_timer = 0.0

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
        Tìm kiếm bục nhảy (Platform) gần nhất ở phía trước mặt.
        - Không giới hạn khoảng cách.
        - Có thể nhìn xuyên qua tiles_2.
        - Bị chặn bởi tiles_1.
        """
        start_x = self.rect.x + self.rect.w // 2
        start_y = self.rect.y + self.rect.h // 2
        
        best_target = None
        min_dist = float('inf')
        
        # --- LẤY GIỚI HẠN MÀN HÌNH HIỆN TẠI ---
        cam = self.game.camera
        screen_rect = sdl2.SDL_Rect(int(cam.x), int(cam.y), self.game.logical_width, self.game.logical_height)
        
        for plat in level.platforms:
            # 1. Kiểm tra giới hạn bục trong màn hình (MỚI)
            if not sdl2.SDL_HasIntersection(plat.rect, screen_rect):
                continue

            # Lấy tâm bục nhảy (điểm Princess sẽ đáp xuống)
            plat_target_x = plat.rect.x + plat.rect.w // 2
            plat_target_y = plat.rect.y
            
            # 1. Kiểm tra hướng (Phía trước mặt)
            is_in_front = False
            if self.facing_right:
                # Nếu nhìn phải, bục phải có phần nằm bên phải tâm Princess
                if plat.rect.x + plat.rect.w > start_x: 
                    is_in_front = True
            else:
                # Nếu nhìn trái, bục phải có phần nằm bên trái tâm Princess
                if plat.rect.x < start_x:
                    is_in_front = True
            
            if not is_in_front:
                continue
            
            # Tính khoảng cách trực tiếp (Chim bay)
            dx = plat_target_x - start_x
            dy = plat_target_y - start_y
            dist = math.hypot(dx, dy)
            
            # --- LOẠI TRỪ NỀN TẢNG ĐANG ĐỨNG (QUAN TRỌNG) ---
            # Nếu Princess đang đứng trên bục này, bỏ qua để tránh tele tại chỗ
            is_on_plat_x = (self.rect.x + self.rect.w > plat.rect.x) and (self.rect.x < plat.rect.x + plat.rect.w)
            is_touching_top = abs((self.rect.y + self.rect.h) - plat.rect.y) < 5
            if is_on_plat_x and is_touching_top:
                continue

            # Bỏ qua nếu bục quá gần (Dưới 32px)
            if dist < 32:
                continue
                
            # 3. Kiểm tra Tầm nhìn (Line of Sight) đối với tiles_1
            blocked = False
            # Quét dọc theo đường thẳng nối từ mắt Princess đến bục
            # Sử dụng bước nhảy 16px (nửa tile) để cân bằng chính xác và hiệu năng
            num_steps = int(max(1, dist / 16))
            for i in range(1, num_steps):
                check_x = start_x + (dx * i / num_steps)
                check_y = start_y + (dy * i / num_steps)
                
                col, row = int(check_x // level.tile_size), int(check_y // level.tile_size)
                if 0 <= col < level.width and 0 <= row < level.height:
                    # Nếu gặp tiles_1 (tường cứng) -> Bị chặn
                    if level.tiles[row][col] == 1:
                        blocked = True
                        break
                    # Lưu ý: tiles_2 (mặt đất) không chặn tầm nhìn theo yêu cầu
            
            if blocked:
                continue
                
            # 4. Chọn bục gần nhất
            if dist < min_dist:
                min_dist = dist
                # Tọa độ đích (căn giữa player trên bục)
                target_x = int(plat_target_x - self.rect.w // 2)
                target_y = int(plat.rect.y - self.rect.h)
                best_target = (target_x, target_y)
        
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
        
        # Bật hiệu ứng hình ảnh
        self.aoe_visual_timer = 0.5
        
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
        
        # 3. Hủy toàn bộ đạn địch trong phạm vi AOE
        for entity in level.entities[:]:
            if isinstance(entity, EnemyFireball) and entity.alive:
                e_center_x = entity.rect.x + entity.rect.w // 2
                e_center_y = entity.rect.y + entity.rect.h // 2
                dx = e_center_x - center_x
                dy = e_center_y - center_y
                if math.hypot(dx, dy) <= self.AOE_RADIUS:
                    entity.alive = False
                    # Tạo hiệu ứng nhỏ nếu cần (tùy chỉnh sau)
        # Hiệu ứng
        self.show_speech("BOOM!")

    def update(self, delta_time, level):
        # Cập nhật cooldown
        if self.teleport_cooldown > 0: self.teleport_cooldown -= delta_time
        if self.aoe_cooldown > 0: self.aoe_cooldown -= delta_time
        if self.aoe_visual_timer > 0: self.aoe_visual_timer -= delta_time
            
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
        # Hiệu ứng AOE (Vòng tròn hồng lan tỏa)
        if self.aoe_visual_timer > 0:
            progress = (0.5 - self.aoe_visual_timer) / 0.5
            current_radius = int(self.AOE_RADIUS * progress)
            center_x = int(self.rect.x + self.rect.w // 2 - camera.x)
            center_y = int(self.rect.y + self.rect.h // 2 - camera.y)
            
            # Vẽ hình tròn đơn giản (SDL RenderDraw có giới hạn, ta có thể vẽ nhiều rect hẹp)
            sdl2.SDL_SetRenderDrawColor(renderer, 255, 100, 200, int(255 * (1 - progress)))
            for angle in range(0, 360, 5):
                rad = math.radians(angle)
                tx = int(center_x + math.cos(rad) * current_radius)
                ty = int(center_y + math.sin(rad) * current_radius)
                sdl2.SDL_RenderDrawPoint(renderer, tx, ty)
                sdl2.SDL_RenderDrawPoint(renderer, tx+1, ty) # Làm dày tí
                sdl2.SDL_RenderDrawPoint(renderer, tx, ty+1)

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