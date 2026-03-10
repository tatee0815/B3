"""
Hằng số toàn cục cho game Hiệp Sĩ Kiếm Huyền Thoại
Dễ dàng chỉnh sửa ở đây mà không cần tìm kiếm khắp nơi
"""

import sdl2

# -------------------------------
# Cấu hình màn hình & hiệu suất
# -------------------------------
SCREEN_WIDTH          = 1280
SCREEN_HEIGHT         = 720
FPS_TARGET            = 60
FPS_FRAME_TIME_MS     = 1000 // FPS_TARGET   # ~16ms

# Có thể bật fullscreen sau này
FULLSCREEN            = False
WINDOW_RESIZABLE      = True

# -------------------------------
# Vật lý & chuyển động
# -------------------------------
GRAVITY               = 0.65          # gia tốc rơi (pixel/frame²)
MAX_FALL_SPEED        = 12.0
PLAYER_SPEED          = 3.8           # pixel/frame khi chạy
PLAYER_ACCELERATION   = 0.8
PLAYER_DECELERATION   = 0.7

JUMP_FORCE            = -13.5         # vận tốc nhảy ban đầu (âm = lên)
DOUBLE_JUMP_FORCE     = -11.0
JUMP_BUFFER_FRAMES    = 6             # cho phép nhảy ngay trước khi chạm đất
COYOTE_TIME_FRAMES    = 8             # cho phép nhảy ngay sau khi rơi khỏi cạnh

# -------------------------------
# Hệ thống combat & tài nguyên
# -------------------------------
PLAYER_MAX_HP         = 3             # số tim
PLAYER_START_HP       = 3

MANA_MAX              = 100
MANA_PER_KILL         = 10            # mana nhận khi giết quái
MANA_PER_BOTTLE       = 25            # mana từ bình mana
MANA_REGEN_PER_SECOND = 8             # regen thụ động (nếu muốn thêm sau)

SKILL_A_COST          = 35            # mana tiêu tốn cho skill A (bắn xa)
SKILL_A_COOLDOWN      = 0.4           # giây
SKILL_A_DAMAGE        = 25            # level 1
SKILL_A_UPGRADE_DAMAGE= 45            # sau level 2

MELEE_DAMAGE          = 20            # chém kiếm cơ bản
MELEE_UPGRADE_DAMAGE  = 35            # sau khi nhận "Diệt Hồn Kiếm"

# -------------------------------
# Tile & map
# -------------------------------
TILE_SIZE             = 32            # pixel
TILEMAP_COLLISION_ID  = 1             # id tile solid trong tileset

# -------------------------------
# Phím điều khiển mặc định
# -------------------------------
KEY_BINDINGS_DEFAULT = {
    "left":     sdl2.SDL_SCANCODE_LEFT,  # Đổi từ SDLK sang SDL_SCANCODE
    "right":    sdl2.SDL_SCANCODE_RIGHT,
    "jump":     sdl2.SDL_SCANCODE_Z,
    "attack":   sdl2.SDL_SCANCODE_X,
    "skill":    sdl2.SDL_SCANCODE_A,
    "dash":     sdl2.SDL_SCANCODE_C,
    "pause":    sdl2.SDL_SCANCODE_P,
    "interact": sdl2.SDL_SCANCODE_E,
}
# Cho phép người chơi tùy chỉnh sau này (lưu trong settings.json)

# -------------------------------
# Màu sắc (RGBA)
# -------------------------------
COLORS = {
    "black":        (0, 0, 0, 255),
    "white":        (255, 255, 255, 255),
    "red":          (220, 40, 40, 255),
    "green":        (60, 220, 60, 255),
    "blue":         (60, 100, 220, 255),
    "yellow":       (240, 220, 60, 255),
    "purple":       (180, 60, 220, 255),
    "orange":       (255, 140, 0, 255),
    "gray":         (100, 100, 100, 255),
    "dark_gray":    (40, 40, 40, 255),
    "bg_forest":    (80, 140, 60, 255),     # nền rừng
    "bg_lava":      (40, 20, 10, 255),      # nền hang lửa
    "mana_bar":     (80, 180, 255, 220),
    "mana_empty":   (40, 60, 100, 180),
}

# -------------------------------
# Đường dẫn asset (tương đối từ root dự án)
# -------------------------------
ASSETS_ROOT = "assets/"

SPRITES_DIR     = ASSETS_ROOT + "sprites/"
TILES_DIR       = ASSETS_ROOT + "tiles/"
BG_DIR          = ASSETS_ROOT + "backgrounds/"
SOUNDS_DIR      = ASSETS_ROOT + "sounds/"
FONTS_DIR       = ASSETS_ROOT + "fonts/"

# Tên file phổ biến (có thể thay đổi sau)
PLAYER_SPRITE_SHEET = SPRITES_DIR + "player/knight_sheet.png"
FONT_PIXEL          = FONTS_DIR + "pixel_font.ttf"

# -------------------------------
# Các giá trị khác
# -------------------------------
COIN_FOR_EXTRA_LIFE   = 100
MAX_EXTRA_LIVES       = 3

DEFAULT_VOLUME_MUSIC  = 0.7
DEFAULT_VOLUME_SFX    = 0.9

GAME_DURATION_WARNING = 600           # giây (10 phút) - có thể hiển thị cảnh báo gần hết giờ

# -------------------------------
# Hệ thống mạng & chết
# -------------------------------
MAX_LIVES              = 5
PLAYER_START_LIVES     = 5
PLAYER_START_DEATHS    = 0

# Khi hết mạng sẽ reset lives và respawn tại start của level
RESPAWN_AT_LEVEL_START_WHEN_NO_LIVES = True