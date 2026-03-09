"""
Quản lý asset: load texture, sound, font với cache
"""

import sdl2
import sdl2.ext
# import sdl2.mixer
import os
from game.constants import ASSETS_ROOT, SPRITES_DIR, SOUNDS_DIR, FONTS_DIR


class AssetManager:
    """Singleton cache cho asset"""
    _textures = {}
    _sounds = {}
    _fonts = {}

    @classmethod
    def load_texture(cls, path, renderer):
        """Load PNG/BMP và cache"""
        full_path = os.path.join(ASSETS_ROOT, path)
        if full_path in cls._textures:
            return cls._textures[full_path]
        
        try:
            surface = sdl2.ext.load_image(full_path)
            texture = sdl2.ext.Texture(renderer, surface)
            cls._textures[full_path] = texture
            return texture
        except Exception as e:
            print(f"Không load được texture: {full_path} - {e}")
            return None

    @classmethod
    def load_sound(cls, path):
        # """Load WAV/OGG và cache"""
        # full_path = os.path.join(ASSETS_ROOT, path)
        # if full_path in cls._sounds:
        #     return cls._sounds[full_path]
        
        # try:
        #     sound = sdl2.mixer.Mix_LoadWAV(full_path.encode())
        #     cls._sounds[full_path] = sound
        #     return sound
        # except Exception as e:
            print(f"Âm thanh bị tắt tạm thời: {path}")
            return None

    @classmethod
    def load_font(cls, path, size=24):
        """Load font TTF"""
        full_path = os.path.join(ASSETS_ROOT, path)
        key = f"{full_path}_{size}"
        if key in cls._fonts:
            return cls._fonts[key]
        
        try:
            font = sdl2.ext.FontManager(full_path, size=size)
            cls._fonts[key] = font
            return font
        except Exception as e:
            print(f"Không load được font: {full_path} - {e}")
            return None

    @classmethod
    def get_cached_texture(cls, path):
        full_path = os.path.join(ASSETS_ROOT, path)
        return cls._textures.get(full_path)


# Hàm tiện ích ngắn gọn
def load_texture(path, renderer):
    return AssetManager.load_texture(path, renderer)

def load_sound(path):
    return AssetManager.load_sound(path)

def load_font(path, size=24):
    return AssetManager.load_font(path, size)

def get_cached_texture(path):
    return AssetManager.get_cached_texture(path)