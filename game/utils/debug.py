import os
import time

class DebugManager:
    def __init__(self, game):
        self.game = game
        self.enabled = False
        self.god_mode = False
        self.fly_mode = False
        self.ghost_mode = False
        self.log_file = "debug_coords.log"

    def toggle_enabled(self):
        self.enabled = not self.enabled
        print(f"[DEBUG] Debug Overlay: {'ON' if self.enabled else 'OFF'}")

    def toggle_god_mode(self, player):
        self.god_mode = not self.god_mode
        player.is_god_mode = self.god_mode
        print(f"[DEBUG] God Mode: {'ON' if self.god_mode else 'OFF'}")

    def toggle_fly_mode(self, player):
        self.fly_mode = not self.fly_mode
        player.is_flying = self.fly_mode
        # Khi tắt bay, reset vận tốc rơi tránh việc bị rơi vèo xuống
        if not self.fly_mode:
            player.vel_y = 0
        print(f"[DEBUG] Fly Mode: {'ON' if self.fly_mode else 'OFF'}")

    def toggle_ghost_mode(self, player):
        self.ghost_mode = not self.ghost_mode
        player.is_ghosting = self.ghost_mode
        print(f"[DEBUG] Ghost Mode: {'ON' if self.ghost_mode else 'OFF'}")

    def log_coords(self, player):
        try:
            timestamp = time.strftime("%H:%M:%S")
            level_name = self.game.player_progress.get("current_level", "unknown")
            log_entry = f"[{timestamp}] Level: {level_name} | Pos: ({int(player.rect.x)}, {int(player.rect.y)})\n"
            
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
            print(f"[DEBUG] Logged: {log_entry.strip()}")
            return True
        except Exception as e:
            print(f"[DEBUG] Error logging coords: {e}")
            return False

    def heal_all(self, player):
        from game.constants import PLAYER_MAX_HP, MAX_LIVES
        player.hp = PLAYER_MAX_HP
        player.mana = 100 # Max mana
        player.lives = MAX_LIVES
        self.game.lives = MAX_LIVES
        print(f"[DEBUG] Healed player to max stats.")

    def next_level(self):
        playing_state = self.game.states.get("playing")
        if playing_state:
            if self.game.game_mode == "single":
                playing_state.complete_level_single()
            else:
                playing_state.complete_level_multi()
            print("[DEBUG] Level skipped.")
