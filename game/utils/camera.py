"""
Camera follow player (smooth scrolling)
"""

from game.constants import SCREEN_WIDTH, SCREEN_HEIGHT


class Camera:
    def __init__(self, width=SCREEN_WIDTH, height=SCREEN_HEIGHT):
        self.x = 0
        self.y = 0
        self.width = width
        self.height = height
        self.smooth_factor = 0.1  # 0.0 = instant, 1.0 = rất chậm

    def update(self, player):
        """Theo dõi player (center player trong màn hình)"""
        target_x = player.rect.centerx - self.width // 2
        target_y = player.rect.centery - self.height // 2
        
        # Giới hạn camera trong map (giả sử biết kích thước level)
        level = player.game.states["playing"].level
        if level:
            target_x = max(0, min(target_x, level.pixel_width - self.width))
            target_y = max(0, min(target_y, level.pixel_height - self.height))
        
        # Smooth follow
        self.x += (target_x - self.x) * self.smooth_factor
        self.y += (target_y - self.y) * self.smooth_factor

    def reset(self):
        self.x = 0
        self.y = 0