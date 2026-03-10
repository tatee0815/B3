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
        # Khởi tạo lớp cha Entity
        super().__init__(game, x=100, y=400, w=24, h=48)
        
        # Chỉ số cơ bản
        self.hp = PLAYER_MAX_HP
        self.mana = 50
        self.gold = 0
        
        # Trạng thái kỹ năng
        self.has_double_jump = game.player_progress["double_jump"]
        self.can_double_jump = self.has_double_jump
        self.jumped_once = False
        
        # Biến điều khiển di chuyển (Để không bị khựng khi Dash)
        self.moving_left = False
        self.moving_right = False
        
        # Logic Dash (Lướt)
        self.is_dashing = False
        self.dash_timer = 0
        self.dash_cooldown = 0.2
        self.DASH_DURATION = 0.2
        self.DASH_SPEED = PLAYER_SPEED * 5
        
        self.state = "idle" # idle, run, jump, attack, dash...
        self.facing_right = True

    def handle_input(self, event):
        """Xử lý sự kiện bàn phím dựa trên KEY_BINDINGS_DEFAULT"""
        scancode = event.key.keysym.scancode
        
        # 1. Khi nhấn phím xuống
        if event.type == sdl2.SDL_KEYDOWN:
            if scancode == KEY_BINDINGS_DEFAULT["left"]:
                self.moving_left = True
                self.facing_right = False
            elif scancode == KEY_BINDINGS_DEFAULT["right"]:
                self.moving_right = True
                self.facing_right = True
            
            # Nhảy (Hỗ trợ phím gán và Space mặc định)
            elif scancode == KEY_BINDINGS_DEFAULT["jump"] or scancode == sdl2.SDL_SCANCODE_SPACE:
                self.jump()
            
            # Tấn công thường
            elif scancode == KEY_BINDINGS_DEFAULT["attack"]:
                self.melee_attack()
            
            # Kỹ năng (Bắn chưởng)
            elif scancode == KEY_BINDINGS_DEFAULT["skill"]:
                self.use_skill()
                
            # Lướt (Dash)
            elif scancode == KEY_BINDINGS_DEFAULT["dash"]:
                self.dash()

            # Tương tác (Trò chuyện/Mở đồ)
            elif scancode == KEY_BINDINGS_DEFAULT["interact"]:
                self.interact()

        # 2. Khi thả phím (Để dừng di chuyển mượt mà)
        elif event.type == sdl2.SDL_KEYUP:
            if scancode == KEY_BINDINGS_DEFAULT["left"]:
                self.moving_left = False
            elif scancode == KEY_BINDINGS_DEFAULT["right"]:
                self.moving_right = False

    def jump(self):
        """Logic nhảy đơn và nhảy đôi"""
        if self.on_ground:
            self.vel_y = JUMP_FORCE
            self.on_ground = False
            self.jumped_once = True
        elif self.can_double_jump and self.jumped_once:
            self.vel_y = DOUBLE_JUMP_FORCE
            self.jumped_once = False

    def dash(self):
        """Kích hoạt Dash nếu không trong thời gian hồi"""
        if self.dash_cooldown <= 0 and not self.is_dashing:
            self.is_dashing = True
            self.dash_timer = self.DASH_DURATION
            self.dash_cooldown = 0.8 # Thời gian chờ để dash tiếp

    def use_skill(self):
        """Sử dụng kỹ năng tiêu tốn Mana"""
        if self.mana >= SKILL_A_COST:
            self.mana -= SKILL_A_COST
            self.skill_a_fire()
        else:
            print("Không đủ Mana!")

    def interact(self):
        """Kiểm tra và tương tác với NPC/Object gần nhất"""
        entities = self.game.states["playing"].level.entities
        for e in entities:
            if e != self and self.collides_with(e):
                if hasattr(e, "on_interact"):
                    e.on_interact()
                    return

    def update(self, delta_time, level):
        """Cập nhật logic hàng frame"""
        # Cập nhật Cooldown
        if self.dash_cooldown > 0:
            self.dash_cooldown -= delta_time

        # Xử lý vận tốc X (Ưu tiên Dash)
        if self.is_dashing:
            self.dash_timer -= delta_time
            direction = 1 if self.facing_right else -1
            self.vel_x = direction * self.DASH_SPEED
            if self.dash_timer <= 0:
                self.is_dashing = False
        else:
            if self.moving_left:
                self.vel_x = -PLAYER_SPEED
            elif self.moving_right:
                self.vel_x = PLAYER_SPEED
            else:
                self.vel_x = 0

        # Cập nhật vật lý từ lớp cha Entity
        super().update(delta_time, level)
        
        # Xử lý va chạm với môi trường
        level.handle_collision(self)
        
        # Hồi phục Mana tự động
        self.mana = min(MANA_MAX, self.mana + 5 * delta_time)

    def melee_attack(self):
        """Tấn công cận chiến"""
        damage = 20
        entities = self.game.states["playing"].level.entities
        for e in entities:
            if e != self and self.collides_with(e):
                if hasattr(e, "take_damage"):
                    e.take_damage(damage)

    def skill_a_fire(self):
        """Bắn đạn projectile"""
        direction = 1 if self.facing_right else -1
        proj_x = self.rect.x + (self.rect.w if direction > 0 else -32)
        proj = Projectile(self.game, proj_x, self.rect.centery - 8, direction)
        self.game.states["playing"].level.entities.append(proj)

    def collides_with(self, other):
        """Kiểm tra va chạm SDL_Rect"""
        return sdl2.SDL_HasIntersection(self.rect, other.rect)

    def take_damage(self, amount):
        """Nhận sát thương"""
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0

    def respawn(self, pos):
        """Hồi sinh tại vị trí chỉ định"""
        self.rect.x, self.rect.y = pos
        self.vel_x = self.vel_y = 0
        self.hp = PLAYER_MAX_HP
        self.mana = 50