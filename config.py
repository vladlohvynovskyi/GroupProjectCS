import os

SCREEN_WIDTH = 960
SCREEN_HEIGHT = 720
FPS = 60
TILE_SIZE = 48

# Grid size in tiles
MAP_COLS = 80
MAP_ROWS = 90

# Colors
COLOR_BLACK = (0, 0, 0)
COLOR_FLOOR = (50, 45, 42)
COLOR_WALL = (25, 22, 20)
COLOR_PLAYER = (180, 160, 120)
COLOR_DOOR = (101, 67, 33)
COLOR_CHEST = (218, 165, 32)
COLOR_TRAP = (120, 40, 40)
COLOR_CAMPFIRE = (255, 140, 0)
COLOR_STAIR = (200, 200, 100)


WHITE = (255, 255, 255)
RED = (200, 0, 0)
GREEN = (0, 200, 0)
BLUE = (0, 100, 200)
YELLOW = (255, 255, 0)
PURPLE = (150, 0, 150)
GRAY = (100, 100, 100)
LIGHT_GRAY = (150, 150, 150)
DARK_GRAY = (50, 50, 50)
ORANGE = (255, 165, 0)


# Tile types
TILE_VOID = 0
TILE_FLOOR = 1
TILE_WALL = 2
TILE_DOOR = 3
TILE_CHEST = 4
TILE_TRAP = 5
TILE_CAMPFIRE = 6
TILE_STAIR = 7

# Room settings
MIN_ROOM_SIZE = 6
MAX_ROOM_SIZE = 14
MAX_ROOMS = 40

# Light & darkness
PLAYER_LIGHT_RADIUS = 130
DARKNESS = 230

# Minimap
MINIMAP_TILE   = 3
MINIMAP_MARGIN = 8


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(SCRIPT_DIR, "assets", "0x72_DungeonTilesetII_v1.7", "frames")
ENEMY_SPRITE_DIR = os.path.join(SCRIPT_DIR, "assets", "images", "enemies")
UI_DIR = os.path.join(SCRIPT_DIR, "assets", "AssetsUIWerdantaN3", "PNG")

