import sdl2
from game.constants import (
    MAX_FALL_SPEED, PLAYER_SPEED, JUMP_FORCE, DOUBLE_JUMP_FORCE,
    GRAVITY, PLAYER_MAX_HP, MANA_MAX, 
    SKILL_A_COST, KEY_BINDINGS_DEFAULT
)
from .base import Entity
from .projectile import Projectile

class Player(Entity):
    def __init__(self, game):
        # Khởi tạo tại tọa độ mặc định, kích thước nhân vật 24x48
        super().__init__(game, x=100, y=400, w=24, h=48)

        progress = self.game.player_progress
        
        # Chỉ số cơ bản
        self.hp = progress.get("hp", PLAYER_MAX_HP)
        self.mana = progress.get("mana", 50)
        self.mana_warning_timer = 0
        self.mana_warning_duration = 1.0  # Thời gian hiển thị cảnh báo thiếu mana (giây)
        self.gold = progress.get("gold", 0)
        self.invincible_time = 0.0   # Thời gian bất tử (giây)
        self.invincible_duration = 2.0        # Thời gian bất tử sau khi bị đánh (giây)
        self.knockback_vel_x = 0.0 # Vận tốc knockback theo trục X (bật lùi)
        
        # Trạng thái di chuyển (Để tránh khựng phím)
        self.moving_left = False
        self.moving_right = False
        self.facing_right = True
        
        # Trạng thái kỹ năng
        self.has_double_jump = game.player_progress.get("double_jump", False)
        self.can_double_jump = self.has_double_jump
        self.jumped_once = False
        
        # Logic Dash (Lướt)
        self.is_dashing = False
        self.dash_timer = 0
        self.dash_cooldown = 0
        self.DASH_DURATION = 0.2
        self.DASH_SPEED = PLAYER_SPEED * 5
        
        # Logic Tấn công & Hitbox
        self.is_attacking = False
        self.attack_damage = 20
        self.attack_timer = 0
        self.ATTACK_DURATION = 0.3
        self.attack_cooldown_timer = 0
        self.ATTACK_COOLDOWN = 0.4
        self.attack_rect = sdl2.SDL_Rect(0, 0, 0, 0)

        self.recoil_timer = 0
        self.recoil_force = 15 # Độ mạnh của lực bật lùi

        self.debug_mode = True # Đổi thành False để ẩn khung đỏ khi xong
        
        self.is_respawning = False
        self.state = "idle"

        if "playing" in self.game.states:
            level_spawn = self.game.states["playing"].level.get_spawn_position()
            self.checkpoint_pos = level_spawn

    def handle_input(self, event):
        """Xử lý phím dựa trên KEY_BINDINGS_DEFAULT"""
        scancode = event.key.keysym.scancode
        
        if event.type == sdl2.SDL_KEYDOWN:
            if self.is_dashing:
                return # Không nhận input mới khi đang dash để tránh xung đột
            if scancode == KEY_BINDINGS_DEFAULT["left"]:
                self.moving_left = True
                self.facing_right = False
            elif scancode == KEY_BINDINGS_DEFAULT["right"]:
                self.moving_right = True
                self.facing_right = True
            elif scancode == KEY_BINDINGS_DEFAULT["jump"] or scancode == sdl2.SDL_SCANCODE_SPACE:
                self.jump()
            elif scancode == KEY_BINDINGS_DEFAULT["dash"]:
                self.dash()
            elif scancode == KEY_BINDINGS_DEFAULT["attack"]:
                self.melee_attack()
            elif scancode == KEY_BINDINGS_DEFAULT["skill"]:
                self.use_skill()
            elif scancode == KEY_BINDINGS_DEFAULT["interact"]:
                self.interact()

        elif event.type == sdl2.SDL_KEYUP:
            if scancode == KEY_BINDINGS_DEFAULT["left"]:
                self.moving_left = False
            elif scancode == KEY_BINDINGS_DEFAULT["right"]:
                self.moving_right = False

    def jump(self):
        if self.on_ground:
            self.vel_y = JUMP_FORCE
            self.on_ground = False
            self.jumped_once = True
            self.state = "jump"
        elif self.can_double_jump and self.jumped_once:
            self.vel_y = DOUBLE_JUMP_FORCE
            self.jumped_once = False

    def dash(self):
        if self.dash_cooldown <= 0 and not self.is_dashing:
            if self.on_ground or self.can_dash_in_air:
                self.is_dashing = True
                self.dash_timer = self.DASH_DURATION
                self.dash_cooldown = 0.8
                
                # Triệt tiêu vận tốc rơi ngay khi bắt đầu lướt để lướt thẳng ngang
                self.vel_y = 0 
                
                if not self.on_ground:
                    self.can_dash_in_air = False # Đã dùng lượt dash trên không

    def melee_attack(self):
        if self.attack_cooldown_timer <= 0 and not self.is_dashing:
            self.is_attacking = True
            self.attack_timer = self.ATTACK_DURATION
            self.attack_cooldown_timer = self.ATTACK_COOLDOWN
            self.state = "attack"
            
            # Tính toán vị trí hitbox gây sát thương
            self._update_attack_hitbox()
            
            # Kiểm tra va chạm gây sát thương lên quái
            entities = self.game.states["playing"].level.entities
            for e in entities:
                if e != self and hasattr(e, "rect"):
                    if sdl2.SDL_HasIntersection(self.attack_rect, e.rect):
                        if hasattr(e, "take_damage"):
                            e.take_damage(20)

    def _update_attack_hitbox(self):
        """Hàm dùng chung để tính toán vị trí hitbox tấn công"""
        # Cấu hình: Hẹp (16px) nhưng Xa (65px)
        attack_range = 65  
        attack_height = 16 
        
        # Tính toán tọa độ X dựa trên hướng nhìn
        if self.facing_right:
            ax = self.rect.x + self.rect.w 
        else:
            ax = self.rect.x - attack_range
            
        # Căn giữa theo trục Y của nhân vật
        ay = self.rect.y + (self.rect.h // 2) - (attack_height // 2)
        
        # Cập nhật trực tiếp vào thuộc tính của object
        self.attack_rect = sdl2.SDL_Rect(int(ax), int(ay), int(attack_range), int(attack_height))
                    
    def apply_recoil(self):
        """Gọi khi trúng quái vật để tạo lực bật lùi"""
        self.recoil_timer = 0.15  # Thời gian bật lùi (giây)
        # Bật lùi ngược hướng nhìn
        direction = -1 if self.facing_right else 1
        self.vel_x = direction * 5.0 # Lực bật lùi (điều chỉnh tùy ý)
        
        # Hollow Knight style: Chém trúng quái khi đang trên không sẽ reset lượt Dash
        if not self.on_ground:
            self.can_dash_in_air = True

    def use_skill(self):
        if self.mana >= SKILL_A_COST:
            self.mana -= SKILL_A_COST
            self.skill_a_fire()
        else:
            self.mana_warning_timer = self.mana_warning_duration

    def skill_a_fire(self):
        direction = 1 if self.facing_right else -1
        proj_x = self.rect.x + (self.rect.w if direction > 0 else -32)
        center_y = self.rect.y + (self.rect.h // 2)
        proj = Projectile(self.game, proj_x, center_y - 8, direction)
        self.game.states["playing"].level.entities.append(proj)

    def interact(self):
        entities = self.game.states["playing"].level.entities
        for e in entities:
            if e != self and self.collides_with(e):
                if hasattr(e, "on_interact"):
                    e.on_interact()
                    return

    def update(self, delta_time, level):
        # 1. Cập nhật các bộ đếm thời gian
        if self.dash_cooldown > 0: self.dash_cooldown -= delta_time
        if self.recoil_timer > 0: self.recoil_timer -= delta_time
        if self.attack_cooldown_timer > 0: self.attack_cooldown_timer -= delta_time
        if self.mana_warning_timer > 0: self.mana_warning_timer -= delta_time
        
        if self.is_attacking:
            self.attack_timer -= delta_time
            if self.attack_timer <= 0: 
                self.is_attacking = False
            else:
                # CẬP NHẬT HITBOX THEO NHÂN VẬT (Tránh bị bỏ lại khi chạy)
                self._update_attack_hitbox()

        if self.on_ground: self.can_dash_in_air = True

        # 2. Quản lý Vận tốc (PHÂN CẤP ƯU TIÊN DI CHUYỂN)
        
        # TRẠNG THÁI 1: Đang bị bật lùi (Recoil) - Khóa điều khiển trái/phải
        if self.recoil_timer > 0:
            # vel_x đã được set trong apply_recoil, ta giữ nguyên nó
            self.vel_y += GRAVITY 
            
        # TRẠNG THÁI 2: Đang lướt (Dash) - Khóa trọng lực và điều khiển
        elif self.is_dashing:
            self.dash_timer -= delta_time
            self.vel_x = (1 if self.facing_right else -1) * self.DASH_SPEED
            self.vel_y = 0 
            if self.dash_timer <= 0: 
                self.is_dashing = False
                self.vel_x = 0
                
        # TRẠNG THÁI 3: Bình thường (Chạy, Nhảy, Chém mượt)
        else:
            # Xử lý di chuyển trái phải
            if self.moving_left: self.vel_x = -PLAYER_SPEED
            elif self.moving_right: self.vel_x = PLAYER_SPEED
            else: self.vel_x = 0

        # 3. Giới hạn vật lý và va chạm
        if self.vel_y > MAX_FALL_SPEED: self.vel_y = MAX_FALL_SPEED

        super().update(delta_time, level)
        level.handle_collision(self)

        # Kiểm tra rơi khỏi thế giới
        map_bottom = level.height * level.tile_size
        if self.rect.y > map_bottom + 100: # Rơi quá xa dưới đáy map
                self.handle_death()
        if self.hp <= 0:
            self.handle_death()
        
        # 5. Hồi Mana và cập nhật State cho animation
        self.mana = min(MANA_MAX, self.mana + 5 * delta_time)
        self._update_state()

        # === XỬ LÝ INVINCIBLE + KNOCKBACK ===
        if self.invincible_time > 0:
            self.invincible_time -= delta_time
        
        # Giảm dần knockback
        if abs(self.knockback_vel_x) > 0.1:
            self.knockback_vel_x *= 0.85
            self.vel_x = self.knockback_vel_x
        else:
            self.knockback_vel_x = 0.0

    
    def take_damage(self, amount, knockback_dir=1):
        """Player bị quái đánh - đã tích hợp invincible + knockback"""
        if self.is_respawning or self.invincible_time > 0:
            return  # Không nhận sát thương khi đang hồi sinh hoặc bất tử
        
        self.hp -= amount
        print(f"Player take damage! HP còn: {self.hp}")
        
        # Bất tử 1 giây
        self.invincible_time = self.invincible_duration
        
        # Knockback (bật lùi)
        self.knockback_vel_x = knockback_dir * 10.0
        self.vel_x = self.knockback_vel_x
        
        if self.hp <= 0:
            self.hp = 0
            self.handle_death()
    
    def handle_death(self):
        """Xử lý tập trung khi nhân vật chết"""
        print("Nhân vật đã chết! Đang hồi sinh...")
        
        # 1. Trừ mạng (Lives) từ instance Game
        if hasattr(self.game, 'lives'):
            self.game.lives -= 1
            if self.game.lives <= 0:
                print("Game Over!")

        if 'total_deaths' in self.game.player_progress:
            self.game.player_progress['total_deaths'] += 1
        else:
            self.game.player_progress['total_deaths'] = 1
    
        # 3. Gọi hàm respawn và hồi phục chỉ số
        self.is_respawning = True
        self.respawn(self.checkpoint_pos)

        self.hp = PLAYER_MAX_HP
        self.is_respawning = False

    def _update_state(self):
        if self.is_attacking: self.state = "attack"
        elif self.is_dashing: self.state = "dash"
        elif not self.on_ground: self.state = "jump"
        elif self.vel_x != 0: self.state = "run"
        else: self.state = "idle"

    def respawn(self, pos):
        # 1. Đưa tọa độ về vị trí an toàn
        self.rect.x = int(pos[0])
        self.rect.y = int(pos[1])
        self.pos_x = int(self.rect.x) # Cập nhật cả pos_x/y của lớp base
        self.pos_y = int(self.rect.y)

        # 2. QUAN TRỌNG: Triệt tiêu toàn bộ vận tốc cũ
        self.vel_x = 0
        self.vel_y = 0
        
        # 3. Reset các trạng thái điều khiển
        self.on_ground = False
        self.moving_left = False
        self.moving_right = False
        self.is_dashing = False
        self.is_attacking = False
        
        # 4. Đặt lại camera ngay lập tức để tránh tính toán sai lệch
        if hasattr(self.game, 'camera'):
            self.game.camera.reset()

    def render(self, renderer, camera):
        if self.invincible_time > 0:
            # Nhấp nháy mỗi 100ms
            if (sdl2.timer.SDL_GetTicks() // 100) % 2 == 0:
                return # Bỏ qua frame này không vẽ
        
        if self.mana_warning_timer > 0:
            # Tính toán vị trí: Trên đầu nhân vật một chút
            # Cho chữ bay nhẹ lên trên theo thời gian để sinh động
            offset_y = (self.mana_warning_duration - self.mana_warning_timer) / 20
            text_x = self.rect.x - camera.x
            text_y = self.rect.y - camera.y - 30 - offset_y
            
            # Mượn hàm vẽ text từ HUD để đảm bảo dùng đúng font UTM-Netmuc
            if hasattr(self.game, 'hud'):
                self.game.hud._draw_text(
                    renderer, 
                    "Không đủ Mana!", 
                    text_x, 
                    text_y, 
                    (80, 180, 255) # Màu xanh Mana cho đồng bộ
                )
        # Ép kiểu int cho tất cả các tham số truyền vào SDL_Rect
        draw_x = int(self.rect.x - camera.x)
        draw_y = int(self.rect.y - camera.y)
        draw_w = int(self.rect.w)
        draw_h = int(self.rect.h)
        
        draw_rect = sdl2.SDL_Rect(draw_x, draw_y, draw_w, draw_h)
        
        # Vẽ hitbox nhân vật (xanh lá)
        sdl2.SDL_SetRenderDrawColor(renderer, 0, 255, 0, 255)
        sdl2.SDL_RenderDrawRect(renderer, draw_rect)

        # Vẽ hitbox tấn công (đỏ) khi đang chém
        if self.debug_mode and self.is_attacking:
            atk_x = int(self.attack_rect.x - camera.x)
            atk_y = int(self.attack_rect.y - camera.y)
            atk_w = int(self.attack_rect.w)
            atk_h = int(self.attack_rect.h)
            
            atk_draw = sdl2.SDL_Rect(atk_x, atk_y, atk_w, atk_h)
            sdl2.SDL_SetRenderDrawColor(renderer, 255, 0, 0, 255)
            sdl2.SDL_RenderDrawRect(renderer, atk_draw)

    def collides_with(self, other):
        return sdl2.SDL_HasIntersection(self.rect, other.rect)
