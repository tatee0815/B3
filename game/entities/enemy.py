import sdl2
import math
import random

from game.entities import player
from game.utils.assets import AssetManager
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
    "death": [
        "Ta... sẽ... trở lại...", "Không thể nào!", "Hự...", 
        "Ước gì chưa đi làm quái...", "Lương thấp quá mà...", "Hẹn gặp lại ở địa ngục!"
    ],
    "hit_head": ["..."],
    "hit_body": ["..."],
    "slash_warn": ["..."], 
    "fire_warn": ["..."],     
    "idle": ["..."],
    "lightning_warn": ["..."],
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
        self.is_dead_body = False # Trạng thái xác chết
        
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
        if self.is_dead_body:
            self.death_timer -= delta_time
            if self.death_timer <= 0:
                playing_state = self.game.states.get("playing")
                if playing_state and self in playing_state.level.entities:
                    playing_state.level.entities.remove(self)
            return

        if not self.alive:
            return

        # Xử lý timer lời thoại
        if self.speech_timer > 0:
            self.speech_timer -= delta_time

        if self.knockback_timer > 0:
            self.knockback_timer -= delta_time
        else:
            player = self.game.player
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
                if level.tiles[row][col] in (1, 2):
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
        
        # --- Khi bị đánh, lập tức quay lại nhìn và dí player ---
        player = self.game.player
        
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
        if not self.alive or self.is_dead_body: return
        
        self.alive = False
        self.is_dead_body = True
        self.death_timer = 2.0  # Để lại xác trong 2 giây
        
        # Ngừng mọi chuyển động
        self.vel_x = 0
        self.vel_y = 0
        
        self.show_speech("death")

        playing_state = self.game.states.get("playing")
        if playing_state:
            playing_state.player.mana = min(100, playing_state.player.mana + MANA_PER_KILL)

    def render(self, renderer, camera):
        # Vẽ lời thoại - đặt ngoài để hiển thị cả khi là xác chết
        if self.speech_timer > 0 and self.speech_text:
            if hasattr(self.game, 'hud'):
                # Tăng offset lên để chữ không bị chồng lên xác
                y_offset = -50 if self.is_dead_body else -30
                self.game.hud._draw_text(
                    renderer,
                    self.speech_text,
                    int(self.rect.x - camera.x),
                    int(self.rect.y - camera.y + y_offset),
                    (255, 255, 255)
                )

# ==================== CLASS CHI TIẾT ====================

