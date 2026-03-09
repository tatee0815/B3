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
        super().__init__(game, x=100, y=400, w=32, h=48)  # cao hơn tí
        
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
        if event.type == sdl2.SDL_KEYDOWN:
            key = event.key.keysym.sym
            
            if key == KEY_BINDINGS_DEFAULT["jump"]:
                if self.on_ground:
                    self.vel_y = JUMP_FORCE
                    self.jumped_once = True
                    self.on_ground = False
                elif self.can_double_jump and self.jumped_once:
                    self.vel_y = DOUBLE_JUMP_FORCE
                    self.jumped_once = False
            
            elif key == KEY_BINDINGS_DEFAULT["attack"]:
                self.melee_attack()
            
            elif key == KEY_BINDINGS_DEFAULT["skill"] and self.mana >= SKILL_A_COST:
                self.skill_a_fire()
                self.mana -= SKILL_A_COST
            
        elif event.type == sdl2.SDL_KEYUP:
            # Dừng di chuyển ngang khi thả phím
            pass

    def update(self, delta_time, level):
        keys = sdl2.SDL_GetKeyboardState(None)
        
        # Di chuyển ngang
        move = 0
        if keys[KEY_BINDINGS_DEFAULT["left"] & 0xFF]:
            move = -PLAYER_SPEED
            self.facing_right = False
        if keys[KEY_BINDINGS_DEFAULT["right"] & 0xFF]:
            move = PLAYER_SPEED
            self.facing_right = True
        
        self.vel_x = move
        
        super().update(delta_time, level)
        
        # Collision với level (sẽ implement chi tiết trong level.py)
        level.resolve_player_collision(self)
        
        # Regen mana thụ động nhẹ
        self.mana = min(MANA_MAX, self.mana + 5 * delta_time)

    def melee_attack(self):
        # Tạm thời: gây damage cho enemy trong phạm vi gần
        damage = 20  # sau này nâng cấp
        for e in self.game.states["playing"].level.entities:
            if isinstance(e, Enemy) and self.collides_with(e):
                e.take_damage(damage)

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