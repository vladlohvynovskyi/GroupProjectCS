import pygame
import math
import random

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE,
    PLAYER_LIGHT_RADIUS, DARKNESS,
    COLOR_BLACK, WHITE, RED, GREEN, BLUE, YELLOW,
    GRAY, DARK_GRAY, LIGHT_GRAY, ORANGE,
)
from enums import GameState, ItemType, BodyPart, Element
from elements import ELEMENT_COLORS
from ui import draw_text, draw_ui_button, draw_ui_button_simple, draw_health_bar, draw_ui_health_bar_angria
from minimap import draw_minimap


def _apply_light(surface, cx, cy, radius, max_alpha):
    for r in range(radius, 0, -4):
        alpha = int(max_alpha * (r / radius) ** 2)
        pygame.draw.circle(surface, (0, 0, 0, alpha), (cx, cy), r)


def draw_darkness(game, camera_x, camera_y):
    darkness = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    darkness.fill((0, 0, 0, DARKNESS))

    # Light around player
    px = int(game.player.x - camera_x)
    py = int(game.player.y - camera_y)
    _apply_light(darkness, px, py, PLAYER_LIGHT_RADIUS, DARKNESS)

    # Light around campfires
    for cf in game.dungeon.campfires:
        cx = int(cf["x"] * TILE_SIZE + TILE_SIZE // 2 - camera_x)
        cy = int(cf["y"] * TILE_SIZE + TILE_SIZE // 2 - camera_y)
        _apply_light(darkness, cx, cy, cf["radius"], DARKNESS)

    game.screen.blit(darkness, (0, 0))


def draw_exploration(game):
    """Draw the exploration mode"""
    game.screen.fill(COLOR_BLACK)
    
    # Calculate camera
    camera_x = game.player.x - SCREEN_WIDTH // 2
    camera_y = game.player.y - SCREEN_HEIGHT // 2
    
    # Draw dungeon
    game.dungeon.draw(game.screen, camera_x, camera_y, game.assets)
    
    # Draw enemies
    for enemy in game.dungeon.enemies:
        if enemy.hp > 0:
            enemy.draw(game.screen, camera_x, camera_y)
    
    # Draw player
    game.player.draw(game.screen, camera_x, camera_y, game.assets)
    draw_darkness(game, camera_x, camera_y)
    
    # Draw minimap
    draw_minimap(game)
    
    # Draw UI text
    draw_text(game, f"HP: {game.player.hp}/{game.player.max_hp}", 10, 10, RED)
    draw_text(game, f"Floor: {game.floor}", 10, 50, WHITE)
    draw_text(game, f"Level: {game.player.level} | XP: {game.player.xp}", 10, 90, WHITE)
    
    if game.player.equipped_weapon:
        draw_text(game, f"Weapon: {game.player.equipped_weapon.name}", 35, 115, YELLOW, game.small_font)
    
    # Draw inventory button
    draw_ui_button(game, game.inventory_button, "Inventory", "title", 0, 0, False)
    
    # Draw controls hint
    draw_text(game, "WASD: Move | E: Interact | I: Inventory", 
              200, SCREEN_HEIGHT - 30, WHITE, game.small_font)


def draw_combat(game):
    """Draw combat - with background image"""
    
    # Draw background image
    if game.assets.combat_bg:
        bg_scaled = pygame.transform.scale(game.assets.combat_bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
        game.screen.blit(bg_scaled, (0, 0))
    else:
        # Fallback gradient if no background
        for y in range(SCREEN_HEIGHT):
            ratio = y / SCREEN_HEIGHT
            r = 30 + int(20 * ratio)
            g = 20 + int(15 * ratio)
            b = 25 + int(20 * ratio)
            pygame.draw.line(game.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
    
    if not game.current_enemy:
        game.state = GameState.EXPLORATION
        return
    
    enemy = game.current_enemy
    
    # Helper function to draw a panel border
    def draw_panel(x, y, width, height, title=None):
        # Outer border
        pygame.draw.rect(game.screen, (60, 55, 65), (x, y, width, height))
        pygame.draw.rect(game.screen, (100, 90, 110), (x, y, width, height), 2)
        # Inner dark area
        pygame.draw.rect(game.screen, (25, 22, 35), (x+4, y+4, width-8, height-8))
        # Corner accents
        corner_len = 12
        pygame.draw.line(game.screen, (140, 120, 100), (x, y), (x+corner_len, y), 2)
        pygame.draw.line(game.screen, (140, 120, 100), (x, y), (x, y+corner_len), 2)
        pygame.draw.line(game.screen, (140, 120, 100), (x+width, y), (x+width-corner_len, y), 2)
        pygame.draw.line(game.screen, (140, 120, 100), (x+width, y), (x+width, y+corner_len), 2)
        pygame.draw.line(game.screen, (140, 120, 100), (x, y+height), (x+corner_len, y+height), 2)
        pygame.draw.line(game.screen, (140, 120, 100), (x, y+height), (x, y+height-corner_len), 2)
        pygame.draw.line(game.screen, (140, 120, 100), (x+width, y+height), (x+width-corner_len, y+height), 2)
        pygame.draw.line(game.screen, (140, 120, 100), (x+width, y+height), (x+width, y+height-corner_len), 2)
        
        if title:
            # Title bar - use actual text width
            title_surface = game.small_font.render(title, True, YELLOW)
            title_width = title_surface.get_width() + 20
            title_rect = pygame.Rect(x + width//2 - title_width//2, y - 12, title_width, 22)
            pygame.draw.rect(game.screen, (40, 35, 50), title_rect)
            pygame.draw.rect(game.screen, (100, 90, 110), title_rect, 1)
            draw_text(game, title, title_rect.x + 10, title_rect.y + 3, YELLOW, game.small_font)
    
    # === PLAYER PANEL ===
    draw_panel(20, 35, 280, 185, "PLAYER")
    draw_text(game, f"LV.{game.player.level}", 240, 45, YELLOW, game.small_font)
    draw_ui_health_bar_angria(game, 35, 75, 240, 50, game.player.hp, game.player.max_hp)
    draw_text(game, f"HP: {game.player.hp}/{game.player.max_hp}", 25, 45, WHITE, game.small_font)
    
    if game.player.equipped_weapon:
        draw_text(game, game.player.equipped_weapon.name, 35, 130, WHITE, game.small_font)
        draw_text(game, f"DMG: {game.player.equipped_weapon.damage}", 35, 155, WHITE, game.small_font)
    
    # === STATUS EFFECTS AREA ===
    status_x = 20
    status_y = 230
    draw_text(game, "STATUS", status_x, status_y, LIGHT_GRAY, game.small_font)
    pygame.draw.line(game.screen, (80, 70, 60), (status_x, status_y + 15), (status_x + 100, status_y + 15), 1)
    draw_text(game, "Normal", status_x + 10, status_y + 25, WHITE, game.small_font)
    
    # === ENEMY PANEL ===
    draw_panel(SCREEN_WIDTH//2 - 170, 25, 380, 305, enemy.name.upper())
    
    # Enemy sprite
    sprite_size = 160
    enemy_x = SCREEN_WIDTH//2 - sprite_size//2
    enemy_y = 70
    
    if enemy.image:
        scaled = pygame.transform.scale(enemy.image, (sprite_size, sprite_size))
        game.screen.blit(scaled, (enemy_x, enemy_y))
    
    # Decorative frame around enemy
    frame_rect = pygame.Rect(enemy_x - 10, enemy_y - 10, sprite_size + 20, sprite_size + 20)
    pygame.draw.rect(game.screen, (80, 60, 50), frame_rect, 3)
    pygame.draw.rect(game.screen, (140, 100, 70), frame_rect, 1)
    # Corner decorations
    for cx, cy in [(frame_rect.x, frame_rect.y), (frame_rect.right, frame_rect.y), 
                   (frame_rect.x, frame_rect.bottom), (frame_rect.right, frame_rect.bottom)]:
        pygame.draw.circle(game.screen, (100, 70, 50), (cx, cy), 6)
        pygame.draw.circle(game.screen, (60, 40, 30), (cx, cy), 3)

    # Enemy health
    draw_ui_health_bar_angria(game, SCREEN_WIDTH//2 - 150, 260, 320, 50, enemy.hp, enemy.max_hp)
    draw_text(game, f"HP: {enemy.hp}/{enemy.max_hp}", SCREEN_WIDTH//2 - 40, 290, WHITE, game.small_font)
    element_color = ELEMENT_COLORS[enemy.element]
    draw_text(game, f"Element: {enemy.element.name}", SCREEN_WIDTH//2 - 50, 310, element_color, game.small_font)
    
    # === BODY PARTS PANEL ===
    draw_panel(SCREEN_WIDTH - 270, 30, 260, 340, "TARGET BODY PARTS")
    
    game.part_buttons = {}
    y_pos = 70
    for part in BodyPart:
        part_data = enemy.body_parts[part]
        part_name = part.name.replace("_", " ").title()
        part_hp = part_data["hp"]
        part_max = part_data["max_hp"]
        disabled = part_data["disabled"]
        
        if disabled:
            color = DARK_GRAY
            text = f"X {part_name}"
        else:
            if part_hp < part_max * 0.25:
                color = RED
            elif part_hp < part_max * 0.5:
                color = ORANGE
            else:
                color = LIGHT_GRAY
            text = f"> {part_name}  {part_hp}/{part_max}"
        
        btn_rect = pygame.Rect(SCREEN_WIDTH - 260, y_pos, 240, 30)
        pygame.draw.rect(game.screen, color, btn_rect)
        pygame.draw.rect(game.screen, COLOR_BLACK, btn_rect, 1)
        
        text_surf = game.small_font.render(text, True, WHITE)
        text_rect = text_surf.get_rect(center=btn_rect.center)
        game.screen.blit(text_surf, text_rect)
        
        if not disabled and game.combat_turn == "player":
            mouse_pos = pygame.mouse.get_pos()
            if btn_rect.collidepoint(mouse_pos):
                pygame.draw.rect(game.screen, YELLOW, btn_rect, 2)
            game.part_buttons[part] = btn_rect
        y_pos += 38
    
    # === COMBAT LOG PANEL ===
    draw_panel(30, SCREEN_HEIGHT - 170, SCREEN_WIDTH - 60, 130, "COMBAT LOG")
    
    for i, msg in enumerate(game.combat_log[-4:]):
        if "CRITICAL" in msg:
            color = YELLOW
        elif "Victory" in msg:
            color = GREEN
        elif "destroyed" in msg:
            color = ORANGE
        else:
            color = WHITE
        draw_text(game, msg[:75], 45, SCREEN_HEIGHT - 140 + i * 24, color, game.small_font)
    
    # === ACTION BUTTONS ===
    button_y = SCREEN_HEIGHT - 70
    btn_width = 140
    btn_height = 40
    
    game.attack_button = pygame.Rect(SCREEN_WIDTH//2 - 230, button_y, btn_width, btn_height)
    game.run_button = pygame.Rect(SCREEN_WIDTH//2 - 70, button_y, btn_width, btn_height)
    game.inventory_button = pygame.Rect(SCREEN_WIDTH//2 + 90, button_y, btn_width, btn_height)
    
    mouse_pos = pygame.mouse.get_pos()
    
    # Draw buttons with assets
    draw_ui_button(game, game.attack_button, "ATTACK", "title", 4, 0, game.attack_button.collidepoint(mouse_pos) and game.combat_turn == "player")
    draw_ui_button(game, game.run_button, "RUN", "title", 2, 0, game.run_button.collidepoint(mouse_pos) and game.combat_turn == "player")
    draw_ui_button(game, game.inventory_button, "ITEMS", "title", 0, 0, game.inventory_button.collidepoint(mouse_pos) and game.combat_turn == "player")
    
    # === TURN INDICATOR ===
    if game.combat_turn == "player":
        turn_text = "YOUR TURN"
        turn_color = GREEN
    else:
        turn_text = "ENEMY TURN"
        turn_color = RED
    
    turn_surf = game.font.render(turn_text, True, turn_color)
    game.screen.blit(turn_surf, turn_surf.get_rect(center=(SCREEN_WIDTH//2, button_y - 35)))

    # Vignette effect
    vignette = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    for i in range(100, 0, -10):
        alpha = 10
        pygame.draw.circle(vignette, (0, 0, 0, alpha), (SCREEN_WIDTH//2, SCREEN_HEIGHT//2), 
                        min(SCREEN_WIDTH, SCREEN_HEIGHT)//2 + i)
    game.screen.blit(vignette, (0, 0))
      

def _draw_placeholder_enemy(game, enemy_rect, enemy, glow_color):
    """Draw animated placeholder when no sprite is available"""
    import math
    x, y, w, h = enemy_rect
    
    color_shift = int(math.sin(game.breath_timer * 0.05) * 15)
    body_color = (
        min(255, max(0, enemy.color[0] + color_shift)),
        min(255, max(0, enemy.color[1] + color_shift)),
        min(255, max(0, enemy.color[2] + color_shift))
    )
    
    pygame.draw.rect(game.screen, body_color, enemy_rect)
    pygame.draw.rect(game.screen, glow_color, enemy_rect.inflate(4, 4), 2)
    
    eye_y = y + h//3
    blink = game.combat_idle_timer > 40
    
    if not blink:
        pygame.draw.circle(game.screen, WHITE, (x + w//3, eye_y), 12)
        pygame.draw.circle(game.screen, WHITE, (x + 2*w//3, eye_y), 12)
        pupil_x = math.sin(game.breath_timer * 0.02) * 2
        pupil_y = math.cos(game.breath_timer * 0.03) * 1
        pygame.draw.circle(game.screen, COLOR_BLACK, (x + w//3 + pupil_x, eye_y + pupil_y), 4)
        pygame.draw.circle(game.screen, COLOR_BLACK, (x + 2*w//3 + pupil_x, eye_y + pupil_y), 4)
    
    mouth_width = 30 + int(math.sin(game.combat_idle_timer * 0.1) * 10)
    mouth_y = y + h//2 + 20
    mouth_rect = pygame.Rect(x + w//2 - mouth_width//2, mouth_y, mouth_width, 8)
    pygame.draw.rect(game.screen, COLOR_BLACK, mouth_rect)

def draw_inventory(game):
    game.screen.fill(DARK_GRAY)
    draw_text(game, "INVENTORY", 350, 20, YELLOW)
    draw_text(game,
        f"Slots: {len(game.player.inventory)}/{game.player.max_inventory}",
        350, 60)

    if not game.player.inventory:
        draw_text(game, "Inventory empty", 300, 200, GRAY)
    else:
        for i, item in enumerate(game.player.inventory):
            if i == game.selected_item_index:
                pygame.draw.rect(game.screen, (70, 70, 70),
                                 (80, 90 + i * 60, 640, 50))
            
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
            
            color = YELLOW if i == game.selected_item_index else WHITE
            draw_text(game, item_text, 100, 100 + i * 60, color, game.small_font)
            
            # Draw equipped indicator
            if item == game.player.equipped_weapon:
                draw_text(game, "[EQUIPPED WEAPON]", 550, 100 + i * 60,
                          GREEN, game.small_font)
            elif item == game.player.equipped_armor:
                draw_text(game, "[EQUIPPED ARMOR]", 550, 100 + i * 60,
                          BLUE, game.small_font)

    draw_ui_button_simple(game, game.use_item_button, "Use/Equip", False)
    draw_ui_button_simple(game, game.drop_item_button, "Drop", False)
    draw_ui_button_simple(game, game.back_button, "Back", False)

    if game.player.keys:
        draw_text(game, f"Keys: {', '.join(sorted(game.player.keys))}",
                  100, 500, YELLOW, game.small_font)

def draw_game_over(game):
    """Draw game over screen"""
    game.screen.fill(COLOR_BLACK)
    draw_text(game, "GAME OVER", 250, 250, RED,
              pygame.font.SysFont(None, 72))
    draw_text(game, f"You reached floor {game.floor}", 300, 350, WHITE)
    draw_text(game, "Press SPACE to restart or ESC to quit",
              200, 450, WHITE, game.small_font)


def draw_victory(game):
    """Draw victory screen"""
    game.screen.fill(DARK_GRAY)
    draw_text(game, "VICTORY!", 300, 200, YELLOW,
              pygame.font.SysFont(None, 72))
    draw_text(game, "All enemies defeated!", 300, 300, GREEN)
    draw_text(game,
        f"Final Level: {game.player.level} | XP: {game.player.xp}",
        280, 350, WHITE)
    draw_text(game, "Press SPACE to play again or ESC to quit",
              200, 450, WHITE, game.small_font)

