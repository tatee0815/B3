import sdl2
from game.constants import GRAVITY

class Entity:
    def __init__(self, game, x=0, y=0, w=12, h=32):
        self.game = game
        self.renderer = game.renderer

        # Tạo SDL_Rect (struct C, dùng cho collision và render)
        self.rect = sdl2.SDL_Rect(int(x), int(y), int(w), int(h))
        self.pos_x = float(x) # Biến lưu tọa độ thực
        self.pos_y = float(y)
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.z_index = 1
        
        self.on_ground = False
        self.facing_right = True

        self.texture = None
        self.color = (255, 255, 255, 255)  # fallback

        self.alive = True  # để đánh dấu đã chết hay chưa, tránh update/render sau khi chết

    def update(self, delta_time, level=None):
        if level:
            # 1. Áp dụng trọng lực
            gravity_value = getattr(level, 'gravity', GRAVITY)
            self.vel_y += gravity_value * delta_time * 60
            if self.vel_y > 12: self.vel_y = 12 # Giới hạn tốc độ rơi

            # 2. Cập nhật tọa độ THỰC
            self.pos_x += self.vel_x * delta_time * 60
            self.pos_y += self.vel_y * delta_time * 60
            
            # 3. Ép kiểu vào Rect để SDL render và tính va chạm
            self.rect.x = int(round(self.pos_x))
            self.rect.y = int(round(self.pos_y))

    def render(self, renderer, camera):
        if self.texture:
            dst_rect = sdl2.SDL_Rect(
                int(self.rect.x - camera.x),
                int(self.rect.y - camera.y),
                self.rect.w, self.rect.h
            )
            sdl2.SDL_RenderCopy(renderer, self.texture, None, dst_rect)
        else:
            # Fallback vuông màu
            sdl2.SDL_SetRenderDrawColor(renderer, *self.color)
            dst_rect = sdl2.SDL_Rect(
                int(self.rect.x - camera.x),
                int(self.rect.y - camera.y),
                self.rect.w, self.rect.h
            )
            sdl2.SDL_RenderFillRect(renderer, dst_rect)

    def collides_with(self, other):
        return (self.rect.x < other.rect.x + other.rect.w and
                self.rect.x + self.rect.w > other.rect.x and
                self.rect.y < other.rect.y + other.rect.h and
                self.rect.y + self.rect.h > other.rect.y)
    
    def kill(self):
        self.alive = False