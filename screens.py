import pygame

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE,
    PLAYER_LIGHT_RADIUS, DARKNESS,
    COLOR_BLACK, WHITE, RED, GREEN, BLUE, YELLOW,
    GRAY, DARK_GRAY,
)
from enums import GameState, ItemType
from elements import ELEMENT_COLORS
from ui import draw_text, draw_button, draw_health_bar
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
        draw_text(game, f"Weapon: {game.player.equipped_weapon.name}", 10, 130, YELLOW, game.small_font)
    
    # Draw inventory button
    draw_button(game, game.inventory_button, "Inventory (I)")
    
    # Draw controls hint
    draw_text(game, "WASD: Move | E: Interact | I: Inventory", 
              200, SCREEN_HEIGHT - 30, WHITE, game.small_font)


def draw_combat(game):
    """Draw the combat mode"""
    game.screen.fill(DARK_GRAY)
    
    # Check if we have a current enemy (safety check)
    if not game.current_enemy:
        # If no enemy, return to exploration
        game.state = GameState.EXPLORATION
        return

    # Player health bar
    draw_health_bar(game, 50, 50, 200, 30, game.player.hp, game.player.max_hp, GREEN)
    draw_text(game, f"Player HP: {game.player.hp}", 260, 55)
    
    # Enemy health bar
    if game.current_enemy:
        draw_health_bar(game, 50, 100, 200, 30, game.current_enemy.hp, 
                        game.current_enemy.max_hp, RED)
        
        # Enemy info
        enemy_element_color = ELEMENT_COLORS[game.current_enemy.element]
        draw_text(game, f"{game.current_enemy.name}", 260, 105, WHITE)
        draw_text(game, f"HP: {game.current_enemy.hp}/{game.current_enemy.max_hp}", 260, 125)
        draw_text(game, f"Element: {game.current_enemy.element.name}", 260, 145, enemy_element_color)
        
        # Draw enemy sprite larger in combat
        if game.current_enemy.image:
            # Draw enemy in center of screen
            enemy_rect = pygame.Rect(SCREEN_WIDTH//2 - 50, 180, 100, 100)
            scaled_img = pygame.transform.scale(game.current_enemy.image, (100, 100))
            game.screen.blit(scaled_img, enemy_rect)

    # Weapon info
    if game.player.equipped_weapon:
        weapon = game.player.equipped_weapon
        weapon_element_color = ELEMENT_COLORS[weapon.element]
        multiplier = weapon.get_damage_multiplier(game.current_enemy.element)
        
        draw_text(game, f"Weapon: {weapon.name}", 50, 200, WHITE)
        draw_text(game, f"Element: {weapon.element.name}", 50, 225, weapon_element_color)
        draw_text(game, f"Damage: {weapon.damage} + {game.player.level * 2} (lvl bonus)", 50, 250, WHITE, game.small_font)
        
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
        draw_text(game, eff_text, 50, 275, eff_color)

    # Combat buttons
    draw_button(game, game.attack_button, "ATTACK")
    draw_button(game, game.run_button, "RUN (50%)")
    draw_button(game, game.inventory_button, "INVENTORY")

    # Combat log (last 5 messages)
    for i, msg in enumerate(game.combat_log[-5:]):
        draw_text(game, msg, 50, 350 + i * 25, WHITE, game.small_font)

    # Turn indicator
    turn_color = GREEN if game.combat_turn == "player" else RED
    draw_text(game, game.combat_message, 300, 500, turn_color)

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

    draw_button(game, game.use_item_button, "Use/Equip")
    draw_button(game, game.drop_item_button, "Drop")
    draw_button(game, game.back_button, "Back")

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

