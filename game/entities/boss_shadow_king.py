import sdl2
import math
import random

from game.entities.enemy import Enemy, EnemyFireball
from game.constants import GRAVITY, SCREEN_WIDTH, SCREEN_HEIGHT
from game.utils.assets import AssetManager

BOSS_QUOTES = {
    "hit_head": [
        "KHÔNG! Điểm (G) yếu của ta!", "Ngươi gan lắm!", "YAMETE ??!!!"
    ],
    "hit_body": ["Ta có khiên!!", "Ngươi quá yếu!", "U i i a a", "Ngươi nên nhắm vào đầu"],
    "slash_warn": ["TA SẼ XÉ XÁC NGƯƠI!"], 
    "fire_warn": ["HỎA CẦU BÓNG TỐI!"],     
    "lightning_warn": ["THIÊN LÔI PHẠT!"],
    "idle": ["Ngươi chỉ có thế thôi sao?"],
    "death": [
        "Bóng tối... không bao giờ tắt...", 
        "Ta nhất định sẽ trở lại!", 
    ],
    "transform": ["THẾ GIỚI NÀY... SẼ THUỘC VỀ TA!"]
}

class BossFireball(EnemyFireball):
    def __init__(self, game, x, y, vx, vy, damage):
        # Gọi init của lớp cha để giữ nguyên logic di chuyển/va chạm
        super().__init__(game, x, y, vx, vy, damage)

        # LƯU TRỮ VẬN TỐC ĐỂ DÙNG CHO HÀM RENDER
        self.vx = vx
        self.vy = vy
        
        # === CHỈNH SỬA SPRITE RIÊNG CHO BOSS ===
        self.anim_state = "boss_fireball" # Sử dụng key đã đăng ký ở Bước 1
        self.anim_frame = 0
        self.anim_timer = 0.0
        self.anim_speed = 0.05 # Lửa rồng nên cháy nhanh và mượt

    def update(self, delta_time, level):
        # Giữ nguyên logic di chuyển của EnemyFireball
        super().update(delta_time, level)
        
        # Thêm logic cập nhật animation frame
        self.anim_timer += delta_time
        if self.anim_timer >= self.anim_speed:
            self.anim_timer = 0
            self.anim_frame += 1
            # Loop qua 14 frames rồng lửa
            self.anim_frame %= AssetManager.ANIM_CONFIG[self.anim_state]["frames"]

    def render(self, renderer, camera):
        # Ghi đè hàm render để vẽ sprite mới
        if not self.alive: return
        
        # Lấy texture và srcrect từ AssetManager
        texture, srcrect = AssetManager.get_anim_info(self.anim_state, self.anim_frame)
        
        if texture:
            # Vị trí vẽ (DSTRECT)
            draw_x = int(self.rect.x - camera.x)
            draw_y = int(self.rect.y - camera.y)
            
            # Kích thước hiển thị (Nên to hơn hitbox một chút cho uy lực)
            scale = 2
            render_w = 64 * scale
            render_h = 64 * scale
            dstrect = sdl2.SDL_Rect(draw_x, draw_y, render_w, render_h)
            
            # Căn chỉnh để sprite nằm giữa hitbox va chạm
            dstrect.y -= (render_h - self.rect.h) // 2
            
            # Tính góc xoay dựa trên vận tốc (vx, vy) để đầu rồng hướng về phía trước
            angle_rad = math.atan2(self.vy, self.vx)
            angle_deg = math.degrees(angle_rad)
            
            # Vẽ sprite có xoay góc
            sdl2.SDL_RenderCopyEx(renderer, texture, srcrect, dstrect, angle_deg, None, sdl2.SDL_FLIP_NONE)

