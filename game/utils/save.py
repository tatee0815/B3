"""
Save/load tiến độ game (level, skill unlock, lives, deaths, high score...)
"""

import json
import os

def save_game(progress, filename="save_sp.json"):
    """Lưu player_progress"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Lỗi lưu game ({filename}): {e}")


def load_game(default_progress, filename="save_sp.json"):
    """Load tiến độ, nếu không có thì trả default"""
    if not os.path.exists(filename):
        return default_progress
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
            new_progress = default_progress.copy()
            new_progress.update(loaded)
            return new_progress
    except Exception as e:
        print(f"Lỗi load game ({filename}): {e}")
        return default_progress
    
def get_save_value(filename, key, default=None):
    """Lấy một giá trị cụ thể (như port) từ file save mà không cần load toàn bộ game"""
    if not os.path.exists(filename):
        return default
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get(key, default)
    except:
        return default