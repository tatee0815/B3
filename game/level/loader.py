"""
Hàm load level từ file JSON
"""

import json
from game.constants import TILE_SIZE
from game.entities import Player, Goblin, Skeleton, Heart, Coin, ManaBottle
from game.objects import Platform, OneWayPlatform, MovingPlatform, BreakableBox, Checkpoint


def load_level_from_json(filename, game):
    """
    Load level từ file JSON trong game/level/levels/
    Trả về instance Level đã sẵn sàng
    """
    path = f"game/level/levels/{filename}"
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Không tìm thấy level: {path}")
        return None
    
    # Tạo level
    level = Level(game,
                  width_tiles=data.get("width", 50),
                  height_tiles=data.get("height", 20))
    
    # Tiles
    if "tiles" in data:
        level.tiles = data["tiles"]
    
    # Spawn point
    if "start_position" in data:
        level.start_position = (data["start_position"]["x"], data["start_position"]["y"])
    
    # Entities & objects
    if "entities" in data:
        for ent in data["entities"]:
            typ = ent.get("type")
            x = ent.get("x", 0)
            y = ent.get("y", 0)
            
            if typ == "player_spawn":
                level.start_position = (x, y)
            elif typ == "goblin":
                level.entities.append(Goblin(game, x, y))
            elif typ == "skeleton":
                level.entities.append(Skeleton(game, x, y))
            elif typ == "platform":
                level.platforms.append(Platform(game, x, y, ent.get("w", TILE_SIZE), ent.get("h", TILE_SIZE)))
            elif typ == "one_way":
                level.platforms.append(OneWayPlatform(game, x, y, ent.get("w", TILE_SIZE), ent.get("h", TILE_SIZE)))
            elif typ == "moving_platform":
                level.platforms.append(MovingPlatform(game, x, y, ent.get("w", TILE_SIZE*3), TILE_SIZE,
                                                      speed=ent.get("speed", 2.0),
                                                      direction=ent.get("direction", 1)))
            elif typ == "breakable":
                level.breakables.append(BreakableBox(game, x, y,
                                                     is_explosive=ent.get("explosive", False)))
            elif typ == "checkpoint":
                cp = Checkpoint(game, x, y)
                level.checkpoints.append(cp)
                level.entities.append(cp)  # để update & render
            elif typ == "coin":
                level.entities.append(Coin(game, x, y, value=ent.get("value", 1)))
            elif typ == "heart":
                level.entities.append(Heart(game, x, y))
            elif typ == "mana":
                level.entities.append(ManaBottle(game, x, y, value=ent.get("value", 25)))
    
    # Background color tùy level
    if "bg_color" in data:
        level.bg_color = tuple(data["bg_color"])
    
    print(f"Loaded level: {filename} | Entities: {len(level.entities)}")
    return level