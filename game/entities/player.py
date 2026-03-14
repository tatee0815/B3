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
        self.z_index = 4

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
        self.can_dash_in_air = True # Cho phép dash trên không nếu đã nhảy
        
        # Trạng thái kỹ năng
        self.has_double_jump = game.player_progress.get("double_jump", False)
        self.can_double_jump = self.has_double_jump
        self.jumped_once = False
        
        # Logic Dash (Lướt)
        self.is_dashing = False
        self.dash_timer = 0
        self.dash_cooldown = 0
        self.DASH_DURATION = 0.2
        self.DASH_SPEED = PLAYER_SPEED * 4
        
        # Logic Tấn công & Hitbox
        self.is_attacking = False
        self.attack_damage = 10
        self.attack_timer = 0
        self.ATTACK_DURATION = 0.3
        self.attack_cooldown_timer = 0
        self.ATTACK_COOLDOWN = 0.4
        self.attack_rect = sdl2.SDL_Rect(0, 0, 0, 0)

        self.recoil_timer = 0
        self.recoil_force = 5 # Độ mạnh của lực bật lùi

        self.debug_mode = False # Đổi thành False để ẩn khung đỏ khi xong
        
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
            self.vel_y = JUMP_FORCE # Hoặc JUMP_FORCE của fen
            self.on_ground = False # Nhảy lên thì không còn trên đất
            self.jumped_once = True # Đánh dấu đã nhảy một lần
        elif self.game.player_progress.get("double_jump", False) and self.jumped_once:
            self.vel_y = DOUBLE_JUMP_FORCE
            self.jumped_once = False # Reset để không thể nhảy lần thứ 3

    def dash(self):
        # Kiểm tra xem đã mở khóa Dash chưa
        if "dash" not in self.game.player_progress.get("unlocked_skills", []):
            return
        
        if self.dash_cooldown <= 0 and (self.on_ground or self.can_dash_in_air):
            self.is_dashing = True
            self.dash_timer = self.DASH_DURATION
            self.dash_cooldown = 0.8
            self.vel_y = 0  # Khóa trục Y khi dash
            if not self.on_ground:
                self.can_dash_in_air = False

    def melee_attack(self):
        if self.attack_cooldown_timer <= 0 and not self.is_dashing:
            self.is_attacking = True
            self.attack_timer = self.ATTACK_DURATION
            self.attack_cooldown_timer = self.ATTACK_COOLDOWN
            self.state = "attack"
            self.hit_enemies = []

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
        self.recoil_timer = 0.15 
        direction = -1 if self.facing_right else 1
        self.vel_x = direction * self.recoil_force 
        
        if not self.on_ground:
            self.can_dash_in_air = True

    def use_skill(self):
        if "skill_a" not in self.game.player_progress.get("unlocked_skills", []):
            return
        
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
        # Nới rộng vùng tương tác để đứng gần rương bấm E là ăn ngay
        interact_rect = sdl2.SDL_Rect(int(self.rect.x - 20), int(self.rect.y - 20), 
                                      int(self.rect.w + 40), int(self.rect.h + 40))
        for e in entities:
            if e != self and hasattr(e, "rect") and sdl2.SDL_HasIntersection(interact_rect, e.rect):
                if hasattr(e, "on_interact"):
                    e.on_interact(self) # Chuyền bản thân Player vào để lưu Checkpoint
                    return

    def update(self, delta_time, level):
        # --- 1. CẬP NHẬT CÁC BỘ ĐẾM THỜI GIAN ---
        if self.dash_cooldown > 0: self.dash_cooldown -= delta_time
        if self.recoil_timer > 0: self.recoil_timer -= delta_time
        if self.attack_cooldown_timer > 0: self.attack_cooldown_timer -= delta_time
        if self.mana_warning_timer > 0: self.mana_warning_timer -= delta_time
        if self.invincible_time > 0: self.invincible_time -= delta_time

        # --- 2. LOGIC TẤN CÔNG (ACTIVE FRAMES) ---
        if self.is_attacking:
            self.attack_timer -= delta_time
            if self.attack_timer <= 0:
                self.is_attacking = False
                # Reset danh sách khi kết thúc đòn đánh
                if hasattr(self, 'hit_enemies'): self.hit_enemies = []
            else:
                self._update_attack_hitbox()
                if level:
                    # Khởi tạo danh sách nếu chưa có
                    if not hasattr(self, 'hit_enemies'): self.hit_enemies = []
                    for enemy in level.enemies:
                        # CHỈ GÂY SÁT THƯƠNG NẾU QUÁI CHƯA BỊ TRÚNG ĐÒN TRONG LƯỢT NÀY
                        if enemy.alive and enemy not in self.hit_enemies:
                            if sdl2.SDL_HasIntersection(self.attack_rect, enemy.rect):
                                k_dir = 1 if self.facing_right else -1
                                enemy.take_damage(self.attack_damage, knockback_dir=k_dir)
                                self.hit_enemies.append(enemy) # Đánh dấu đã chém trúng
                                
                                self.apply_recoil()
                                if not self.on_ground:
                                    self.can_dash_in_air = True

        # Hồi lượt dash khi chân chạm đất
        if self.on_ground:
            self.can_dash_in_air = True

        # --- 3. QUẢN LÝ VẬN TỐC (PHÂN CẤP ƯU TIÊN) ---
        
        # Lưu vị trí X và trạng thái on_ground trước khi va chạm
        old_x = self.pos_x
        was_standing_on_platform = self.on_ground 

        if self.recoil_timer > 0:
            # Trạng thái bị bật lùi: Giữ nguyên vel_x đã set, chỉ thêm trọng lực
            self.vel_y += GRAVITY 
            
        elif self.is_dashing:
            # Trạng thái lướt: Khóa trục Y, di chuyển nhanh trục X
            self.dash_timer -= delta_time
            self.vel_x = (1 if self.facing_right else -1) * self.DASH_SPEED
            self.vel_y = 0 
            if self.dash_timer <= 0: 
                self.is_dashing = False
                
        else:
            # Trạng thái bình thường: Di chuyển phím + Trọng lực
            if self.moving_left: self.vel_x = -PLAYER_SPEED
            elif self.moving_right: self.vel_x = PLAYER_SPEED
            else: self.vel_x = 0

        # Giới hạn tốc độ rơi tối đa
        from game.constants import MAX_FALL_SPEED
        if self.vel_y > MAX_FALL_SPEED: self.vel_y = MAX_FALL_SPEED

        # --- 4. DI CHUYỂN VẬT LÝ VÀ VA CHẠM ---
        
        # Cộng vận tốc vào vị trí (Hàm của lớp Entity cơ bản)
        super().update(delta_time, level)

        if level:
            # Xử lý va chạm với gạch (Tiles)
            level.handle_collision(self)
            
            # PHỤC HỒI ON_GROUND: Nếu PlayingState đã xác nhận đứng trên Platform, 
            # đừng để level.handle_collision (vốn chỉ check gạch) reset nó về False.
            if was_standing_on_platform:
                self.on_ground = True

            # CHẶN XUYÊN TƯỜNG KHI DASH:
            # Nếu đang Dash mà vị trí X không thay đổi (do bị handle_collision đẩy lại)
            if self.is_dashing:
                if abs(self.pos_x - old_x) < 0.01 and abs(self.vel_x) > 1:
                    self.is_dashing = False
                    self.vel_x = 0

            for plat in level.platforms:
                if hasattr(plat, "vel_x"):
                    # Check va chạm chân với đầu platform
                    p_bottom = self.rect.y + self.rect.h
                    if (p_bottom <= plat.rect.y + 5 and 
                        p_bottom >= plat.rect.y - 5 and
                        self.rect.x + self.rect.w > plat.rect.x and 
                        self.rect.x < plat.rect.x + plat.rect.w):
                        
                        # Cưỡi lên platform
                        self.pos_x += plat.vel_x * delta_time
                        self.pos_y += plat.vel_y * delta_time
                        self.on_ground = True # Đứng trên platform cũng là on_ground
                        break

                # Sau đó mới cập nhật rect thực tế
                self.rect.x = int(self.pos_x)
                self.rect.y = int(self.pos_y)

        # --- 5. KIỂM TRA ĐIỀU KIỆN SỐNG CÒN ---
        # Kiểm tra rơi vực
        map_bottom = level.height * level.tile_size if level else 1000
        if self.rect.y > map_bottom + 100 or self.hp <= 0:
            if not self.is_respawning:
                self.handle_death()

        # --- 6. HẬU XỬ LÝ (MANA, KNOCKBACK, ANIMATION) ---
        from game.constants import MANA_MAX
        self.mana = min(MANA_MAX, self.mana + 5 * delta_time)
        
        # Giảm dần lực đẩy lùi từ quái (Knockback) nếu có
        if hasattr(self, 'knockback_vel_x'):
            if abs(self.knockback_vel_x) > 0.1:
                self.knockback_vel_x *= 0.85
                self.vel_x = self.knockback_vel_x
            else:
                self.knockback_vel_x = 0.0

        self._update_state() # Cập nhật animation state (idle, run, jump...)

        # Nếu rơi quá sâu (vượt quá chiều cao của Map)
        if self.pos_y > level.pixel_height:
            if hasattr(self, 'hp'):
                self.hp = 0 # Hiệp sĩ tử trận
            else:
                self.alive = False # Quái biến mất
    
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
        print("Nhân vật đã chết!")
        
        if hasattr(self.game, 'lives'):
            self.game.lives -= 1
            if self.game.lives <= 0:
                print("Hết mạng! Game Over!")
                self.game.change_state("game_over") # Chuyển thẳng ra màn hình Game Over
                return

        if 'total_deaths' in self.game.player_progress:
            self.game.player_progress['total_deaths'] += 1
        # Hồi sinh nếu còn mạng
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

    def check_bounds(self):
        # Chặn trái
        if self.rect.x < 0:
            self.rect.x = 0
            self.pos_x = 0.0
        # Chặn phải
        if self.rect.x + self.rect.w > self.level.pixel_width:
            self.rect.x = self.level.pixel_width - self.rect.w
            self.pos_x = float(self.rect.x)
        # Rơi xuống vực (Y quá lớn) -> Chết
        if self.rect.y > self.level.pixel_height + 100:
            self.take_damage(999)

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
