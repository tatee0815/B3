import sdl2
from game.constants import (
    PLAYER_SPEED, JUMP_FORCE, DOUBLE_JUMP_FORCE,
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
        self.gold = progress.get("gold", 0)
        
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
        self.attack_timer = 0
        self.ATTACK_DURATION = 0.3
        self.attack_rect = sdl2.SDL_Rect(0, 0, 0, 0)
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
            self.is_dashing = True
            self.dash_timer = self.DASH_DURATION
            self.dash_cooldown = 0.8

    def melee_attack(self):
        if not self.is_attacking and not self.is_dashing:
            self.is_attacking = True
            self.attack_timer = self.ATTACK_DURATION
            self.state = "attack"
            
            # Tính toán vị trí hitbox gây sát thương
            attack_width = 40
            ax = self.rect.x + self.rect.w if self.facing_right else self.rect.x - attack_width
            self.attack_rect = sdl2.SDL_Rect(ax, self.rect.y, attack_width, self.rect.h)
            
            # Kiểm tra va chạm gây sát thương lên quái
            entities = self.game.states["playing"].level.entities
            for e in entities:
                if e != self and hasattr(e, "rect"):
                    if sdl2.SDL_HasIntersection(self.attack_rect, e.rect):
                        if hasattr(e, "take_damage"):
                            e.take_damage(20)

    def use_skill(self):
        if self.mana >= SKILL_A_COST:
            self.mana -= SKILL_A_COST
            self.skill_a_fire()
        else:
            print("Không đủ Mana!")

    def skill_a_fire(self):
        direction = 1 if self.facing_right else -1
        proj_x = self.rect.x + (self.rect.w if direction > 0 else -32)
        proj = Projectile(self.game, proj_x, self.rect.centery - 8, direction)
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
        if self.is_attacking:
            self.attack_timer -= delta_time
            if self.attack_timer <= 0: self.is_attacking = False

        # 2. Xử lý Vận tốc X (Ưu tiên Dash > Attack > Walk)
        if self.is_dashing:
            self.dash_timer -= delta_time
            self.vel_x = (1 if self.facing_right else -1) * self.DASH_SPEED
            if self.dash_timer <= 0: self.is_dashing = False
        elif self.is_attacking:
            self.vel_x = 0
        else:
            if self.moving_left: self.vel_x = -PLAYER_SPEED
            elif self.moving_right: self.vel_x = PLAYER_SPEED
            else: self.vel_x = 0

        # 3. Cập nhật vật lý và va chạm môi trường
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
        self.respawn(self.checkpoint_pos)

        self.hp = 100
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

    def take_damage(self, amount):
        if self.is_respawning: return # Tránh nhận sát thương khi đang trong quá trình hồi sinh
        
        self.hp -= amount
        print(f"Player take damage! HP còn: {self.hp}")
        
        if self.hp <= 0:
            self.hp = 0 # Tránh HP âm
            self.handle_death()