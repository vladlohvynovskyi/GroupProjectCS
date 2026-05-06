import pygame
import math
import random

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE,
    PLAYER_LIGHT_RADIUS, DARKNESS,
    COLOR_BLACK, WHITE, RED, GREEN, BLUE, YELLOW,
    GRAY, DARK_GRAY, LIGHT_GRAY, ORANGE, FONTS_DIR
)
from enums import GameState, ItemType, BodyPart, Element
from elements import ELEMENT_COLORS
from ui import draw_text, draw_ui_button, draw_ui_button_simple, draw_health_bar, draw_ui_health_bar_angria, draw_button
from minimap import draw_minimap
from status import StatusType


def _apply_light(surface, cx, cy, radius, max_alpha):
    d = radius * 2
    light_surf = pygame.Surface((d, d), pygame.SRCALPHA)
    light_surf.fill((0, 0, 0, max_alpha))
    for r in range(radius, 0, -4):
        alpha = int(max_alpha * (r / radius) ** 2)
        pygame.draw.circle(light_surf, (0, 0, 0, alpha), (radius, radius), r)
    surface.blit(light_surf, (cx - radius, cy - radius), special_flags=pygame.BLEND_RGBA_MIN)


def draw_darkness(game, camera_x, camera_y):
    darkness = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    darkness.fill((0, 0, 0, DARKNESS))

    px = int(game.player.x - camera_x)
    py = int(game.player.y - camera_y)

    light_radius = PLAYER_LIGHT_RADIUS
    
    #Too low hunger makes the game darker (vision drops)
    if game.player.hunger <= 10:
        light_radius = int(light_radius * 0.65)
    elif game.player.hunger <= 20:
        light_radius = int(light_radius * 0.8)

    if game.player.sanity <= 20:
        light_radius = int(light_radius * 0.75)

    if game.player.torch_time_left > 0:
        light_radius += game.player.torch_radius_bonus

    _apply_light(darkness, px, py, light_radius, DARKNESS)

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

     #Sanity screen shake
    if game.player.sanity <= 10:
        camera_x += random.randint(-6, 6)
        camera_y += random.randint(-6, 6)
    elif game.player.sanity <= 20:
        camera_x += random.randint(-3, 3)
        camera_y += random.randint(-3, 3)
    
    # Draw dungeon
    game.dungeon.draw(game.screen, camera_x, camera_y, game.assets)
    
    # Draw enemies
    for enemy in game.dungeon.enemies:
        if enemy.hp > 0:
            enemy.draw(game.screen, camera_x, camera_y)

    #Draw NPCs
    for npc in game.npcs:
        npc.draw(game.screen, camera_x, camera_y, game.assets)

    
    
    # Draw player
    game.player.draw(game.screen, camera_x, camera_y, game.assets)
    draw_darkness(game, camera_x, camera_y)
    
    # Draw minimap
    draw_minimap(game)
    
    # Draw UI text
    draw_text(game, f"HP: {game.player.hp}/{game.player.max_hp}", 10, 10, RED)
    draw_text(game, f"Hunger: {game.player.hunger}/{game.player.max_hunger}", 10, 40, YELLOW)
    draw_text(game, f"Sanity: {game.player.sanity}/{game.player.max_sanity}", 10, 70, BLUE)
    draw_text(game, f"Floor: {game.floor}", 10, 100, WHITE)
    draw_text(game, f"Level: {game.player.level} | XP: {game.player.xp}", 10, 130, WHITE)
    
    #Quest UI
    if game.quest_active or game.quest_completed:
        if game.quest_type == "kill":
            draw_text(
                game,
                f"Quest: Defeat enemies {game.quest_kills}/{game.quest_goal}",
                10,
                225,
                YELLOW,
                game.small_font
            )
        elif game.quest_type == "collect":
            draw_text(
                game,
                f"Quest: Collect crystals {game.player.crystal_bag}/{game.player.crystal_bag_max}",
                10,
                225,
                BLUE,
                game.small_font
            )

        if game.quest_completed:
            draw_text(
                game,
                "Quest complete! Return to quest giver.",
                10,
                250,
                GREEN,
                game.small_font
            )
    # Warnings in bottom-middle
    warning_messages = []

    if game.player.hunger == 0:
        warning_messages.append(("STARVING! Find food!", RED))
    elif game.player.hunger <= 10:
        warning_messages.append(("CRITICAL HUNGER!", RED))
    elif game.player.hunger <= 20:
        warning_messages.append(("Hunger is low", YELLOW))
    if game.player.torch_time_left <= 0 and game.player.darkness_timer >= 90:
        warning_messages.append(("It's too dark.... Find a torch", BLUE))


    if game.player.sanity == 0:

        warning_messages.append(("SANITY LOST!", RED))
    elif game.player.sanity <= 20:
        warning_messages.append(("MENTAL BREAKDOWN!", RED))
    elif game.player.sanity <= 40:
        warning_messages.append(("Sanity is low", BLUE))

    warning_y = SCREEN_HEIGHT - 250
    for text, color in warning_messages:
        text_surf = game.medium_font.render(text, True, color)
        text_x = SCREEN_WIDTH // 2 - text_surf.get_width() // 2
        game.screen.blit(text_surf, (text_x, warning_y))
        warning_y += 32
    
    
    # Draw inventory button
    game.inventory_button = pygame.Rect(640, 608, 220, 52)
    draw_button(game, game.inventory_button, "Inventory (I)")

    #Show the messages on screen
    log_y = SCREEN_HEIGHT - 155
    for i, msg in enumerate(game.combat_log[-4:]):
        draw_text(game, msg, 10, log_y + i * 22, WHITE, game.small_font)
    
    # Draw controls hint
    draw_text(game, "WASD: Move | E: Interact | I: Inventory",
              200, SCREEN_HEIGHT - 25, WHITE, game.small_font)
    
    draw_npc_dialogue(game)


