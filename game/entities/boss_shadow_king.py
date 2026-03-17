import sdl2
import math
import random

from game.entities.enemy import Enemy, EnemyFireball
from game.constants import GRAVITY, SCREEN_WIDTH, SCREEN_HEIGHT
from game.utils.assets import AssetManager

BOSS_QUOTES = {
    "detected": ["Ngươi dám bước vào lãnh địa của ta?", "Hahaha..."],
    "hit_head": ["KHÔNG! Điểm yếu của ta!", "Ngươi gan lắm!"],
    "hit_body": ["Vô ích thôi!", "Giáp ta quá dày!"],
    "slash_warn": ["TA SE XE NAT NGUOI! (Gồng 2s)"], 
    "fire_warn": ["HOA NGUC TROI DAY!"],     
    "lightning_warn": ["THIEN LOI PHAT!"],
    "idle": ["Ngươi chi co the thoi sao?"],
    "death": [
        "Bóng tối... không bao giờ tắt...", 
        "Nhà vua sẽ trở lại!", 
        "Ngươi... chỉ là kẻ may mắn..."
    ]
}

class BossShadowKing(Enemy):
    def __init__(self, game, x, y):
        # Khung bao quát: w=120, h=310
        super().__init__(game, int(x), int(y), w=120, h=310, hp=100, damage=1)
        self.z_index = 5
        self.color = (40, 0, 60, 255)
        
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
            "boss_idle":     0.8,   # chậm hơn một chút khi đứng yên
            "boss_attack1":  0.2,   # slash nhanh hơn
            "boss_attack2":  0.21,   # lightning rất nhanh
            "boss_attack3":  0.12,
            "boss_hurt":     0.2,   # hurt chậm để nhấn mạnh đau
            "boss_death":    0.45    # death chậm để fade đẹp
        }           
        
        self.direction = 1                 
        self.attack_anim_timer = 0.0
        self.attack_anim_duration = 1.4     

    def update(self, delta_time, level):
        if self.is_dead_body:
            self.anim_state = "boss_death"
            self.death_timer -= delta_time
            self._update_anim_frame(delta_time)
            
            # Vẫn fade, rơi, particle khi là xác chết (giữ nguyên code cũ)
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

        # Logic bình thường khi còn sống
        self._update_anim_frame(delta_time)
        self.timer += delta_time
        
        player = self.game.states["playing"].player if "playing" in self.game.states else None
        if player:
            # Cập nhật hướng quay mặt
            self.direction = 1 if player.rect.x > self.fixed_x else -1

        # --- Chọn animation state (ưu tiên theo thứ tự) ---
        if self.is_dead_body:
            self.anim_state = "boss_death"
        elif self.action_delay > 0 or self.slash_warning_visual > 0 or self.is_lightning_active:
            # GỒNG CHIÊU → chuyển sprite attack NGAY
            if self.pending_action == "slash" or self.slash_warning_visual > 0:
                self.anim_state = "boss_attack1"
            elif self.pending_action == "lightning" or self.is_lightning_active:
                self.anim_state = "boss_attack2"
            elif self.pending_action == "fire":
                self.anim_state = "boss_attack3"
        elif self.hp < 90 and random.random() < 0.03:
            self.anim_state = "boss_hurt"
        else:
            self.anim_state = "boss_idle"

        # Giảm timer animation attack
        if self.attack_anim_timer > 0:
            self.attack_anim_timer -= delta_time
            if self.attack_anim_timer <= 0 and self.anim_state.startswith("boss_attack"):
                self.anim_state = "boss_idle"

        if self.anim_state == "boss_idle":
            self.head_anim_timer += delta_time
            if self.head_anim_timer >= self.head_anim_speed:
                self.head_anim_timer -= self.head_anim_speed
                self.head_anim_frame += 1
                head_config = AssetManager.ANIM_CONFIG.get("boss_head_idle", {})
                if head_config and "frames" in head_config:
                    self.head_anim_frame %= head_config["frames"]

        # Logic bình thường khi còn sống
        self._update_ai_state(self.game.states["playing"].player, level)
        if self.speech_timer > 0:
            self.speech_timer -= delta_time

    def _update_anim_frame(self, delta_time):
        current_speed = self.anim_speeds.get(self.anim_state, 0.14)

        self.anim_timer += delta_time
        if self.anim_timer >= current_speed:
            self.anim_timer -= current_speed
            self.anim_frame += 1

    def _update_ai_state(self, player, level):
        # Cộng dồn thời gian (Đã hết lỗi nhờ self.timer ở init)
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
        player = self.game.states["playing"].player
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
            fb = EnemyFireball(self.game, cx, cy, vx, vy, 1)
            fb.speed = 4.5
            level.entities.append(fb)
        self.start_idle()

    def start_idle(self):
        """Sau khi ra chiêu, nghỉ 5 giây + nhô đầu ra"""
        self.state = "idle"
        self.idle_timer = 5.0               
        self.is_slashing = False
        self.pending_action = None

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

        # 2. Render sprite boss 128x128
        texture, srcrect = AssetManager.get_anim_info(self.anim_state, self.anim_frame)

        if texture:
            sprite_w = 128
            sprite_h = 128
            scale = 2.75

            draw_w = int(sprite_w * scale)   # = 384
            draw_h = int(sprite_h * scale)   # = 384

            # Offset chính xác cho boss lớn
            offset_x = (sprite_w - self.body_w) // 2 + 150       # căn giữa + điều chỉnh nhỏ
            offset_y = 185                      # sprite nằm ở phần đầu (thử nghiệm giá trị này)

            # Dịch chuyển khi attack (jut)
            if 'attack' in self.anim_state:
                jut_offset = self.attack_jut if self.direction > 0 else -self.attack_jut
                offset_x += jut_offset

            draw_x = int(self.fixed_x - camera.x - offset_x)
            draw_y = int(self.fixed_y - camera.y - offset_y)

            dstrect = sdl2.SDL_Rect(draw_x, draw_y, draw_w, draw_h)

            flip = sdl2.SDL_FLIP_HORIZONTAL if self.direction < 0 else sdl2.SDL_FLIP_NONE

            sdl2.SDL_SetTextureAlphaMod(texture, alpha)
            sdl2.SDL_RenderCopyEx(renderer, texture, srcrect, dstrect, 0, None, flip)
            sdl2.SDL_SetTextureAlphaMod(texture, 255)

        else:
            # Fallback (nếu sprite chưa load)
            bdx = int(self.fixed_x - camera.x)
            bdy = int(self.fixed_y - camera.y)
            sdl2.SDL_SetRenderDrawColor(renderer, *self.color[:3], alpha)
            sdl2.SDL_RenderFillRect(renderer, sdl2.SDL_Rect(bdx, bdy, self.body_w, self.body_h))
            
            hdx = int(self.head_rect.x - camera.x)
            hdy = int(self.head_rect.y - camera.y)
            sdl2.SDL_SetRenderDrawColor(renderer, 255, 0, 255, alpha)
            sdl2.SDL_RenderFillRect(renderer, sdl2.SDL_Rect(hdx, hdy, self.head_w, self.head_h))
        
        # Render HEAD (chỉ khi idle và còn sống)
        if self.anim_state == "boss_idle" and not self.is_dead_body:
            head_texture, head_srcrect = AssetManager.get_anim_info("boss_head", self.head_anim_frame)
            
            if head_texture:
                head_sprite_w = head_sprite_h = 80   # kích thước gốc của head sprite
                head_scale = 1.5                     # có thể chỉnh khác body
                head_draw_w = int(head_sprite_w * head_scale)
                head_draw_h = int(head_sprite_h * head_scale)

                # Offset để head nằm đúng vị trí trên body (cần tune tay)
                head_offset_x = 15                   # dịch ngang
                head_offset_y = -90                  # dịch lên trên (âm = lên)

                # Flip khi hướng trái
                if self.direction < 0:
                    head_offset_x = -head_offset_x - (head_draw_w - self.head_w)

                head_x = int(self.fixed_x - camera.x + head_offset_x)
                head_y = int(self.fixed_y - camera.y + head_offset_y)

                head_dst = sdl2.SDL_Rect(head_x, head_y, head_draw_w, head_draw_h)
                head_flip = sdl2.SDL_FLIP_HORIZONTAL if self.direction < 0 else sdl2.SDL_FLIP_NONE

                sdl2.SDL_SetTextureAlphaMod(head_texture, alpha)
                sdl2.SDL_RenderCopyEx(renderer, head_texture, head_srcrect, head_dst, 0, None, head_flip)
                sdl2.SDL_SetTextureAlphaMod(head_texture, 255)

        # # === DEBUG HITBOX (HIỆN RÕ ĐỂ DỄ CHỈNH) ===
        # # Main hitbox (xanh lá - toàn bộ thân)
        # sdl2.SDL_SetRenderDrawColor(renderer, 0, 255, 0, 180)   # xanh lá, hơi trong
        # main_rect = sdl2.SDL_Rect(
        #     int(self.rect.x - camera.x),
        #     int(self.rect.y - camera.y),
        #     self.rect.w,
        #     self.rect.h
        # )
        # sdl2.SDL_RenderDrawRect(renderer, main_rect)

        # # Head hitbox (đỏ - điểm yếu)
        # sdl2.SDL_SetRenderDrawColor(renderer, 255, 0, 0, 255)   # đỏ đậm
        # head_screen = sdl2.SDL_Rect(
        #     int(self.head_rect.x - camera.x),
        #     int(self.head_rect.y - camera.y),
        #     self.head_w,
        #     self.head_h
        # )
        # sdl2.SDL_RenderDrawRect(renderer, head_screen)
        # sdl2.SDL_RenderDrawRect(renderer, head_screen)

        # 3. Render particle khi chết
        for p in self.particles:
            px = int(p['x'] - camera.x)
            py = int(p['y'] - camera.y)
            size = int(6 * (p['life'] / p['max_life'])) + 2  # nhỏ dần
            sdl2.SDL_SetRenderDrawColor(renderer, *p['color'][:3], int(p['color'][3] * (p['life'] / p['max_life'])))
            sdl2.SDL_RenderFillRect(renderer, sdl2.SDL_Rect(px, py, size, size))
        
        # 4. Thanh máu (ẩn khi chết)
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