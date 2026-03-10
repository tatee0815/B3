"""
Camera follow player (smooth scrolling)
"""

from game.constants import SCREEN_WIDTH, SCREEN_HEIGHT


class Camera:
    def __init__(self,game, width=SCREEN_WIDTH, height=SCREEN_HEIGHT):
        self.game = game
        self.x = 0
        self.y = 0
        self.width = width
        self.height = height
        self.smooth_factor = 0.1  # 0.0 = instant, 1.0 = rất chậm

    def update(self, player):
        """Theo dõi player (tính toán tâm thủ công cho SDL_Rect)"""
        # Tính toán center_x và center_y từ rect của player
        p_center_x = player.rect.x + (player.rect.w // 2)
        p_center_y = player.rect.y + (player.rect.h // 2)
        
        target_x = p_center_x - self.width // 2
        target_y = p_center_y - self.height // 2
        
        # Giới hạn camera trong map
        # Truy cập level thông qua self.game đã lưu
        playing_state = self.game.states.get("playing")
        if playing_state and playing_state.level:
            level = playing_state.level
            # Giới hạn không cho camera trượt ra ngoài 0 hoặc quá chiều rộng map
            target_x = max(0, min(target_x, level.pixel_width - self.width))
            target_y = max(0, min(target_y, level.pixel_height - self.height))
        
        # Di chuyển mượt mà (Lerp)
        self.x += (target_x - self.x) * self.smooth_factor
        self.y += (target_y - self.y) * self.smooth_factor

    def reset(self, start_x=0, start_y=0):
        self.x = start_x
        self.y = start_y