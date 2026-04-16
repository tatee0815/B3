import sdl2
from game.constants import (
    MAX_FALL_SPEED, PLAYER_SPEED, JUMP_FORCE, DOUBLE_JUMP_FORCE,
    GRAVITY, PLAYER_MAX_HP, MANA_MAX, 
    SKILL_A_COST, KEY_BINDINGS_DEFAULT
)
from game.utils.assets import AssetManager
from .base import Entity
from .projectile import Projectile

class Player(Entity):
    @property
    def progress(self):
        """Dynamic access to the correct progress record in game.player_progress"""
        if "players" in self.game.player_progress:
            return self.game.player_progress["players"].get(self.role, {})
        return self.game.player_progress

    def __init__(self, game, role="knight"):
        # Khởi tạo tại tọa độ mặc định, kích thước nhân vật 36x60
        super().__init__(game, x=-1000, y=-1000, w=36, h=60)
        self.is_remote = False
        self.z_index = 4
        self.is_visible = True
        self.role = role
        
        # Chỉ số cơ bản (Khởi tạo từ progress hiện tại)
        self.hp = self.progress.get("hp", PLAYER_MAX_HP)
        self.mana = self.progress.get("mana", 50)
        from game.constants import MAX_LIVES
        self.lives = self.progress.get("lives", MAX_LIVES)
        self.mana_warning_timer = 0
        self.mana_warning_duration = 1.0  # Thời gian hiển thị cảnh báo thiếu mana (giây)

        # Coin is now a property to share between players
        if "coin" not in self.game.player_progress:
            self.game.player_progress["coin"] = 0
            
        self.gold_milestone = self.gold // 20
        self.invincible_time = 0.0   # Thời gian bất tử (giây)
        self.invincible_duration = 2.0        # Thời gian bất tử sau khi bị đánh (giây)
        self.knockback_vel_x = 0.0 # Vận tốc knockback theo trục X (bật lùi)
        self.checkpoint_pos = self.progress.get("checkpoint")

        # Trạng thái di chuyển (Để tránh khựng phím)
        self.moving_left = False
        self.moving_right = False
        self.facing_right = True
        self.can_dash_in_air = True # Cho phép dash trên không nếu đã nhảy
        
        # Trạng thái kỹ năng (Luôn check trực tiếp từ progress)
        self.has_double_jump = self.progress.get("double_jump", False)
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
        self.mele_anim_frame = 0

        self.recoil_timer = 0
        self.recoil_force = 5 # Độ mạnh của lực bật lùi
        
        self.is_respawning = False
        self.is_using_skill = False
        self.state = "idle"

        self.speech_text = ""
        self.speech_timer = 0.0

        if "playing" in self.game.states:
            level_spawn = self.game.states["playing"].level.get_spawn_position()
            # Chỉ lấy spawn của level nếu trong progress chưa có checkpoint
            if not self.checkpoint_pos:
                self.checkpoint_pos = level_spawn

        AssetManager.load_all_player_sprites(game.renderer)
        self.anim_frame = 0
        self.anim_timer = 0
        self.anim_speed = 0.1 # Tốc độ chuyển frame (giây)

        self.debug_mode = False # Bật lại khung đỏ hitbox theo yêu cầu
        self.is_god_mode = False
        self.is_flying = False
        self.is_ghosting = False

    def handle_input(self, event):
        """Xử lý phím dựa trên KEY_BINDINGS_DEFAULT"""
        scancode = event.key.keysym.scancode
        
        if event.type == sdl2.SDL_KEYDOWN:
            # --- DEBUG CHEAT KEYS ---
            if scancode == sdl2.SDL_SCANCODE_F1:
                self.activate_cheat_mode()
            # ------------------------
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
                if not getattr(self, "is_attack_key_down", False):
                    self.is_attack_key_down = True
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
            elif scancode == KEY_BINDINGS_DEFAULT["attack"]:
                self.is_attack_key_down = False

    def jump(self):
        if self.on_ground:
            self.vel_y = JUMP_FORCE # Hoặc JUMP_FORCE của fen
            self.on_ground = False # Nhảy lên thì không còn trên đất
            self.jumped_once = True # Đánh dấu đã nhảy một lần
        elif self.progress.get("double_jump", False) and self.jumped_once:
            self.vel_y = DOUBLE_JUMP_FORCE
            self.jumped_once = False # Reset để không thể nhảy lần thứ 3

    def dash(self):
        # Kiểm tra xem đã mở khóa Dash chưa
        if "dash" not in self.progress.get("unlocked_skills", []):
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
            self.is_using_skill = False
            self.attack_timer = self.ATTACK_DURATION
            self.attack_cooldown_timer = self.ATTACK_COOLDOWN
            self.state = "attack"
            self.hit_enemies = []
            self.anim_frame = 0 # Bắt đầu animation đánh từ frame 0

    def _update_attack_hitbox(self):
        """Tính toán vị trí hitbox và cập nhật frame cho hiệu ứng chém"""
        attack_range = 65  
        attack_height = 16 
        
        if self.facing_right:
            ax = self.rect.x + self.rect.w -10
        else:
            ax = self.rect.x - 55 # điều chỉnh để khi quay sang trái thì đều nhau
                
        ay = self.rect.y + (self.rect.h // 2) - (attack_height // 2)
        self.attack_rect = sdl2.SDL_Rect(int(ax), int(ay), int(attack_range), int(attack_height))

        # Tính toán frame cho sprite 'mele' (có 8 frames theo file assets của bạn)
        # Chúng ta dùng tỷ lệ thời gian còn lại của đòn đánh
        total_mele_frames = 8
        progress = 1.0 - (self.attack_timer / self.ATTACK_DURATION)
        self.mele_anim_frame = int(progress * total_mele_frames)
        
        if self.mele_anim_frame >= total_mele_frames:
            self.mele_anim_frame = total_mele_frames - 1
                    
    def apply_recoil(self):
        self.recoil_timer = 0.15 
        direction = -1 if self.facing_right else 1
        self.vel_x = direction * self.recoil_force 

    def update_attack_collisions(self, level):
        """
        Logic quét va chạm và gây sát thương. 
        Được tách ra để Host có thể gọi cho cả Remote Player.
        """
        if not self.is_attacking or not level:
            return

        self._update_attack_hitbox()
        
        # Khởi tạo danh sách nếu chưa có
        if not hasattr(self, 'hit_enemies'): self.hit_enemies = []
        
        for i, enemy in enumerate(level.enemies):
            # CHỈ GÂY SÁT THƯƠNG NẾU QUÁI CHƯA BỊ TRÚNG ĐÒN TRONG LƯỢT NÀY
            if enemy.alive and enemy not in self.hit_enemies:
                if sdl2.SDL_HasIntersection(self.attack_rect, enemy.rect):
                    k_dir = 1 if self.facing_right else -1
                    enemy.take_damage(self.attack_damage, knockback_dir=k_dir)
                    self.hit_enemies.append(enemy) # Đánh dấu đã chém trúng
                    
                    # GỬI TÍN HIỆU VỀ HOST NẾU LÀ CLIENT
                    if self.game.game_mode == "multi" and not self.game.network.is_host:
                        self.game.network.send_data({
                            "type": "hit_enemy",
                            "enemy_idx": i,
                            "damage": self.attack_damage,
                            "k_dir": k_dir
                        })

                    self.apply_recoil()
                    if not self.on_ground:
                        self.can_dash_in_air = True
        
    def update_animation(self, delta_time):
        """Cập nhật animation frame và timer chém cho cả local và remote player"""
        # 1. Cập nhật frame hoạt ảnh chính của sprite
        self.anim_timer += delta_time
        current_anim_speed = 0.12 
        if self.state in ["skill", "attack2"]:
            current_anim_speed = 0.05
        elif self.state == "attack":
            current_anim_speed = 0.08

        if self.anim_timer >= current_anim_speed:
            self.anim_timer = 0
            self.anim_frame += 1
            
        # 2. Cập nhật đếm ngược cho đòn tấn công (để hiện tia chém Slash)
        if self.is_attacking:
            self.attack_timer -= delta_time
            if self.attack_timer <= 0:
                self.is_attacking = False
            else:
                self._update_attack_hitbox()
        
        if not self.on_ground:
            self.can_dash_in_air = True

    def use_skill(self):
        if "skill_a" not in self.progress.get("unlocked_skills", []):
            return
        
        if self.mana >= SKILL_A_COST:
            self.mana -= SKILL_A_COST

            # Kích hoạt hoạt ảnh kỹ năng
            self.state = "skill"
            self.anim_frame = 0
            self.is_attacking = True # Tận dụng cờ này để khóa các hành động khác
            self.is_using_skill = True
            self.attack_timer = 0.4 # Thời gian hoạt ảnh skill lâu hơn chém thường
            
            self.skill_a_fire()
        else:
            self.mana_warning_timer = self.mana_warning_duration

    def skill_a_fire(self):
        direction = 1 if self.facing_right else -1
        proj_x = self.rect.x + (self.rect.w if direction > 0 else -32)
        center_y = self.rect.y + (self.rect.h // 2)
        proj = Projectile(self.game, proj_x, center_y - 8, direction)
        self.game.states["playing"].level.entities.append(proj)
        
        # GỬI LỆNH QUA MẠNG
        if self.game.game_mode == "multi":
            self.game.network.send_data({
                "type": "spawn_projectile",
                "x": proj_x,
                "y": center_y - 8,
                "dir": direction
            })

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
        # --- 1. CẬP NHẬT CÁC BỘ ĐẾM THỜI GIAN (Dùng cho cả Local và Remote) ---
        if self.dash_cooldown > 0: self.dash_cooldown -= delta_time
        if self.recoil_timer > 0: self.recoil_timer -= delta_time
        if self.attack_cooldown_timer > 0: self.attack_cooldown_timer -= delta_time
        if self.mana_warning_timer > 0: self.mana_warning_timer -= delta_time
        if self.invincible_time > 0: 
            self.invincible_time -= delta_time
            if self.invincible_time < 0: self.invincible_time = 0
            
        if self.speech_timer > 0: self.speech_timer -= delta_time

        # --- 2. LOGIC HOẠT ẢNH ---
        self.update_animation(delta_time)

        # NẾU LÀ REMOTE PLAYER -> DỪNG TẠI ĐÂY (Vật lý sẽ được nội suy ở PlayingState)
        if getattr(self, "is_remote", False):
            return

        # --- 3. LOGIC TẤN CÔNG (ACTIVE FRAMES) ---
        if self.is_attacking:
            # Nếu là remote player đang tấn công, cần cập nhật frame hiệu ứng chém
            # (Thực hiện trong update_animation để đồng bộ hình ảnh)
            pass 

        if self.attack_timer <= 0:
            self.is_attacking = False
            self.is_using_skill = False
            # Reset danh sách khi kết thúc đòn đánh
            if hasattr(self, 'hit_enemies'): self.hit_enemies = []
        else:
            # Chỉ Local Player tự chạy logic va chạm trong update
            # Remote Player sẽ được Host gọi thông qua PlayingState
            if not getattr(self, "is_remote", False):
                self.update_attack_collisions(level)

        # Hồi lượt dash khi chân chạm đất
        if self.on_ground:
            self.can_dash_in_air = True

        # --- 3. QUẢN LÝ VẬN TỐC (PHÂN CẤP ƯU TIÊN) ---
        
        # Lưu vị trí X và trạng thái on_ground trước khi va chạm
        old_x = self.pos_x
        was_standing_on_platform = self.on_ground 

        if self.recoil_timer > 0:
            # Trạng thái bị bật lùi: Giữ nguyên vel_x đã set
            pass 
            
        elif self.is_dashing:
            # Trạng thái lướt: Khóa trục Y, di chuyển nhanh trục X
            self.dash_timer -= delta_time
            self.vel_x = (1 if self.facing_right else -1) * self.DASH_SPEED
            self.vel_y = 0 
            if self.dash_timer <= 0: 
                self.is_dashing = False
                
        elif self.is_flying:
            # Chế độ bay: Di chuyển tự do 8 hướng, không trọng lực
            self.vel_x = 0
            if self.moving_left: self.vel_x = -PLAYER_SPEED * 2
            if self.moving_right: self.vel_x = PLAYER_SPEED * 2
            
            self.vel_y = 0
            keys = sdl2.SDL_GetKeyboardState(None)
            if keys[sdl2.SDL_SCANCODE_W] or keys[sdl2.SDL_SCANCODE_UP]:
                self.vel_y = -PLAYER_SPEED * 2
            if keys[sdl2.SDL_SCANCODE_S] or keys[sdl2.SDL_SCANCODE_DOWN]:
                self.vel_y = PLAYER_SPEED * 2
                
            # Tự cập nhật tọa độ cho chế độ bay (vì đã skip super().update)
            self.pos_x += self.vel_x * delta_time * 60
            self.pos_y += self.vel_y * delta_time * 60
        else:
            # Trạng thái bình thường: Di chuyển phím
            if self.moving_left: self.vel_x = -PLAYER_SPEED
            elif self.moving_right: self.vel_x = PLAYER_SPEED
            else: self.vel_x = 0

        # Giới hạn tốc độ rơi tối đa
        if self.vel_y > MAX_FALL_SPEED: self.vel_y = MAX_FALL_SPEED

        # --- 4. DI CHUYỂN VẬT LÝ VÀ VA CHẠM ---
        
        # Cộng vận tốc vào vị trí (Chỉ chạy khi không trong chế độ bay)
        if not self.is_flying:
            super().update(delta_time, level)
        else:
            # Cập nhật rect cho chế độ bay
            self.rect.x = int(round(self.pos_x))
            self.rect.y = int(round(self.pos_y))

        if level and not self.is_ghosting:
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

            # --- 5. GIỚI HẠN BIÊN THẾ GIỚI (WORLD BOUNDARIES) ---
            # Ngăn nhân vật đi quá biên trái (0) hoặc quá biên phải (map width)
            # Cho phép rớt hố một đoạn nhỏ trước khi chết tự nhiên
            self.pos_x = max(0.0, min(self.pos_x, float(level.pixel_width - self.rect.w)))
            
            # Cập nhật rect thực tế sau khi kẹp biên
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

    @property
    def gold(self):
        return self.game.player_progress.get("coin", 0)

    @gold.setter
    def gold(self, value):
        self.game.player_progress["coin"] = value

    def add_gold(self, amount):
        """Cộng vàng, kiểm tra mốc để tăng mạng."""
        self.gold += amount

        new_milestone = self.gold // 20
        if new_milestone > self.gold_milestone:
            extra = new_milestone - self.gold_milestone
            self.game.lives += extra
            self.game.player_progress["lives"] = self.game.lives
            self.gold_milestone = new_milestone

            # Hiển thị thông báo (tuỳ chọn)
            if hasattr(self, 'show_speech'):
                self.show_speech(f"+{extra} Mạng!", 2.0)

    def take_damage(self, amount, knockback_dir=1):
        if self.is_god_mode: # Chống bị trừ máu
            return
        """Player bị quái đánh - đã tích hợp invincible + knockback"""
        if self.is_respawning or self.invincible_time > 0 or self.is_using_skill:
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
        print(f"Nhân vật {self.role} đã chết!")
        
        # Mạng sống độc lập cho từng người chơi (Theo yêu cầu: HP và Lives là dùng riêng)
        self.lives -= 1
        
        # Cập nhật vào progress để lưu trữ
        if "players" in self.game.player_progress and self.role in self.game.player_progress["players"]:
            self.game.player_progress["players"][self.role]["lives"] = self.lives
        else:
            self.game.player_progress["lives"] = self.lives

        if self.lives <= 0:
            # ĐỒNG BỘ GAME OVER QUA MẠNG
            if self.game.game_mode == "multi":
                self.game.network.send_data({"type": "game_over"})
                self.game.change_state("intro", mode="multi_fail")
                return # THOÁT NGAY, KHÔNG HỒI SINH
            else:
                self.game.change_state("fail")
                return # THOÁT NGAY, KHÔNG HỒI SINH
        # Hồi sinh nếu còn mạng
        self.is_respawning = True
        spawn_pos = self.checkpoint_pos
        if not spawn_pos:
            if "playing" in self.game.states:
                spawn_pos = self.game.states["playing"].level.get_spawn_position()
            else:
                spawn_pos = (-1000, -1000)
        self.respawn(spawn_pos)
        self.hp = PLAYER_MAX_HP
        self.is_respawning = False

    def _update_state(self):
        if self.is_attacking: 
            if self.state not in ["attack", "skill", "attack2"]:
                self.state = "attack"
            return
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
        self.pos_x = float(self.rect.x) 
        self.pos_y = float(self.rect.y)

        # 2. QUAN TRỌNG: Triệt tiêu toàn bộ vận tốc cũ và trạng thái bất tử
        self.vel_x = 0
        self.vel_y = 0
        self.invincible_time = 0
        
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
        if hasattr(self, 'is_visible') and not self.is_visible:
            return
            
        # 1. Hiệu ứng nhấp nháy khi bất tử (Giữ nguyên logic cũ)
        if hasattr(self, 'invincible_time') and self.invincible_time > 0:
            if (sdl2.timer.SDL_GetTicks() // 100) % 2 == 0:
                return 
        
        # --- PHẦN VẼ NHÂN VẬT TỪ SPRITE SHEET ---
        anim_key = self.state
        # Tự động chuyển sang bộ animation 2 cho Princess (idle2, run2,...)
        if self.role == "princess" and (anim_key + "2") in AssetManager.ANIM_CONFIG:
            anim_key += "2"
            
        texture, srcrect = AssetManager.get_anim_info(anim_key, self.anim_frame)

        # Tính toán vị trí vẽ
        draw_x = int(self.rect.x - camera.x)
        draw_y = int(self.rect.y - camera.y)
        
        # Vẽ kích thước 128x128 theo yêu cầu (Sprite gốc)
        render_w = 96
        render_h = 96
        dst_x = draw_x - (render_w - self.rect.w) // 2
        dst_y = draw_y - (render_h - self.rect.h)
        
        # Vì bộ Biker là 48x48, ta có thể vẽ to hơn hoặc giữ nguyên
        dstrect = sdl2.SDL_Rect(dst_x, dst_y, render_w, render_h)
        
        flip = sdl2.SDL_FLIP_NONE if self.facing_right else sdl2.SDL_FLIP_HORIZONTAL

        # Vẽ nhân vật
        if texture:
            sdl2.SDL_RenderCopyEx(renderer, texture, srcrect, dstrect, 0, None, flip)
        
        # Vẽ hiệu ứng attack
        if self.is_attacking and not getattr(self, "is_using_skill", False):
            # Hiển thị hiệu ứng chém Melee
            mele_tex, mele_srcrect = AssetManager.get_anim_info("mele", self.mele_anim_frame)
            if mele_tex:
                # Đổi màu tia chém theo Role: Knight (Cyan), Princess (Pink)
                if self.role == "princess":
                    sdl2.SDL_SetTextureColorMod(mele_tex, 255, 100, 200) # Pink
                else:
                    sdl2.SDL_SetTextureColorMod(mele_tex, 0, 255, 255)   # Cyan
                    
                # Vị trí vẽ dựa trên attack_rect đã tính ở update
                m_draw_x = int(self.attack_rect.x - camera.x)
                m_draw_y = int(self.attack_rect.y - camera.y)
                
                m_dstrect = sdl2.SDL_Rect(m_draw_x, m_draw_y, 62, 32) 
                m_dstrect.y -= 12

                if not self.facing_right:
                    m_dstrect.x -= 0

                sdl2.SDL_RenderCopyEx(renderer, mele_tex, mele_srcrect, m_dstrect, 0, None, flip)

        # 2. Logic vẽ Mana Warning (Giữ nguyên)
        if self.mana_warning_timer > 0:
            offset_y = (self.mana_warning_duration - self.mana_warning_timer) / 20
            text_x = self.rect.x - camera.x
            text_y = self.rect.y - camera.y - 30 - offset_y
            
            if hasattr(self.game, 'hud'):
                self.game.hud._draw_text(
                    renderer, "Không đủ Mana!", text_x, text_y, (80, 180, 255)
                )
        
        # 3. Logic vẽ Speech Text (Giữ nguyên)
        if self.speech_timer > 0 and self.speech_text:
            offset_y = (self.mana_warning_duration - self.mana_warning_timer) / 20
            text_x = self.rect.x - camera.x
            text_y = self.rect.y - camera.y - 30 - offset_y

            if hasattr(self.game, 'hud'):
                self.game.hud._draw_text(
                    renderer, self.speech_text, text_x, text_y, (255, 255, 255)
                )

        # 4. Vẽ Hitbox Debug (Giữ nguyên)
        if self.debug_mode:
            # Hitbox nhân vật (xanh lá) - VẼ ĐÚNG TỌA ĐỘ VẬT LÝ
            hit_draw_x = int(self.rect.x - camera.x)
            hit_draw_y = int(self.rect.y - camera.y)
            hit_draw_w = int(self.rect.w)
            hit_draw_h = int(self.rect.h)
            hit_rect = sdl2.SDL_Rect(hit_draw_x, hit_draw_y, hit_draw_w, hit_draw_h)
            
            sdl2.SDL_SetRenderDrawColor(renderer, 0, 255, 0, 255)
            sdl2.SDL_RenderDrawRect(renderer, hit_rect)

            # Hitbox tấn công (đỏ)
            if self.is_attacking:
                atk_x = int(self.attack_rect.x - camera.x)
                atk_y = int(self.attack_rect.y - camera.y)
                atk_w = int(self.attack_rect.w)
                atk_h = int(self.attack_rect.h)
                
                atk_draw = sdl2.SDL_Rect(atk_x, atk_y, atk_w, atk_h)
                sdl2.SDL_SetRenderDrawColor(renderer, 255, 0, 0, 255)
                sdl2.SDL_RenderDrawRect(renderer, atk_draw)

    def show_speech(self, text, duration=None):
        self.speech_text = text
        self.speech_timer = duration if duration is not None else self.mana_warning_duration

    def collides_with(self, other):
        return sdl2.SDL_HasIntersection(self.rect, other.rect)

    def activate_cheat_mode(self):
        self.is_god_mode = True
        all_skills = ["dash", "double_jump", "skill_a", "teleport", "aoe"]
        self.progress["unlocked_skills"] = all_skills
        self.progress["double_jump"] = True
        
        self.has_double_jump = True
        self.can_double_jump = True
        self.hp = PLAYER_MAX_HP
        self.mana = MANA_MAX
        self.show_speech("GOD MODE & ALL SKILLS UNLOCKED!", 3.0)