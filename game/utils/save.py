"""
Save/load tiến độ game (level, skill unlock, lives, deaths, high score...)
"""

import json
import os


SAVE_FILE = "save_data.json"


def save_game(progress):
    """Lưu player_progress"""
    try:
        with open(SAVE_FILE, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=4)
        print("Đã lưu tiến độ game")
    except Exception as e:
        print(f"Lỗi lưu game: {e}")


def load_game(default_progress):
    """Load tiến độ, nếu không có thì trả default"""
    if not os.path.exists(SAVE_FILE):
        return default_progress
    
    try:
        with open(SAVE_FILE, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
            # Merge với default để tránh thiếu key
            default_progress.update(loaded)
            print("Đã load tiến độ game")
            return default_progress
    except Exception as e:
        print(f"Lỗi load game: {e}")
        return default_progress