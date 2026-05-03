import os
import random

import pygame

from config import (
    TILE_SIZE, MAP_COLS, MAP_ROWS, ENEMY_SPRITE_DIR,
    TILE_FLOOR, TILE_CAMPFIRE,
    RED, ORANGE, BLUE, GREEN, PURPLE,
)
from enums import Element

class Enemy:
    """Tile-based enemy with wandering AI and sprite-sheet animation."""
    sprite_sheet = None

    @classmethod
    def load_sprite_sheet(cls):
        """Load the sprite sheet once for all enemies."""
        if cls.sprite_sheet is None:
            sheet_path = os.path.join(ENEMY_SPRITE_DIR, "beasts.png")
            try:
                cls.sprite_sheet = pygame.image.load(sheet_path).convert_alpha()
            except Exception as e:
                print(f"[Warning] Could not load enemy sprite sheet: {e}")
                cls.sprite_sheet = None

    def __init__(self, tile_x, tile_y, enemy_type="basic", difficulty_mult=1.0):
        # Tile position
        self.current_tile_x = tile_x
        self.current_tile_y = tile_y

        # Pixel position (center of tile) for smooth rendering
        self.pixel_x = tile_x * TILE_SIZE + TILE_SIZE // 2
        self.pixel_y = tile_y * TILE_SIZE + TILE_SIZE // 2

        # Smooth movement between tiles
        self.target_tile_x = tile_x
        self.target_tile_y = tile_y
        self.move_progress = 1.0  # 1.0 = arrived, 0.0 = just started

        Enemy.load_sprite_sheet()

        # Sprite animation
        self.sprite_width = 48
        self.sprite_height = 64
        self.current_frame = 0
        self.facing_right = True
        self.animation_timer = 0.0  
        self.image = None  # Current display image (may be None if no sheet)

        # Movement AI state
        self.move_timer = 0
        self.move_delay = random.uniform(0.5, 2.0)
        self.current_dx = 0
        self.current_dy = 0
        self.is_moving = False

        # Which room this enemy belongs to
        self.room_index = None

        # --- Per-type stats ---
        if enemy_type == "basic":
            self.name = "Beast"
            self.speed = 2.0
            self.max_hp = 60
            self.hp = 60
            self.damage = 10
            self.element = Element.NORMAL
            self.row = 0
            self.columns = [0, 1, 2, 3]
            self.xp_reward = 30
            self.color = RED
        elif enemy_type == "fire":
            self.name = "Werebeast"
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
            self.name = "Forklift"
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
            self.name = "Smallbeast"
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
            self.name = "Undead"
            self.speed = 1.2
            self.max_hp = 200
            self.hp = 200
            self.damage = 25
            self.element = Element.FIRE
            self.row = 4
            self.columns = [0, 1, 2]
            self.xp_reward = 200
            self.color = PURPLE

        # Difficulty scaling 
        self.max_hp = max(1, int(self.max_hp * difficulty_mult))
        self.hp = self.max_hp
        self.damage = max(1, int(self.damage * difficulty_mult))
        self.xp_reward = max(1, int(self.xp_reward * difficulty_mult))

        # Load sprite frames from the sheet
        self.frames_images = []
        if Enemy.sprite_sheet:
            for col in self.columns:
                x = col * self.sprite_width
                y = self.row * self.sprite_height
                try:
                    frame = Enemy.sprite_sheet.subsurface(
                        (x, y, self.sprite_width, self.sprite_height))
                    frame = pygame.transform.scale(frame, (TILE_SIZE, TILE_SIZE))
                    self.frames_images.append(frame)
                except Exception:
                    pass
            if self.frames_images:
                self.image = self.frames_images[0]

    # --- Movement / AI ---

    def can_move_to(self, tiles, tx, ty):
        """Check if the enemy can step onto (tx, ty)."""
        walkable = [TILE_FLOOR, TILE_CAMPFIRE]
        if tx < 0 or tx >= MAP_COLS or ty < 0 or ty >= MAP_ROWS:
            return False
        return tiles[ty][tx] in walkable

    def update_movement(self, dt, tiles):
        """Tile-based wandering AI with smooth interpolation."""
        if self.is_moving:
            self.move_progress += self.speed * dt
            if self.move_progress >= 1.0:
                # Snap to target tile
                self.move_progress = 1.0
                self.is_moving = False
                self.current_tile_x = self.target_tile_x
                self.current_tile_y = self.target_tile_y
                self.pixel_x = self.current_tile_x * TILE_SIZE + TILE_SIZE // 2
                self.pixel_y = self.current_tile_y * TILE_SIZE + TILE_SIZE // 2
            else:
                # Interpolate pixel position
                sx = self.current_tile_x * TILE_SIZE + TILE_SIZE // 2
                sy = self.current_tile_y * TILE_SIZE + TILE_SIZE // 2
                tx = self.target_tile_x * TILE_SIZE + TILE_SIZE // 2
                ty = self.target_tile_y * TILE_SIZE + TILE_SIZE // 2
                self.pixel_x = sx + (tx - sx) * self.move_progress
                self.pixel_y = sy + (ty - sy) * self.move_progress
                self._update_sprite_for_direction()
        else:
            self.move_timer += dt
            if self.move_timer >= self.move_delay:
                self.move_timer = 0
                self.move_delay = random.uniform(0.5, 2.0)
                directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
                random.shuffle(directions)
                for dx, dy in directions:
                    nx = self.current_tile_x + dx
                    ny = self.current_tile_y + dy
                    if self.can_move_to(tiles, nx, ny):
                        self.target_tile_x = nx
                        self.target_tile_y = ny
                        self.is_moving = True
                        self.move_progress = 0.0
                        self.current_dx = dx
                        self.current_dy = dy
                        self._update_sprite_for_direction()
                        break

    def _update_sprite_for_direction(self):
        """Pick the correct sprite frame based on movement direction."""
        if not self.frames_images:
            return
        dx = self.target_tile_x - self.current_tile_x
        dy = self.target_tile_y - self.current_tile_y
       
        if dx > 0 and len(self.frames_images) > 2:
            self.image = pygame.transform.flip(self.frames_images[2], True, False)
            self.facing_right = True
        elif dx < 0 and len(self.frames_images) > 2:
            self.image = self.frames_images[2]
            self.facing_right = False
        elif dy < 0 and len(self.frames_images) > 0:
            self.image = self.frames_images[0]  # back view
        elif dy > 0 and len(self.frames_images) > 1:
            self.image = self.frames_images[1]  # front view

    # --- Combat helpers ---

    def take_damage(self, damage):
        self.hp -= damage
        return self.hp <= 0

    # --- Drawing ---

    def draw(self, screen, camera_x, camera_y):
        """Draw the enemy with camera offset."""
        sx = int(self.pixel_x - camera_x) - TILE_SIZE // 2
        sy = int(self.pixel_y - camera_y) - TILE_SIZE // 2
        if self.image:
            screen.blit(self.image, (sx, sy))
        else:
            # Fallback coloured rectangle when sprites are unavailable
            pygame.draw.rect(screen, self.color,
                             pygame.Rect(sx, sy, TILE_SIZE, TILE_SIZE))
