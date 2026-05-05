import random

import pygame

from config import (
    TILE_SIZE, MAP_COLS, MAP_ROWS,
    MIN_ROOM_SIZE, MAX_ROOM_SIZE, MAX_ROOMS,
    SCREEN_WIDTH, SCREEN_HEIGHT,
    TILE_VOID, TILE_FLOOR, TILE_WALL, TILE_DOOR, TILE_CHEST,
    TILE_TRAP, TILE_CAMPFIRE, TILE_STAIR,
)
from enemy import Enemy


class DungeonMap:
    TRAP_FRAME_DURATION = 0.30
    CAMPFIRE_FRAME_DURATION = 0.12
    DIFFICULTY_PER_FLOOR = 0.15

    def __init__(self):
        self.tiles     = []
        self.rooms     = []
        self.doors     = []
        self.chests    = []
        self.traps     = []
        self.campfires = []
        self.staircase = None
        self.floor_variants = []
        self.enemies = []
        self.floor = 1

        self.trap_anim_frame = 0
        self.trap_anim_timer = 0.0
        self.campfire_anim_frame = 0
        self.campfire_anim_timer = 0.0

    def _difficulty_mult(self):
        return 1.0 + self.DIFFICULTY_PER_FLOOR * (self.floor - 1)

    def generate(self, floor=1):
        self.floor = floor
        self.tiles = []
        for row in range(MAP_ROWS):
            self.tiles.append([TILE_VOID] * MAP_COLS)
        self.rooms = []
        self.enemies = []  

        for _ in range(MAX_ROOMS):
            # Random room size
            w = random.randint(MIN_ROOM_SIZE, MAX_ROOM_SIZE)
            h = random.randint(MIN_ROOM_SIZE, MAX_ROOM_SIZE)

            # Random position (leave 1 tile border around map edges)
            x = random.randint(1, MAP_COLS - w - 1)
            y = random.randint(1, MAP_ROWS - h - 1)

            if self._overlaps(x, y, w, h):
                continue

            self._carve_room(x, y, w, h)
            self.rooms.append((x, y, w, h))

            # Connect to previous room with a corridor
            if len(self.rooms) > 1:
                # Center of new room
                new_cx = x + w // 2
                new_cy = y + h // 2

                # Center of previous room
                px, py, pw, ph = self.rooms[-2]
                prev_cx = px + pw // 2
                prev_cy = py + ph // 2

                # Randomly choose: go horizontal first or vertical first
                if random.random() < 0.5:
                    self._carve_corridor(prev_cx, prev_cy, new_cx, new_cy)
                else:
                    self._carve_corridor(new_cx, new_cy, prev_cx, prev_cy)

        self._add_walls()
        self.doors = self._find_doors()
        self.chests, self.traps, self.campfires = self._decorate_rooms()
        self._add_locked_doors(max_locks=6)
        self._place_staircase()
        self.floor_variants = [[random.randint(0, 2) for _ in range(MAP_COLS)] for _ in range(MAP_ROWS)]
        self._spawn_enemies()  

    def _overlaps(self, x, y, w, h):
        for room in self.rooms:
            rx, ry, rw, rh = room
            new_left   = x - 2
            new_right  = x + w + 2
            new_top    = y - 2
            new_bottom = y + h + 2

            old_left   = rx
            old_right  = rx + rw
            old_top    = ry
            old_bottom = ry + rh

            x_overlap = new_left < old_right and new_right > old_left
            y_overlap = new_top < old_bottom and new_bottom > old_top

            if x_overlap and y_overlap:
                return True
        return False

    def _carve_room(self, room_x, room_y, room_w, room_h):
        for y in range(room_y, room_y + room_h):
            for x in range(room_x, room_x + room_w):
                if 0 <= y < MAP_ROWS and 0 <= x < MAP_COLS:
                    self.tiles[y][x] = TILE_FLOOR

    def _carve_corridor(self, x1, y1, x2, y2):
        # Horizontal tunnel from x1 to x2 at row y1
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if 0 <= y1 < MAP_ROWS and 0 <= x < MAP_COLS:
                self.tiles[y1][x] = TILE_FLOOR
        # Vertical tunnel from y1 to y2 at column x2
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if 0 <= y < MAP_ROWS and 0 <= x2 < MAP_COLS:
                self.tiles[y][x2] = TILE_FLOOR

    def _add_walls(self):
        for y in range(MAP_ROWS):
            for x in range(MAP_COLS):
                if self.tiles[y][x] != TILE_VOID:
                    continue  # skip tiles that are already floor

                # Check all 8 neighbors
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        ny = y + dy  # neighbour y
                        nx = x + dx  # neighbour x

                        if 0 <= ny < MAP_ROWS and 0 <= nx < MAP_COLS:
                            if self.tiles[ny][nx] == TILE_FLOOR:
                                self.tiles[y][x] = TILE_WALL
                                break
                    else:
                        continue
                    break

    def _is_in_room(self, x, y):
        # True if (x,y) is inside the interior rectangle of any room.
        for rx, ry, rw, rh in self.rooms:
            if rx <= x < rx + rw and ry <= y < ry + rh:
                return True
        return False

    def _find_doors(self):
        doors = []
        tiles = self.tiles

        for y in range(1, MAP_ROWS - 1):
            for x in range(1, MAP_COLS - 1):

                # Must be floor
                if tiles[y][x] != TILE_FLOOR:
                    continue

                # Place doors in corridor entrance tiles, not inside rooms
                if self._is_in_room(x, y):
                    continue

                # Entrance patterns:

                # Room on LEFT -> corridor continues RIGHT, walls up/down
                if (self._is_in_room(x - 1, y) and tiles[y][x + 1] == TILE_FLOOR and
                        tiles[y - 1][x] == TILE_WALL and tiles[y + 1][x] == TILE_WALL):
                    tiles[y][x] = TILE_DOOR
                    doors.append({"x": x, "y": y, "locked": False, "key_id": None, "open": False})
                    continue

                # Room on RIGHT -> corridor continues LEFT, walls up/down
                if (self._is_in_room(x + 1, y) and tiles[y][x - 1] == TILE_FLOOR and
                        tiles[y - 1][x] == TILE_WALL and tiles[y + 1][x] == TILE_WALL):
                    tiles[y][x] = TILE_DOOR
                    doors.append({"x": x, "y": y, "locked": False, "key_id": None, "open": False})
                    continue

                # Room ABOVE -> corridor continues DOWN, walls left/right
                if (self._is_in_room(x, y - 1) and tiles[y + 1][x] == TILE_FLOOR and
                        tiles[y][x - 1] == TILE_WALL and tiles[y][x + 1] == TILE_WALL):
                    tiles[y][x] = TILE_DOOR
                    doors.append({"x": x, "y": y, "locked": False, "key_id": None, "open": False})
                    continue

                # Room BELOW -> corridor continues UP, walls left/right
                if (self._is_in_room(x, y + 1) and tiles[y - 1][x] == TILE_FLOOR and
                        tiles[y][x - 1] == TILE_WALL and tiles[y][x + 1] == TILE_WALL):
                    tiles[y][x] = TILE_DOOR
                    doors.append({"x": x, "y": y, "locked": False, "key_id": None, "open": False})
                    continue

        return doors

    def _reachable_rooms(self, blocked_tiles):
        """BFS from room 0 center, treating all blocked_tiles as impassable.
        Returns set of room indices reachable from room 0."""
        from collections import deque

        # Start BFS from the center of the spawn room (room 0)
        start_room = self.rooms[0]
        sx = start_room[0] + start_room[2] // 2
        sy = start_room[1] + start_room[3] // 2

        visited = set()
        queue = deque([(sx, sy)])
        visited.add((sx, sy))

        walkable = {TILE_FLOOR, TILE_DOOR, TILE_CHEST, TILE_TRAP, TILE_CAMPFIRE, TILE_STAIR}

        # Traverse from spawn, skipping locked door tiles
        while queue:
            x, y = queue.popleft()
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = x + dx, y + dy
                # Treat locked door tiles as walls
                if (nx, ny) in blocked_tiles:
                    continue
                if 0 <= nx < MAP_COLS and 0 <= ny < MAP_ROWS and (nx, ny) not in visited:
                    if self.tiles[ny][nx] in walkable:
                        visited.add((nx, ny))
                        queue.append((nx, ny))

        # Check which rooms were reached by testing their center tile
        reachable = set()
        for i, (rx, ry, rw, rh) in enumerate(self.rooms):
            cx, cy = rx + rw // 2, ry + rh // 2
            if (cx, cy) in visited:
                reachable.add(i)

        return reachable

    def _add_locked_doors(self, max_locks=4):
        lockable = list(self.doors)
        random.shuffle(lockable)
        used_chests = set()
        locked_tiles = set() 

        for j, door in enumerate(lockable[:max_locks]):
            # Block this door AND all previously locked doors
            blocked = locked_tiles | {(door["x"], door["y"])} 
            # Find rooms the player can reach without passing through any blocked door
            reachable = self._reachable_rooms(blocked)
            # Only place the key in a chest the player can actually get to
            eligible = [
                c for c in self.chests
                if c["room_index"] in reachable and id(c) not in used_chests 
            ]
            if not eligible:
                continue  # no reachable chest available — keep door unlocked
            key_id = f"key_{j}"
            chest = random.choice(eligible)
            used_chests.add(id(chest))
            locked_tiles.add((door["x"], door["y"]))
            door["locked"]    = True
            door["key_id"]    = key_id
            chest["contents"] = key_id

    def _decorate_rooms(self):
        chests = []
        traps = []
        campfires = []
        mult = self._difficulty_mult()

        for i, room in enumerate(self.rooms):
            rx, ry, rw, rh = room

            # Chests
            if i > 0 and random.random() < 0.8:  # i > 0 to prevent spawning in the first room
                cx = random.randint(rx, rx + rw - 1)
                cy = random.randint(ry, ry + rh - 1)
                if self.tiles[cy][cx] == TILE_FLOOR:
                    self.tiles[cy][cx] = TILE_CHEST
                    chests.append({
                        "x": cx,
                        "y": cy,
                        "contents": random.choice(["smth", "torch"]),
                        "opened": False,
                        "room_index": i
                    })

            # Traps
            if i > 0 and random.random() < 0.3:
                tx = random.randint(rx,  rx + rw - 1)
                ty = random.randint(ry, ry + rh - 1)
                if self.tiles[ty][tx] == TILE_FLOOR:
                    self.tiles[ty][tx] = TILE_TRAP
                    traps.append({
                        "x": tx,
                        "y": ty,
                        "damage": max(1, int(random.randint(5, 15) * mult)),
                        "triggered": False,
                    })

            # Campfires
            if i > 0 and random.random() < 0.2:
                lx = random.randint(rx, rx + rw - 1)
                ly = random.randint(ry, ry + rh - 1)
                if self.tiles[ly][lx] == TILE_FLOOR:
                    self.tiles[ly][lx] = TILE_CAMPFIRE
                    campfires.append({
                        "x": lx,
                        "y": ly,
                        "radius": 150,
                    })

        return chests, traps, campfires

    def _place_staircase(self):
        rx, ry, rw, rh = self.rooms[-1]

        # Collect all free floor tiles in the last room
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

    
    def _spawn_enemies(self):
        """Spawn enemies in rooms (skip room 0 = player spawn)."""
        mult = self._difficulty_mult()
        for i, room in enumerate(self.rooms):
            if i == 0:
                continue
            # Spawn chance increases with room depth
            spawn_chance = 0.3 + (i * 0.02)
            if random.random() > spawn_chance:
                continue

            rx, ry, rw, rh = room
            floor_tiles = []
            for y in range(ry, ry + rh):
                for x in range(rx, rx + rw):
                    if self.tiles[y][x] == TILE_FLOOR:
                        floor_tiles.append((x, y))
            
            if not floor_tiles:
                continue

            num_enemies = min(3, max(1, rw * rh // 30))
            for _ in range(num_enemies):
                if not floor_tiles:
                    break
                ex, ey = random.choice(floor_tiles)
                floor_tiles.remove((ex, ey))

                # Difficulty scales with room index
                if i < 5:
                    enemy_type = random.choice(["basic", "basic", "fire"])  # Early rooms
                elif i < 10:
                    enemy_type = random.choice(["fire", "water", "earth"])
                elif i < 20:
                    enemy_type = random.choice(["water", "earth", "fire"])
                else:
                    # Later rooms have chance for mini_boss
                    enemy_type = random.choice(
                        ["earth", "mini_boss"] if random.random() < 0.2
                        else ["earth", "fire", "water"])

                # Create enemy
                enemy = Enemy(ex, ey, enemy_type, difficulty_mult=mult)
                enemy.room_index = i
                self.enemies.append(enemy)
    

    def open_door(self, x, y, player_keys):
        """Try to open the door at (x, y). Returns 'opened', 'unlocked', 'locked', or None."""
        for door in self.doors:
            if door["x"] != x or door["y"] != y:
                continue
            if door["locked"]:
                if door["key_id"] not in player_keys:
                    return "locked"
                door["locked"] = False
                door["open"] = True
                self.tiles[y][x] = TILE_FLOOR
                return "unlocked"
            door["open"] = True
            self.tiles[y][x] = TILE_FLOOR
            return "opened"
        return None

    def open_chest(self, x, y):
        """Open the chest at (x, y). Returns its contents, or None if no unopened chest."""
        for chest in self.chests:
            if chest["x"] == x and chest["y"] == y and not chest["opened"]:
                chest["opened"] = True
                self.tiles[y][x] = TILE_FLOOR
                return chest["contents"]
        return None

    def update(self, dt):
        """Advance shared tile animations"""
        self.trap_anim_timer += dt
        if self.trap_anim_timer >= self.TRAP_FRAME_DURATION:
            self.trap_anim_timer -= self.TRAP_FRAME_DURATION
            self.trap_anim_frame = (self.trap_anim_frame + 1) % 4

        self.campfire_anim_timer += dt
        if self.campfire_anim_timer >= self.CAMPFIRE_FRAME_DURATION:
            self.campfire_anim_timer -= self.CAMPFIRE_FRAME_DURATION
            self.campfire_anim_frame = (self.campfire_anim_frame + 1) % 6

    def trigger_trap(self, x, y):
        """Trigger the trap at (x, y) if present. Returns damage dealt, or None."""
        for trap in self.traps:
            if trap["x"] == x and trap["y"] == y and not trap["triggered"]:
                trap["triggered"] = True
                self.tiles[y][x] = TILE_FLOOR
                return trap["damage"]
        return None

    def draw(self, screen, camera_x, camera_y, assets):
        for y in range(MAP_ROWS):
            for x in range(MAP_COLS):
                tile = self.tiles[y][x]
                if tile == TILE_VOID:
                    continue

                # Convert tile coordinates to pixel coordinates
                pixel_x = x * TILE_SIZE - camera_x
                pixel_y = y * TILE_SIZE - camera_y

                if pixel_x + TILE_SIZE < 0 or pixel_x > SCREEN_WIDTH:
                    continue
                if pixel_y + TILE_SIZE < 0 or pixel_y > SCREEN_HEIGHT:
                    continue

                pos = (pixel_x, pixel_y)

                if tile == TILE_FLOOR:
                    variant = self.floor_variants[y][x]
                    screen.blit(assets.floor_tiles[variant], pos)
                elif tile == TILE_WALL:
                   screen.blit(assets.wall, pos)
                elif tile == TILE_DOOR:
                    screen.blit(assets.door, pos)
                elif tile == TILE_CHEST:
                    variant = self.floor_variants[y][x]
                    screen.blit(assets.floor_tiles[variant], pos)
                    screen.blit(assets.chest, pos)
                elif tile == TILE_TRAP:
                    variant = self.floor_variants[y][x]
                    screen.blit(assets.floor_tiles[variant], pos)
                    screen.blit(assets.trap_frames[self.trap_anim_frame], pos)
                elif tile == TILE_CAMPFIRE:
                    variant = self.floor_variants[y][x]
                    screen.blit(assets.floor_tiles[variant], pos)
                    screen.blit(assets.campfire_frames[self.campfire_anim_frame], pos)
                elif tile == TILE_STAIR:
                    variant = self.floor_variants[y][x]
                    screen.blit(assets.floor_tiles[variant], pos)
                    screen.blit(assets.stairs, pos)

