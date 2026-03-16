import sdl2
import math
import random

from game.entities.enemy import Enemy, EnemyFireball
from game.constants import SCREEN_WIDTH, SCREEN_HEIGHT

BOSS_QUOTES = {
    "detected": ["Ngươi dám bước vào lãnh địa của ta?", "Hahaha..."],
    "hit_head": ["KHÔNG! Điểm yếu của ta!", "Ngươi gan lắm!"],
    "hit_body": ["Vô ích thôi!", "Giáp ta quá dày!"],
    "slash_warn": ["TA SE XE NAT NGUOI! (Gồng 2s)"], 
    "fire_warn": ["HOA NGUC TROI DAY!"],     
    "lightning_warn": ["THIEN LOI PHAT!"],
    "idle": ["Ngươi chi co the thoi sao?"]
}

class BossShadowKing(Enemy):
    def __init__(self, game, x, y):
        # Khung bao quát: w=120, h=310
        super().__init__(game, int(x), int(y), w=120, h=310, hp=300, damage=1)
        self.z_index = 5
        self.color = (40, 0, 60, 255)
        
        self.fixed_x = float(x)
        self.fixed_y = float(y)
        self.is_flying = True 
        
        # --- FIX LỖI: KHAI BÁO TIMER ---
        self.timer = 0.0 
        
        # Hitbox bộ phận
        self.body_w, self.body_h = 120, 240
        self.head_w, self.head_h = 80, 70
        self.head_rect = sdl2.SDL_Rect(0, 0, self.head_w, self.head_h)
        
        # Độ nhô (Idle = 0 theo yêu cầu)
        self.idle_jut = 0   
        self.attack_jut = 45 
        
        # Cơ chế sét (HP < 50%)
        self.lightning_x_positions = []
        self.lightning_warning_timer = 0.0
        self.is_lightning_active = False
        self.lightning_width = 50
        self.lightning_gap = 170 # Khoảng cách an toàn rộng rãi hơn

        self.state = "idle"
        self.idle_timer = 3.5
        self.action_delay = 0.0       
        self.pending_action = None    
        self.slash_warning_visual = 0.0
        self.is_slashing = False
        self.slash_y_target = 0

    def update(self, delta_time, level):
        self._update_ai_state(self.game.states["playing"].player, level)
        if self.speech_timer > 0:
            self.speech_timer -= delta_time

    def _update_ai_state(self, player, level):
        # Cộng dồn thời gian (Đã hết lỗi nhờ self.timer ở init)
        self.timer += 1/60.0
        
        # 1. Logic vị trí đầu: Mặc định ở giữa, chỉ nhô khi gồng chiêu
        current_jut = self.attack_jut if (self.action_delay > 0 or self.slash_warning_visual > 0) else self.idle_jut
        self.head_rect.x = int(self.fixed_x + (self.body_w - self.head_w)//2 - current_jut)
        self.head_rect.y = int(self.fixed_y - self.head_h + 5)
        
        # Cập nhật khung va chạm bao phủ để đạn không bay xuyên
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

    def decide_attack(self, player):
        attacks = ["slash", "fire"]
        if self.hp <= 150: # Phase 2: HP dưới 50%
            attacks.append("lightning")
        
        choice = random.choice(attacks)
        if choice == "slash":
            self.show_speech("slash_warn")
            self.pending_action = "slash"; self.action_delay = 2.0
        elif choice == "fire":
            self.show_speech("fire_warn")
            self.pending_action = "fire"; self.action_delay = 1.2
        else:
            self.show_speech("lightning_warn")
            self.pending_action = "lightning"; self.action_delay = 1.5
            px = player.rect.x + player.rect.w//2
            self.lightning_x_positions = [px + (i - 2) * self.lightning_gap for i in range(5)]

    def start_lightning_execution(self):
        self.state = "attacking"
        self.lightning_warning_timer = 1.5 # Cảnh báo sét trong 1.5s

    def start_slash_logic(self, player):
        self.state = "attacking"; self.slash_warning_visual = 1.0 
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
        self.state = "idle"; self.idle_timer = 3.5; self.is_slashing = False

    def render(self, renderer, camera):
        if not self.alive: return
        
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

        # 2. Render Boss
        bdx, bdy = int(self.fixed_x - camera.x), int(self.fixed_y - camera.y)
        sdl2.SDL_SetRenderDrawColor(renderer, *self.color)
        sdl2.SDL_RenderFillRect(renderer, sdl2.SDL_Rect(bdx, bdy, self.body_w, self.body_h))
        
        hdx, hdy = int(self.head_rect.x - camera.x), int(self.head_rect.y - camera.y)
        sdl2.SDL_SetRenderDrawColor(renderer, 255, 0, 255, 255) # Đầu hồng
        sdl2.SDL_RenderFillRect(renderer, sdl2.SDL_Rect(hdx, hdy, self.head_w, self.head_h))
        sdl2.SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255)
        sdl2.SDL_RenderDrawRect(renderer, sdl2.SDL_Rect(hdx, hdy, self.head_w, self.head_h))
        
        # 3. Render Thanh Máu có VIỀN (Border)
        bar_w, bar_h, bar_x, bar_y = 400, 20, (SCREEN_WIDTH - 400) // 2, 30
        # Viền ngoài trắng
        sdl2.SDL_SetRenderDrawColor(renderer, 255, 255, 255, 255)
        sdl2.SDL_RenderDrawRect(renderer, sdl2.SDL_Rect(bar_x - 3, bar_y - 3, bar_w + 6, bar_h + 6))
        # Nền đen
        sdl2.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 200)
        sdl2.SDL_RenderFillRect(renderer, sdl2.SDL_Rect(bar_x, bar_y, bar_w, bar_h))
        # Phần máu đỏ
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
            try: self.game.hud._draw_text(renderer, self.speech_text, bdx + self.body_w // 2, bdy - 100, (255, 255, 255))
            except: pass