class BossShadowKing(Enemy):
    def __init__(self, game, x, y):
        # Khung bao quát: w=120, h=310
        super().__init__(game, int(x), int(y), w=120, h=310, hp=300, damage=1)
        self.z_index = 5
        self.color = (40, 0, 60, 255)

        self.max_hp = 100
        self.hp = self.max_hp
        self.spawned_milestones = {
            "75": False,
            "50": False,
            "25": False
        }
        
        self.fixed_x = float(x)
        self.fixed_y = float(y)
        self.is_flying = True 
        
        self.timer = 0.0 
        
        # Hitbox bộ phận
        self.body_w, self.body_h = 120, 240
        self.head_w, self.head_h = 80, 80
        self.head_rect = sdl2.SDL_Rect(0, 0, self.head_w, self.head_h)
        
        # Độ nhô (Idle = 0 theo yêu cầu)
        self.idle_jut = 0   
        self.attack_jut = 45 
        
        # Cơ chế sét (HP < 50%)
        self.lightning_x_positions = []
        self.lightning_warning_timer = 0.0
        self.is_lightning_active = False
        self.lightning_width = 50
        self.lightning_gap = 120 # Khoảng cách an toàn rộng rãi hơn

        self.state = "idle"
        self.idle_timer = 3.5
        self.action_delay = 0.0       
        self.pending_action = None    
        self.slash_warning_visual = 0.0
        self.is_slashing = False
        self.slash_y_target = 0

        self.death_timer = 0.0
        self.death_alpha = 255
        self.death_vel_x = 0.0
        self.death_vel_y = 0.0
        self.particles = []

        # === TRẠNG THÁI BIẾN HÌNH ===
        self.is_transforming = False
        self.has_transformed = False
        self.transform_timer = 0.0

        # === ANIMATION SPRITE ===
        self.sprite_frame_w = 128
        self.sprite_frame_h = 128
        
        self.anim_state = "boss_idle"      
        self.anim_frame = 0
        self.anim_timer = 0.0

        self.head_anim_frame = 0
        self.head_anim_timer = 0.0
        self.head_anim_speed = 0.12

        self.anim_speeds = {
            "boss_idle":     0.8,  
            "boss_attack1":  0.33,  
            "boss_attack2":  0.7,  
            "boss_attack3":  0.14,

            "boss_transform": 3/7,

            "boss_idle_p2":     0.8,
            "boss_attack1_p2":  0.2,
            "boss_attack2_p2":  0.21,
            "boss_attack3_p2":  0.12,

            "boss_death":    0.45,   
        }           
        
        self.direction = 1                 
        self.attack_anim_timer = 0.0
        self.attack_anim_duration = 1.4     

    def update(self, delta_time, level):
        if self.is_dead_body:
            self.anim_state = "boss_death"
            self.death_timer -= delta_time
            self._update_anim_frame(delta_time)
            
            # Vẫn fade, rơi, particle khi là xác chết
            self.death_alpha = int(255 * (self.death_timer / 4.0))
            self.fixed_x += self.death_vel_x * delta_time * 60
            
            for p in self.particles[:]:
                p['x'] += p['vx'] * delta_time * 60
                p['y'] += p['vy'] * delta_time * 60
                p['vy'] += GRAVITY * delta_time * 60 * 0.3
                p['life'] -= delta_time
                if p['life'] <= 0:
                    self.particles.remove(p)
            
            if self.speech_timer > 0:
                self.speech_timer -= delta_time
            
            if self.death_timer <= 0:
                if self in level.entities:
                    level.entities.remove(self)
            return

        self.timer += delta_time
        player = self.game.player
        
        # --- LOGIC BIẾN HÌNH ---
        # 1. Bắt đầu biến hình
        if self.hp <= (self.max_hp * 0.5) and not self.has_transformed and not self.is_transforming:
            self.is_transforming = True
            self.transform_timer = 3.0 # Đứng gồng 3 giây
            
            # Hủy bỏ các đòn đánh đang dở dang
            self.action_delay = 0 
            self.pending_action = None
            self.slash_warning_visual = 0
            self.is_lightning_active = False
            
            self.show_speech("transform", duration=3.0)
            
        # 2. Đang trong quá trình biến hình
        if self.is_transforming:
            self.transform_timer -= delta_time

            self.anim_state = "boss_transform"
            self._update_anim_frame(delta_time)
            
            if self.speech_timer > 0:
                self.speech_timer -= delta_time

            # Kết thúc biến hình
            if self.transform_timer <= 0:
                self.is_transforming = False
                self.has_transformed = True
                
                # Gọi rơi máu/mana ở mốc 50%
                self.spawn_mid_battle_items()
                self.spawned_milestones["50"] = True
                self.start_idle() # Khởi động lại AI
                
            # Đang biến hình thì DỪNG CẬP NHẬT AI và HÀNH ĐỘNG KHÁC
            return 
            
        # --- KẾT THÚC LOGIC BIẾN HÌNH ---
        
        # Cập nhật sprite bình thường
        self._update_anim_frame(delta_time)
        if player:
            self.direction = 1 if player.rect.x > self.fixed_x else -1
        
        # --- Tùy chỉnh suffix (Phase 1 / Phase 2) ---
        suffix = "_p2" if self.has_transformed else ""

        # --- Chọn animation state (ưu tiên theo thứ tự) ---
        if self.is_dead_body:
            self.anim_state = "boss_death"
        elif self.action_delay > 0 or self.slash_warning_visual > 0 or self.is_lightning_active:
            # GỒNG CHIÊU → chuyển sprite attack NGAY
            if self.pending_action == "slash" or self.slash_warning_visual > 0:
                self.anim_state = f"boss_attack1{suffix}"
            elif self.pending_action == "lightning" or self.is_lightning_active:
                self.anim_state = f"boss_attack2{suffix}"
            elif self.pending_action == "fire":
                self.anim_state = f"boss_attack3{suffix}"
        else:
            self.anim_state = f"boss_idle{suffix}"

        # Giảm timer animation attack
        if self.attack_anim_timer > 0:
            self.attack_anim_timer -= delta_time
            if self.attack_anim_timer <= 0 and self.anim_state.startswith("boss_attack"):
                self.anim_state = f"boss_idle{suffix}"

        if self.anim_state in ["boss_idle", "boss_idle_p2"]:
            self.head_anim_timer += delta_time
            if self.head_anim_timer >= self.head_anim_speed:
                self.head_anim_timer -= self.head_anim_speed
                self.head_anim_frame += 1
                head_config = AssetManager.ANIM_CONFIG.get("boss_head", {})
                if head_config and "frames" in head_config:
                    self.head_anim_frame %= head_config["frames"]

        # Logic AI bình thường
        self._update_ai_state(player, level)
        if self.speech_timer > 0:
            self.speech_timer -= delta_time

    def show_speech(self, category, duration=2.0):
        # Danh sách các câu thoại quan trọng (không được ghi đè)
        important_states = (self.action_delay > 0 or 
                            self.slash_warning_visual > 0 or 
                            self.is_lightning_active or 
                            self.is_dead_body or
                            self.is_transforming)
        
        # Nếu đang gồng chiêu hoặc đã chết mà lời thoại định hiển thị là "bị đánh" thì BỎ QUA
        if important_states and category in ["hit_head", "hit_body"]:
            return

        # Nếu không bị chặn, tiến hành lấy text ngẫu nhiên và hiển thị
        if category in BOSS_QUOTES:
            self.speech_text = random.choice(BOSS_QUOTES[category])
            self.speech_timer = duration

    def _update_anim_frame(self, delta_time):
        current_speed = self.anim_speeds.get(self.anim_state, 0.14)

        self.anim_timer += delta_time
        if self.anim_timer >= current_speed:
            self.anim_timer -= current_speed
            self.anim_frame += 1

    def _update_ai_state(self, player, level):
        # Cộng dồn thời gian
        self.timer += 1/60.0
        
        is_resting_or_attacking = (
            self.state == "idle" or 
            self.action_delay > 0 or 
            self.slash_warning_visual > 0 or 
            self.is_lightning_active
        )
        current_jut = self.attack_jut if is_resting_or_attacking else self.idle_jut
        
        self.head_rect.x = int(self.fixed_x + (self.body_w - self.head_w)//2 - current_jut)
        self.head_rect.y = int(self.fixed_y - self.head_h + 5)
        
        # Cập nhật hitbox tổng
        self.rect.x = min(int(self.fixed_x), self.head_rect.x)
        self.rect.y = self.head_rect.y
        self.rect.w = self.body_w + current_jut
        self.rect.h = self.body_h + self.head_h

        # 2. Logic Chiêu Sét
        if self.lightning_warning_timer > 0:
            self.lightning_warning_timer -= 1/60.0
            if self.lightning_warning_timer <= 0:
                if not self.is_lightning_active:
                    self.is_lightning_active = True
                    self.lightning_warning_timer = 0.6 # Sét tồn tại 0.6s
                    # Check sát thương sét
                    px_center = player.rect.x + player.rect.w//2
                    for lx in self.lightning_x_positions:
                        if abs(px_center - lx) < self.lightning_width//2:
                            player.take_damage(2)
                else:
                    self.is_lightning_active = False
                    self.start_idle()
            pass

        # 3. Gồng chiêu (Action Delay)
        if self.action_delay > 0:
            self.action_delay -= 1/60.0
            if self.action_delay <= 0:
                if self.pending_action == "slash": self.start_slash_logic(player)
                elif self.pending_action == "fire": self.execute_fire_3_tia(player, level)
                elif self.pending_action == "lightning": self.start_lightning_execution()
            return

        # Chiêu chém ngang
        if self.slash_warning_visual > 0:
            self.slash_warning_visual -= 1/60.0
            if 0 < self.slash_warning_visual < 0.2:
                self.is_slashing = True
                if abs((player.rect.y + player.rect.h//2) - self.slash_y_target) < 30:
                    player.take_damage(1)
            else: self.is_slashing = False
            if self.slash_warning_visual <= 0: self.start_idle()
            return

        if self.state == "idle":
            self.idle_timer -= 1/60.0
            if self.idle_timer <= 0: self.decide_attack(player)

    def take_damage(self, amount, knockback_dir=0):
        # Đang biến hình thì không nhận damage (miễn nhiễm)
        if self.is_transforming:
            return
            
        player = self.game.player
        level = self.game.states["playing"].level
        is_headshot = False

        # Kiểm tra đạn bắn trúng đầu
        for entity in level.entities:
            if entity.__class__.__name__ == "Projectile" and entity.alive:
                if sdl2.SDL_HasIntersection(entity.rect, self.head_rect):
                    is_headshot = True
                    entity.die()
                    break

        # Kiểm tra chém cận chiến trúng đầu
        if not is_headshot and player.is_attacking:
            if sdl2.SDL_HasIntersection(player.attack_rect, self.head_rect):
                is_headshot = True

        # Kiểm tra mốc 75%
        if not self.spawned_milestones["75"] and self.hp <= (self.max_hp * 0.75):
            self.spawn_mid_battle_items()
            self.spawned_milestones["75"] = True
            
        # LƯU Ý: Mốc 50% đã được chuyển vào hàm Update để chạy đồng bộ với biến hình
            
        # Kiểm tra mốc 25%
        if not self.spawned_milestones["25"] and self.hp <= (self.max_hp * 0.25):
            self.spawn_mid_battle_items()
            self.spawned_milestones["25"] = True

        if is_headshot:
            super().take_damage(amount, knockback_dir=0)
            self.show_speech("hit_head")
            self.color = (255, 0, 0, 255)
        else:
            self.show_speech("hit_body")
            self.color = (60, 20, 80, 255)

    def die(self):
        if not self.alive:
            return
        
        self.alive = False
        self.is_dead_body = True
        self.death_timer = 4.5  # hiệu ứng kéo dài 3 giây
        
        # Bật sprite death ngay lập tức
        self.anim_state = "boss_death"
        self.anim_frame = 0             # reset frame chết
        
        # Hiệu ứng bay lên + rung
        self.death_vel_x = random.uniform(-1.5, 1.5)
        self.death_vel_y = -2.5
        
        # Lời thoại trăn trối
        self.speech_text = random.choice(BOSS_QUOTES["death"])
        self.speech_timer = 4.0  # nói lâu hơn bình thường
        
        # Tạo particle nổ ra (màu tím/đen)
        for _ in range(40):
            px = self.fixed_x + self.body_w // 2 + random.uniform(-60, 60)
            py = self.fixed_y + self.body_h // 2 + random.uniform(-150, 150)
            vx = random.uniform(-3, 3)
            vy = random.uniform(-5, -1)  # bay lên trên chủ yếu
            lifetime = random.uniform(1.0, 2.5)
            self.particles.append({
                'x': px, 'y': py,
                'vx': vx, 'vy': vy,
                'life': lifetime, 'max_life': lifetime,
                'color': (random.randint(100, 180), 0, random.randint(150, 255), 200)
            })
        
        self.game.trigger_slowmo(duration=3.5, strength=0.3)
        self.spawn_exit_platform()

    def decide_attack(self, player):
        attacks = ["slash", "fire"]
        if self.hp <= 150:
            attacks.append("lightning")
        
        choice = random.choice(attacks)
        
        if choice == "slash":
            self.show_speech("slash_warn")
            self.pending_action = "slash"
            self.action_delay = 2.0          # gồng 2 giây
            
        elif choice == "fire":
            self.show_speech("fire_warn")
            self.pending_action = "fire"
            self.action_delay = 1.2
            
        else:  # lightning
            self.show_speech("lightning_warn")
            self.pending_action = "lightning"
            self.action_delay = 1.5
            px = player.rect.x + player.rect.w//2
            self.lightning_x_positions = [px + (i - 2) * self.lightning_gap for i in range(5)]

    def start_lightning_execution(self):
        self.state = "attacking"
        self.lightning_warning_timer = 1.5

    def start_slash_logic(self, player):
        self.state = "attacking"
        self.slash_warning_visual = 1.0
        self.slash_y_target = player.rect.y + (player.rect.h // 2)

    def execute_fire_3_tia(self, player, level):
        self.state = "attacking"
        cx, cy = self.head_rect.x + self.head_w//2, self.head_rect.y + self.head_h//2
        dx, dy = (player.rect.x + player.rect.w//2) - cx, (player.rect.y + player.rect.h//2) - cy
        base_angle = math.atan2(dy, dx)
        for spread in [-0.3, 0, 0.3]: 
            vx, vy = math.cos(base_angle + spread), math.sin(base_angle + spread)

            # Tạo BossFireball thay vì EnemyFireball
            fb = BossFireball(self.game, cx, cy, vx, vy, 1)

            # Chuyển sprite cầu lửa sang p2 nếu Boss dưới 50% máu
            if self.has_transformed:
                fb.anim_state = "boss_fireball_p2"
                fb.speed = 5.5 # Có thể buff thêm speed lửa ở Phase 2
            else:
                fb.speed = 4.5
                
            level.entities.append(fb)
        self.start_idle()

    def start_idle(self):
        """Sau khi ra chiêu, nghỉ 5 giây + nhô đầu ra"""
        self.state = "idle"
        self.show_speech("idle")
        self.idle_timer = 5.0               
        self.is_slashing = False
        self.pending_action = None

    def spawn_mid_battle_items(self):
        """Hàm spawn Heart và Mana khi Boss còn 50% máu"""
        # ĐIỀN TỌA ĐỘ X, Y TẠI ĐÂY
        item_x = 450 
        item_y = random.randint(200, 350)
        
        level = self.game.states["playing"].level
        try:
            from game.entities.collectible import Heart, ManaBottle
            level.entities.append(Heart(self.game, item_x, item_y))
            level.entities.append(ManaBottle(self.game, item_x + 50, item_y)) # Lệch x một chút để không chồng nhau
        except ImportError:
            pass

    def spawn_exit_platform(self):
        """Triệu hồi bục nhảy di động sau khi boss bị hạ gục"""
        # Lấy vị trí trung tâm của Boss để spawn bục
        p_x = 1100
        p_y = 350
        level = self.game.states["playing"].level
        
        try:
            from game.objects.platform import MovingPlatform
            # Tạo một bục di chuyển dọc (is_horizontal=False) để đưa người chơi lên cao
            exit_plat = MovingPlatform(
                self.game, 
                x=p_x, 
                y=p_y, 
                w=120, 
                h=25, 
                speed=1.5, 
                distance=300, 
                is_horizontal=False
            )
            level.platforms.append(exit_plat)
        except ImportError:
            pass

    def render(self, renderer, camera):
        if not self.alive and not self.is_dead_body:
            return
        alpha = self.death_alpha if self.is_dead_body else 255
        
        # 1. Render Sét (Nếu có)
        if self.lightning_warning_timer > 0 or self.is_lightning_active:
            sdl2.SDL_SetRenderDrawBlendMode(renderer, sdl2.SDL_BLENDMODE_BLEND)
            for lx in self.lightning_x_positions:
                ldx = int(lx - camera.x - self.lightning_width//2)
                if self.is_lightning_active:
                    sdl2.SDL_SetRenderDrawColor(renderer, 150, 220, 255, 200) # Sét sáng
                else:
                    sdl2.SDL_SetRenderDrawColor(renderer, 255, 255, 0, 80) # Vàng mờ cảnh báo
                sdl2.SDL_RenderFillRect(renderer, sdl2.SDL_Rect(ldx, 0, self.lightning_width, SCREEN_HEIGHT))
            sdl2.SDL_SetRenderDrawBlendMode(renderer, sdl2.SDL_BLENDMODE_NONE)

        # === 2. AURA PHASE 2 (CHẬM VÀ VÁT GÓC MỀM HƠN) ===
        if self.has_transformed and not self.is_dead_body:
            sdl2.SDL_SetRenderDrawBlendMode(renderer, sdl2.SDL_BLENDMODE_BLEND)
            
            # Nhấp nháy chậm hơn (nhân 2.5 thay vì 5)
            aura_size = int(12 * math.sin(self.timer * 1.5)) 
            
            base_x = int(self.fixed_x - camera.x - aura_size)
            base_y = int(self.fixed_y - camera.y - aura_size)
            base_w = self.body_w + aura_size * 2
            base_h = self.body_h + aura_size * 2
            
            # Bán kính bo góc ảo
            r = 25 
            
            # Vẽ nhiều lớp hình chữ nhật chữ thập mờ dần để tạo cảm giác bo tròn phát sáng
            # Các thông số: (Alpha, Độ mở rộng thêm)
            layers = [(20, 15), (40, 5), (60, 0)]
            
            for a_layer, expand in layers:
                w = base_w + expand + 10
                h = base_h + expand
                if w <= 0 or h <= 0: continue
                
                x = base_x - expand//2 -30
                y = base_y - expand//2 -20
                
                sdl2.SDL_SetRenderDrawColor(renderer, 138, 43, 226, a_layer)
                
                # Rect dọc (bỏ qua 4 góc vát)
                rect_v = sdl2.SDL_Rect(x + r, y, w - 2*r, h)
                # Rect ngang (bỏ qua 4 góc vát)
                rect_h = sdl2.SDL_Rect(x, y + r, w, h - 2*r)
                
                sdl2.SDL_RenderFillRect(renderer, rect_v)
                sdl2.SDL_RenderFillRect(renderer, rect_h)
                
            sdl2.SDL_SetRenderDrawBlendMode(renderer, sdl2.SDL_BLENDMODE_NONE)

        # 3. Render sprite boss 128x128
        texture, srcrect = AssetManager.get_anim_info(self.anim_state, self.anim_frame)

        if texture:
            sprite_w = 128
            sprite_h = 128
            scale = 2.75

            draw_w = int(sprite_w * scale)   # = 384
            draw_h = int(sprite_h * scale)   # = 384

            offset_x = (sprite_w - self.body_w) // 2 + 150       
            offset_y = 185                                      

            if 'attack' in self.anim_state:
                jut_offset = self.attack_jut if self.direction > 0 else -self.attack_jut
                offset_x += jut_offset

            draw_x = int(self.fixed_x - camera.x - offset_x)
            draw_y = int(self.fixed_y - camera.y - offset_y)
            
            # Hiệu ứng rung bần bật khi đang gồng biến hình
            if self.is_transforming:
                draw_x += random.randint(-4, 4)
                draw_y += random.randint(-4, 4)

            dstrect = sdl2.SDL_Rect(draw_x, draw_y, draw_w, draw_h)
            flip = sdl2.SDL_FLIP_HORIZONTAL if self.direction < 0 else sdl2.SDL_FLIP_NONE

            sdl2.SDL_SetTextureAlphaMod(texture, alpha)
            sdl2.SDL_RenderCopyEx(renderer, texture, srcrect, dstrect, 0, None, flip)
            sdl2.SDL_SetTextureAlphaMod(texture, 255)

        else:
            bdx = int(self.fixed_x - camera.x)
            bdy = int(self.fixed_y - camera.y)
            sdl2.SDL_SetRenderDrawColor(renderer, *self.color[:3], alpha)
            sdl2.SDL_RenderFillRect(renderer, sdl2.SDL_Rect(bdx, bdy, self.body_w, self.body_h))
            
            hdx = int(self.head_rect.x - camera.x)
            hdy = int(self.head_rect.y - camera.y)
            sdl2.SDL_SetRenderDrawColor(renderer, 255, 0, 255, alpha)
            sdl2.SDL_RenderFillRect(renderer, sdl2.SDL_Rect(hdx, hdy, self.head_w, self.head_h))
        
        # Render HEAD (chỉ khi idle và còn sống, ẨN khi đang gồng biến hình)
        if self.anim_state in ["boss_idle", "boss_idle_p2"] and not self.is_dead_body and not self.is_transforming:
            head_texture, head_srcrect = AssetManager.get_anim_info("boss_head", self.head_anim_frame)
            
            if head_texture:
                head_sprite_w = head_sprite_h = 80   
                head_scale = 1.5                     
                head_draw_w = int(head_sprite_w * head_scale)
                head_draw_h = int(head_sprite_h * head_scale)

                head_offset_x = 15                   
                head_offset_y = -90                  

                if self.direction < 0:
                    head_offset_x = -head_offset_x - (head_draw_w - self.head_w)

                head_x = int(self.fixed_x - camera.x + head_offset_x)
                head_y = int(self.fixed_y - camera.y + head_offset_y)

                head_dst = sdl2.SDL_Rect(head_x, head_y, head_draw_w, head_draw_h)
                head_flip = sdl2.SDL_FLIP_HORIZONTAL if self.direction < 0 else sdl2.SDL_FLIP_NONE

                sdl2.SDL_SetTextureAlphaMod(head_texture, alpha)
                sdl2.SDL_RenderCopyEx(renderer, head_texture, head_srcrect, head_dst, 0, None, head_flip)
                sdl2.SDL_SetTextureAlphaMod(head_texture, 255)
        
        # 5. Thanh máu (ẩn khi chết)
        if not self.is_dead_body:
            bar_w, bar_h, bar_x, bar_y = 400, 20, (SCREEN_WIDTH - 400) // 2, 30
            sdl2.SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255)
            sdl2.SDL_RenderDrawRect(renderer, sdl2.SDL_Rect(bar_x - 3, bar_y - 3, bar_w + 6, bar_h + 6))
            sdl2.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 200)
            sdl2.SDL_RenderFillRect(renderer, sdl2.SDL_Rect(bar_x, bar_y, bar_w, bar_h))
            health_ratio = max(0, self.hp / 300)
            sdl2.SDL_SetRenderDrawColor(renderer, 255, 0, 0, 255)
            sdl2.SDL_RenderFillRect(renderer, sdl2.SDL_Rect(bar_x, bar_y, int(bar_w * health_ratio), bar_h))

        # Hiệu ứng Slash
        if self.slash_warning_visual > 0:
            alpha = 100 if not self.is_slashing else 255
            sdl2.SDL_SetRenderDrawBlendMode(renderer, sdl2.SDL_BLENDMODE_BLEND)
            sdl2.SDL_SetRenderDrawColor(renderer, 255, 0, 0, alpha)
            sdl2.SDL_RenderFillRect(renderer, sdl2.SDL_Rect(0, int(self.slash_y_target - camera.y - 30), SCREEN_WIDTH, 60))
            sdl2.SDL_SetRenderDrawBlendMode(renderer, sdl2.SDL_BLENDMODE_NONE)

        # Thoại
        if self.speech_timer > 0 and self.speech_text:
            try:
                self.game.hud._draw_text(
                    renderer, self.speech_text,
                    int(self.fixed_x - camera.x + self.body_w // 2 - 100),
                    int(self.fixed_y - camera.y - 120),
                    (255, 255, 255)
                )
            except:
                pass