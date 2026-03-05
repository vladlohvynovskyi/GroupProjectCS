import pygame
import sys
import random

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

# Minimap
MINIMAP_TILE   = 3
MINIMAP_MARGIN = 8


class Player:
    SIZE  = TILE_SIZE - 12
    SPEED = 500

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.keys: set = set()

    def tile_x(self) -> int:
        return int(self.x) // TILE_SIZE

    def tile_y(self) -> int:
        return int(self.y) // TILE_SIZE

    def can_move(self, tiles, x: float, y: float) -> bool:
        walkable = [TILE_FLOOR, TILE_CAMPFIRE, TILE_TRAP, TILE_STAIR]
        half = self.SIZE // 2

        # Check all four corners of the player's bounding box
        corners = [
            (x - half, y - half),  # top-left
            (x + half, y - half),  # top-right
            (x - half, y + half),  # bottom-left
            (x + half, y + half),  # bottom-right
        ]

        for corner_x, corner_y in corners:
            # Convert pixel to tile
            tile_x = int(corner_x) // TILE_SIZE
            tile_y = int(corner_y) // TILE_SIZE

            # Out of bounds check
            if tile_x < 0 or tile_x >= MAP_COLS or tile_y < 0 or tile_y >= MAP_ROWS:
                return False

            # Check if not walkable (not floor tile)
            if tiles[tile_y][tile_x] not in walkable:
                return False

        return True

    def update(self, keys_pressed, dt: float, tiles) -> None:
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

    def draw(self, screen, camera_x: float, camera_y: float) -> None:
        rect = pygame.Rect(
            int(self.x - camera_x) - self.SIZE // 2,
            int(self.y - camera_y) - self.SIZE // 2,
            self.SIZE,
            self.SIZE,
        )
        pygame.draw.rect(screen, COLOR_PLAYER, rect)


