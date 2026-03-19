# HIỆP SĨ SKIBIDI HUYỀN THOẠI

Game phiêu lưu hành động 2D viết bằng Python và SDL2.

## Yêu cầu hệ thống

- Windows 10/11 (hoặc Linux/macOS với SDL2 tương thích)
- Python 3.8 – 3.11 (khuyến nghị 3.10)
- Các thư viện Python (xem `requirements.txt`)

## Cài đặt và chạy game

### 1. Cài đặt Python và tạo môi trường ảo (khuyến khích)

```bash
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate   # Linux/macOS

# Cài đặt
pip install -r requirements.txt

# Sau khi cài pysdl2-dll, các file DLL của SDL2 sẽ nằm trong thư mục venv/Lib/site-packages/pysdl2_dll/dll/. 
# Bạn cần copy toàn bộ các file .dll từ đó vào thư mục gốc của dự án (nơi chứa file main.py). 
# Các file quan trọng bao gồm:

SDL2.dll

SDL2_image.dll

SDL2_ttf.dll

SDL2_mixer.dll

libpng16-16.dll

libtiff-5.dll

# Chạy
python main.py