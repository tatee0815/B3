import sdl2
from game.entities.projectile import Projectile
from game.level.level import Level
from game.objects.portal import EndPortal

class PlayingState:
    def __init__(self, game):
        self.game = game
        self.name = "playing"
        self.level = Level(self.game)
        self.is_initialized = False
        self.local_player = None
        self.remote_player = None
        self.sync_timer = 0.0
        self.SYNC_INTERVAL = 0.016 # Đồng bộ 60 lần/giây (Tương đương 60 FPS)
        self.local_at_portal = False
        self.remote_at_portal = False
        self.last_local_portal_state = False
        self.last_remote_portal_state = False
        self.multi_completed = False  # tránh gọi nhiều lần

    @property
    def player(self):
        return self.game.player

    def on_enter(self, **kwargs):
        force_reset = kwargs.get("reset", False)
        menu_continue = kwargs.get("menu_continue", False)
        from_intro = kwargs.get("from_intro", False)

        just_loaded_map = False
        self.multi_completed = False

        # --- BƯỚC 1: NẠP DỮ LIỆU ---
        if not self.is_initialized or force_reset or from_intro:
            if force_reset or from_intro:
                self.game.reset_progress()

            level_name = self.game.player_progress["current_level"]
            if self.level.load_from_json(level_name):
                # Always spawn entities so both host and client have the map populated
                self.level.spawn_all_entities(self.game)
                self.is_initialized = True
                just_loaded_map = True

        # --- ĐỒNG BỘ LEVEL CHO MULTIPLAYER ---
        if self.game.game_mode == "multi":
            from game.entities.player import Player
            from game.entities.princess import Princess
            
            if self.game.network.is_host:
                # 1. HOST LÀ MÁY CHỦ -> LUÔN LÀ KNIGHT
                # Đảm bảo local_player là class Player gốc
                if not type(self.game.player) is Player:
                    self.game.player = Player(self.game)
                self.local_player = self.game.player
                self.local_player.role = "knight"
                
                # Remote player (người chơi bên kia) là Princess
                self.remote_player = Princess(self.game)
                
                self.remote_player.is_remote = True
                self.remote_player.target_x = float(self.remote_player.rect.x)
                self.remote_player.target_y = float(self.remote_player.rect.y)
            else:
                # 2. CLIENT LÀ MÁY KHÁCH -> LUÔN LÀ PRINCESS
                # Đảm bảo local_player là class Princess với bộ skill riêng
                if not isinstance(self.game.player, Princess):
                    self.game.player = Princess(self.game)
                self.local_player = self.game.player
                self.local_player.role = "princess"
                
                # Remote player (máy chủ) là Knight
                self.remote_player = Player(self.game)
                self.remote_player.role = "knight"
                self.remote_player.is_remote = True
        else:
            # Chơi đơn
            self.local_player = self.game.player
            self.remote_player = None



        # --- BƯỚC 2: XỬ LÝ VỊ TRÍ NHÂN VẬT & CHECKPOINT ---
        saved_cp = self.player.progress.get("checkpoint")

        is_client = (self.game.game_mode == "multi" and not self.game.network.is_host)
        is_host = (self.game.game_mode == "multi" and self.game.network.is_host)

        if from_intro:
            self.game.player_progress["checkpoint"] = None
            spawn_pos = self.level.get_spawn_position(is_p2=is_client)
            self.player.respawn(spawn_pos)
            self.player.checkpoint_pos = spawn_pos
            self.player.progress["checkpoint"] = spawn_pos
            self.game.player_progress["checkpoint"] = spawn_pos

        elif menu_continue:
            if saved_cp:
                self.player.respawn(saved_cp)
                self.player.checkpoint_pos = saved_cp
            else:
                spawn_pos = self.level.get_spawn_position(is_p2=is_client)
                self.player.respawn(spawn_pos)
                self.player.checkpoint_pos = spawn_pos
                self.player.progress["checkpoint"] = spawn_pos
                self.game.player_progress["checkpoint"] = spawn_pos

        elif force_reset or just_loaded_map:
            if saved_cp:
                self.player.respawn(saved_cp)
                self.player.checkpoint_pos = saved_cp
            else:
                spawn_pos = self.level.get_spawn_position(is_p2=is_client)
                self.player.respawn(spawn_pos)
                self.player.checkpoint_pos = spawn_pos
                self.game.player_progress["checkpoint"] = spawn_pos

        # Đặt trước vị trí sinh ra cho remote_player tránh lỗi bị rớt map ở những frame đầu tiên
        if self.remote_player:
            if saved_cp:
                remote_spawn = (saved_cp[0] + 50, saved_cp[1])
            else:
                remote_spawn = self.level.get_spawn_position(is_p2=is_host)
            self.remote_player.rect.x = int(remote_spawn[0])
            self.remote_player.rect.y = int(remote_spawn[1])
            self.remote_player.pos_x = float(remote_spawn[0])
            self.remote_player.pos_y = float(remote_spawn[1])
            self.remote_player.target_x = self.remote_player.pos_x
            self.remote_player.target_y = self.remote_player.pos_y

        if hasattr(self.game, 'camera'):
            self.game.camera.update(self.player)

        if self.game.game_mode == "multi" and self.game.network.is_host:
            entities_data = []

            for e in self.level.entities:
                if hasattr(e, "type"):
                    entities_data.append({
                        "type": getattr(e, "type", "unknown"),
                        "x": e.rect.x,
                        "y": e.rect.y
                    })

            self.game.network.send_data({
                "type": "full_state",
                "entities": entities_data
            })

    def handle_network(self, packets):
        if not packets:
            return
            
        for packet in packets:
            ptype = packet.get("type")
            
            if ptype == "game_sync" and self.remote_player:
                # Cập nhật thông số của người chơi kia
                self.remote_player.target_x = float(packet.get("x", self.remote_player.rect.x))
                self.remote_player.target_y = float(packet.get("y", self.remote_player.rect.y))
                self.remote_player.state = packet.get("state", "idle")
                self.remote_player.facing_right = packet.get("facing", True)
                self.remote_player.hp = packet.get("hp", self.remote_player.hp)
                self.remote_player.mana = packet.get("mana", getattr(self.remote_player, "mana", 50))
                # Cập nhật checkpoint nếu máy kia báo có checkpoint mới
                new_cp = packet.get("checkpoint")
                if new_cp:
                    self.remote_player.checkpoint_pos = new_cp
                
                self.remote_player.is_using_skill = packet.get("is_using_skill", False)
                
                # Đồng bộ trạng thái chém thường
                is_attacking = packet.get("is_attacking", False)
                if is_attacking and not self.remote_player.is_attacking:
                    self.remote_player.is_attacking = True
                    self.remote_player.attack_timer = self.remote_player.ATTACK_DURATION
                
                # Cập nhật vị trí quái vật từ Host
                if not self.game.network.is_host and "enemies" in packet:
                    for edata in packet["enemies"]:
                        idx = edata.get("i")
                        if idx is not None and idx < len(self.level.enemies):
                            e = self.level.enemies[idx]
                            e.rect.x = edata["x"]
                            e.rect.y = edata["y"]
                            e.pos_x = float(e.rect.x)
                            e.pos_y = float(e.rect.y)
                            e.alive = edata["a"]
                            if hasattr(e, "direction"):
                                e.direction = edata.get("d", e.direction)
                            if hasattr(e, "hp"):
                                e.hp = edata.get("hp", e.hp)
                
            elif ptype == "platform_sync":
                # ĐỒNG BỘ VỊ TRÍ SÀN 1 LẦN
                incoming_platforms = packet.get("platforms", [])
                moving_platforms = [p for p in self.level.platforms if isinstance(p, MovingPlatform)]
                for i, p_data in enumerate(incoming_platforms):
                    if i < len(moving_platforms):
                        p = moving_platforms[i]
                        p.rect.x = p_data["x"]
                        p.rect.y = p_data["y"]
                        p.pos_x = float(p.rect.x)
                        p.pos_y = float(p.rect.y)
                print(f"[PlayingState] Platforms synced from Host.")

            elif ptype == "chest_opened":
                chest_id = packet["chest_id"]
                for entity in self.level.entities:
                    if hasattr(entity, "rect") and f"{entity.rect.x}_{entity.rect.y}" == chest_id:
                        entity.opened = True
                        break

            elif ptype == "entity_collected":
                # CHỈ HOST MỚI XỬ LÝ LƯU TRỮ VĨNH VIỄN
                if self.game.network.is_host:
                    eid = packet.get("entity_id")
                    self.level.mark_entity_collected(eid)
                    
            elif ptype == "item_collected":
                item_id = packet.get("item_id")
                is_coin = packet.get("is_coin", False)
                val = packet.get("value", 0)
                for e in self.level.entities:
                    if hasattr(e, "item_id") and e.item_id == item_id:
                        # Nếu là tiền vàng thì cả 2 cùng được chia sẻ
                        if is_coin and val > 0:
                            self.local_player.add_gold(val)
                        e.kill()
                        break
                        
            elif ptype == "box_broken":
                box_id = packet.get("box_id")
                drop_type = packet.get("drop")
                for e in self.level.entities:
                    if hasattr(e, "box_id") and e.box_id == box_id:
                        if hasattr(e, "break_box"):
                            e.break_box(sync_drop_type=drop_type)
                        break
            elif ptype == "level_change":
                new_level = packet["level"]
                self.game.player_progress["current_level"] = new_level
                self.is_initialized = False
                self.on_enter()
                
            elif ptype == "portal_ready":
                self.remote_at_portal = packet.get("ready", False)

            elif ptype == "spawn_projectile":
                from game.entities.projectile import Projectile
                px = packet.get("x")
                py = packet.get("y")
                pdir = packet.get("dir")
                if px is not None and py is not None:
                    # Tạo đạn trên máy này
                    proj = Projectile(self.game, px, py, pdir)
                    self.level.entities.append(proj)
                    print(f"[Network] Spawned remote projectile at ({px}, {py})")

            elif ptype == "hit_enemy":
                # CHỈ HOST MỚI XỬ LÝ SÁT THƯƠNG THỰC SỰ TRÊN QUÁI VẬT
                if self.game.network.is_host:
                    idx = packet.get("enemy_idx")
                    dmg = packet.get("damage", 10)
                    k_dir = packet.get("k_dir", 0)
                    
                    if idx is not None and idx < len(self.level.enemies):
                        enemy = self.level.enemies[idx]
                        if enemy.alive:
                            enemy.take_damage(dmg, knockback_dir=k_dir)
                            print(f"[Network] Remote player hit enemy {idx} for {dmg} damage")

    def update(self, delta_time):
        if not self.player or not self.level:
            return

        # 1. Reset cờ portal đầu mỗi frame (để tránh bị kẹt trạng thái)
        self.local_at_portal = False

        # 2. Cập nhật bản thân (Local) và Level
        self.level.update(delta_time)
        self.level.update_entities(delta_time)
        self.player.update(delta_time, self.level)

        # --- 3. LÀM MƯỢT DI CHUYỂN CỦA REMOTE PLAYER (NỘI SUY - LERP) ---
        if self.remote_player and hasattr(self.remote_player, 'target_x'):
            # Nếu khoảng cách quá lớn (Teleport hoặc Respawn), dịch chuyển tức thì để tránh trượt mượt quá mức
            dist_sq = (self.remote_player.target_x - self.remote_player.pos_x)**2 + \
                      (self.remote_player.target_y - self.remote_player.pos_y)**2
            
            if dist_sq > 10000: # 100^2
                self.remote_player.pos_x = self.remote_player.target_x
                self.remote_player.pos_y = self.remote_player.target_y
            else:
                self.remote_player.pos_x += (self.remote_player.target_x - self.remote_player.pos_x) * 0.3
                self.remote_player.pos_y += (self.remote_player.target_y - self.remote_player.pos_y) * 0.3
            
            # Khóa tọa độ về số nguyên để render chuẩn
            self.remote_player.rect.x = int(self.remote_player.pos_x)
            self.remote_player.rect.y = int(self.remote_player.pos_y)
            
            # Cập nhật frame hoạt ảnh cho Remote Player
            if hasattr(self.remote_player, 'update_animation'):
                self.remote_player.update_animation(delta_time)
            

        # 4. Kiểm tra va chạm với Portal (Gom lại thành 1 vòng lặp duy nhất)
        from game.objects.portal import EndPortal
        for entity in self.level.entities:
            if isinstance(entity, EndPortal):
                if sdl2.SDL_HasIntersection(self.player.rect, entity.rect):
                    self.local_at_portal = True
                    break

        # ================= KIỂM TRA ĐIỀU KIỆN QUA MÀN =================
        if self.game.game_mode == "single":
            # Chơi đơn: Qua màn nếu chạm Portal HOẶC hoàn thành nhiệm vụ (Princess)
            if self.local_at_portal or self.level.check_win(self.player):
                self.complete_level_single()

        elif self.game.game_mode == "multi":
            packets = self.game.network.get_packets()
            if packets:
                self.handle_network(packets)
            # --- GỬI TÍN HIỆU ĐỒNG BỘ ĐỊNH KỲ ---
            self.sync_timer += delta_time
            if self.sync_timer >= self.SYNC_INTERVAL:
                self.sync_timer = 0.0
                sync_data = {
                    "type": "game_sync",
                    "x": self.local_player.rect.x,
                    "y": self.local_player.rect.y,
                    "state": self.local_player.state,
                    "facing": self.local_player.facing_right,
                    "hp": self.local_player.hp,
                    "mana": self.local_player.mana,
                    "checkpoint": self.local_player.checkpoint_pos,
                    "is_using_skill": getattr(self.local_player, "is_using_skill", False),
                    "is_attacking": self.local_player.is_attacking
                }
                
                # Nếu là Host, gửi thêm dữ liệu quái vật để Client đồng bộ chính xác
                if self.game.network.is_host:
                    enemies_sync = []
                    for i, e in enumerate(self.level.enemies):
                        enemies_sync.append({
                            "i": i,
                            "x": e.rect.x,
                            "y": e.rect.y,
                            "a": e.alive,
                            "d": getattr(e, "direction", 1),
                            "hp": getattr(e, "hp", 0)
                        })
                    sync_data["enemies"] = enemies_sync

                self.game.network.send_data(sync_data)

            # --- ĐỒNG BỘ TRẠNG THÁI PORTAL ---
            if self.local_at_portal != self.last_local_portal_state:
                self.last_local_portal_state = self.local_at_portal
                self.game.network.send_data({
                    "type": "portal_ready",
                    "ready": self.local_at_portal
                })

            # --- CHECK WIN MULTIPLAYER (Đợi cả 2 cùng vào portal) ---
            if not self.multi_completed and self.local_at_portal and self.remote_at_portal:
                print("✅ BOTH PLAYERS AT PORTAL")
                self.multi_completed = True
                self.complete_level_multi()

        # ================= VẬT LÝ VÀ VA CHẠM =================
        
        # 1. Xử lý va chạm platform
        if hasattr(self.level, 'platforms'):
            for plat in self.level.platforms:
                if hasattr(plat, 'resolve_collision'):
                    plat.resolve_collision(self.player, delta_time)

        # 2. Va chạm Player - Enemy
        for enemy in self.level.enemies[:]:
            if enemy.alive and sdl2.SDL_HasIntersection(self.player.rect, enemy.rect):
                knock_dir = -1 if self.player.rect.x < enemy.rect.x else 1
                self.player.take_damage(enemy.damage, knock_dir)
                
        # 3. Cập nhật Camera đi theo người chơi Local
        if hasattr(self.game, 'camera'):
            self.game.camera.update(self.player)

        # 4. Va chạm Projectile (Đạn/Kỹ năng) với Enemy
        from game.entities.projectile import Projectile
        projectiles = [e for e in self.level.entities if isinstance(e, Projectile)]
        for proj in projectiles[:]:
            if not proj.alive:
                continue
            for enemy in self.level.enemies:
                if enemy.alive and sdl2.SDL_HasIntersection(proj.rect, enemy.rect):
                    enemy.take_damage(proj.damage)
                    enemy.vel_x = proj.direction * 5.0 # Đẩy lùi quái nhẹ
                    proj.die()
                    break

    def complete_level_single(self):
        current_lv = self.game.player_progress.get("current_level", "level1_village")
        self.game.player_progress["coin"] = self.player.gold
        self.game.player_progress["lives"] = self.game.lives
        self.game.player_progress["checkpoint"] = None
        # Xóa checkpoint cho tất cả role (knight/princess)
        if "players" in self.game.player_progress:
            for role in self.game.player_progress["players"]:
                self.game.player_progress["players"][role]["checkpoint"] = None

        if current_lv == "level1_village":
            self.game.player_progress["current_level"] = "level2_valley"
        elif current_lv == "level2_valley":
            self.game.player_progress["current_level"] = "level3_mountain"
        elif current_lv == "level3_mountain":
            self.game.player_progress["current_level"] = "boss_arena"
        else:
            self.game.change_state("win")
            return
        self.is_initialized = False
        if self.player: self.player.checkpoint_pos = None
        self.game.save_current_game() 
        self.game.change_state("playing", reset=False)

    def complete_level_multi(self):
        current_lv = self.game.player_progress.get("current_level", "level1_village")
        # Lưu tiến trình: Dùng chung coin
        self.game.player_progress["coin"] = self.game.player_progress.get("coin", 0)
        self.game.player_progress["checkpoint"] = None
        # Xóa checkpoint cho tất cả người chơi để tránh lỗi tọa độ màn cũ
        if "players" in self.game.player_progress:
            for role in self.game.player_progress["players"]:
                self.game.player_progress["players"][role]["checkpoint"] = None

        if current_lv == "level1_village":
            new_level = "level2_valley"
        elif current_lv == "level2_valley":
            new_level = "level3_mountain"
        elif current_lv == "level3_mountain":
            new_level = "boss_arena"
        else:
            self.game.change_state("win")
            return

        self.game.player_progress["current_level"] = new_level
        # Gửi gói tin level_change cho client (nếu là host)
        if self.game.network.is_host:
            self.game.network.send_data({"type": "level_change", "level": new_level})
        
        self.is_initialized = False
        if self.player: self.player.checkpoint_pos = None
        self.game.save_current_game() 
        self.game.change_state("playing", reset=False)

    def render(self, renderer):
        sdl2.SDL_SetRenderDrawColor(renderer, *self.level.bg_color)
        sdl2.SDL_RenderClear(renderer)

        if self.level:
            self.level.render(renderer, self.game.camera)
            if hasattr(self.level, 'platforms'):
                for plat in self.level.platforms:
                    plat.render(renderer, self.game.camera)
            self.level.render_entities(renderer, self.game.camera)

        if self.player:
            self.player.render(renderer, self.game.camera)
        if self.remote_player:
            self.remote_player.render(renderer, self.game.camera)

    def handle_event(self, event):
        if event.type == sdl2.SDL_KEYDOWN:
            scancode = event.key.keysym.scancode
            from game.constants import KEY_BINDINGS_DEFAULT
            if scancode == KEY_BINDINGS_DEFAULT["pause"] or scancode == sdl2.SDL_SCANCODE_ESCAPE:
                self.game.change_state("pause")
                return
            if scancode == KEY_BINDINGS_DEFAULT["interact"]:
                if hasattr(self, 'player'):
                    self.player.interact()
                return

        if self.player:
            self.player.handle_input(event)
        self.game.last_time = sdl2.timer.SDL_GetTicks()

    def on_exit(self):
        pass