import sdl2
from game.constants import COLORS
from game.entities.base import Entity

class Button(Entity):
    def __init__(self, game, x, y, gate_id, w=32, h=16, revert=False):
        super().__init__(game, x, y, w, h)
        self.gate_id = gate_id
        self.revert = revert
        self.pressed = False
        self.color = COLORS["red"] if self.revert else COLORS["yellow"]
        self.z_index = 2

    def on_interact(self, player):
        if not self.pressed:
            self.pressed = True
            
            # Kích hoạt gate tương ứng
            level = self.game.states["playing"].level
            
            # Lưu state của button và gate
            level_name = level.name
            btn_key = f"{level_name}_{self.rect.x}_{self.rect.y}"
            
            progress = self.game.player_progress
            if "pressed_buttons" not in progress:
                progress["pressed_buttons"] = []
            if btn_key not in progress["pressed_buttons"]:
                progress["pressed_buttons"].append(btn_key)
                
            if "gate_states" not in progress:
                progress["gate_states"] = {}
            if level_name not in progress["gate_states"]:
                progress["gate_states"][level_name] = {}
            
            if self.revert:
                progress["gate_states"][level_name][self.gate_id] = "closed"
            else:
                progress["gate_states"][level_name][self.gate_id] = "open"
                
            for gate in level.gates:
                if gate.gate_id == self.gate_id:
                    if self.revert:
                        gate.close()
                    else:
                        gate.open()
            
            self.color = COLORS["gray"] # Xám đi sau khi bấm
            
            # Đồng bộ qua mạng nếu có player (nghĩa là bấm trực tiếp, không phải qua mạng)
            if player and self.game.game_mode == "multi":
                self.game.network.send_data({
                    "type": "button_pressed",
                    "btn_id": f"{self.rect.x}_{self.rect.y}"
                })

    def update(self, delta_time, level):
        # Kiểm tra va chạm với cả 2 player (Local + Remote) để tự động kích hoạt
        playing_state = level.game.states["playing"]
        players = [playing_state.local_player]
        if hasattr(playing_state, "remote_player") and playing_state.remote_player:
            players.append(playing_state.remote_player)
            
        for player in players:
            # Chỉ local player mới kích hoạt interaction chủ động
            if player and not getattr(player, "is_remote", False) and not self.pressed and self.collides_with(player):
                self.on_interact(player)
                break

    def render(self, renderer, camera):
        draw_rect = sdl2.SDL_Rect(
            int(self.rect.x - camera.x),
            int(self.rect.y - camera.y),
            self.rect.w, self.rect.h
        )
        sdl2.SDL_SetRenderDrawColor(renderer, *self.color, 255)
        sdl2.SDL_RenderFillRect(renderer, draw_rect)