import os
import random

import pygame

from config import (
    TILE_SIZE, MAP_COLS, MAP_ROWS, ENEMY_SPRITE_DIR,
    TILE_FLOOR, TILE_CAMPFIRE,
    RED, ORANGE, BLUE, GREEN, PURPLE,
)
from enums import Element
from enums import Element, BodyPart 

class Enemy:
    """Tile-based enemy with wandering AI and sprite-sheet animation."""
    sprite_sheet = None

    @classmethod
    def load_sprite_sheet(cls, custom_path=None):
        """Load a sprite sheet. If custom_path is provided, use that instead."""
        if custom_path:
            sheet_path = custom_path
        else:
            sheet_path = os.path.join(ENEMY_SPRITE_DIR, "beasts.png")
        
        try:
            sprite_sheet = pygame.image.load(sheet_path).convert_alpha()
            return sprite_sheet
        except Exception as e:
            print(f"[Warning] Could not load sprite sheet {sheet_path}: {e}")
            return None

    def __init__(self, tile_x, tile_y, enemy_type="basic", custom_sprite_path=None, difficulty_mult=1.0):
        # Tile position
  
        self.current_tile_x = tile_x
        self.current_tile_y = tile_y

        # Pixel position (center of tile) for smooth rendering
        self.pixel_x = tile_x * TILE_SIZE + TILE_SIZE // 2
        self.pixel_y = tile_y * TILE_SIZE + TILE_SIZE // 2

        # Smooth movement between tiles
        self.target_tile_x = tile_x
        self.target_tile_y = tile_y
        self.move_progress = 1.0
        self.is_moving = False
        self.move_timer = 0
        self.move_delay = random.uniform(0.5, 2.0)
        self.current_dx = 0
        self.current_dy = 0

        # Which room this enemy belongs to
        self.room_index = None

        # --- Animation System ---
        self.current_animation = "down"
        self.animation_frame_index = 0
        self.animation_timer = 0.0
        self.frames_by_animation = {}
        self.image = None
        self.facing_right = True
        self.flip_sprite = False
        
        # 4x4 grid configuration (for grid-based sprites)
        self.sprite_grid_rows = 4
        self.sprite_grid_cols = 4
        self.frame_width = 0
        self.frame_height = 0
        self.sprite_format = "grid"  # "grid" or "separate"
        
        # Direction-based animation definitions for 4x4 sprite sheet
        self.animation_definitions = {
            "down": {"row": 0, "frames": [0, 1, 2, 3], "speed": 0.1, "loop": True},
            "up": {"row": 1, "frames": [0, 1, 2, 3], "speed": 0.1, "loop": True},
            "right": {"row": 2, "frames": [0, 1, 2, 3], "speed": 0.1, "loop": True},
            "left": {"row": 3, "frames": [0, 1, 2, 3], "speed": 0.1, "loop": True},
            "attack": {"row": 2, "frames": [0, 1, 2, 3], "speed": 0.08, "loop": False},
            "hurt": {"row": 3, "frames": [0, 1], "speed": 0.1, "loop": False},
            "death": {"row": 3, "frames": [2, 3], "speed": 0.15, "loop": False},
        }

        # --- Combat animation properties ---
        self.combat_animation_state = "idle"
        self.combat_animation_timer = 0.0
        self.combat_x_offset = 0
        self.combat_y_offset = 0
        self.hurt_flash_timer = 0.0
        self.hurt_alpha = 255
        self.damage_numbers = []

        # --- Per-type stats and SPRITE configuration ---
        if enemy_type == "basic":
            self.name = "Flying Monstrosity"
            self.speed = 2.0
            self.max_hp = 60
            self.hp = 60
            self.damage = 10
            self.element = Element.NORMAL
            self.xp_reward = 30
            self.color = RED
            self.needs_flip = True
            self.explore_size = 64
            # Use 4x4 grid format
            self.sprite_format = "grid"
            if not custom_sprite_path:
                custom_sprite_path = os.path.join(ENEMY_SPRITE_DIR, "1hoursheet-removebg-preview.png")

        elif enemy_type == "fire":
            self.name = "Bee Scared"
            self.speed = 1.8
            self.max_hp = 80
            self.hp = 80
            self.damage = 15
            self.element = Element.FIRE
            self.xp_reward = 50
            self.color = ORANGE
            self.needs_flip = False
            self.explore_size = 48
            # Use separate PNG files
            self.sprite_format = "separate"
            self.sprite_paths = {
                "down": os.path.join(ENEMY_SPRITE_DIR, "bee_scared", "idle.png"),
                "up": os.path.join(ENEMY_SPRITE_DIR, "bee_scared", "idle.png"),
                "right": os.path.join(ENEMY_SPRITE_DIR, "bee_scared", "walk.png"),
                "left": os.path.join(ENEMY_SPRITE_DIR, "bee_scared", "walk.png"),
                "attack": os.path.join(ENEMY_SPRITE_DIR, "bee_scared", "attack.png"),
                "hurt": os.path.join(ENEMY_SPRITE_DIR, "bee_scared", "hurt.png"),
                "death": os.path.join(ENEMY_SPRITE_DIR, "bee_scared", "death.png"),
            }

        elif enemy_type == "water":
            self.name = "Battering Bat"
            self.speed = 1.5
            self.max_hp = 70
            self.hp = 70
            self.damage = 12
            self.element = Element.WATER
            self.xp_reward = 45
            self.color = BLUE
            self.needs_flip = True
            self.explore_size = 70
            self.sprite_format = "separate"
            self.sprite_paths = {
                "down": os.path.join(ENEMY_SPRITE_DIR, "Bat", "walk.png"),
                "up": os.path.join(ENEMY_SPRITE_DIR, "Bat", "walk.png"),
                "right": os.path.join(ENEMY_SPRITE_DIR, "Bat", "walk.png"),
                "left": os.path.join(ENEMY_SPRITE_DIR, "Bat", "walk.png"),
                "attack": os.path.join(ENEMY_SPRITE_DIR, "Bat", "attack.png"),
                "hurt": os.path.join(ENEMY_SPRITE_DIR, "Bat", "hurt.png"),
                "death": os.path.join(ENEMY_SPRITE_DIR, "Bat", "death.png"),
            }

        elif enemy_type == "earth":
            self.name = "Spikey Slime"
            self.speed = 2.5
            self.max_hp = 75
            self.hp = 75
            self.damage = 13
            self.element = Element.EARTH
            self.xp_reward = 45
            self.color = GREEN
            self.needs_flip = True
            self.explore_size = 60
            self.sprite_format = "separate"
            self.sprite_paths = {
                "down": os.path.join(ENEMY_SPRITE_DIR, "spiked_slime", "idle.png"),
                "up": os.path.join(ENEMY_SPRITE_DIR, "spiked_slime", "idle.png"),
                "right": os.path.join(ENEMY_SPRITE_DIR, "spiked_slime", "walk.png"),
                "left": os.path.join(ENEMY_SPRITE_DIR, "spiked_slime", "walk.png"),
                "attack": os.path.join(ENEMY_SPRITE_DIR, "spiked_slime", "attack.png"),
                "hurt": os.path.join(ENEMY_SPRITE_DIR, "spiked_slime", "hurt.png"),
                "death": os.path.join(ENEMY_SPRITE_DIR, "spiked_slime", "death.png"),
            }

        elif enemy_type == "mini_boss":
            self.name = "Armored Golem"
            self.speed = 1.2
            self.max_hp = 200
            self.hp = 200
            self.damage = 25
            self.element = Element.FIRE
            self.xp_reward = 200
            self.color = PURPLE
            self.needs_flip = True
            self.explore_size = 72
            self.sprite_format = "separate"
            self.sprite_paths = {
                "down": os.path.join(ENEMY_SPRITE_DIR, "armored_golem", "idle.png"),
                "up": os.path.join(ENEMY_SPRITE_DIR, "armored_golem", "idle.png"),
                "right": os.path.join(ENEMY_SPRITE_DIR, "armored_golem", "walk.png"),
                "left": os.path.join(ENEMY_SPRITE_DIR, "armored_golem", "walk.png"),
                "attack": os.path.join(ENEMY_SPRITE_DIR, "armored_golem", "attack.png"),
                "hurt": os.path.join(ENEMY_SPRITE_DIR, "armored_golem", "hurt.png"),
                "death": os.path.join(ENEMY_SPRITE_DIR, "armored_golem", "death.png"),
            }

        else:
            # Default fallback
            self.name = "Enemy"
            self.speed = 2.0
            self.max_hp = 50
            self.hp = 50
            self.damage = 10
            self.element = Element.NORMAL
            self.xp_reward = 30
            self.color = RED
            self.sprite_format = "grid"
            if not custom_sprite_path:
                custom_sprite_path = os.path.join(ENEMY_SPRITE_DIR, "1hoursheet-removebg-preview.png.png")
        
        # Difficulty scaling 
        self.max_hp = max(1, int(self.max_hp * difficulty_mult))
        self.hp = self.max_hp
        self.damage = max(1, int(self.damage * difficulty_mult))
        self.xp_reward = max(1, int(self.xp_reward * difficulty_mult))
        self._init_body_parts()

        # --- Load sprites based on format ---
        if self.sprite_format == "grid":
            self._load_grid_sprite_sheet(custom_sprite_path)
        else:
            self._load_separate_sprites()

        # Set initial frame
        if self.frames_by_animation and "down" in self.frames_by_animation:
            if self.frames_by_animation["down"]:
                self.image = self.frames_by_animation["down"][0]
                self.current_animation = "down"

    def _init_body_parts(self):
        """Initialize body parts for the enemy"""
        base_part_hp = max(1, self.max_hp // 4)
        
        self.body_parts = {
            BodyPart.HEAD: {"hp": int(base_part_hp * 1.5), "max_hp": int(base_part_hp * 1.5), "disabled": False},  # 50% more HP
            BodyPart.TORSO: {"hp": base_part_hp * 2, "max_hp": base_part_hp * 2, "disabled": False},
            BodyPart.LEFT_ARM: {"hp": base_part_hp, "max_hp": base_part_hp, "disabled": False},
            BodyPart.RIGHT_ARM: {"hp": base_part_hp, "max_hp": base_part_hp, "disabled": False},
            BodyPart.LEFT_LEG: {"hp": base_part_hp, "max_hp": base_part_hp, "disabled": False},
            BodyPart.RIGHT_LEG: {"hp": base_part_hp, "max_hp": base_part_hp, "disabled": False},
        }

    def handle_part_destroyed(self, part):
        """Handle effects when body part is destroyed"""
        if part == BodyPart.HEAD:
            self.hp = 0
        elif part == BodyPart.LEFT_ARM or part == BodyPart.RIGHT_ARM:
            self.damage = max(1, int(self.damage * 0.5))
        elif part == BodyPart.LEFT_LEG or part == BodyPart.RIGHT_LEG:
            self.speed = max(0.5, self.speed * 0.5)
        elif part == BodyPart.TORSO:
            self.hp = 0

    def _load_grid_sprite_sheet(self, sprite_path):
        """Load a 4x4 grid sprite sheet"""
        try:
            self.sprite_sheet = pygame.image.load(sprite_path).convert_alpha()
            
            if self.sprite_sheet:
                sheet_width = self.sprite_sheet.get_width()
                sheet_height = self.sprite_sheet.get_height()
                
                self.frame_width = sheet_width // self.sprite_grid_cols
                self.frame_height = sheet_height // self.sprite_grid_rows
                
                print(f"[Enemy] Loaded grid sprite sheet for {self.name}: {sprite_path}")
                
                # Extract frames for each animation
                for anim_name, anim_data in self.animation_definitions.items():
                    frames = []
                    row = anim_data["row"]
                    for col in anim_data["frames"]:
                        x = col * self.frame_width
                        y = row * self.frame_height
                        try:
                            frame = self.sprite_sheet.subsurface((x, y, self.frame_width, self.frame_height))
                            frame = pygame.transform.scale(frame, (TILE_SIZE, TILE_SIZE))
                            frames.append(frame)
                        except Exception as e:
                            print(f"[Warning] Could not extract {anim_name} frame {col}: {e}")
                    
                    if frames:
                        self.frames_by_animation[anim_name] = frames
            else:
                self._create_fallback_sprites()
                
        except Exception as e:
            print(f"[Warning] Could not load grid sprite sheet for {self.name}: {e}")
            self._create_fallback_sprites()

    def _load_separate_sprites(self):
        """Auto-detect grid layout from image dimensions"""
        print(f"[Enemy] Loading separate animated sprites for {self.name}")
        
        for anim_name, sprite_path in self.sprite_paths.items():
            print(f"  Trying to load: {sprite_path}")  # DEBUG LINE
            try:
                sheet = pygame.image.load(sprite_path).convert_alpha()
                print(f"    Success! Size: {sheet.get_width()}x{sheet.get_height()}")  # DEBUG LINE
                
                sheet_width = sheet.get_width()
                sheet_height = sheet.get_height()
                
                # AUTO-DETECT GRID LAYOUT
                if self.name == "Bee Scared" and anim_name in ["right", "left"]:
                    # Just take the first frame (assuming 1x8 grid)
                    frame_width = sheet_width // 8
                    frame_height = sheet_height
                    frame = sheet.subsurface((0, 0, frame_width, frame_height))
                    frame = pygame.transform.scale(frame, (TILE_SIZE, TILE_SIZE))
                    self.frames_by_animation[anim_name] = [frame]
                    print(f"  {anim_name}: Bee Scared special - using single frame")
                    continue  # Skip normal detection
                
                # Normal auto-detection for everything else
                cols = 1
                rows = 1
                
                if sheet_width == sheet_height:
                    possible_frames = [2, 3, 4, 6, 8]
                    for frames in possible_frames:
                        if sheet_width // frames == sheet_height // frames:
                            cols = frames
                            rows = frames
                            break
                    else:
                        cols = 4
                        rows = 4
                        
                elif sheet_width > sheet_height * 2:
                    rows = 1
                    frame_height = sheet_height
                    cols = sheet_width // frame_height
                    
                elif sheet_height > sheet_width * 2:
                    cols = 1
                    frame_width = sheet_width
                    rows = sheet_height // frame_width
                    
                else:
                    best_cols = 1
                    best_rows = 1
                    best_score = float('inf')
                    
                    for cols_guess in range(1, 9):
                        for rows_guess in range(1, 9):
                            frame_w = sheet_width // cols_guess
                            frame_h = sheet_height // rows_guess
                            if frame_w > 0 and frame_h > 0:
                                ratio = max(frame_w, frame_h) / min(frame_w, frame_h)
                                if ratio < best_score:
                                    best_score = ratio
                                    best_cols = cols_guess
                                    best_rows = rows_guess
                    
                    cols = best_cols
                    rows = best_rows
                
                cols = min(cols, 8)
                rows = min(rows, 8)
                
                frame_width = sheet_width // cols
                frame_height = sheet_height // rows
                
                print(f"  {anim_name}: detected {rows}x{cols} grid ({rows*cols} frames)")
                
                frames = []
                for row in range(rows):
                    for col in range(cols):
                        x = col * frame_width
                        y = row * frame_height
                        try:
                            frame = sheet.subsurface((x, y, frame_width, frame_height))
                            frame = pygame.transform.scale(frame, (TILE_SIZE, TILE_SIZE))
                            frames.append(frame)
                        except Exception:
                            pass
                
                if frames:
                    self.frames_by_animation[anim_name] = frames
                    print(f" Loaded {len(frames)} frames")
                else:
                    print(f" Failed to load frames")
                    self._create_fallback_for_animation(anim_name)
                    
            except Exception as e:
                print(f"[Warning] Could not load {anim_name}: {e}")
                self._create_fallback_for_animation(anim_name)

    def _create_fallback_for_animation(self, anim_name):
        """Create a fallback sprite for a specific animation"""
        fallback = pygame.Surface((TILE_SIZE, TILE_SIZE))
        fallback.fill(self.color)
        try:
            from config import WHITE
            pygame.draw.rect(fallback, WHITE, fallback.get_rect(), 2)
        except:
            pygame.draw.rect(fallback, (255, 255, 255), fallback.get_rect(), 2)
        self.frames_by_animation[anim_name] = [fallback]

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
        """Change animation based on movement direction and flip sprite accordingly."""
        if not self.frames_by_animation:
            return
        
        dx = self.target_tile_x - self.current_tile_x
        dy = self.target_tile_y - self.current_tile_y
        
        # Determine which direction animation to use
        if dx > 0:  # Moving right
            self.set_animation("right")
            # Flip if enemy faces left originally (Bee Scared)
            if hasattr(self, 'needs_flip') and not self.needs_flip:
                self.flip_sprite = True
            else:
                self.flip_sprite = False
                
        elif dx < 0:  # Moving left
            self.set_animation("right")  # Use right animation but flip it
            # Flip if enemy faces right originally (most enemies)
            if hasattr(self, 'needs_flip') and self.needs_flip:
                self.flip_sprite = True
            else:
                self.flip_sprite = False
                
        elif dy > 0:  # Moving down
            self.set_animation("down")
            self.flip_sprite = False
        elif dy < 0:  # Moving up
            self.set_animation("up")
            self.flip_sprite = False

    def update_animation(self, dt):
        """Update current animation frame"""
        if not self.frames_by_animation:
            return
        
        anim_frames = self.frames_by_animation.get(self.current_animation, [])
        if not anim_frames:
            return
        
        anim_speed = self.animation_definitions.get(self.current_animation, {}).get("speed", 0.1)
        
        self.animation_timer += dt
        if self.animation_timer >= anim_speed:
            self.animation_timer = 0
            self.animation_frame_index = (self.animation_frame_index + 1) % len(anim_frames)
            self.image = anim_frames[self.animation_frame_index]

    def update_combat_animation(self, dt):
        """Update combat animations (damage numbers, hurt flash, etc.)"""
        # Update damage numbers
        for dn in self.damage_numbers[:]:
            dn["timer"] -= dt
            dn["y_offset"] -= 50 * dt  # Float upward
            if dn["timer"] <= 0:
                self.damage_numbers.remove(dn)
        
        # Update hurt flash
        if self.hurt_flash_timer > 0:
            self.hurt_flash_timer -= dt
            # Create pulsing effect
            if self.hurt_flash_timer > 0:
                flash_intensity = int(255 * (self.hurt_flash_timer / 0.3))
                self.hurt_alpha = max(0, min(255, flash_intensity))
            else:
                self.hurt_alpha = 255
        
        # Update attack/hurt lunge offsets
        if self.combat_animation_state == "attacking":
            self.combat_animation_timer += dt
            if self.combat_animation_timer < 0.1:
                # Lunge forward
                progress = self.combat_animation_timer / 0.1
                self.combat_x_offset = 30 * progress
            elif self.combat_animation_timer < 0.2:
                # Return to idle
                progress = (self.combat_animation_timer - 0.1) / 0.1
                self.combat_x_offset = 30 * (1 - progress)
            else:
                self.combat_animation_state = "idle"
                self.combat_x_offset = 0
        
        elif self.combat_animation_state == "hurt":
            self.combat_animation_timer += dt
            if self.combat_animation_timer < 0.15:
                # Knockback
                progress = self.combat_animation_timer / 0.15
                self.combat_x_offset = -15 * (1 - progress)
                self.combat_y_offset = -10 * (1 - progress)
            elif self.combat_animation_timer < 0.3:
                # Return
                progress = (self.combat_animation_timer - 0.15) / 0.15
                self.combat_x_offset = -15 * progress
                self.combat_y_offset = -10 * progress
            else:
                self.combat_animation_state = "idle"
                self.combat_x_offset = 0
                self.combat_y_offset = 0
        
        elif self.combat_animation_state == "dying":
            self.combat_animation_timer += dt
            if self.combat_animation_timer < 0.5:
                # Shake
                self.combat_x_offset = random.randint(-8, 8)
                self.combat_y_offset = random.randint(-8, 8)
                # Fade out gradually
                self.hurt_alpha = int(255 * (1 - self.combat_animation_timer / 0.5))
            else:
                self.combat_animation_state = "dead"

    def set_animation(self, animation_name):
        """Switch to a different animation (down, up, right, left)"""
        if animation_name in self.frames_by_animation and self.current_animation != animation_name:
            self.current_animation = animation_name
            self.animation_frame_index = 0
            self.animation_timer = 0.0
            if self.frames_by_animation[animation_name]:
                self.image = self.frames_by_animation[animation_name][0]

    def set_combat_animation(self):
        """Set the enemy to face the player during combat (use down/row 0)"""
        self.set_animation("down")

    # Update your combat animation methods to use the new system
    def start_attack_animation(self):
        """Called when enemy attacks the player"""
        self.set_animation("attack")
        self.combat_animation_state = "attacking"
        self.combat_animation_timer = 0.0
        # Reset back to idle after attack finishes (you'll need a timer)

    def start_hurt_animation(self, damage_amount):
        """Called when enemy takes damage"""
        self.set_animation("hurt")
        self.combat_animation_state = "hurt"
        self.combat_animation_timer = 0.0
        self.hurt_flash_timer = 0.3
        
        self.damage_numbers.append({
            "value": damage_amount,
            "timer": 5.0,
            "x_offset": random.randint(-20, 20),
            "y_offset": 0
    })

    def start_dying_animation(self):
        """Called when enemy HP reaches 0"""
        self.set_animation("death")
        self.combat_animation_state = "dying"
        self.combat_animation_timer = 0.0

    # --- Combat helpers ---

    def take_damage(self, damage):
        self.hp -= damage
        return self.hp <= 0

    # --- Drawing ---

    def draw(self, screen, camera_x, camera_y):
        """Draw the enemy with camera offset and flipping."""
        sx = int(self.pixel_x - camera_x) - TILE_SIZE // 2
        sy = int(self.pixel_y - camera_y) - TILE_SIZE // 2
        
        # Get custom size for exploration (default to TILE_SIZE)
        explore_size = getattr(self, 'explore_size', TILE_SIZE)
        
        if self.image:
            # Scale to custom size
            scaled_image = pygame.transform.scale(self.image, (explore_size, explore_size))
            
            # Flip if needed
            if hasattr(self, 'flip_sprite') and self.flip_sprite:
                scaled_image = pygame.transform.flip(scaled_image, True, False)
            
            # Adjust position to center the scaled sprite
            draw_x = sx - (explore_size - TILE_SIZE) // 2
            draw_y = sy - (explore_size - TILE_SIZE) // 2
            screen.blit(scaled_image, (draw_x, draw_y))
        else:
            # Fallback rectangle
            pygame.draw.rect(screen, self.color,
                            pygame.Rect(sx, sy, TILE_SIZE, TILE_SIZE))
