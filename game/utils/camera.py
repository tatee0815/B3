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

        self.zoom_factor = 1.15

    def update(self, player):
        # Tính toán tâm Player
        p_center_x = player.rect.x + (player.rect.w // 2)
        p_center_y = player.rect.y + (player.rect.h // 2)
        
        # Vị trí lý tưởng để đưa player vào giữa màn hình
        target_x = p_center_x - self.width // 2
        target_y = p_center_y - self.height // 2
        
        # Sync viewport size to actual logical window
        self.width = self.game.logical_width
        self.height = self.game.logical_height

        playing_state = self.game.states.get("playing")
        if playing_state and playing_state.level:
            lvl = playing_state.level
            
            # GIỚI HẠN TRỤC X
            max_x = max(0, lvl.pixel_width - self.width)
            target_x = max(0, min(target_x, max_x))
            
            # GIỚI HẠN TRỤC Y
            max_y = max(0, lvl.pixel_height - self.height)
            target_y = max(0, min(target_y, max_y))

        if abs(target_x - self.x) > 400 or abs(target_y - self.y) > 400:
            self.x = float(target_x)
            self.y = float(target_y)
        else:
            # Tính toán mức di chuyển dự định
            move_x = (target_x - self.x) * self.smooth_factor
            move_y = (target_y - self.y) * self.smooth_factor

            # Giới hạn mức dịch chuyển tối đa mỗi frame
            self.x += max(-60, min(60, move_x))
            self.y += max(-60, min(60, move_y))
            
        # CLAMP LẦN CUỐI ĐỂ ĐẢM BẢO KHÔNG TRÔI BIÊN
        if playing_state and playing_state.level:
            lvl = playing_state.level
            max_x = max(0, lvl.pixel_width - self.width)
            max_y = max(0, lvl.pixel_height - self.height)
            self.x = max(0.0, min(float(self.x), float(max_x)))
            self.y = max(0.0, min(float(self.y), float(max_y)))

    def reset(self, player=None):
        """Nếu truyền player vào, camera sẽ snap thẳng đến vị trí player mà không bị trượt (smooth)"""
        if player:
            p_center_x = player.rect.x + (player.rect.w // 2)
            p_center_y = player.rect.y + (player.rect.h // 2)
            
            target_x = p_center_x - self.width // 2
            target_y = p_center_y - self.height // 2
            
            playing_state = self.game.states.get("playing")
            if playing_state and playing_state.level:
                lvl = playing_state.level
                max_x = max(0, lvl.pixel_width - self.width)
                max_y = max(0, lvl.pixel_height - self.height)
                target_x = max(0, min(target_x, max_x))
                target_y = max(0, min(target_y, max_y))
            
            self.x = float(target_x)
            self.y = float(target_y)
        else:
            self.x = 0
            self.y = 0