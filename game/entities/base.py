import sdl2.ext

from game.constants import TILE_SIZE


class Entity:
    def __init__(self, game, x=0, y=0, w=TILE_SIZE, h=TILE_SIZE):
        self.game = game
        self.renderer = game.renderer
        
        # Vị trí & kích thước (rect cho collision)
        self.rect = sdl2.ext.Rect(x, y, w, h)
        
        # Vận tốc
        self.vel_x = 0.0
        self.vel_y = 0.0
        
        # Trạng thái
        self.on_ground = False
        self.facing_right = True
        
        # Texture (sẽ load sau)
        self.texture = None
        self.color = (255, 255, 255, 255)  # fallback nếu chưa có sprite

    def update(self, delta_time, level=None):
        """Cập nhật vị trí + gravity cơ bản"""
        if level:
            self.vel_y += level.gravity * delta_time * 60  # điều chỉnh theo frame rate
            
            self.rect.x += int(self.vel_x * delta_time * 60)
            self.rect.y += int(self.vel_y * delta_time * 60)
            
            # Giới hạn rơi
            if self.vel_y > 12:
                self.vel_y = 12

    def render(self, renderer, camera):
        if self.texture:
            # Vẽ sprite (sẽ implement sau khi có assets)
            renderer.copy(self.texture,
                          dstrect=(self.rect.x - camera.x,
                                   self.rect.y - camera.y,
                                   self.rect.w, self.rect.h))
        else:
            # Fallback màu
            renderer.fill(self.color,
                          (self.rect.x - camera.x,
                           self.rect.y - camera.y,
                           self.rect.w, self.rect.h))

    def flip_if_needed(self):
        """Xử lý lật sprite theo hướng di chuyển (sau này)"""
        pass

    def collides_with(self, other):
        return self.rect.colliderect(other.rect)