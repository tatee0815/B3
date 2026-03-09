"""
Hàm tiện ích kiểm tra và xử lý va chạm AABB (Axis-Aligned Bounding Box)
"""

def check_collision(rect1, rect2):
    """Kiểm tra hai rect có chồng chéo không"""
    return (rect1.x < rect2.x + rect2.w and
            rect1.x + rect1.w > rect2.x and
            rect1.y < rect2.y + rect2.h and
            rect1.y + rect1.h > rect2.y)


def resolve_collision(player_rect, other_rect, vel_x, vel_y):
    """
    Resolve va chạm đơn giản: đẩy player ra khỏi object
    Trả về vel_x, vel_y đã điều chỉnh
    """
    # Tính overlap
    overlap_left = (player_rect.x + player_rect.w) - other_rect.x
    overlap_right = other_rect.x + other_rect.w - player_rect.x
    overlap_top = (player_rect.y + player_rect.h) - other_rect.y
    overlap_bottom = other_rect.y + other_rect.h - player_rect.y

    # Tìm hướng overlap nhỏ nhất
    overlaps = [overlap_left, overlap_right, overlap_top, overlap_bottom]
    min_overlap = min(o for o in overlaps if o > 0)

    if min_overlap == overlap_left:
        player_rect.x -= min_overlap
        vel_x = 0
    elif min_overlap == overlap_right:
        player_rect.x += min_overlap
        vel_x = 0
    elif min_overlap == overlap_top:
        player_rect.y -= min_overlap
        vel_y = 0
    elif min_overlap == overlap_bottom:
        player_rect.y += min_overlap
        vel_y = 0

    return vel_x, vel_y