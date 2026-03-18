"""
main.py - Điểm khởi động chính của game Hiệp Sĩ Kiếm Huyền Thoại
- Khởi tạo SDL2
- Tạo cửa sổ game
- Chạy vòng lặp chính từ class Game
- Cleanup khi thoát
"""

import sys
import sdl2

# Import từ package game (đã được định nghĩa trong game/__init__.py)
from game import GAME_TITLE, SCREEN_WIDTH, SCREEN_HEIGHT, KnightQuestGame
from game.constants import FPS_TARGET


def main():
    """
    Hàm chính: khởi tạo và chạy game
    """

    # 1. Khởi tạo SDL2 core
    ret = sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO)
    if ret < 0:
        print("LỖI: SDL_Init thất bại!")
        print("Mã lỗi:", ret)
        err = sdl2.SDL_GetError()
        print("Chi tiết SDL:", err.decode('utf-8') if err else "Không có lỗi")
        sys.exit(1)

    # print("SDL2 init thành công (low-level)!")

    # Tạo window thủ công (không dùng sdl2.ext.Window)
    window = sdl2.SDL_CreateWindow(
        GAME_TITLE.encode('utf-8'),
        sdl2.SDL_WINDOWPOS_CENTERED,
        sdl2.SDL_WINDOWPOS_CENTERED,
        SCREEN_WIDTH, SCREEN_HEIGHT,
        sdl2.SDL_WINDOW_SHOWN | sdl2.SDL_WINDOW_ALLOW_HIGHDPI # ← thêm dòng này
    )

    if not window:
        print("Không tạo được window!")
        print("Lỗi SDL:", sdl2.SDL_GetError().decode('utf-8'))
        sdl2.SDL_Quit()
        sys.exit(1)

    print("Cửa sổ game đã mở!")

    # Tạo renderer (thay vì window.get_renderer())
    renderer = sdl2.SDL_CreateRenderer(
        window, 
        -1, 
        sdl2.SDL_RENDERER_ACCELERATED | sdl2.SDL_RENDERER_PRESENTVSYNC
    )
    if not renderer:
        print("Không tạo được renderer!")
        print("Lỗi SDL:", sdl2.SDL_GetError().decode('utf-8'))
        sdl2.SDL_DestroyWindow(window)
        sdl2.SDL_Quit()
        sys.exit(1)

    # 3. Tạo và chạy instance Game chính
    game = KnightQuestGame(window, renderer)
    
    # Chạy game loop (update, render, event)
    game.run()

    # 4. Cleanup khi thoát
    sdl2.SDL_DestroyRenderer(renderer)
    sdl2.SDL_DestroyWindow(window)
    sdl2.SDL_Quit()

    return 0


if __name__ == "__main__":
    sys.exit(main())