class DungeonMap:
    def __init__(self):
        self.tiles     = []
        self.rooms     = []
        self.doors     = []
        self.chests    = []
        self.traps     = []
        self.campfires = []
        self.staircase = None

    def generate(self):
        self.tiles = []
        for row in range(MAP_ROWS):
            self.tiles.append([TILE_VOID] * MAP_COLS)
        self.rooms = []

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

    def _add_locked_doors(self, max_locks=6):
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

        for i, room in enumerate(self.rooms):
            rx, ry, rw, rh = room

            # Chests
            if i > 0 and random.random() < 0.4:  # i > 0 to prevent spawning in the first room
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

            # Traps
            if i > 0 and random.random() < 0.3:
                tx = random.randint(rx,  rx + rw - 1)
                ty = random.randint(ry, ry + rh - 1)
                if self.tiles[ty][tx] == TILE_FLOOR:
                    self.tiles[ty][tx] = TILE_TRAP
                    traps.append({
                        "x": tx,
                        "y": ty,
                        "damage": random.randint(5, 15),
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

    def draw(self, screen, camera_x, camera_y):
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
                    pygame.draw.rect(screen, COLOR_TRAP, rect) # Change to COLOR_FLOOR to make invisible
                elif tile == TILE_CAMPFIRE:
                    pygame.draw.rect(screen, COLOR_FLOOR, rect)
                    center = (pixel_x + TILE_SIZE // 2, pixel_y + TILE_SIZE // 2)
                    pygame.draw.circle(screen, COLOR_CAMPFIRE, center, 8)
                elif tile == TILE_STAIR:
                    pygame.draw.rect(screen, COLOR_STAIR, rect)
    


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Dreadful Depths")
        self.clock = pygame.time.Clock()

        self.floor = 1

        self.dungeon = DungeonMap()
        self.dungeon.generate()


        first_room = self.dungeon.rooms[0]
        spawn_x = float(first_room[0] * TILE_SIZE + first_room[2] * TILE_SIZE / 2)
        spawn_y = float(first_room[1] * TILE_SIZE + first_room[3] * TILE_SIZE / 2)
        self.player = Player(spawn_x, spawn_y)

    def _descend(self):
        self.floor += 1
        print(f"Descending to floor {self.floor}...")
        self.dungeon = DungeonMap()
        self.dungeon.generate()

        first_room = self.dungeon.rooms[0]
        self.player.x = float(first_room[0] * TILE_SIZE + first_room[2] * TILE_SIZE / 2)
        self.player.y = float(first_room[1] * TILE_SIZE + first_room[3] * TILE_SIZE / 2)
        self.player.keys = set()

    def _handle_interact(self):
        player  = self.player
        dungeon = self.dungeon

        for adj_dx, adj_dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            check_x = player.tile_x() + adj_dx
            check_y = player.tile_y() + adj_dy

            if not (0 <= check_x < MAP_COLS and 0 <= check_y < MAP_ROWS):
                continue

            tile = dungeon.tiles[check_y][check_x]

            if tile == TILE_STAIR:
                self._descend()
                break

            elif tile == TILE_DOOR:
                for door in dungeon.doors:
                    if door["x"] == check_x and door["y"] == check_y:
                        if door["locked"]:
                            if door["key_id"] in player.keys:
                                door["locked"] = False
                                print(f"Unlocked with {door['key_id']}!")
                            else:
                                print(f"Door is locked! Need {door['key_id']}.")
                                break

                        door["open"] = True
                        dungeon.tiles[check_y][check_x] = TILE_FLOOR
                        print("Door opened!")
                        break
                break

            elif tile == TILE_CHEST:
                for chest in dungeon.chests:
                    if chest["x"] == check_x and chest["y"] == check_y and not chest["opened"]:
                        chest["opened"] = True
                        dungeon.tiles[check_y][check_x] = TILE_FLOOR
                        found = chest["contents"]
                        print(f"Found: {found}")

                        if isinstance(found, str) and found.startswith("key_"):
                            player.keys.add(found)
                            print(f"Picked up {found}. Keys: {sorted(player.keys)}")
                        break
                break


    def _draw_minimap(self):
        mw = MAP_COLS * MINIMAP_TILE
        mh = MAP_ROWS * MINIMAP_TILE
        mx = SCREEN_WIDTH  - mw - MINIMAP_MARGIN
        my = MINIMAP_MARGIN

        # Semi-transparent background
        bg = pygame.Surface((mw, mh), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 160))
        self.screen.blit(bg, (mx, my))

        # Tile colors on the minimap (Show locked doors differently?)
        color_map = {
            TILE_FLOOR:    COLOR_FLOOR,
            TILE_WALL:     COLOR_WALL,
            TILE_DOOR:     COLOR_DOOR,
            TILE_CHEST:    COLOR_CHEST,
            TILE_TRAP:     COLOR_TRAP,
            TILE_CAMPFIRE: COLOR_CAMPFIRE,
            TILE_STAIR:    COLOR_STAIR,
        }

        for y in range(MAP_ROWS):
            for x in range(MAP_COLS):
                color = color_map.get(self.dungeon.tiles[y][x])
                if color is None:
                    continue
                rect = pygame.Rect(mx + x * MINIMAP_TILE, my + y * MINIMAP_TILE, MINIMAP_TILE, MINIMAP_TILE)
                pygame.draw.rect(self.screen, color, rect)

        # Player dot
        px = mx + self.player.tile_x() * MINIMAP_TILE + MINIMAP_TILE // 2
        py = my + self.player.tile_y() * MINIMAP_TILE + MINIMAP_TILE // 2
        pygame.draw.rect(self.screen, COLOR_PLAYER, pygame.Rect(px - 1, py - 1, 3, 3))

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                self._handle_interact()

    def _check_traps(self):
        player  = self.player
        dungeon = self.dungeon
        for trap in dungeon.traps:
            if (trap["x"] == player.tile_x() and
                    trap["y"] == player.tile_y() and
                    not trap["triggered"]):
                trap["triggered"] = True
                dungeon.tiles[trap["y"]][trap["x"]] = TILE_FLOOR
                print(f"Trap! {trap['damage']} damage!")
                # player.hp -= trap["damage"]  # when health system exists
                break

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0

            self._handle_events()
            self.player.update(pygame.key.get_pressed(), dt, self.dungeon.tiles)
            self._check_traps()

            camera_x = self.player.x - SCREEN_WIDTH  // 2
            camera_y = self.player.y - SCREEN_HEIGHT // 2

            self.screen.fill(COLOR_BLACK)
            self.dungeon.draw(self.screen, camera_x, camera_y)
            self.player.draw(self.screen, camera_x, camera_y)
            self._draw_minimap()
            pygame.display.flip()


if __name__ == "__main__":
    Game().run()
