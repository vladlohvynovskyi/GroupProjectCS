import pygame
import os
import sys
import random
from enum import Enum

# Initialize Pygame
pygame.init()

# Constants - We'll use the dimensions from main.py since it has the larger map
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 720
FPS = 60
TILE_SIZE = 48

# Grid size in tiles
MAP_COLS = 80
MAP_ROWS = 90

#Get the directory where this is stored
SCRIPT_DIR = os.path.dirname(__file__)
#Define paths to asset folder
ASSETS_DIR = os.path.join(SCRIPT_DIR, "assets")
IMAGES_DIR = os.path.join(ASSETS_DIR, "images")
ENEMY_DIR = os.path.join(IMAGES_DIR, "enemies")
SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")


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
BLACK = (0, 0, 0)
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

class GameState(Enum):
    EXPLORATION = 0
    COMBAT = 1
    INVENTORY = 2
    PAUSED = 3
    GAME_OVER = 4
    VICTORY = 5

class Element(Enum):
    NORMAL = 0
    FIRE = 1
    WATER = 2
    EARTH = 3
    HOLY = 4
    DARK = 5

class ItemType(Enum):
    WEAPON = 0
    HEALTH = 1
    ARMOR = 2

EFFECTIVENESS = {
    (Element.FIRE, Element.EARTH): 1.5,
    (Element.WATER, Element.FIRE): 1.5,
    (Element.EARTH, Element.WATER): 1.5,
    (Element.EARTH, Element.FIRE): 0.5,
    (Element.FIRE, Element.WATER): 0.5,
    (Element.WATER, Element.EARTH): 0.5,
    (Element.HOLY, Element.FIRE): 2.0,
    (Element.HOLY, Element.EARTH): 2.0,
    (Element.HOLY, Element.WATER): 2.0,
    (Element.DARK, Element.HOLY): 2.5
}

ELEMENT_COLORS = {
    Element.NORMAL: (255, 255, 255),
    Element.FIRE: (200, 0, 0),
    Element.WATER: (0, 100, 200),
    Element.EARTH: (0, 200, 0),
    Element.HOLY: (255, 255, 0),
    Element.DARK: (50, 50, 50)
}

class Item:
    def __init__(self, name, item_type, element=Element.NORMAL, value=0, damage=0, defense=0, description=""):
        self.name = name
        self.type = item_type
        self.element = element
        self.value = value
        self.damage = damage
        self.defense = defense
        self.description = description
    
    def get_damage_multiplier(self, enemy_element):
        if self.type != ItemType.WEAPON:
            return 1.0
        return EFFECTIVENESS.get((self.element, enemy_element), 1.0)

class Weapon(Item):
    def __init__(self, name, element, damage, description=""):
        super().__init__(name, ItemType.WEAPON, element, damage, damage, 0, description)

class HealthPotion(Item):
    def __init__(self, name, heal_amount):
        super().__init__(name, ItemType.HEALTH, Element.NORMAL, heal_amount, 0, 0, f"Heals {heal_amount} HP")

class Armor(Item):
    def __init__(self, name, defense, description=""):
        super().__init__(name, ItemType.ARMOR, Element.NORMAL, 0, 0, defense, description)