class Goblin(Enemy):
    def __init__(self, game, x, y):
        # Goblin: Tốc độ chạy nhanh hơn khi đuổi (chasing)
        super().__init__(game, x, y, hp=40, damage=1)
        self.color = COLORS["green"]
        self.patrol_speed = 0.8
        self.chase_speed = self.patrol_speed * 1.5  # Tốc độ khi phát hiện player
        self.is_chasing = False

        self.state = "goblin_walk"
        self.anim_frame = 0
        self.anim_timer = 0.0

        self.death_alpha = 255

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

    def update(self, delta_time, level):
        if self.is_dead_body:
            self.state = "goblin_death"
            self.death_alpha = max(0, int((self.death_timer / 2.0) * 255))
            self._update_anim_frame(delta_time)
            super().update(delta_time, level)
            return

        self._update_anim_frame(delta_time)

        # Chọn state animation
        if self.is_dead_body:
            self.state = "goblin_death"
        elif abs(self.vel_x) > 0.1:
            self.state = "goblin_walk"
        else:
            self.state = "goblin_idle"

        super().update(delta_time, level)

    def _update_anim_frame(self, delta_time):
        self.anim_timer += delta_time
        if self.anim_timer > 0.15:           # tốc độ frame ~8-9 fps
            self.anim_timer -= 0.15
            self.anim_frame += 1

    def render(self, renderer, camera):
        texture, srcrect = AssetManager.get_anim_info(self.state, self.anim_frame)

        if texture:
            sprite_w = 48
            sprite_h = 48

            offset_x = 0
            if self.direction < 0:
                offset_x = sprite_w - self.rect.w  # sửa flip cho đẹp

            draw_x = int(self.rect.x - camera.x - offset_x)
            draw_y = int(self.rect.y - camera.y - (sprite_h - self.rect.h))

            dstrect = sdl2.SDL_Rect(draw_x, draw_y, sprite_w, sprite_h)

            flip = sdl2.SDL_FLIP_NONE if self.direction >= 0 else sdl2.SDL_FLIP_HORIZONTAL

            if self.is_dead_body:
                sdl2.SDL_SetTextureAlphaMod(texture, self.death_alpha)
            else:
                # Đảm bảo quái còn sống luôn có Alpha tối đa
                sdl2.SDL_SetTextureAlphaMod(texture, 255)

            sdl2.SDL_RenderCopyEx(
                renderer, texture, srcrect, dstrect,
                0, None, flip
            )

            if self.is_dead_body:
                sdl2.SDL_SetTextureAlphaMod(texture, 255)

        # Vẽ lời thoại (gọi super)
        super().render(renderer, camera)

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
        self.sword_width = 15 

        # --- PHẦN THÊM SPRITE ---
        self.state = "skeleton_walk"
        self.anim_frame = 0
        self.anim_timer = 0

        self.death_alpha = 255

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

            self.is_chasing = True
            self.direction = 1 if dx > 0 else -1
            
            # Nếu lọt vào tầm vung kiếm
            if abs_dx < self.attack_range - 5:
                self.vel_x = 0
                if self.attack_timer <= 0:
                    self.prep_timer = 1 # Khựng lại chuẩn bị chém
            else:
                self.vel_x = self.direction * 1.5

                ahead_x = self.rect.x + (self.rect.w if self.direction > 0 else 0) + (self.direction * 5)
                # Nếu phía trước không có đất (vực), dừng lại ngay
                if not level.is_solid_at(ahead_x, self.rect.y + self.rect.h + 5):
                    self.vel_x = 0
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
        if self.direction > 0:
            sword_x = self.rect.x + self.rect.w
            sword_y = self.rect.y + 10          # chém ngang ngực
        else:
            sword_x = self.rect.x - self.attack_range
            sword_y = self.rect.y + 10

        # Tạo Rect giả lập lưỡi kiếm (Hẹp và dài)
        sword_hitbox = sdl2.SDL_Rect(
            int(sword_x), 
            int(sword_y), # Kiếm chém ở tầm ngang ngực
            self.attack_range, 
            self.sword_width
        )
        
        # Kiểm tra va chạm giữa lưỡi kiếm và Player
        if sdl2.SDL_HasIntersection(sword_hitbox, player.rect):
            player.take_damage(self.damage, self.direction)

    def render(self, renderer, camera):
        # 1. Vẽ Sprite
        texture, srcrect = AssetManager.get_anim_info(self.state, self.anim_frame)
    
        if texture:
            sprite_w = 48
            sprite_h = 48

            offset_x = 0
            if self.direction < 0:
                offset_x = sprite_w - self.rect.w  # đẩy sprite sang phải khi nhìn trái

            draw_x = int(self.rect.x - camera.x - offset_x)
            draw_y = int(self.rect.y - camera.y - (sprite_h - self.rect.h))

            dstrect = sdl2.SDL_Rect(draw_x, draw_y, sprite_w, sprite_h)
            
            if self.is_dead_body:
                sdl2.SDL_SetTextureAlphaMod(texture, self.death_alpha)
            
            flip = sdl2.SDL_FLIP_NONE if self.direction >= 0 else sdl2.SDL_FLIP_HORIZONTAL
            sdl2.SDL_RenderCopyEx(renderer, texture, srcrect, dstrect, 0, None, flip)
            
            if self.is_dead_body:
                sdl2.SDL_SetTextureAlphaMod(texture, 255)

        # 2. Vẽ Debug Hitbox kiếm (Chỉ khi còn sống)
        if not self.is_dead_body:
            if self.prep_timer > 0 or (self.attack_timer > 1.3):
                self._render_sword_debug(renderer, camera)
        
        # 3. Vẽ lời thoại (Gọi hàm cha)
        super().render(renderer, camera)

    def _render_sword_debug(self, renderer, camera):
        debug_color = (255, 255, 0, 255) if self.prep_timer > 0 else (255, 0, 0, 255)
        sdl2.SDL_SetRenderDrawColor(renderer, *debug_color)
        
        sword_x = self.rect.x + self.rect.w if self.direction > 0 else self.rect.x - self.attack_range
        sword_render_rect = sdl2.SDL_Rect(
            int(sword_x - camera.x),
            int(self.rect.y + 15 - camera.y),
            self.attack_range,
            self.sword_width
        )
        if self.prep_timer <= 0:
            sdl2.SDL_RenderFillRect(renderer, sword_render_rect)

    def update(self, delta_time, level):
        # Nếu đã chết (được die() set is_dead_body = True)
        if self.is_dead_body:
            self.state = "skeleton_death"
            # Mờ dần dựa trên death_timer của lớp Enemy cha (2.0s)
            self.death_alpha = max(0, int((self.death_timer / 2.0) * 255))
            self._update_anim_frame(delta_time)
            super().update(delta_time, level)
            return

        # Cập nhật animation frame
        self._update_anim_frame(delta_time)
        
        # Quyết định State và Hướng nhìn
        if self.prep_timer > 0:
            self.state = "skeleton_attack"
        elif abs(self.vel_x) > 0.1:
            self.state = "skeleton_walk"
            # FIX: Luôn cập nhật direction theo vận tốc thực tế
            self.direction = 1 if self.vel_x > 0 else -1
        else:
            self.state = "skeleton_idle"

        super().update(delta_time, level)

    def _update_anim_frame(self, delta_time):
        self.anim_timer += delta_time
        if self.anim_timer > 0.1:
            self.anim_timer = 0
            self.anim_frame += 1

