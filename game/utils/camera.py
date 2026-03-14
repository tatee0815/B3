# game/utils/camera.py
from game.constants import SCREEN_WIDTH, SCREEN_HEIGHT

class Camera:
    def __init__(self, game, width=SCREEN_WIDTH, height=SCREEN_HEIGHT):
        self.game = game
        self.x = 0
        self.y = 0
        self.width = width
        self.height = height
        self.smooth_factor = 0.1 

    def update(self, player):
        # Tính toán tâm Player
        p_center_x = player.rect.x + (player.rect.w // 2)
        p_center_y = player.rect.y + (player.rect.h // 2)
        
        # Vị trí lý tưởng để đưa player vào giữa màn hình
        target_x = p_center_x - self.width // 2
        target_y = p_center_y - self.height // 2
        
        playing_state = self.game.states.get("playing")
        if playing_state and playing_state.level:
            lvl = playing_state.level
            
            # GIỚI HẠN TRỤC X
            max_x = max(0, lvl.pixel_width - self.width)
            target_x = max(0, min(target_x, max_x))
            
            # GIỚI HẠN TRỤC Y (Quan trọng để leo trèo)
            # Nếu map cao hơn màn hình, max_y sẽ > 0
            max_y = max(0, lvl.pixel_height - self.height)
            target_y = max(0, min(target_y, max_y))

        if abs(target_x - self.x) > 400 or abs(target_y - self.y) > 400:
            self.x = float(target_x)
            self.y = float(target_y)
        else:
            # Tính toán mức di chuyển dự định
            move_x = (target_x - self.x) * self.smooth_factor
            move_y = (target_y - self.y) * self.smooth_factor

            # Giới hạn mức dịch chuyển tối đa mỗi frame để tránh giật hình (ví dụ: 60px)
            self.x += max(-60, min(60, move_x))
            self.y += max(-60, min(60, move_y))

    def reset(self, start_x=0, start_y=0):
        self.x = start_x
        self.y = start_y