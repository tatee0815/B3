import sdl2
import sdl2.ext
import sdl2.sdlmixer as mixer
import os
from game.constants import ASSETS_ROOT

class AssetManager:
    _textures = {}
    
    # Cấu hình số khung hình cho từng file ảnh lẻ bạn đã gửi
    ANIM_CONFIG = {
        # Player 1
        "idle":     {"file": "sprites/hero_idle.png",   "frames": 8,    "frame_w": 128, "frame_h": 128},
        "run":      {"file": "sprites/hero_run.png",    "frames": 8,    "frame_w": 128, "frame_h": 128},
        "jump":     {"file": "sprites/hero_jump.png",   "frames": 8,    "frame_w": 128, "frame_h": 128},
        "attack":   {"file": "sprites/hero_attack.png", "frames": 9,    "frame_w": 128, "frame_h": 128},
        "skill":    {"file": "sprites/hero_skill.png",  "frames": 7,    "frame_w": 128, "frame_h": 128},
        "death":    {"file": "sprites/hero_death.png",  "frames": 4,    "frame_w": 128, "frame_h": 128},
        "dash":     {"file": "sprites/hero_dash.png",   "frames": 8,    "frame_w": 128, "frame_h": 128},
        "mele":     {"file": "sprites/mele.png",        "frames": 8,    "frame_w": 128, "frame_h": 128}, 
        # Player 2
        "idle2":     {"file": "sprites/hero_idle2.png",   "frames": 7,    "frame_w": 128, "frame_h": 128},
        "run2":      {"file": "sprites/hero_run2.png",    "frames": 8,    "frame_w": 128, "frame_h": 128},
        "jump2":     {"file": "sprites/hero_jump2.png",   "frames": 8,    "frame_w": 128, "frame_h": 128},
        "attack2":   {"file": "sprites/hero_attack2.png", "frames": 10,   "frame_w": 128, "frame_h": 128},
        "skill2":    {"file": "sprites/hero_skill2.png",  "frames": 7,    "frame_w": 128, "frame_h": 128},
        "death2":    {"file": "sprites/hero_death2.png",  "frames": 5,    "frame_w": 128, "frame_h": 128},
        "dash2":     {"file": "sprites/hero_dash2.png",   "frames": 7,    "frame_w": 128, "frame_h": 128},
        "mele":      {"file": "sprites/mele.png",         "frames": 8,    "frame_w": 128, "frame_h": 128}, 
        # Goblin
        "goblin_idle":   {"file": "enemies/Scorpio_idle.png",   "frames": 4},
        "goblin_walk":   {"file": "enemies/Scorpio_walk.png",   "frames": 4},
        "goblin_death":  {"file": "enemies/Scorpio_death.png",  "frames": 4},
        # Skeleton
        "skeleton_idle":   {"file": "enemies/Mummy_idle.png",   "frames": 4},
        "skeleton_walk":   {"file": "enemies/Mummy_walk.png",   "frames": 6},
        "skeleton_attack": {"file": "enemies/Mummy_attack.png", "frames": 6},
        "skeleton_death":  {"file": "enemies/Mummy_death.png",  "frames": 6},
        # Firebat
        "firebat_idle":     {"file": "enemies/Vulture_idle.png",    "frames": 4},
        "firebat_walk":     {"file": "enemies/Vulture_walk.png",    "frames": 4},
        "firebat_attack":   {"file": "enemies/Vulture_attack.png",  "frames": 2},
        "firebat_death":    {"file": "enemies/Vulture_death.png",   "frames": 4},
        # Boss 
        "boss_idle":        {"file": "boss/idle_1.png",     "frames": 5,    "frame_w": 128, "frame_h": 128},
        "boss_attack1":     {"file": "boss/attack_1_1.png", "frames": 6,    "frame_w": 128, "frame_h": 128},
        "boss_attack2":     {"file": "boss/attack_2_1.png", "frames": 3,    "frame_w": 128, "frame_h": 128},
        "boss_attack3":     {"file": "boss/attack_3_1.png", "frames": 6,    "frame_w": 128, "frame_h": 128},
        "boss_fireball":    {"file": "boss/fire_ball_1.png","frames": 4,    "frame_w": 48,  "frame_h": 48},
        "boss_transform":   {"file": "boss/death_1.png",    "frames": 8,    "frame_w": 128, "frame_h": 128},
        #Boss p2
        "boss_idle_p2":     {"file": "boss/idle.png",       "frames": 6,    "frame_w": 128, "frame_h": 128},
        "boss_attack1_p2":  {"file": "boss/attack_1.png",   "frames": 10,   "frame_w": 128, "frame_h": 128},
        "boss_attack2_p2":  {"file": "boss/attack_2.png",   "frames": 10,   "frame_w": 128, "frame_h": 128},
        "boss_attack3_p2":  {"file": "boss/attack_3.png",   "frames": 7,    "frame_w": 128, "frame_h": 128},
        "boss_fireball_p2": {"file": "boss/fire_ball.png",  "frames": 14,   "frame_w": 64,  "frame_h": 64},
        "boss_death":       {"file": "boss/death.png",      "frames": 10,   "frame_w": 128, "frame_h": 128},
        "boss_head":        {"file": "boss/head.png",       "frames": 8,    "frame_w": 72,  "frame_h": 72},
        # Princess
        "princess_idle":        {"file": "sprites/princess_idle.png",       "frames": 9, "frame_w": 128, "frame_h": 128},
        "princess_special":     {"file": "sprites/princess_special.png",    "frames": 8, "frame_w": 128, "frame_h": 128},
        "princess_protection":  {"file": "sprites/princess_protection.png", "frames": 4, "frame_w": 128, "frame_h": 128},
        "princess_walk":        {"file": "sprites/princess_walk.png",       "frames": 12, "frame_w": 128, "frame_h": 128},
    }

    BACKGROUND_ASSETS = {
        # map 1
        "bg_1": "backgrounds/sky_mountain_1.png",          
        "mid_1": "backgrounds/shadow_village_1.png", 
        "end_1": "backgrounds/grass_gate_1.png",
        # map 2
        "bg_2": "backgrounds/sky_2.png",          
        "mid_2": "backgrounds/cloud_ground_2.png", 
        "end_2": "backgrounds/tree_2.png",
        # map 3
        "bg_3":  "backgrounds/sky_3.png",  
        "mid_3": "backgrounds/mountain_cloud_3.png",
        "end_3": "backgrounds/rock_3.png",
        # boss
        "boss_bg": "backgrounds/boss_bg.png"
    }

    @classmethod
    def load_all_player_sprites(cls, renderer):
        """Nạp tất cả các trạng thái vào cache"""
        for state, config in cls.ANIM_CONFIG.items():
            cls.load_texture(config["file"], renderer)

    @classmethod
    def load_texture(cls, path, renderer):
        full_path = os.path.join(ASSETS_ROOT, path)
        if full_path in cls._textures:
            return cls._textures[full_path]
        
        try:
            surface = sdl2.ext.load_image(full_path)
            # Dùng hàm gốc để tránh lỗi AttributeError đã gặp
            texture = sdl2.SDL_CreateTextureFromSurface(renderer, surface)
            sdl2.SDL_FreeSurface(surface)
            cls._textures[full_path] = texture
            return texture
        except Exception as e:
            print(f"Lỗi nạp {full_path}: {e}")
            return None

    @classmethod
    def get_anim_info(cls, state, frame_index):
        """Bây giờ hàm này sẽ tìm được cả 'idle' lẫn 'skeleton_idle'"""
        config = cls.ANIM_CONFIG.get(state)
        if not config:
            return None, None
            
        texture = cls._textures.get(os.path.join(ASSETS_ROOT, config["file"]))
        if not texture:
            return None, None
        
        frame_w = config.get("frame_w", 48)   # mặc định 48 cho các entity cũ
        frame_h = config.get("frame_h", 48)

        actual_frame = int(frame_index) % config["frames"]
        srcrect = sdl2.SDL_Rect(actual_frame * frame_w, 0, frame_w, frame_h)
        
        return texture, srcrect
    
