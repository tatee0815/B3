import sdl2

from game.constants import (
    PLAYER_SPEED, JUMP_FORCE, DOUBLE_JUMP_FORCE,
    GRAVITY, PLAYER_MAX_HP, MANA_MAX, MANA_PER_KILL,
    SKILL_A_COST, SKILL_A_DAMAGE, KEY_BINDINGS_DEFAULT
)
from .base import Entity
from .projectile import Projectile


class Player(Entity):
    def __init__(self, game):
        super().__init__(game, x=100, y=400, w=24, h=48)  # cao hơn tí
        
        self.hp = PLAYER_MAX_HP
        self.mana = 50
        self.gold = 0
        
        # Skill unlock (lấy từ game.progress)
        self.has_double_jump = game.player_progress["double_jump"]
        self.skill_a_upgraded = game.player_progress["skill_a_upgraded"]
        
        self.can_double_jump = self.has_double_jump
        self.jumped_once = False
        
        # Animation state (sau này mở rộng)
        self.state = "idle"  # idle, run, jump, attack...

    def handle_input(self, event):
        # 1. Xử lý khi nhấn phím xuống (KEYDOWN)
        if event.type == sdl2.SDL_KEYDOWN:
            scancode = event.key.keysym.scancode
            
            # Di chuyển sang trái
            if scancode == sdl2.SDL_SCANCODE_LEFT :
                self.vel_x = -PLAYER_SPEED
                self.facing_right = False
            # Di chuyển sang phải
            elif scancode == sdl2.SDL_SCANCODE_RIGHT:
                self.vel_x = PLAYER_SPEED
                self.facing_right = True
            
            # Nhảy
            elif scancode == KEY_BINDINGS_DEFAULT["jump"] or scancode == sdl2.SDL_SCANCODE_SPACE:
                if self.on_ground:
                    self.vel_y = JUMP_FORCE
                    self.on_ground = False
                    self.jumped_once = True
                elif self.can_double_jump and self.jumped_once:
                    self.vel_y = DOUBLE_JUMP_FORCE
                    self.jumped_once = False
            
            # Tấn công
            elif scancode == KEY_BINDINGS_DEFAULT["attack"]:
                self.melee_attack()

        # 2. Xử lý khi thả phím ra (KEYUP) - Quan trọng để hết bị khựng
        elif event.type == sdl2.SDL_KEYUP:
            scancode = event.key.keysym.scancode
            
            # Nếu đang đi trái mà thả phím trái/A ra thì dừng vel_x
            if (scancode == sdl2.SDL_SCANCODE_LEFT ) and self.vel_x < 0:
                self.vel_x = 0
            # Nếu đang đi phải mà thả phím phải/D ra thì dừng vel_x
            elif (scancode == sdl2.SDL_SCANCODE_RIGHT ) and self.vel_x > 0:
                self.vel_x = 0

    def update(self, delta_time, level):
        # KHÔNG CÒN GetKeyboardState ở đây nữa
        
        # Cập nhật vị trí dựa trên vel_x, vel_y (đã được set trong handle_input)
        super().update(delta_time, level)
        
        # Xử lý va chạm
        level.handle_collision(self)
        
        # Mana hồi phục theo thời gian
        self.mana = min(MANA_MAX, self.mana + 5 * delta_time)

    def melee_attack(self):
        damage = 20
        # Lấy danh sách quái từ level
        entities = self.game.states["playing"].level.entities
        
        for e in entities:
            # Kiểm tra nếu e là quái vật và có va chạm với đòn đánh của Player
            # (Bạn có thể tạo một Rect tấn công rộng hơn rect của player tí)
            if e != self and self.collides_with(e):
                if hasattr(e, "take_damage"):
                    e.take_damage(damage)

    def collides_with(self, other):
        """Hàm hỗ trợ kiểm tra va chạm giữa 2 SDL_Rect"""
        return sdl2.SDL_HasIntersection(self.rect, other.rect)

    def skill_a_fire(self):
        # Bắn projectile
        direction = 1 if self.facing_right else -1
        proj_x = self.rect.x + (self.rect.w if direction > 0 else -32)
        proj = Projectile(self.game, proj_x, self.rect.centery - 8, direction)
        self.game.states["playing"].level.entities.append(proj)

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            # chết → xử lý trong playing state

    def respawn(self, pos):
        self.rect.x = pos[0]
        self.rect.y = pos[1]
        self.vel_x = 0
        self.vel_y = 0
        self.hp = PLAYER_MAX_HP
        self.mana = 50