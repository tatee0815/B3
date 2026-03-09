"""
main.py - Entry point chính của game Hiệp Sĩ Kiếm Huyền Thoại
Khởi tạo window, chạy Game loop và xử lý cleanup
"""

import sys
import sdl2
import sdl2.ext

from game import GAME_TITLE, SCREEN_WIDTH, SCREEN_HEIGHT, KnightQuestGame
from game.constants import FPS_TARGET


def main():
    # Khởi tạo SDL2
 # Trong hàm main(), thay phần init bằng:
    ret = sdl2.ext.init()
    if ret != 0:
        print("SDL2 init thất bại! Mã lỗi:", ret)
        print("Lỗi chi tiết từ SDL:", sdl2.SDL_GetError().decode('utf-8') if sdl2.SDL_GetError() else "Không có lỗi chi tiết")
        return 1
    # # Khởi tạo mixer cho âm thanh (nếu dùng sound)
    # if sdl2.mixer.Mix_OpenAudio(44100, sdl2.mixer.MIX_DEFAULT_FORMAT, 2, 2048) != 0:
    #     print("Không khởi tạo được mixer âm thanh:", sdl2.mixer.Mix_GetError())
    #     # Không return vì âm thanh không bắt buộc

    # Tạo window
    flags = sdl2.SDL_WINDOW_SHOWN
    if sdl2.SDL_GetCurrentDisplayMode(0).refresh_rate > 0:
        flags |= sdl2.SDL_WINDOW_ALLOW_HIGHDPI  # hỗ trợ retina/high dpi nếu có

    window = sdl2.ext.Window(
        GAME_TITLE,
        size=(SCREEN_WIDTH, SCREEN_HEIGHT),
        flags=flags
    )
    window.show()

    # Tạo instance Game chính
    game = KnightQuestGame(window)

    # Vòng lặp game chính
    print("Game đang chạy... Nhấn ESC để tạm dừng, ESC lại để tiếp tục.")
    game.run()

    # Cleanup khi thoát
    print("Game đã thoát.")
    
    # # Giải phóng mixer nếu dùng
    # sdl2.mixer.Mix_CloseAudio()
    
    sdl2.ext.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())