import sdl2

class Entity:
    def __init__(self, game, x=0, y=0, w=32, h=32):
        self.game = game
        self.renderer = game.renderer

        # Tạo SDL_Rect (struct C, dùng cho collision và render)
        self.rect = sdl2.SDL_Rect(x, y, w, h)

        self.vel_x = 0.0
        self.vel_y = 0.0
        self.on_ground = False
        self.facing_right = True

        self.texture = None
        self.color = (255, 255, 255, 255)  # fallback

    def update(self, delta_time, level=None):
        if level:
            self.vel_y += level.gravity * delta_time * 60

            self.rect.x += int(self.vel_x * delta_time * 60)
            self.rect.y += int(self.vel_y * delta_time * 60)

            if self.vel_y > 12:
                self.vel_y = 12

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