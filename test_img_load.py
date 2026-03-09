import sdl2
from sdl2 import sdlimage # Import trực tiếp module xử lý ảnh

print("Nạp thư viện OK")

# Khởi tạo (Dùng sdlimage thay vì sdl2.image)
flags = sdlimage.IMG_INIT_PNG
if (sdlimage.IMG_Init(flags) & flags) != flags:
    print("IMG_Init thất bại:", sdlimage.IMG_GetError().decode('utf-8'))
else:
    print("IMG_Init OK")

# Load ảnh
surface = sdlimage.IMG_Load(b"assets/backgrounds/menu_bg.png")
if surface:
    print("Load PNG thành công!")
    sdl2.SDL_FreeSurface(surface)
else:
    print("Lỗi load:", sdlimage.IMG_GetError().decode('utf-8'))

sdlimage.IMG_Quit()