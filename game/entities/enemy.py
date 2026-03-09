from .base import Entity


class Enemy(Entity):
    def __init__(self, game, x, y, hp=30, damage=10):
        super().__init__(game, x, y, 32, 32)
        self.hp = hp
        self.damage = damage
        self.patrol_speed = 1.5
        self.direction = 1  # 1: phải, -1: trái

    def update(self, delta_time, level):
        super().update(delta_time, level)
        
        # Patrol đơn giản
        self.vel_x = self.patrol_speed * self.direction
        
        # Đổi hướng khi chạm tường (sẽ cải thiện sau)
        if level.is_solid_at(self.rect.x + self.vel_x * 10, self.rect.y + 16):
            self.direction *= -1

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.die()

    def die(self):
        # Tăng mana cho player
        player = self.game.states["playing"].player
        player.mana = min(player.mana + MANA_PER_KILL, 100)
        player.gold += 5
        
        # Xóa enemy khỏi level
        level = self.game.states["playing"].level
        if self in level.entities:
            level.entities.remove(self)


class Goblin(Enemy):
    def __init__(self, game, x, y):
        super().__init__(game, x, y, hp=25, damage=8)
        self.patrol_speed = 1.2


class Skeleton(Enemy):
    def __init__(self, game, x, y):
        super().__init__(game, x, y, hp=40, damage=12)
        self.patrol_speed = 0.8


class FireBat(Enemy):
    def __init__(self, game, x, y):
        super().__init__(game, x, y, hp=20, damage=15)
        self.patrol_speed = 2.5  # bay nhanh

class BossShadowKing(Enemy):
    def __init__(self, game, x, y):
        super().__init__(game, x, y, hp=150, damage=30)  # boss mạnh hơn
        self.patrol_speed = 0.0  # đứng yên hoặc di chuyển đặc biệt
        self.color = (100, 0, 150, 255)  # tím đen
        self.phase = 1  # phase 1,2,3 sau này

    def update(self, delta_time, level=None):
        super().update(delta_time, level)
        # Logic boss: bắn cầu lửa, triệu hồi goblin...
        # tạm thời patrol chậm
        self.vel_x = 0.5 * (1 if level else 0)