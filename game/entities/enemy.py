import sdl2
import math
import random

from game.entities import player

from .base import Entity
from game.constants import GRAVITY, TILE_SIZE, COLORS

ENEMY_QUOTES = {
    "detected": [
        "Đứng lại đó!", "Ngươi là ai?!", "Có kẻ xâm nhập!", 
        "Thịt người kìa!", "Đừng hòng chạy thoát!", "Chết đi!"
    ],
    "hit": [
        "Á!", "Đau quá!", "Tên khốn!", "Chờ đấy!", 
        "Hự!", "Này thì chém!", "Không thể nào!"
    ],
    "hit_head": ["KHÔNG! Điểm yếu của ta!", "Ngươi gan lắm!"],
    "hit_body": ["Vô ích thôi!", "Giáp ta quá dày!"],
    "slash_warn": ["TA SE XE NAT NGUOI!"], 
    "fire_warn": ["HOA NGUC TROI DAY!"],     
    "idle": ["Ngươi chi co the thoi sao?"],
    "lightning_warn": ["THIEN LOI PHAT! (Tìm khe hở mau!)"],
}

MANA_PER_KILL = 15

class Enemy(Entity):
    def __init__(self, game, x, y, w=32, h=32, hp=30, damage=1):
        super().__init__(game, x, y, w, h)
        self.z_index = 3
        self.hp = hp
        self.damage = damage
        self.patrol_speed = 1.2
        self.direction = 1
        self.color = [200, 50, 50, 255]
        self.alive = True
        
        # === STATUS & PHYSICS ===
        self.knockback_timer = 0.0
        self.is_chasing = False
        self.is_flying = False 

        self.speech_text = ""
        self.death_timer = 0.0
        self.speech_timer = 0.0
        self.speech_duration = 2.0 # Hiện chữ trong 2 giây
        self.has_spoken_detected = False

    def show_speech(self, category):
        """Kích hoạt hiển thị lời thoại ngẫu nhiên"""
        self.speech_text = random.choice(ENEMY_QUOTES[category])
        self.speech_timer = self.speech_duration

    def update(self, delta_time, level):
        if not self.alive:
                return

        # Xử lý timer lời thoại
        if self.speech_timer > 0:
            self.speech_timer -= delta_time

        if self.knockback_timer > 0:
            self.knockback_timer -= delta_time
        else:
            playing_state = self.game.states.get("playing")
            player = playing_state.player if playing_state else None
            if player:
                self._update_ai_state(player, level)

        # Vật lý trọng lực
        if not self.is_flying:
            self.vel_y += GRAVITY * delta_time * 60
            if self.vel_y > 12: self.vel_y = 12

        # Di chuyển Y
        self.pos_y += self.vel_y * delta_time * 60
        self.rect.y = int(self.pos_y)
        self._resolve_collision(level, is_y=True)

        # Di chuyển X
        self.pos_x += self.vel_x * delta_time * 60
        self.rect.x = int(self.pos_x)
        self._resolve_collision(level, is_y=False)

        self.pos_x = max(0, min(self.pos_x, level.pixel_width - self.rect.w))
        if self.pos_y > level.pixel_height: self.die()

    def _has_line_of_sight(self, player, level):
        """Kiểm tra đường thẳng nối giữa quái và player có bị cản bởi tường không"""
        dx = player.rect.x - self.rect.x

        if (self.direction > 0 and dx < 0) or (self.direction < 0 and dx > 0):
            # Trừ khi đã vào trạng thái đuổi (is_chasing), còn đi tuần thì không thấy sau lưng
            if not self.is_chasing:
                return False

        x1, y1 = self.rect.x + self.rect.w//2, self.rect.y + self.rect.h//2
        x2, y2 = player.rect.x + player.rect.w//2, player.rect.y + player.rect.h//2
        steps = 25
        for i in range(1, steps):
            check_x = x1 + (x2 - x1) * (i / steps)
            check_y = y1 + (y2 - y1) * (i / steps)
            if  level.is_solid_at(check_x, check_y) or \
                level.is_solid_at(check_x + 2, check_y) or \
                level.is_solid_at(check_x - 2, check_y):
                    return False
        return True

    def _check_ledge_or_wall(self, level):
        """Quay đầu nếu gặp tường hoặc vực"""
        ahead_x = self.rect.x + (self.rect.w if self.direction > 0 else 0) + (self.direction * 5)
        # Check tường
        if level.is_solid_at(ahead_x, self.rect.y + 5):
            self.direction *= -1
            return True
        # Check vực (chỉ quái đi bộ)
        if not self.is_flying:
            if not level.is_solid_at(ahead_x, self.rect.y + self.rect.h + 5):
                self.direction *= -1
                return True
        return False

    def _resolve_collision(self, level, is_y):
        start_row = max(0, self.rect.y // TILE_SIZE)
        end_row = min(len(level.tiles), (self.rect.y + self.rect.h) // TILE_SIZE + 1)
        start_col = max(0, self.rect.x // TILE_SIZE)
        end_col = min(len(level.tiles[0]), (self.rect.x + self.rect.w) // TILE_SIZE + 1)

        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                if level.tiles[row][col] == 1:
                    tile_rect = sdl2.SDL_Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    if sdl2.SDL_HasIntersection(self.rect, tile_rect):
                        if is_y:
                            if self.vel_y > 0: self.rect.y = tile_rect.y - self.rect.h
                            elif self.vel_y < 0: self.rect.y = tile_rect.y + TILE_SIZE
                            self.pos_y = float(self.rect.y)
                            self.vel_y = 0
                        else:
                            if self.vel_x > 0: self.rect.x = tile_rect.x - self.rect.w
                            elif self.vel_x < 0: self.rect.x = tile_rect.x + TILE_SIZE
                            self.pos_x = float(self.rect.x)
                            self.vel_x = 0
                            self.direction *= -1

    def take_damage(self, amount, knockback_dir=0):
        if not self.alive: return
        self.hp -= amount
        self.show_speech("hit")
        
        # --- FIX: Khi bị đánh, lập tức quay lại nhìn và dí player ---
        playing_state = self.game.states.get("playing")
        player = playing_state.player if playing_state else None
        
        if player:
            self.is_chasing = True
            # Reset cờ thoại để khi bắt đầu đuổi mới nói (tránh spam khi đang bị chém)
            self.has_spoken_detected = True 
            
            # Quay mặt về phía player
            dx = player.rect.x - self.rect.x
            if dx != 0:
                self.direction = 1 if dx > 0 else -1

        if knockback_dir != 0:
            self.knockback_timer = 0.2
            self.vel_x = knockback_dir * 5.0
            self.vel_y = -3.0
            
        if self.hp <= 0: self.die()

    def die(self):
        if not self.alive: return
        self.alive = False
        
        playing_state = self.game.states.get("playing")
        if playing_state:
            playing_state.player.mana = min(100, playing_state.player.mana + MANA_PER_KILL)
            # Quái chết là biến mất luôn cho nhẹ máy
            if self in playing_state.level.entities:
                playing_state.level.entities.remove(self)

    def render(self, renderer, camera):
        if not self.alive: return
        
        draw_rect = sdl2.SDL_Rect(int(self.rect.x - camera.x), int(self.rect.y - camera.y), self.rect.w, self.rect.h)
        sdl2.SDL_SetRenderDrawColor(renderer, self.color[0], self.color[1], self.color[2], 255)
        sdl2.SDL_RenderFillRect(renderer, draw_rect)

        # Vẽ lời thoại
        if self.speech_timer > 0 and self.speech_text:
            if hasattr(self.game, 'hud'):
                self.game.hud._draw_text(renderer, self.speech_text, 
                                       draw_rect.x - 20, draw_rect.y - 30, (255, 255, 255))

# ==================== CLASS CHI TIẾT ====================

class Goblin(Enemy):
    def __init__(self, game, x, y):
        # Goblin: Tốc độ chạy nhanh hơn khi đuổi (chasing)
        super().__init__(game, x, y, hp=40, damage=1)
        self.color = COLORS["green"]
        self.patrol_speed = 0.8
        self.chase_speed = self.patrol_speed * 1.5  # Tốc độ khi phát hiện player
        self.is_chasing = False

    def _update_ai_state(self, player, level):
        dx = player.rect.x - self.rect.x
        dy = player.rect.y - self.rect.y
        abs_dx = abs(dx)
        
        # --- LOGIC PHÁT HIỆN ---
        # Nếu Player ở gần (250px) và cùng mặt phẳng (dy < 60) và có Line of Sight
        if abs_dx < 250 and abs(dy) < 60 and self._has_line_of_sight(player, level):
            if not self.is_chasing:
                self.is_chasing = True
                if not getattr(self, 'has_spoken_detected', False):
                    self.show_speech("detected")
                    self.has_spoken_detected = True
        else:
            if abs_dx > 350:
                if not self.has_spoken_detected:
                    self.is_chasing = False
                    self.has_spoken_detected = False

        # --- THỰC THI DI CHUYỂN ---
        if self.is_chasing:
            self.direction = 1 if dx > 0 else -1
            self.vel_x = self.direction * self.chase_speed
            
            # Goblin vẫn phải biết check vực khi đang đuổi để không bị "ngáo" mà lao xuống hố
            ahead_x = self.rect.x + (self.rect.w if self.direction > 0 else 0) + (self.direction * 5)
            if not level.is_solid_at(ahead_x, self.rect.y + self.rect.h + 5):
                self.vel_x = 0 # Dừng lại ở mép vực chứ không nhảy xuống
        else:
            # Đi tuần bình thường
            self._check_ledge_or_wall(level)
            self.vel_x = self.patrol_speed * self.direction

        # --- GÂY SÁT THƯƠNG KHI CHẠM ---
        if sdl2.SDL_HasIntersection(self.rect, player.rect):
            player.take_damage(self.damage, self.direction)

class Skeleton(Enemy):
    def __init__(self, game, x, y):
        # Body Hitbox: Cho chiều rộng (w) hẹp lại thành 20 để giống bộ xương hơn
        super().__init__(game, x, y, w=20, h=48, hp=80, damage=1)
        self.color = COLORS["white"]
        self.patrol_speed = 0.8
        self.attack_timer = 0
        self.prep_timer = 0
        
        # Tầm xa của kiếm (Sword Reach)
        self.attack_range = 60 
        # Độ dày của lưỡi kiếm khi chém xuống (Sword Thickness)
        self.sword_width = 15 

    def _update_ai_state(self, player, level):
        if self.attack_timer > 0: self.attack_timer -= 1/60
        
        # Logic gồng và chém
        if self.prep_timer > 0:
            self.prep_timer -= 1/60
            self.vel_x = 0
            if self.prep_timer <= 0:
                self._perform_sword_slash(player)
            return

        dx = player.rect.x - self.rect.x
        abs_dx = abs(dx)
        
        # Phát hiện player
        if abs_dx < 250 and self._has_line_of_sight(player, level):
            # LỜI THOẠI: Chỉ nói 1 lần khi bắt đầu nhìn thấy
            if not self.is_chasing:
                self.is_chasing = True
                if not getattr(self, 'has_spoken_detected', False):
                    self.show_speech("detected")
                    self.has_spoken_detected = True
            
            self.direction = 1 if dx > 0 else -1
            
            # Nếu lọt vào tầm vung kiếm
            if abs_dx < self.attack_range - 5:
                self.vel_x = 0
                if self.attack_timer <= 0:
                    self.prep_timer = 1 # Khựng lại chuẩn bị chém
            else:
                self.vel_x = self.direction * 1.5
        else:
            # Khi player chạy mất hút, reset cờ để lần sau gặp lại nói tiếp
            if abs_dx > 400:
                self.is_chasing = False
                self.has_spoken_detected = False
                
            self._check_ledge_or_wall(level)
            self.vel_x = self.patrol_speed * self.direction

    def _perform_sword_slash(self, player):
        """Tạo ra một Hitbox thanh kiếm hẹp để kiểm tra va chạm"""
        self.attack_timer = 2.0 # Cooldown sau khi chém xong
        
        # Tính toán vị trí của lưỡi kiếm dựa trên hướng nhìn
        # Kiếm sẽ vươn từ mép của Skeleton ra phía trước
        sword_x = self.rect.x + self.rect.w if self.direction > 0 else self.rect.x - self.attack_range
        
        # Tạo Rect giả lập lưỡi kiếm (Hẹp và dài)
        sword_hitbox = sdl2.SDL_Rect(
            int(sword_x), 
            int(self.rect.y + 10), # Kiếm chém ở tầm ngang ngực
            self.attack_range, 
            self.sword_width
        )
        
        # Kiểm tra va chạm giữa lưỡi kiếm và Player
        if sdl2.SDL_HasIntersection(sword_hitbox, player.rect):
            player.take_damage(self.damage, self.direction)

    def render(self, renderer, camera):
        # 1. Vẽ thân hình Skeleton (hẹp)
        super().render(renderer, camera)
        
        # 2. DEBUG HITBOX KIẾM
        # Khi đang gồng (Vàng) hoặc vừa chém xong (Đỏ)
        if self.prep_timer > 0 or (self.attack_timer > 1.3):
            # Màu vàng khi đang gồng, màu đỏ khi đang vung kiếm
            debug_color = (255, 255, 0, 255) if self.prep_timer > 0 else (255, 0, 0, 255)
            sdl2.SDL_SetRenderDrawColor(renderer, *debug_color)
            
            # Vị trí hiển thị trên màn hình
            sword_x = self.rect.x + self.rect.w if self.direction > 0 else self.rect.x - self.attack_range
            
            # Vẽ đường kẻ đại diện cho thanh kiếm
            sword_render_rect = sdl2.SDL_Rect(
                int(sword_x - camera.x),
                int(self.rect.y + 15 - camera.y),
                self.attack_range,
                self.sword_width
            )
            
            if self.prep_timer > 0:
                # Vẽ khung rỗng khi đang gồng
                sdl2.SDL_RenderDrawRect(renderer, sword_render_rect)
            else:
                # Vẽ đặc khi đang gây sát thương
                sdl2.SDL_RenderFillRect(renderer, sword_render_rect)

class FireBat(Enemy):
    def __init__(self, game, x, y):
        # FireBat: Máu thấp, cơ động, bắn đạn định hướng
        super().__init__(game, x, y, w=24, h=24, hp=20, damage=1)
        self.is_flying = True
        self.color = (255, 100, 0, 255)
        self.attack_timer = 0
        self.is_chasing = False
        
        # --- CÂN CHỈNH ---
        self.attack_cooldown = 3.5  # Bắn chậm lại (3.5 giây/phát)
        self.view_range = 350       # Tầm nhìn

    def _update_ai_state(self, player, level):
        if self.attack_timer > 0: self.attack_timer -= 1/60
        
        dx = player.rect.x - self.rect.x
        dy = player.rect.y - self.rect.y
        dist_sq = dx**2 + dy**2

        # Phát hiện player
        if not self.is_chasing:
            if dist_sq < self.view_range**2 and self._has_line_of_sight(player, level):
                self.is_chasing = True
                # LỜI THOẠI: Chỉ nói 1 lần khi bắt đầu đuổi
                if not getattr(self, 'has_spoken_detected', False) and self.speech_timer <= 0:
                    self.show_speech("detected")
                    self.has_spoken_detected = True
        else:
            # Khoảng cách để quái mất dấu (view_range + 50)
            if not self._has_line_of_sight(player, level) or dist_sq > (self.view_range + 50)**2:
                self.is_chasing = False
                self.has_spoken_detected = False

        if self.is_chasing:
            self.direction = 1 if dx > 0 else -1
            
            # AI bay giữ khoảng cách an toàn (Target Y cao hơn đầu player một chút)
            target_y = player.rect.y - 40 
            self.vel_y = (0.8 if self.rect.y < target_y else -0.8) if abs(self.rect.y - target_y) > 10 else 0
            
            # Giữ khoảng cách X (180px) để tỉa
            if abs(dx) < 170: self.vel_x = -self.direction * 1.2
            elif abs(dx) > 200: self.vel_x = self.direction * 1.2
            else:
                self.vel_x = 0
                # TẤN CÔNG: Bắn đạn hướng về phía Player
                if self.attack_timer <= 0 and self._has_line_of_sight(player, level):
                    self._shoot_at_player(player, level)
                    self.attack_timer = self.attack_cooldown
        else:
            # Tuần tra lơ lửng
            self.vel_y = 0
            self._check_ledge_or_wall(level)
            self.vel_x = self.patrol_speed * self.direction

    def _shoot_at_player(self, player, level):
        """Tính toán vector hướng để bắn trúng đích"""
        start_x = self.rect.x + self.rect.w // 2
        start_y = self.rect.y + self.rect.h // 2
        
        target_x = player.rect.x + player.rect.w // 2
        target_y = player.rect.y + player.rect.h // 2
        
        # Tính toán vector hướng (normalized)
        angle = math.atan2(target_y - start_y, target_x - start_x)
        dir_x = math.cos(angle)
        dir_y = math.sin(angle)
        
        # Tạo đạn với hướng đã tính
        fireball = EnemyFireball(self.game, start_x, start_y, dir_x, dir_y, self.damage)
        level.entities.append(fireball)

class EnemyFireball(Entity):
    def __init__(self, game, x, y, dir_x, dir_y, damage):
        super().__init__(game, x, y, 12, 12) # Đạn nhỏ hơn tí cho dễ né
        self.dir_x = dir_x
        self.dir_y = dir_y
        self.damage = damage
        self.speed = 4.0
        self.color = (255, 50, 0, 255)
        self.life_time = 3.0
        self.z_index = 4

    def update(self, delta_time, level):
        # Bay theo hướng xiên thay vì chỉ bay ngang
        self.pos_x += self.dir_x * self.speed * delta_time * 60
        self.pos_y += self.dir_y * self.speed * delta_time * 60
        
        self.rect.x = int(self.pos_x)
        self.rect.y = int(self.pos_y)

        if level.is_solid_at(self.rect.x + self.rect.w//2, self.rect.y + self.rect.h//2):
            self.alive = False
            return
        
        self.life_time -= delta_time
        
        # Kiểm tra va chạm
        player = self.game.states["playing"].player
        if player and sdl2.SDL_HasIntersection(self.rect, player.rect):
            # Lấy hướng đẩy lùi dựa trên hướng bay của đạn
            k_dir = 1 if self.dir_x > 0 else -1
            player.take_damage(self.damage, k_dir)
            self.alive = False
            
        if self.life_time <= 0: self.alive = False

    def render(self, renderer, camera):
        # Vẽ viên đạn (hình vuông nhỏ màu cam/đỏ)
        draw_rect = sdl2.SDL_Rect(int(self.rect.x - camera.x), int(self.rect.y - camera.y), self.rect.w, self.rect.h)
        sdl2.SDL_SetRenderDrawColor(renderer, *self.color)
        sdl2.SDL_RenderFillRect(renderer, draw_rect)