class AudioManager:
    _bgm = None
    _sfx = {}
    _music_volume = 70
    _sfx_volume = 85

    @classmethod
    def init(cls):
        # Khởi tạo SDL_mixer
        if mixer.Mix_OpenAudio(44100, mixer.MIX_DEFAULT_FORMAT, 2, 2048) < 0:
            print(f"Mixer Error: {mixer.Mix_GetError()}")
            return
        
        # Nạp nhạc nền
        bgm_path = os.path.join(ASSETS_ROOT, "audio/bga.mp3")
        cls._bgm = mixer.Mix_LoadMUS(bgm_path.encode())
        
        # Nạp SFX
        cls._load_sfx("choice", "audio/choice.mp3")
        cls._load_sfx("select", "audio/select.mp3")
        cls._load_sfx("win", "audio/win.mp3")
        cls._load_sfx("game_over", "audio/game_over.mp3")

    @classmethod
    def _load_sfx(cls, name, path):
        full_path = os.path.join(ASSETS_ROOT, path)
        chunk = mixer.Mix_LoadWAV(full_path.encode())
        if chunk: cls._sfx[name] = chunk

    @classmethod
    def play_bgm(cls):
        if cls._bgm:
            mixer.Mix_PlayMusic(cls._bgm, -1)
            cls.apply_volumes()

    @classmethod
    def stop_bgm(cls):
        mixer.Mix_HaltMusic()

    @classmethod
    def play_sfx(cls, name):
        if name in cls._sfx:
            mixer.Mix_HaltChannel(-1)
            mixer.Mix_PlayChannel(-1, cls._sfx[name], 0)

    @classmethod
    def set_volumes(cls, music_vol, sfx_vol):
        cls._music_volume = music_vol
        cls._sfx_volume = sfx_vol
        cls.apply_volumes()

    @classmethod
    def apply_volumes(cls):
        # Chuyển đổi từ thang 0-100 sang 0-128 của SDL_mixer
        mixer.Mix_VolumeMusic(int(cls._music_volume * 1.28))
        for chunk in cls._sfx.values():
            mixer.Mix_VolumeChunk(chunk, int(cls._sfx_volume * 1.28))