class Enemy:
    sprite_sheet = None
    
    @classmethod
    def load_sprite_sheet(cls):
        """Load the sprite sheet once for all enemies"""
        if cls.sprite_sheet is None:
            sheet_path = os.path.join("assets", "images", "enemies", "beasts.png")
            try:
                cls.sprite_sheet = pygame.image.load(sheet_path).convert_alpha()
                print("Loaded sprite sheet")
            except Exception as e:
                print(f"Failed to load sprite sheet: {e}")
                cls.sprite_sheet = None
               
    def __init__(self, tile_x, tile_y, enemy_type="basic"):
        # Store tile position instead of pixel position
        self.current_tile_x = tile_x
        self.current_tile_y = tile_y
        
        # Pixel position for rendering (center of tile)
        self.pixel_x = tile_x * TILE_SIZE + TILE_SIZE // 2
        self.pixel_y = tile_y * TILE_SIZE + TILE_SIZE // 2
        
        # For smooth movement between tiles
        self.target_tile_x = tile_x
        self.target_tile_y = tile_y
        self.move_progress = 1.0  # 1.0 = at target, 0.0 = just started moving
        
        Enemy.load_sprite_sheet()
        
        # Sprite animation attributes
        self.sprite_width = 48
        self.sprite_height = 64
        self.current_frame = 0  # Start with first frame
        self.facing_right = True
        
        # Enemy type stats (from combat.py)
        if enemy_type == "basic":
            self.name = "beast"
            self.speed = 2.0  # Tiles per second (slower than player's 500px/sec ≈ 10 tiles/sec)
            self.max_hp = 60
            self.hp = 60
            self.damage = 10
            self.element = Element.NORMAL
            self.row = 0
            self.columns = [0, 1, 2, 3]
            self.xp_reward = 30
            self.color = RED
        elif enemy_type == "fire":
            self.name = "werebeast"
            self.speed = 1.8
            self.max_hp = 80
            self.hp = 80
            self.damage = 15
            self.element = Element.FIRE
            self.row = 1
            self.columns = [0, 1, 2, 3]
            self.xp_reward = 50
            self.color = ORANGE
        elif enemy_type == "water":
            self.name = "forklift"
            self.speed = 1.5
            self.max_hp = 70
            self.hp = 70
            self.damage = 12
            self.element = Element.WATER
            self.row = 2
            self.columns = [0, 1, 2]
            self.xp_reward = 45
            self.color = BLUE
        elif enemy_type == "earth":
            self.name = "smallbeast"
            self.speed = 2.5
            self.max_hp = 75
            self.hp = 75
            self.damage = 13
            self.element = Element.EARTH
            self.row = 3
            self.columns = [0, 1, 2]
            self.xp_reward = 45
            self.color = GREEN
        elif enemy_type == "mini_boss":
            self.name = "undead"
            self.speed = 1.2
            self.max_hp = 200
            self.hp = 200
            self.damage = 25
            self.element = Element.FIRE
            self.row = 4
            self.columns = [0, 1, 2]
            self.xp_reward = 200
            self.color = PURPLE
        
        # Load all frames
        self.frames_images = []
        

        if Enemy.sprite_sheet:
            for col in self.columns:
                x = col * self.sprite_width
                y = self.row * self.sprite_height
                try:
                    frame = Enemy.sprite_sheet.subsurface((x, y, self.sprite_width, self.sprite_height))
                    frame = pygame.transform.scale(frame, (TILE_SIZE, TILE_SIZE))
                    self.frames_images.append(frame)
                    # Store flipped version for right movement
                    self.frames_images.append(pygame.transform.flip(frame, True, False))
                except:
                    pass
            
            # Set initial image to frame 0 (back view)
            if self.frames_images:
                self.image = self.frames_images[0]
                self.current_frame = 0
        
        # Movement AI
        self.move_timer = 0
        self.move_delay = random.uniform(0.5, 2.0)  # Wait between moves
        self.dx = 0
        self.dy = 0
        self.is_moving = False
        
        # Room tracking (for wandering within room)
        self.room_index = None
        
    def update_animation(self, dt):
        """Update animation frame"""
        if not self.frames_images:
            return
        
        self.animation_timer += dt
        if self.animation_timer > 0.15:  # Change frame every 0.15 seconds
            self.animation_timer = 0
            self.current_frame = (self.current_frame + 1) % len(self.frames_images)
            
            if self.facing_right:
                self.image = self.frames_images[self.current_frame]
            else:
                self.image = self.frames_images_left[self.current_frame]
    
    def can_move_to(self, tiles, target_tile_x, target_tile_y):
        """Check if enemy can move to target tile"""
        walkable = [TILE_FLOOR, TILE_CAMPFIRE]  # Enemies can walk on floors and campfires
        
        # Check bounds
        if target_tile_x < 0 or target_tile_x >= MAP_COLS or target_tile_y < 0 or target_tile_y >= MAP_ROWS:
            return False
        
        # Check if tile is walkable
        if tiles[target_tile_y][target_tile_x] not in walkable:
            return False
        
        return True
    
    def update_movement(self, dt, tiles):
        """Update enemy movement (tile-based)"""
        if self.is_moving:
            # Continue current move
            self.move_progress += self.speed * dt
            
            if self.move_progress >= 1.0:
                # Reached target tile
                self.move_progress = 1.0
                self.is_moving = False
                self.current_tile_x = self.target_tile_x
                self.current_tile_y = self.target_tile_y
                
                # Update pixel position
                self.pixel_x = self.current_tile_x * TILE_SIZE + TILE_SIZE // 2
                self.pixel_y = self.current_tile_y * TILE_SIZE + TILE_SIZE // 2
            else:
                # Interpolate pixel position
                start_x = self.current_tile_x * TILE_SIZE + TILE_SIZE // 2
                start_y = self.current_tile_y * TILE_SIZE + TILE_SIZE // 2
                target_x = self.target_tile_x * TILE_SIZE + TILE_SIZE // 2
                target_y = self.target_tile_y * TILE_SIZE + TILE_SIZE // 2
                
                self.pixel_x = start_x + (target_x - start_x) * self.move_progress
                self.pixel_y = start_y + (target_y - start_y) * self.move_progress
                
                # Update sprite based on movement direction during movement
                self._update_sprite_for_direction()
        else:
            # Decide next move
            self.move_timer += dt
            if self.move_timer >= self.move_delay:
                self.move_timer = 0
                self.move_delay = random.uniform(0.5, 2.0)
                
                # Choose random direction
                directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
                random.shuffle(directions)
                
                for dx, dy in directions:
                    new_x = self.current_tile_x + dx
                    new_y = self.current_tile_y + dy
                    
                    if self.can_move_to(tiles, new_x, new_y):
                        self.target_tile_x = new_x
                        self.target_tile_y = new_y
                        self.is_moving = True
                        self.move_progress = 0.0
                        
                        # Store movement direction for sprite updates
                        self.current_dx = dx
                        self.current_dy = dy
                        
                        # Update sprite immediately when starting to move
                        self._update_sprite_for_direction()
                        break

    def _update_sprite_for_direction(self):
        """Update the enemy sprite based on current movement direction"""
        if not self.frames_images:
            return
        
        dx = self.target_tile_x - self.current_tile_x
        dy = self.target_tile_y - self.current_tile_y
        
        # Normalize direction (should be -1, 0, or 1)
        if dx != 0:
            dx = 1 if dx > 0 else -1
        if dy != 0:
            dy = 1 if dy > 0 else -1
        
        # Select sprite based on direction
        if dx > 0:  # Moving right
            # Use left-facing frame (index 2) flipped horizontally
            if len(self.frames_images) > 2:
                self.image = pygame.transform.flip(self.frames_images[2], True, False)
                self.facing_right = True
        elif dx < 0:  # Moving left
            # Use left-facing frame (index 2)
            if len(self.frames_images) > 2:
                self.image = self.frames_images[2]
                self.facing_right = False
        elif dy < 0:  # Moving up (away from camera)
            # Use back view frame (index 0)
            if len(self.frames_images) > 0:
                self.image = self.frames_images[0]
        elif dy > 0:  # Moving down (towards camera)
            # Use front view frame (index 1)
            if len(self.frames_images) > 1:
                self.image = self.frames_images[1]
    
    def take_damage(self, damage):
        self.hp -= damage
        return self.hp <= 0
    
    def draw(self, screen, camera_x, camera_y):
        """Draw enemy with camera offset"""
        screen_x = int(self.pixel_x - camera_x - TILE_SIZE // 2)
        screen_y = int(self.pixel_y - camera_y - TILE_SIZE // 2)
        
        if self.image:
            screen.blit(self.image, (screen_x, screen_y))
        else:
            # Fallback rectangle
            rect = pygame.Rect(screen_x, screen_y, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(screen, self.color, rect)

class Player:
    SIZE = TILE_SIZE - 12
    SPEED = 500  # pixels per second

    def __init__(self, tile_x, tile_y):
        # Tile position
        self.current_tile_x = tile_x
        self.current_tile_y = tile_y
        
        # Pixel position (center of tile)
        self.x = tile_x * TILE_SIZE + TILE_SIZE // 2
        self.y = tile_y * TILE_SIZE + TILE_SIZE // 2
        
        # Combat stats (from combat.py)
        self.max_hp = 100
        self.hp = 100
        self.xp = 0
        self.level = 1
        
        # Inventory
        self.inventory = []
        self.max_inventory = 5
        self.equipped_weapon = None
        self.equipped_armor = None
        self.keys = set()  # For locked doors
        
        # Starting equipment
        self._setup_starting_gear()
    
    def _setup_starting_gear(self):
        """Give player starting items"""
        starter_sword = Weapon("Wooden Sword", Element.NORMAL, 15, "A basic wooden sword")
        starter_armor = Armor("Cloth Armor", 2, "Basic protection")
        health_potion = HealthPotion("Health Potion", 30)
        
        self.add_item(starter_sword)
        self.add_item(starter_armor)
        self.add_item(health_potion)
        self.equip_weapon(starter_sword)
        self.equip_armor(starter_armor)
    
    def add_item(self, item):
        if len(self.inventory) < self.max_inventory:
            self.inventory.append(item)
            return True
        return False
    
    def remove_item(self, item):
        if item in self.inventory:
            self.inventory.remove(item)
            return True
        return False
    
    def equip_weapon(self, weapon):
        if weapon.type == ItemType.WEAPON and weapon in self.inventory:
            self.equipped_weapon = weapon
    
    def equip_armor(self, armor):
        if armor.type == ItemType.ARMOR and armor in self.inventory:
            self.equipped_armor = armor
    
    def take_damage(self, damage):
        # Armor reduces damage
        if self.equipped_armor:
            damage = max(1, damage - self.equipped_armor.defense)
        self.hp -= damage
        return self.hp <= 0
    
    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)
    
    def gain_xp(self, amount):
        self.xp += amount
        # Level up every 100 XP
        if self.xp >= self.level * 100:
            self.level += 1
            self.max_hp += 20
            self.hp = self.max_hp
            return True
        return False
    
    def calculate_damage(self, enemy_element):
        if not self.equipped_weapon:
            return 5  # Bare hands damage
        
        base_damage = self.equipped_weapon.damage + (self.level * 2)
        multiplier = self.equipped_weapon.get_damage_multiplier(enemy_element)
        
        # Critical hit chance (10%)
        if random.random() < 0.1:
            return int(base_damage * multiplier * 2)
        
        return int(base_damage * multiplier)
    
    def tile_x(self):
        return int(self.x) // TILE_SIZE
    
    def tile_y(self):
        return int(self.y) // TILE_SIZE
    
    def can_move(self, tiles, x, y):
        walkable = [TILE_FLOOR, TILE_CAMPFIRE, TILE_TRAP, TILE_STAIR]
        half = self.SIZE // 2

        # Check all four corners of the player's bounding box
        corners = [
            (x - half, y - half),
            (x + half, y - half),
            (x - half, y + half),
            (x + half, y + half),
        ]

        for corner_x, corner_y in corners:
            tile_x = int(corner_x) // TILE_SIZE
            tile_y = int(corner_y) // TILE_SIZE

            if tile_x < 0 or tile_x >= MAP_COLS or tile_y < 0 or tile_y >= MAP_ROWS:
                return False

            if tiles[tile_y][tile_x] not in walkable:
                return False

        return True

    def update(self, keys_pressed, dt, tiles):
        dx, dy = 0, 0
        if keys_pressed[pygame.K_w] or keys_pressed[pygame.K_UP]:
            dy = -1
        if keys_pressed[pygame.K_s] or keys_pressed[pygame.K_DOWN]:
            dy = 1
        if keys_pressed[pygame.K_a] or keys_pressed[pygame.K_LEFT]:
            dx = -1
        if keys_pressed[pygame.K_d] or keys_pressed[pygame.K_RIGHT]:
            dx = 1
            
        if dx != 0 or dy != 0:
            new_x = self.x + dx * self.SPEED * dt
            new_y = self.y + dy * self.SPEED * dt
            
            if self.can_move(tiles, new_x, self.y):
                self.x = new_x
            if self.can_move(tiles, self.x, new_y):
                self.y = new_y
            
            # Update tile position
            self.current_tile_x = int(self.x) // TILE_SIZE
            self.current_tile_y = int(self.y) // TILE_SIZE

    def draw(self, screen, camera_x, camera_y):
        rect = pygame.Rect(
            int(self.x - camera_x) - self.SIZE // 2,
            int(self.y - camera_y) - self.SIZE // 2,
            self.SIZE,
            self.SIZE,
        )
        pygame.draw.rect(screen, COLOR_PLAYER, rect)

# Room settings
MIN_ROOM_SIZE = 6
MAX_ROOM_SIZE = 14
MAX_ROOMS = 40

# Minimap settings
MINIMAP_TILE = 3
MINIMAP_MARGIN = 8

class DungeonMap:
    def __init__(self):
        self.tiles = []
        self.rooms = []
        self.doors = []
        self.chests = []
        self.traps = []
        self.campfires = []
        self.staircase = None
        self.enemies = []  # NEW: Store enemies
        
    def generate(self):
        # Clear previous data
        self.tiles = []
        self.rooms = []
        self.doors = []
        self.chests = []
        self.traps = []
        self.campfires = []
        self.staircase = None
        self.enemies = []  # NEW: Clear enemies
        
        # Initialize tiles as void
        for row in range(MAP_ROWS):
            self.tiles.append([TILE_VOID] * MAP_COLS)
        
        # Generate rooms and corridors (from main.py)
        for _ in range(MAX_ROOMS):
            w = random.randint(MIN_ROOM_SIZE, MAX_ROOM_SIZE)
            h = random.randint(MIN_ROOM_SIZE, MAX_ROOM_SIZE)
            x = random.randint(1, MAP_COLS - w - 1)
            y = random.randint(1, MAP_ROWS - h - 1)

            if self._overlaps(x, y, w, h):
                continue

            self._carve_room(x, y, w, h)
            self.rooms.append((x, y, w, h))

            # Connect to previous room
            if len(self.rooms) > 1:
                new_cx = x + w // 2
                new_cy = y + h // 2
                px, py, pw, ph = self.rooms[-2]
                prev_cx = px + pw // 2
                prev_cy = py + ph // 2

                if random.random() < 0.5:
                    self._carve_corridor(prev_cx, prev_cy, new_cx, new_cy)
                else:
                    self._carve_corridor(new_cx, new_cy, prev_cx, prev_cy)

        # Add walls and features
        self._add_walls()
        self.doors = self._find_doors()
        self.chests, self.traps, self.campfires = self._decorate_rooms()
        self._add_locked_doors(max_locks=6)
        self._place_staircase()
        
        # NEW: Spawn enemies in rooms
        self._spawn_enemies()
    
    def _overlaps(self, x, y, w, h):
        """Check if room overlaps with existing rooms"""
        for room in self.rooms:
            rx, ry, rw, rh = room
            if (x - 2 < rx + rw and x + w + 2 > rx and
                y - 2 < ry + rh and y + h + 2 > ry):
                return True
        return False
    
    def _carve_room(self, room_x, room_y, room_w, room_h):
        """Carve out a room"""
        for y in range(room_y, room_y + room_h):
            for x in range(room_x, room_x + room_w):
                if 0 <= y < MAP_ROWS and 0 <= x < MAP_COLS:
                    self.tiles[y][x] = TILE_FLOOR
    
    def _carve_corridor(self, x1, y1, x2, y2):
        """Carve a corridor between points"""
        # Horizontal tunnel
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if 0 <= y1 < MAP_ROWS and 0 <= x < MAP_COLS:
                self.tiles[y1][x] = TILE_FLOOR
        # Vertical tunnel
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if 0 <= y < MAP_ROWS and 0 <= x2 < MAP_COLS:
                self.tiles[y][x2] = TILE_FLOOR
    
    def _add_walls(self):
        """Add walls around floor tiles"""
        for y in range(MAP_ROWS):
            for x in range(MAP_COLS):
                if self.tiles[y][x] != TILE_VOID:
                    continue
                
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < MAP_ROWS and 0 <= nx < MAP_COLS:
                            if self.tiles[ny][nx] == TILE_FLOOR:
                                self.tiles[y][x] = TILE_WALL
                                break
                    else:
                        continue
                    break
    
    def _is_in_room(self, x, y):
        """Check if coordinates are inside any room"""
        for rx, ry, rw, rh in self.rooms:
            if rx <= x < rx + rw and ry <= y < ry + rh:
                return True
        return False
    
    def _find_doors(self):
        """Find and place doors"""
        doors = []
        
        for y in range(1, MAP_ROWS - 1):
            for x in range(1, MAP_COLS - 1):
                if self.tiles[y][x] != TILE_FLOOR:
                    continue
                
                if self._is_in_room(x, y):
                    continue
                
                # Check door patterns
                if (self._is_in_room(x - 1, y) and self.tiles[y][x + 1] == TILE_FLOOR and
                    self.tiles[y - 1][x] == TILE_WALL and self.tiles[y + 1][x] == TILE_WALL):
                    self.tiles[y][x] = TILE_DOOR
                    doors.append({"x": x, "y": y, "locked": False, "key_id": None, "open": False})
                
                elif (self._is_in_room(x + 1, y) and self.tiles[y][x - 1] == TILE_FLOOR and
                      self.tiles[y - 1][x] == TILE_WALL and self.tiles[y + 1][x] == TILE_WALL):
                    self.tiles[y][x] = TILE_DOOR
                    doors.append({"x": x, "y": y, "locked": False, "key_id": None, "open": False})
                
                elif (self._is_in_room(x, y - 1) and self.tiles[y + 1][x] == TILE_FLOOR and
                      self.tiles[y][x - 1] == TILE_WALL and self.tiles[y][x + 1] == TILE_WALL):
                    self.tiles[y][x] = TILE_DOOR
                    doors.append({"x": x, "y": y, "locked": False, "key_id": None, "open": False})
                
                elif (self._is_in_room(x, y + 1) and self.tiles[y - 1][x] == TILE_FLOOR and
                      self.tiles[y][x - 1] == TILE_WALL and self.tiles[y][x + 1] == TILE_WALL):
                    self.tiles[y][x] = TILE_DOOR
                    doors.append({"x": x, "y": y, "locked": False, "key_id": None, "open": False})
        
        return doors
    
    def _reachable_rooms(self, blocked_tiles):
        """BFS from room 0 to find reachable rooms"""
        from collections import deque
        
        start_room = self.rooms[0]
        sx = start_room[0] + start_room[2] // 2
        sy = start_room[1] + start_room[3] // 2
        
        visited = set()
        queue = deque([(sx, sy)])
        visited.add((sx, sy))
        
        walkable = {TILE_FLOOR, TILE_DOOR, TILE_CHEST, TILE_TRAP, TILE_CAMPFIRE, TILE_STAIR}
        
        while queue:
            x, y = queue.popleft()
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = x + dx, y + dy
                if (nx, ny) in blocked_tiles:
                    continue
                if 0 <= nx < MAP_COLS and 0 <= ny < MAP_ROWS and (nx, ny) not in visited:
                    if self.tiles[ny][nx] in walkable:
                        visited.add((nx, ny))
                        queue.append((nx, ny))
        
        reachable = set()
        for i, (rx, ry, rw, rh) in enumerate(self.rooms):
            cx, cy = rx + rw // 2, ry + rh // 2
            if (cx, cy) in visited:
                reachable.add(i)
        
        return reachable
    
    def _add_locked_doors(self, max_locks=6):
        """Add locked doors and place keys in chests"""
        lockable = list(self.doors)
        random.shuffle(lockable)
        used_chests = set()
        locked_tiles = set()
        
        for j, door in enumerate(lockable[:max_locks]):
            blocked = locked_tiles | {(door["x"], door["y"])}
            reachable = self._reachable_rooms(blocked)
            
            eligible = [
                c for c in self.chests
                if c["room_index"] in reachable and id(c) not in used_chests
            ]
            
            if not eligible:
                continue
            
            key_id = f"key_{j}"
            chest = random.choice(eligible)
            used_chests.add(id(chest))
            locked_tiles.add((door["x"], door["y"]))
            door["locked"] = True
            door["key_id"] = key_id
            chest["contents"] = key_id
    
    def _decorate_rooms(self):
        """Add chests, traps, and campfires to rooms"""
        chests = []
        traps = []
        campfires = []
        
        for i, room in enumerate(self.rooms):
            rx, ry, rw, rh = room
            
            # Chests
            if i > 0 and random.random() < 0.4:
                for _ in range(5):  # Try 5 times to find a valid spot
                    cx = random.randint(rx, rx + rw - 1)
                    cy = random.randint(ry, ry + rh - 1)
                    if self.tiles[cy][cx] == TILE_FLOOR:
                        self.tiles[cy][cx] = TILE_CHEST
                        chests.append({
                            "x": cx,
                            "y": cy,
                            "contents": random.choice(["smth"]),
                            "opened": False,
                            "room_index": i
                        })
                        break
            
            # Traps
            if i > 0 and random.random() < 0.3:
                for _ in range(5):
                    tx = random.randint(rx, rx + rw - 1)
                    ty = random.randint(ry, ry + rh - 1)
                    if self.tiles[ty][tx] == TILE_FLOOR:
                        self.tiles[ty][tx] = TILE_TRAP
                        traps.append({
                            "x": tx,
                            "y": ty,
                            "damage": random.randint(5, 15),
                            "triggered": False,
                        })
                        break
            
            # Campfires
            if i > 0 and random.random() < 0.2:
                for _ in range(5):
                    lx = random.randint(rx, rx + rw - 1)
                    ly = random.randint(ry, ry + rh - 1)
                    if self.tiles[ly][lx] == TILE_FLOOR:
                        self.tiles[ly][lx] = TILE_CAMPFIRE
                        campfires.append({
                            "x": lx,
                            "y": ly,
                            "radius": 150,
                        })
                        break
        
        return chests, traps, campfires
    
    def _place_staircase(self):
        """Place stairs in the last room"""
        if not self.rooms:
            return
            
        rx, ry, rw, rh = self.rooms[-1]
        
        free = []
        for y in range(ry, ry + rh):
            for x in range(rx, rx + rw):
                if self.tiles[y][x] == TILE_FLOOR:
                    free.append((x, y))
        
        if not free:
            return
        
        sx, sy = random.choice(free)
        self.tiles[sy][sx] = TILE_STAIR
        self.staircase = {"x": sx, "y": sy}
    
    # NEW METHOD: Spawn enemies in rooms
    def _spawn_enemies(self):
        """Spawn enemies in rooms (but not the first room)"""
        enemy_types = ["basic", "fire", "water", "earth", "mini_boss"]
        
        for i, room in enumerate(self.rooms):
            # Skip first room (player spawn)
            if i == 0:
                continue
            
            # Chance to have enemies in this room (increases with room index)
            spawn_chance = 0.3 + (i * 0.02)  # 30% + 2% per room
            if random.random() > spawn_chance:
                continue
            
            rx, ry, rw, rh = room
            
            # Find all floor tiles in this room
            floor_tiles = []
            for y in range(ry, ry + rh):
                for x in range(rx, rx + rw):
                    if self.tiles[y][x] == TILE_FLOOR:
                        floor_tiles.append((x, y))
            
            if not floor_tiles:
                continue
            
            # Determine number of enemies (1-3 based on room size)
            num_enemies = min(3, max(1, rw * rh // 30))
            
            for _ in range(num_enemies):
                if not floor_tiles:
                    break
                
                # Pick a random floor tile
                ex, ey = random.choice(floor_tiles)
                floor_tiles.remove((ex, ey))  # Don't spawn two enemies on same tile
                
                # Choose enemy type based on room depth
                if i < 5:
                    enemy_type = random.choice(["basic", "basic", "fire"])  # Early rooms
                elif i < 10:
                    enemy_type = random.choice(["fire", "water", "earth"])
                elif i < 20:
                    enemy_type = random.choice(["water", "earth", "fire"])
                else:
                    # Later rooms have chance for mini_boss
                    enemy_type = random.choice(["earth", "mini_boss"] if random.random() < 0.2 else ["earth", "fire", "water"])
                
                # Create enemy
                enemy = Enemy(ex, ey, enemy_type)
                enemy.room_index = i  # Track which room they belong to
                self.enemies.append(enemy)
    
    def draw(self, screen, camera_x, camera_y):
        """Draw the dungeon"""
        for y in range(MAP_ROWS):
            for x in range(MAP_COLS):
                tile = self.tiles[y][x]
                if tile == TILE_VOID:
                    continue
                
                pixel_x = x * TILE_SIZE - camera_x
                pixel_y = y * TILE_SIZE - camera_y
                
                if pixel_x + TILE_SIZE < 0 or pixel_x > SCREEN_WIDTH:
                    continue
                if pixel_y + TILE_SIZE < 0 or pixel_y > SCREEN_HEIGHT:
                    continue
                
                rect = pygame.Rect(pixel_x, pixel_y, TILE_SIZE, TILE_SIZE)
                
                if tile == TILE_FLOOR:
                    pygame.draw.rect(screen, COLOR_FLOOR, rect)
                elif tile == TILE_WALL:
                    pygame.draw.rect(screen, COLOR_WALL, rect)
                elif tile == TILE_DOOR:
                    pygame.draw.rect(screen, COLOR_DOOR, rect)
                elif tile == TILE_CHEST:
                    pygame.draw.rect(screen, COLOR_FLOOR, rect)
                    chest_rect = pygame.Rect(pixel_x + 8, pixel_y + 12, TILE_SIZE - 16, TILE_SIZE - 20)
                    pygame.draw.rect(screen, COLOR_CHEST, chest_rect)
                elif tile == TILE_TRAP:
                    pygame.draw.rect(screen, COLOR_TRAP, rect)
                elif tile == TILE_CAMPFIRE:
                    pygame.draw.rect(screen, COLOR_FLOOR, rect)
                    center = (pixel_x + TILE_SIZE // 2, pixel_y + TILE_SIZE // 2)
                    pygame.draw.circle(screen, COLOR_CAMPFIRE, center, 8)
                elif tile == TILE_STAIR:
                    pygame.draw.rect(screen, COLOR_STAIR, rect)

# dreadful_depths.py (continued)

class Game:
    def __init__(self):
        # Initialize Pygame screen
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Dreadful Depths")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 36)
        self.small_font = pygame.font.SysFont(None, 24)
        
        # Game state
        self.state = GameState.EXPLORATION
        self.floor = 1
        
        # Generate dungeon
        self.dungeon = DungeonMap()
        self.dungeon.generate()
        
        # Spawn player in first room
        first_room = self.dungeon.rooms[0]
        spawn_tile_x = first_room[0] + first_room[2] // 2
        spawn_tile_y = first_room[1] + first_room[3] // 2
        self.player = Player(spawn_tile_x, spawn_tile_y)
        
        # Combat state
        self.current_enemy = None
        self.combat_message = ""
        self.combat_turn = "player"
        self.combat_log = []
        self.selected_item_index = 0
        
        # UI Buttons (for combat/inventory)
        self.attack_button = pygame.Rect(100, 450, 150, 50)
        self.run_button = pygame.Rect(300, 450, 150, 50)
        self.inventory_button = pygame.Rect(500, 450, 150, 50)
        self.use_item_button = pygame.Rect(100, 500, 150, 40)
        self.drop_item_button = pygame.Rect(300, 500, 150, 40)
        self.back_button = pygame.Rect(600, 500, 150, 40)
    
    def _descend(self):
        """Go down to next floor"""
        self.floor += 1
        print(f"Descending to floor {self.floor}...")
        
        # Generate new dungeon
        self.dungeon = DungeonMap()
        self.dungeon.generate()
        
        # Reset player position
        first_room = self.dungeon.rooms[0]
        spawn_tile_x = first_room[0] + first_room[2] // 2
        spawn_tile_y = first_room[1] + first_room[3] // 2
        self.player.x = spawn_tile_x * TILE_SIZE + TILE_SIZE // 2
        self.player.y = spawn_tile_y * TILE_SIZE + TILE_SIZE // 2
        self.player.tile_x = spawn_tile_x
        self.player.tile_y = spawn_tile_y
        
        # Clear combat state
        self.current_enemy = None
        self.combat_log = []

    def _handle_interact(self):
        """Handle player interaction (E key)"""
        player = self.player
        dungeon = self.dungeon
        
        # Check adjacent tiles
        for adj_dx, adj_dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            check_x = player.tile_x() + adj_dx
            check_y = player.tile_y() + adj_dy
            
            if not (0 <= check_x < MAP_COLS and 0 <= check_y < MAP_ROWS):
                continue
            
            tile = dungeon.tiles[check_y][check_x]
            
            # Stairs - go to next floor
            if tile == TILE_STAIR:
                self._descend()
                break
            
            # Doors - open or unlock
            elif tile == TILE_DOOR:
                for door in dungeon.doors:
                    if door["x"] == check_x and door["y"] == check_y:
                        if door["locked"]:
                            if door["key_id"] in player.keys:
                                door["locked"] = False
                                self.combat_log.append(f"Unlocked with {door['key_id']}!")
                            else:
                                self.combat_log.append(f"Door is locked! Need {door['key_id']}.")
                                break
                        
                        door["open"] = True
                        dungeon.tiles[check_y][check_x] = TILE_FLOOR
                        self.combat_log.append("Door opened!")
                        break
                break
            
            # Chests - open and get item
            elif tile == TILE_CHEST:
                for chest in dungeon.chests:
                    if chest["x"] == check_x and chest["y"] == check_y and not chest["opened"]:
                        chest["opened"] = True
                        dungeon.tiles[check_y][check_x] = TILE_FLOOR
                        found = chest["contents"]
                        self.combat_log.append(f"Found: {found}")
                        
                        # Handle key pickup
                        if isinstance(found, str) and found.startswith("key_"):
                            player.keys.add(found)
                            self.combat_log.append(f"Picked up {found}. Keys: {sorted(player.keys)}")
                        
                        # TODO: Add item generation for chests
                        # For now, just give a health potion
                        elif found == "smth":
                            health_potion = HealthPotion("Health Potion", 30)
                            if player.add_item(health_potion):
                                self.combat_log.append("Found Health Potion!")
                            else:
                                self.combat_log.append("Inventory full!")
                        break
                break
    
    def _check_traps(self):
        """Check if player stepped on a trap"""
        player = self.player
        dungeon = self.dungeon
        
        for trap in dungeon.traps:
            if (trap["x"] == player.tile_x() and
                trap["y"] == player.tile_y() and
                not trap["triggered"]):
                trap["triggered"] = True
                dungeon.tiles[trap["y"]][trap["x"]] = TILE_FLOOR
                damage = trap["damage"]
                self.player.take_damage(damage)
                self.combat_log.append(f"Trap! {damage} damage!")
                
                # Check if player died
                if self.player.hp <= 0:
                    self.state = GameState.GAME_OVER
                break
    
    def _check_combat_trigger(self):
        """Check if player is adjacent to an enemy"""
        if self.state != GameState.EXPLORATION:
            return
        
        # Use the methods that calculate current tile from pixel position
        player_tile_x = self.player.tile_x()  # This calls the method
        player_tile_y = self.player.tile_y()  # This calls the method
        
        for enemy in self.dungeon.enemies[:]:
            if enemy.hp <= 0:
                continue
                
            # Check if enemy is adjacent to player
            if (abs(enemy.current_tile_x - player_tile_x) <= 1 and 
                abs(enemy.current_tile_y - player_tile_y) <= 1):
                
                self.state = GameState.COMBAT
                self.current_enemy = enemy
                self.combat_turn = "player"
                self.combat_message = f"Encountered {enemy.name}!"
                self.combat_log.append(f"Encountered {enemy.name}!")
                break
    
    def _update_enemies(self, dt):
        """Update all enemies"""
        for enemy in self.dungeon.enemies:
            if enemy.hp > 0:  # Only update alive enemies
                enemy.update_movement(dt, self.dungeon.tiles)
        
        # Remove dead enemies
        self.dungeon.enemies = [e for e in self.dungeon.enemies if e.hp > 0]

    # UI Helper Methods
    def draw_text(self, text, x, y, color=WHITE, font_obj=None):
        """Draw text on screen"""
        if font_obj is None:
            font_obj = self.font
        self.screen.blit(font_obj.render(text, True, color), (x, y))
    
    def draw_button(self, rect, text, color=LIGHT_GRAY, text_color=WHITE):
        """Draw a button"""
        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, BLACK, rect, 2)
        text_surf = self.small_font.render(text, True, text_color)
        text_rect = text_surf.get_rect(center=rect.center)
        self.screen.blit(text_surf, text_rect)
    
    def draw_health_bar(self, x, y, width, height, current, maximum, color):
        """Draw a health bar"""
        # Background
        pygame.draw.rect(self.screen, DARK_GRAY, (x, y, width, height))
        # Health
        health_width = (current / maximum) * width
        if health_width > 0:
            pygame.draw.rect(self.screen, color, (x, y, health_width, height))
        # Border
        pygame.draw.rect(self.screen, WHITE, (x, y, width, height), 2)
    
    # Exploration Drawing
    def _draw_minimap(self):
        """Draw the minimap in exploration mode"""
        mw = MAP_COLS * MINIMAP_TILE
        mh = MAP_ROWS * MINIMAP_TILE
        mx = SCREEN_WIDTH - mw - MINIMAP_MARGIN
        my = MINIMAP_MARGIN
        
        # Semi-transparent background
        bg = pygame.Surface((mw, mh), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 160))
        self.screen.blit(bg, (mx, my))
        
        # Tile colors on the minimap
        color_map = {
            TILE_FLOOR: COLOR_FLOOR,
            TILE_WALL: COLOR_WALL,
            TILE_DOOR: COLOR_DOOR,
            TILE_CHEST: COLOR_CHEST,
            TILE_TRAP: COLOR_TRAP,
            TILE_CAMPFIRE: COLOR_CAMPFIRE,
            TILE_STAIR: COLOR_STAIR,
        }
        
        for y in range(MAP_ROWS):
            for x in range(MAP_COLS):
                color = color_map.get(self.dungeon.tiles[y][x])
                if color is None:
                    continue
                rect = pygame.Rect(mx + x * MINIMAP_TILE, my + y * MINIMAP_TILE, 
                                  MINIMAP_TILE, MINIMAP_TILE)
                pygame.draw.rect(self.screen, color, rect)
        
        # Player dot
        px = mx + self.player.tile_x() * MINIMAP_TILE + MINIMAP_TILE // 2
        py = my + self.player.tile_y() * MINIMAP_TILE + MINIMAP_TILE // 2
        pygame.draw.rect(self.screen, COLOR_PLAYER, pygame.Rect(px - 1, py - 1, 3, 3))
        
        # Draw enemies on minimap (small red dots)
        for enemy in self.dungeon.enemies:
            if enemy.hp > 0:
                ex = mx + enemy.current_tile_x * MINIMAP_TILE + MINIMAP_TILE // 2
                ey = my + enemy.current_tile_y * MINIMAP_TILE + MINIMAP_TILE // 2
                pygame.draw.rect(self.screen, RED, pygame.Rect(ex - 1, ey - 1, 3, 3))
    
    def draw_exploration(self):
        """Draw the exploration mode"""
        self.screen.fill(COLOR_BLACK)
        
        # Calculate camera
        camera_x = self.player.x - SCREEN_WIDTH // 2
        camera_y = self.player.y - SCREEN_HEIGHT // 2
        
        # Draw dungeon
        self.dungeon.draw(self.screen, camera_x, camera_y)
        
        # Draw enemies
        for enemy in self.dungeon.enemies:
            if enemy.hp > 0:
                enemy.draw(self.screen, camera_x, camera_y)
        
        # Draw player
        self.player.draw(self.screen, camera_x, camera_y)
        
        # Draw minimap
        self._draw_minimap()
        
        # Draw UI text
        self.draw_text(f"HP: {self.player.hp}/{self.player.max_hp}", 10, 10, RED)
        self.draw_text(f"Floor: {self.floor}", 10, 50, WHITE)
        self.draw_text(f"Level: {self.player.level} | XP: {self.player.xp}", 10, 90, WHITE)
        
        if self.player.equipped_weapon:
            self.draw_text(f"Weapon: {self.player.equipped_weapon.name}", 10, 130, YELLOW, self.small_font)
        
        # Draw inventory button
        self.draw_button(self.inventory_button, "Inventory (I)")
        
        # Draw controls hint
        self.draw_text("WASD: Move | E: Interact | I: Inventory", 
                      200, SCREEN_HEIGHT - 30, WHITE, self.small_font)
    
    # Combat Drawing
    def draw_combat(self):
        """Draw the combat mode"""
        self.screen.fill(DARK_GRAY)
        
        # Check if we have a current enemy (safety check)
        if not self.current_enemy:
            # If no enemy, return to exploration
            self.state = GameState.EXPLORATION
            return
        
        # Player health bar
        self.draw_health_bar(50, 50, 200, 30, self.player.hp, self.player.max_hp, GREEN)
        self.draw_text(f"Player HP: {self.player.hp}", 260, 55)
        
        # Enemy health bar
        if self.current_enemy:
            self.draw_health_bar(50, 100, 200, 30, self.current_enemy.hp, 
                                self.current_enemy.max_hp, RED)
            
            # Enemy info
            enemy_element_color = ELEMENT_COLORS[self.current_enemy.element]
            self.draw_text(f"{self.current_enemy.name}", 260, 105, WHITE)
            self.draw_text(f"HP: {self.current_enemy.hp}/{self.current_enemy.max_hp}", 260, 125)
            self.draw_text(f"Element: {self.current_enemy.element.name}", 260, 145, enemy_element_color)
            
            # Draw enemy sprite larger in combat
            if self.current_enemy.image:
                # Draw enemy in center of screen
                enemy_rect = pygame.Rect(SCREEN_WIDTH//2 - 50, 180, 100, 100)
                scaled_img = pygame.transform.scale(self.current_enemy.image, (100, 100))
                self.screen.blit(scaled_img, enemy_rect)
        
        # Weapon info
        if self.player.equipped_weapon:
            weapon = self.player.equipped_weapon
            weapon_element_color = ELEMENT_COLORS[weapon.element]
            multiplier = weapon.get_damage_multiplier(self.current_enemy.element)
            
            self.draw_text(f"Weapon: {weapon.name}", 50, 200, WHITE)
            self.draw_text(f"Element: {weapon.element.name}", 50, 225, weapon_element_color)
            self.draw_text(f"Damage: {weapon.damage} + {self.player.level * 2} (lvl bonus)", 50, 250, WHITE, self.small_font)
            
            # Show effectiveness
            if multiplier > 1:
                eff_text = f"SUPER EFFECTIVE! ({multiplier}x)"
                eff_color = GREEN
            elif multiplier < 1:
                eff_text = f"NOT VERY EFFECTIVE ({multiplier}x)"
                eff_color = RED
            else:
                eff_text = "NORMAL DAMAGE"
                eff_color = WHITE
            self.draw_text(eff_text, 50, 275, eff_color)
        
        # Combat buttons
        self.draw_button(self.attack_button, "ATTACK")
        self.draw_button(self.run_button, "RUN (50%)")
        self.draw_button(self.inventory_button, "INVENTORY")
        
        # Combat log (last 5 messages)
        for i, msg in enumerate(self.combat_log[-5:]):
            self.draw_text(msg, 50, 350 + i * 25, WHITE, self.small_font)
        
        # Turn indicator
        turn_color = GREEN if self.combat_turn == "player" else RED
        self.draw_text(self.combat_message, 300, 500, turn_color)
    
    # Inventory Drawing
    def draw_inventory(self):
        """Draw the inventory mode"""
        self.screen.fill(DARK_GRAY)
        
        self.draw_text("INVENTORY", 350, 20, YELLOW)
        self.draw_text(f"Slots: {len(self.player.inventory)}/{self.player.max_inventory}", 350, 60)
        
        if not self.player.inventory:
            self.draw_text("Inventory empty", 300, 200, GRAY)
        else:
            for i, item in enumerate(self.player.inventory):
                # Draw background for selected item
                if i == self.selected_item_index:
                    pygame.draw.rect(self.screen, (70, 70, 70), (80, 90 + i * 60, 640, 50))
                
                # Item name and type
                item_text = f"{item.name}"
                if item.type == ItemType.WEAPON:
                    item_text += f" (DMG: {item.damage}, {item.element.name})"
                elif item.type == ItemType.HEALTH:
                    item_text += f" (Heal: {item.value})"
                elif item.type == ItemType.ARMOR:
                    item_text += f" (DEF: {item.defense})"
                
                # Truncate if too long
                if len(item_text) > 40:
                    item_text = item_text[:37] + "..."
                
                color = YELLOW if i == self.selected_item_index else WHITE
                self.draw_text(item_text, 100, 100 + i * 60, color, self.small_font)
                
                # Draw equipped indicator
                if item == self.player.equipped_weapon:
                    self.draw_text("[EQUIPPED WEAPON]", 550, 100 + i * 60, GREEN, self.small_font)
                elif item == self.player.equipped_armor:
                    self.draw_text("[EQUIPPED ARMOR]", 550, 100 + i * 60, BLUE, self.small_font)
        
        # Buttons
        self.draw_button(self.use_item_button, "Use/Equip")
        self.draw_button(self.drop_item_button, "Drop")
        self.draw_button(self.back_button, "Back")
        
        # Keys info
        if self.player.keys:
            keys_text = f"Keys: {', '.join(sorted(self.player.keys))}"
            self.draw_text(keys_text, 100, 500, YELLOW, self.small_font)
    
    # Game Over and Victory Drawing
    def draw_game_over(self):
        """Draw game over screen"""
        self.screen.fill(BLACK)
        self.draw_text("GAME OVER", 250, 250, RED, pygame.font.SysFont(None, 72))
        self.draw_text(f"You reached floor {self.floor}", 300, 350, WHITE)
        self.draw_text("Press SPACE to restart or ESC to quit", 200, 450, WHITE, self.small_font)
    
    def draw_victory(self):
        """Draw victory screen"""
        self.screen.fill(DARK_GRAY)
        self.draw_text("VICTORY!", 300, 200, YELLOW, pygame.font.SysFont(None, 72))
        self.draw_text("All enemies defeated!", 300, 300, GREEN)
        self.draw_text(f"Final Level: {self.player.level} | XP: {self.player.xp}", 280, 350, WHITE)
        self.draw_text("Press SPACE to play again or ESC to quit", 200, 450, WHITE, self.small_font)

    # dreadful_depths.py (continued)
# Add these methods inside the Game class

    def handle_exploration(self, events):
        """Handle events in exploration mode"""
        # Player movement (handled in update, not here)
        
        # Check for enemy encounters
        self._check_combat_trigger()
        
        # Check for traps
        self._check_traps()
        
        # Handle events
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e:
                    self._handle_interact()
                elif event.key == pygame.K_i:
                    self.state = GameState.INVENTORY
                    self.combat_log.append("Opened inventory")
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.inventory_button.collidepoint(event.pos):
                    self.state = GameState.INVENTORY
                    self.combat_log.append("Opened inventory")
    
    def handle_combat(self, events):
        """Handle events in combat mode"""
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                # Attack button
                if self.attack_button.collidepoint(mouse_pos) and self.combat_turn == "player":
                    # Player attacks
                    damage = self.player.calculate_damage(self.current_enemy.element)
                    
                    # Check for critical hit (10% chance)
                    is_critical = random.random() < 0.1
                    if is_critical:
                        damage = int(damage * 2)
                    
                    # Apply damage
                    enemy_defeated = self.current_enemy.take_damage(damage)
                    
                    # Add to combat log
                    crit_text = "CRITICAL! " if is_critical else ""
                    element_text = f"({self.player.equipped_weapon.element.name} vs {self.current_enemy.element.name})"
                    self.combat_log.append(f"{crit_text}You dealt {damage} damage {element_text}")
                    
                    if enemy_defeated:
                        # Victory
                        xp_gained = self.current_enemy.xp_reward
                        leveled_up = self.player.gain_xp(xp_gained)
                        self.combat_log.append(f"Victory! Gained {xp_gained} XP")
                        if leveled_up:
                            self.combat_log.append(f"Level Up! Now level {self.player.level}!")
                        
                        # Remove enemy from dungeon
                        self.dungeon.enemies.remove(self.current_enemy)
                        
                        # Check if all enemies are defeated
                        if not self.dungeon.enemies:
                            self.state = GameState.VICTORY
                        else:
                            self.state = GameState.EXPLORATION
                        self.current_enemy = None
                    else:
                        # Enemy turn
                        self.combat_turn = "enemy"
                        self.combat_message = "Enemy's turn..."
                
                # Run button
                elif self.run_button.collidepoint(mouse_pos) and self.combat_turn == "player":
                    # Attempt to run (50% chance)
                    if random.random() < 0.5:
                        # Success - push player away from enemy
                        if self.current_enemy:
                            # Move player away from enemy direction
                            dx = self.player.tile_x() - self.current_enemy.tile_x
                            dy = self.player.tile_y() - self.current_enemy.tile_y
                            
                            # Normalize and push
                            if abs(dx) > abs(dy):
                                self.player.x += (1 if dx > 0 else -1) * TILE_SIZE * 2
                            else:
                                self.player.y += (1 if dy > 0 else -1) * TILE_SIZE * 2
                            
                            # Keep player in bounds
                            self.player.x = max(TILE_SIZE//2, min(self.player.x, MAP_COLS * TILE_SIZE - TILE_SIZE//2))
                            self.player.y = max(TILE_SIZE//2, min(self.player.y, MAP_ROWS * TILE_SIZE - TILE_SIZE//2))
                        
                        self.state = GameState.EXPLORATION
                        self.combat_log.append("You escaped!")
                        self.current_enemy = None
                    else:
                        self.combat_log.append("Couldn't escape!")
                        self.combat_turn = "enemy"
                
                # Inventory button
                elif self.inventory_button.collidepoint(mouse_pos):
                    self.state = GameState.INVENTORY
                    self.combat_log.append("Opened inventory")
        
        # Enemy turn (delayed)
        if self.combat_turn == "enemy" and self.current_enemy:
            pygame.time.wait(500)  # Short delay for dramatic effect
            damage = self.current_enemy.damage
            player_dead = self.player.take_damage(damage)
            self.combat_log.append(f"{self.current_enemy.name} dealt {damage} damage!")
            
            if player_dead:
                self.state = GameState.GAME_OVER
                self.combat_message = "You died!"
            else:
                self.combat_turn = "player"
                self.combat_message = "Your turn!"
    
    def handle_inventory(self, events):
        """Handle events in inventory mode"""
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                # Item selection (click on items)
                for i, item in enumerate(self.player.inventory):
                    item_rect = pygame.Rect(80, 90 + i * 60, 640, 50)
                    if item_rect.collidepoint(mouse_pos):
                        self.selected_item_index = i
                        self.combat_log.append(f"Selected {item.name}")
                
                # Use/Equip button
                if self.use_item_button.collidepoint(mouse_pos):
                    if self.selected_item_index < len(self.player.inventory):
                        item = self.player.inventory[self.selected_item_index]
                        
                        if item.type == ItemType.HEALTH:
                            # Use health potion
                            self.player.heal(item.value)
                            self.player.inventory.pop(self.selected_item_index)
                            self.combat_log.append(f"Used {item.name}, healed {item.value} HP")
                            
                            # Adjust selection if needed
                            if self.selected_item_index >= len(self.player.inventory):
                                self.selected_item_index = max(0, len(self.player.inventory) - 1)
                        
                        elif item.type == ItemType.WEAPON:
                            # Equip weapon
                            self.player.equip_weapon(item)
                            self.combat_log.append(f"Equipped {item.name}")
                        
                        elif item.type == ItemType.ARMOR:
                            # Equip armor
                            self.player.equip_armor(item)
                            self.combat_log.append(f"Equipped {item.name}")
                
                # Drop button
                elif self.drop_item_button.collidepoint(mouse_pos):
                    if self.selected_item_index < len(self.player.inventory):
                        dropped_item = self.player.inventory.pop(self.selected_item_index)
                        self.combat_log.append(f"Dropped {dropped_item.name}")
                        
                        # Adjust selection if needed
                        if self.selected_item_index >= len(self.player.inventory):
                            self.selected_item_index = max(0, len(self.player.inventory) - 1)
                
                # Back button
                elif self.back_button.collidepoint(mouse_pos):
                    # Return to previous state
                    if self.current_enemy:
                        self.state = GameState.COMBAT
                    else:
                        self.state = GameState.EXPLORATION
                    self.combat_log.append("Closed inventory")
            
            # Keyboard navigation
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_item_index = max(0, self.selected_item_index - 1)
                elif event.key == pygame.K_DOWN:
                    self.selected_item_index = min(len(self.player.inventory) - 1, self.selected_item_index + 1)
                elif event.key == pygame.K_RETURN:
                    # Use selected item
                    if self.selected_item_index < len(self.player.inventory):
                        item = self.player.inventory[self.selected_item_index]
                        if item.type == ItemType.HEALTH:
                            self.player.heal(item.value)
                            self.player.inventory.pop(self.selected_item_index)
                            self.combat_log.append(f"Used {item.name}, healed {item.value} HP")
                            if self.selected_item_index >= len(self.player.inventory):
                                self.selected_item_index = max(0, len(self.player.inventory) - 1)
                elif event.key == pygame.K_ESCAPE:
                    # Back to previous state
                    if self.current_enemy:
                        self.state = GameState.COMBAT
                    else:
                        self.state = GameState.EXPLORATION
                    self.combat_log.append("Closed inventory")

    # dreadful_depths.py (continued)
# Add this method inside the Game class

    def run(self):
        """Main game loop"""
        running = True
        
        while running:
            # Calculate delta time
            dt = self.clock.tick(FPS) / 1000.0
            
            # Get events
            events = pygame.event.get()
            
            # Handle quit events
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                
                # Global key handlers
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state == GameState.INVENTORY:
                            # Back from inventory
                            if self.current_enemy:
                                self.state = GameState.COMBAT
                            else:
                                self.state = GameState.EXPLORATION
                        elif self.state == GameState.EXPLORATION:
                            # Maybe pause menu? For now just continue
                            pass
                    
                    # Restart on game over or victory
                    if self.state in [GameState.GAME_OVER, GameState.VICTORY]:
                        if event.key == pygame.K_SPACE:
                            # Restart game
                            self.__init__()
                            return self.run()  # Restart the game loop
                        elif event.key == pygame.K_ESCAPE:
                            running = False
            
            # Handle states
            if self.state == GameState.EXPLORATION:
                # Update player movement
                self.player.update(pygame.key.get_pressed(), dt, self.dungeon.tiles)
                
                # Update enemies
                self._update_enemies(dt)
                
                # Handle exploration events
                self.handle_exploration(events)
                
                # Draw exploration
                self.draw_exploration()
                
            elif self.state == GameState.COMBAT:
                # Handle combat events
                self.handle_combat(events)
                
                # Draw combat
                self.draw_combat()
                
            elif self.state == GameState.INVENTORY:
                # Handle inventory events
                self.handle_inventory(events)
                
                # Draw inventory
                self.draw_inventory()
                
            elif self.state == GameState.GAME_OVER:
                # Draw game over screen
                self.draw_game_over()
                
            elif self.state == GameState.VICTORY:
                # Draw victory screen
                self.draw_victory()
            
            # Update display
            pygame.display.flip()
        
        # Quit game
        pygame.quit()
        sys.exit()


# Add this at the very end of the file to run the game
if __name__ == "__main__":
    game = Game()
    game.run()