class FireBat(Enemy):
    def __init__(self, game, x, y):
        # FireBat: Máu thấp, cơ động, bắn đạn định hướng
        super().__init__(game, x, y, w=24, h=24, hp=20, damage=1)
        self.is_flying = True
        self.color = (255, 100, 0, 255)
        self.attack_timer = 0
        self.is_chasing = False

        # --- Animation ---
        self.state = "firebat_walk"      
        self.anim_frame = 0
        self.anim_timer = 0.0
        self.anim_speed = 0.12
        
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

    def _update_anim_frame(self, delta_time):
        self.anim_timer += delta_time
        if self.anim_timer > self.anim_speed:
            self.anim_timer -= self.anim_speed
            self.anim_frame += 1

    def update(self, delta_time, level):
        if self.is_dead_body:
            self.state = "firebat_death"
            self.death_timer -= delta_time  # nếu có fade
            self._update_anim_frame(delta_time)
            super().update(delta_time, level)
            return

        self._update_anim_frame(delta_time)

        # Chọn state dựa trên hành động
        if self.is_dead_body:
            self.state = "firebat_death"
        elif self.attack_timer <= 0 and self.is_chasing:
            self.state = "firebat_attack"  # nếu có animation attack riêng
        else:
            self.state = "firebat_walk"     # bay bình thường

        super().update(delta_time, level)

    def render(self, renderer, camera):
        texture, srcrect = AssetManager.get_anim_info(self.state, self.anim_frame)
        if not texture:
            # Fallback vẽ hình chữ nhật nếu sprite lỗi
            super().render(renderer, camera)  # hoặc vẽ màu cam
            return

        # Kích thước frame (điều chỉnh nếu khác 32x32)
        sprite_w = 32
        sprite_h = 32

        # Offset để căn giữa (vì rect 24x24, sprite lớn hơn một chút)
        offset_x = (sprite_w - self.rect.w) // 2
        offset_y = (sprite_h - self.rect.h) // 2  # hoặc -10 nếu cánh dưới thấp

        draw_x = int(self.rect.x - camera.x - offset_x)
        draw_y = int(self.rect.y - camera.y - offset_y)

        dstrect = sdl2.SDL_Rect(draw_x, draw_y, sprite_w, sprite_h)

        # Flip theo hướng bay
        flip = sdl2.SDL_FLIP_HORIZONTAL if self.direction < 0 else sdl2.SDL_FLIP_NONE

        # Nếu chết thì fade alpha (tương tự Goblin)
        if self.is_dead_body:
            alpha = int((self.death_timer / 2.0) * 255) if hasattr(self, 'death_timer') else 255
            sdl2.SDL_SetTextureAlphaMod(texture, max(0, alpha))

        sdl2.SDL_RenderCopyEx(
            renderer, texture, srcrect, dstrect,
            0, None, flip
        )

        # Reset alpha nếu cần
        if self.is_dead_body:
            sdl2.SDL_SetTextureAlphaMod(texture, 255)

        # Vẽ lời thoại / debug nếu có
        super().render(renderer, camera)

class EnemyFireball(Entity):
    def __init__(self, game, x, y, dir_x, dir_y, damage):
        super().__init__(game, x, y, 15, 15) # Đạn nhỏ hơn tí cho dễ né
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
        player = self.game.player
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