def draw_combat(game):

    shake_x = 0
    shake_y = 0
    if hasattr(game, 'screen_shake') and game.screen_shake > 0:
        game.screen_shake -= 1
        intensity = game.screen_shake / 4
        shake_x = random.randint(-int(5 * intensity), int(5 * intensity))
        shake_y = random.randint(-int(3 * intensity), int(3 * intensity))

    """Draw combat - with background image"""
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
    
    # ===== FLASH RED WHEN PLAYER TAKES DAMAGE =====
    if hasattr(game, 'player_flash_timer') and game.player_flash_timer > 0:
        game.player_flash_timer -= 1
        flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        flash_surf.fill((255, 0, 0, 80))
        game.screen.blit(flash_surf, (0, 0))
    
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
    draw_panel(20, 35, 260, 185, "PLAYER")
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
    pygame.draw.line(game.screen, (80, 70, 60), (status_x, status_y + 15), (status_x + 150, status_y + 15), 1)

    # Show active status effects
    y_offset = 25
    if game.player.status_effects:
        for effect in game.player.status_effects:
            effect_name = effect.type.value.replace("_", " ").upper()
            duration_text = f" ({effect.duration})"
            
            # Color coding
            if "UP" in effect.type.value.upper():
                color = GREEN
            elif "DOWN" in effect.type.value.upper():
                color = RED
            elif effect.type == StatusType.POISON:
                color = (100, 255, 100)  # Toxic green
            elif effect.type == StatusType.STUN:
                color = YELLOW
            else:
                color = WHITE
            
            draw_text(game, f"• {effect_name}{duration_text}", status_x + 5, status_y + y_offset, color, game.small_font)
            y_offset += 18
    else:
        draw_text(game, "• None", status_x + 5, status_y + y_offset, WHITE, game.small_font)
    
    # === ENEMY PANEL ===
    draw_panel(SCREEN_WIDTH//2 - 185, 25, 370, 305, enemy.name.upper())
    
    # Enemy sprite
    sprite_size = getattr(enemy, 'combat_size', 160)
    enemy_x = SCREEN_WIDTH//2 - sprite_size//2 - 10
    enemy_y = 70
    
    if enemy.image:
        scaled = pygame.transform.scale(enemy.image, (sprite_size, sprite_size))
        game.screen.blit(scaled, (enemy_x, enemy_y))

    # Draw damage numbers on enemy
    for dn in enemy.damage_numbers:
        font = pygame.font.Font(None, 28)
        text = game.small_font.render(str(dn["value"]), True, (255, 100, 100))
        text_x = enemy_x + sprite_size//2 + dn["x_offset"]
        text_y = enemy_y - 20 + dn["y_offset"]
        game.screen.blit(text, (text_x - text.get_width()//2, text_y))
    
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
    draw_ui_health_bar_angria(game, SCREEN_WIDTH//2 - 160, 260, 320, 50, enemy.hp, enemy.max_hp)
    draw_text(game, f"HP: {enemy.hp}/{enemy.max_hp}", SCREEN_WIDTH//2 - 50, 290, WHITE, game.small_font)
    element_color = ELEMENT_COLORS[enemy.element]
    draw_text(game, f"Element: {enemy.element.name}", SCREEN_WIDTH//2 - 60, 310, element_color, game.small_font)
    
    # === BODY PARTS PANEL ===
    draw_panel(SCREEN_WIDTH - 280, 30, 260, 340, "TARGET BODY PARTS")
    
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
        
        btn_rect = pygame.Rect(SCREEN_WIDTH - 270, y_pos, 240, 30)
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
    draw_panel(30, SCREEN_HEIGHT - 190, SCREEN_WIDTH - 60, 130, "COMBAT LOG")
    
    for i, msg in enumerate(game.combat_log[-4:]):
        if "CRITICAL" in msg:
            color = YELLOW
        elif "Victory" in msg:
            color = GREEN
        elif "destroyed" in msg:
            color = ORANGE
        else:
            color = WHITE
        draw_text(game, msg[:75], 45, SCREEN_HEIGHT - 160 + i * 24, color, game.small_font)
    
    # === ACTION BUTTONS ===
    button_y = SCREEN_HEIGHT - 75
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

    # Draw critical hit popup
    if hasattr(game, 'crit_popup_timer') and game.crit_popup_timer > 0:
        game.crit_popup_timer -= 1
        alpha = min(255, game.crit_popup_timer * 8)
        crit_font = pygame.font.Font(FONTS_DIR + "/MedievalSharp-Regular.ttf", 48)
        crit_surf = crit_font.render("CRITICAL!", True, (255, 200, 0))
        game.screen.blit(crit_surf, (game.crit_popup_x - crit_surf.get_width()//2, game.crit_popup_y - game.crit_popup_timer))
      
    # Draw status effect popup
    if hasattr(game, 'status_popup_timer') and game.status_popup_timer > 0:
        game.status_popup_timer -= 1
        # Fade out effect
        alpha = min(255, game.status_popup_timer * 4)
        # Use larger font for status
        status_font = pygame.font.Font(FONTS_DIR + "/MedievalSharp-Regular.ttf", 48)
        status_surf = status_font.render(game.status_popup_text, True, game.status_popup_color)
        # Float upward
        float_y = 150 - game.status_popup_timer // 2
        status_x = SCREEN_WIDTH // 2 - status_surf.get_width() // 2
        game.screen.blit(status_surf, (status_x, float_y))

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
    game.screen.fill(COLOR_BLACK)

    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    game.screen.blit(overlay, (0, 0))

    panel_rect = pygame.Rect(50, 90, 860, 540)

    if game.assets.combat_bg:
        bg = pygame.transform.scale(game.assets.combat_bg, panel_rect.size)
        game.screen.blit(bg, panel_rect.topleft)
    else:
        pygame.draw.rect(game.screen, DARK_GRAY, panel_rect)

    pygame.draw.rect(game.screen, LIGHT_GRAY, panel_rect, 3)

    title = game.title_font.render("INVENTORY", True, YELLOW)
    game.screen.blit(title, title.get_rect(center=(panel_rect.centerx, panel_rect.y + 55)))

    # Player sprite
    frames = game.assets.player_idle
    frame = frames[game.player.anim_frame]
    if game.player.facing_left:
        frame = pygame.transform.flip(frame, True, False)

    player_big = pygame.transform.scale(frame, (240, 240))
    game.screen.blit(player_big, (panel_rect.x + 55, panel_rect.y + 145))

    # Inventory list box
    inv_box = pygame.Rect(panel_rect.x + 330, panel_rect.y + 120, 470, 260)
    pygame.draw.rect(game.screen, (20, 18, 25), inv_box)
    pygame.draw.rect(game.screen, LIGHT_GRAY, inv_box, 2)

    draw_text(
        game,
        f"Slots: {len(game.player.inventory)}/{game.player.max_inventory}",
        inv_box.x + 20,
        inv_box.y + 15,
        WHITE,
        game.medium_font
    )

    visible_count = 5
    start_index = max(0, game.selected_item_index - visible_count + 1)
    visible_items = game.player.inventory[start_index:start_index + visible_count]

    if not game.player.inventory:
        draw_text(game, "Inventory empty", inv_box.x + 25, inv_box.y + 70, GRAY, game.medium_font)
    else:
        for visible_i, item in enumerate(visible_items):
            real_i = start_index + visible_i
            y = inv_box.y + 60 + visible_i * 36

            if real_i == game.selected_item_index:
                pygame.draw.rect(game.screen, (70, 70, 70), (inv_box.x + 10, y - 4, inv_box.width - 20, 32))

            item_text = item.name

            if item.type == ItemType.WEAPON:
                item_text += f" (DMG {item.damage}, {item.element.name})"
            elif item.type == ItemType.HEALTH:
                item_text += f" (Heal {item.value})"
            elif item.type == ItemType.ARMOR:
                item_text += f" (DEF {item.defense})"
            elif item.type == ItemType.TORCH:
                item_text += f" (Light {int(item.duration)}s)"
            elif item.type == ItemType.FOOD:
                item_text += f" (Hunger {item.value})"
            elif item.type == ItemType.SANITY:
                item_text += f" (Sanity {item.value})"

            if len(item_text) > 38:
                item_text = item_text[:35] + "..."

            color = YELLOW if real_i == game.selected_item_index else WHITE
            draw_text(game, item_text, inv_box.x + 25, y, color, game.small_font)

            if item == game.player.equipped_weapon:
                draw_text(game, "E", inv_box.right - 35, y, GREEN, game.small_font)
            elif item == game.player.equipped_armor:
                draw_text(game, "E", inv_box.right - 35, y, BLUE, game.small_font)

    # Buttons
    game.use_item_button = pygame.Rect(panel_rect.x + 330, panel_rect.y + 405, 160, 50)
    game.drop_item_button = pygame.Rect(panel_rect.x + 510, panel_rect.y + 405, 160, 50)
    game.back_button = pygame.Rect(panel_rect.x + 690, panel_rect.y + 405, 160, 50)

    draw_button(game, game.use_item_button, "Use/Equip")
    draw_button(game, game.drop_item_button, "Drop")
    draw_button(game, game.back_button, "Back")

    draw_text(
        game,
        "W/S or UP/DOWN: Select | ENTER: Use | ESC: Back",
        panel_rect.x + 250,
        panel_rect.y + panel_rect.height - 45,
        WHITE,
        game.small_font
    )

    if game.player.keys:
        keys_text = f"Keys: {', '.join(sorted(game.player.keys))}"
        draw_text(game, keys_text[:55], panel_rect.x + 330, panel_rect.y + 470, YELLOW, game.small_font)

def draw_game_over(game):
    """Draw game over screen"""
    game.screen.fill((24, 21, 35))
    draw_text(game, "GAME OVER", 250, 250, RED,
              pygame.font.SysFont(None, 72))
    draw_text(game, f"You reached floor {game.floor}", 300, 350, WHITE)
    draw_text(game, "Press SPACE to restart or ESC to quit",
              200, 450, WHITE, game.small_font)


def draw_victory(game):
    """Draw victory screen"""
    game.screen.fill((24, 21, 35))
    draw_text(game, "VICTORY!", 300, 200, YELLOW,
              pygame.font.SysFont(None, 72))
    draw_text(game, "All enemies defeated!", 300, 300, GREEN)
    draw_text(game,
        f"Final Level: {game.player.level} | XP: {game.player.xp}",
        280, 350, WHITE)
    draw_text(game, "Press SPACE to play again or ESC to quit",
              200, 450, WHITE, game.small_font)

def draw_shop(game):
    game.screen.fill(COLOR_BLACK)

    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    game.screen.blit(overlay, (0, 0))

    # Bigger shop window
    panel_rect = pygame.Rect(50, 90, 860, 540)

    if game.assets.combat_bg:
        bg = pygame.transform.scale(game.assets.combat_bg, panel_rect.size)
        game.screen.blit(bg, panel_rect.topleft)
    else:
        pygame.draw.rect(game.screen, DARK_GRAY, panel_rect)

    pygame.draw.rect(game.screen, LIGHT_GRAY, panel_rect, 3)

    title = game.title_font.render("MERCHANT SHOP", True, YELLOW)
    game.screen.blit(title, title.get_rect(center=(panel_rect.centerx, panel_rect.y + 55)))

    # Merchant sprite
    frames = game.assets.npc_merchant_idle
    frame = frames[game.shop_npc.anim_frame] if game.shop_npc else frames[0]
    merchant_big = pygame.transform.scale(frame, (240, 240))
    game.screen.blit(merchant_big, (panel_rect.x + 55, panel_rect.y + 145))

    # Shop list box
    shop_box = pygame.Rect(panel_rect.x + 330, panel_rect.y + 120, 470, 260)
    pygame.draw.rect(game.screen, (20, 18, 25), shop_box)
    pygame.draw.rect(game.screen, LIGHT_GRAY, shop_box, 2)

    draw_text(game, f"Your XP: {game.player.xp}", shop_box.x + 20, shop_box.y + 15, WHITE, game.medium_font)

    # Show max 5 items so it cannot overlap
    visible_count = 5
    start_index = max(0, game.selected_shop_index - visible_count + 1)
    visible_items = game.shop_items[start_index:start_index + visible_count]

    for visible_i, item in enumerate(visible_items):
        real_i = start_index + visible_i
        y = shop_box.y + 60 + visible_i * 36

        if real_i == game.selected_shop_index:
            pygame.draw.rect(game.screen, (70, 70, 70), (shop_box.x + 10, y - 4, shop_box.width - 20, 32))

        color = YELLOW if real_i == game.selected_shop_index else WHITE
        draw_text(game, item.name, shop_box.x + 25, y, color, game.small_font)
        draw_text(game, f"{game.shop_prices[real_i]} XP", shop_box.x + 335, y, GREEN, game.small_font)


    if hasattr(game, "shop_message") and game.shop_message:
        msg_surf = game.small_font.render(game.shop_message, True, YELLOW)
        msg_x = panel_rect.centerx - msg_surf.get_width() // 2
        game.screen.blit(msg_surf, (msg_x, panel_rect.y + 385))

    # Buttons
    game.shop_buy_button = pygame.Rect(panel_rect.x + 370, panel_rect.y + 405, 170, 50)
    game.shop_back_button = pygame.Rect(panel_rect.x + 570, panel_rect.y + 405, 170, 50)

    draw_button(game, game.shop_buy_button, "Buy")
    draw_button(game, game.shop_back_button, "Back")

    # Controls text at bottom of window
    draw_text(
        game,
        "W/S or UP/DOWN: Select | ENTER: Buy | ESC: Back",
        panel_rect.x + 250,
        panel_rect.y + panel_rect.height - 45,
        WHITE,
        game.small_font
    )
def draw_npc_dialogue(game):
    if game.dialogue_npc is None:
        return

    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    game.screen.blit(overlay, (0, 0))

    panel_rect = pygame.Rect(80, 130, 800, 420)

    if game.assets.combat_bg:
        bg = pygame.transform.scale(game.assets.combat_bg, panel_rect.size)
        game.screen.blit(bg, panel_rect.topleft)
    else:
        pygame.draw.rect(game.screen, DARK_GRAY, panel_rect)

    pygame.draw.rect(game.screen, LIGHT_GRAY, panel_rect, 3)

    npc = game.dialogue_npc
    title_text = npc.name.upper()
    title = game.title_font.render(title_text, True, YELLOW)
    game.screen.blit(title, (panel_rect.x + 310, panel_rect.y + 25))

    if npc.role == "guide":
        frames = game.assets.npc_guide_idle
    elif npc.role == "healer":
        frames = game.assets.npc_healer_idle
    elif npc.role == "quest":
        frames = game.assets.npc_quest_idle
    else:
        frames = game.assets.npc_guide_idle

    frame = frames[npc.anim_frame]
    npc_big = pygame.transform.scale(frame, (220, 220))
    game.screen.blit(npc_big, (panel_rect.x + 45, panel_rect.y + 105))

    text_box = pygame.Rect(panel_rect.x + 290, panel_rect.y + 125, 450, 160)
    pygame.draw.rect(game.screen, (20, 18, 25), text_box)
    pygame.draw.rect(game.screen, LIGHT_GRAY, text_box, 2)

    words = game.dialogue_text.split()
    line = ""
    y = text_box.y + 25

    for word in words:
        test_line = line + word + " "
        if game.medium_font.size(test_line)[0] > text_box.width - 40:
            draw_text(game, line, text_box.x + 20, y, WHITE, game.medium_font)
            line = word + " "
            y += 32
        else:
            line = test_line

    if line:
        draw_text(game, line, text_box.x + 20, y, WHITE, game.medium_font)

    button_count = len(game.dialogue_buttons)
    total_width = button_count * 180 + max(0, button_count - 1) * 25
    start_x = panel_rect.centerx - total_width // 2
    button_y = panel_rect.y + 330

    for i, button in enumerate(game.dialogue_buttons):
        button["rect"] = pygame.Rect(start_x + i * 205, button_y, 180, 50)
        draw_button(game, button["rect"], button["text"])