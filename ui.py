import pygame

from config import COLOR_BLACK, WHITE, LIGHT_GRAY, DARK_GRAY, YELLOW, RED


def draw_text(game, text, x, y, color=WHITE, font_obj=None):
    if font_obj is None:
        font_obj = game.font
    game.screen.blit(font_obj.render(text, True, color), (x, y))


def draw_button(game, rect, text, color=LIGHT_GRAY, text_color=WHITE):
    pygame.draw.rect(game.screen, color, rect)
    pygame.draw.rect(game.screen, COLOR_BLACK, rect, 2)
    text_surf = game.small_font.render(text, True, text_color)
    text_rect = text_surf.get_rect(center=rect.center)
    game.screen.blit(text_surf, text_rect)


def draw_health_bar(game, x, y, width, height, current, maximum, color):
    # Background
    pygame.draw.rect(game.screen, DARK_GRAY, (x, y, width, height))
    # Health
    health_width = (current / maximum) * width
    if health_width > 0:
        pygame.draw.rect(game.screen, color, (x, y, health_width, height))
    # Border
    pygame.draw.rect(game.screen, WHITE, (x, y, width, height), 2)

def draw_ui_panel(game, x, y, width, height):
    """Simple clean panel (no assets needed)"""
    # Outer border
    pygame.draw.rect(game.screen, (40, 35, 45), (x, y, width, height))
    pygame.draw.rect(game.screen, (80, 70, 90), (x, y, width, height), 2)
    # Inner area
    pygame.draw.rect(game.screen, (20, 18, 25), (x+4, y+4, width-8, height-8))
    # Corner accents
    pygame.draw.line(game.screen, (120, 100, 80), (x, y), (x+12, y), 2)
    pygame.draw.line(game.screen, (120, 100, 80), (x, y), (x, y+12), 2)
    pygame.draw.line(game.screen, (120, 100, 80), (x+width, y), (x+width-12, y), 2)
    pygame.draw.line(game.screen, (120, 100, 80), (x+width, y), (x+width, y+12), 2)
    pygame.draw.line(game.screen, (120, 100, 80), (x, y+height), (x+12, y+height), 2)
    pygame.draw.line(game.screen, (120, 100, 80), (x, y+height), (x, y+height-12), 2)
    pygame.draw.line(game.screen, (120, 100, 80), (x+width, y+height), (x+width-12, y+height), 2)
    pygame.draw.line(game.screen, (120, 100, 80), (x+width, y+height), (x+width, y+height-12), 2)


def draw_ui_dialog_box(game, x, y, width, height):
    """Simple dialog box"""
    pygame.draw.rect(game.screen, (25, 22, 30), (x, y, width, height))
    pygame.draw.rect(game.screen, (100, 80, 60), (x, y, width, height), 2)
    pygame.draw.rect(game.screen, (60, 45, 35), (x+2, y+2, width-4, 22))
    pygame.draw.rect(game.screen, (80, 60, 45), (x+4, y+4, width-8, height-8), 1)


def draw_ui_health_bar_angria(game, x, y, width, height, current, maximum):
    """Draw health bar using Angria health bar assets"""
    
    if not game.assets.ui_health:
        draw_health_bar(game, x, y, width, height, current, maximum, RED)
        return
    
    try:
        percent = current / maximum
        
        # Determine column
        if percent >= 1.0:
            col = 7
        elif percent >= 0.9:
            col = 6
        elif percent >= 0.8:
            col = 5
        elif percent >= 0.65:
            col = 4
        elif percent >= 0.5:
            col = 3
        elif percent >= 0.3:
            col = 2
        elif percent >= 0.1:
            col = 1
        else:
            col = 0
        
        
        frame_width = 48
        frame_height = 16
        
        bar_piece = game.assets.ui_health.subsurface((col * frame_width, 0, frame_width, frame_height))
        bar_scaled = pygame.transform.scale(bar_piece, (width, height))
        game.screen.blit(bar_scaled, (x, y))
        
    except Exception as e:
        draw_health_bar(game, x, y, width, height, current, maximum, RED)
    
    pygame.draw.rect(game.screen, WHITE, (x, y, width, height), 1)


def draw_ui_button(game, rect, text, asset_name, sheet_col, sheet_row, is_hovered=False):
    """
    Draw a button using a specific asset from a UI sheet
    
    For UI-Title-screen2.png:
    - Each button is 48x32 pixels
    - 14 columns, 3 rows
    - sheet_col: 0-13 (which column)
    - sheet_row: 0-2 (which row)
    """
    # Select the right asset sheet
    if asset_name == "menu":
        sheet = game.assets.ui_menu
    elif asset_name == "title":
        sheet = game.assets.ui_title
    elif asset_name == "dialog":
        sheet = game.assets.ui_dialog
    else:
        sheet = None
    
    if not sheet:
        draw_ui_button_simple(game, rect, text, is_hovered)
        return
    
    try:
        # For title sheet, each button is 48x32 pixels
        if asset_name == "title":
            button_width = 48
            button_height = 32
        else:
            # Default for other sheets
            button_width = 32
            button_height = 16
        
        # Extract the button from the sheet
        button_piece = sheet.subsurface((sheet_col * button_width, sheet_row * button_height, button_width, button_height))
        button_scaled = pygame.transform.scale(button_piece, (rect.width, rect.height))
        
        game.screen.blit(button_scaled, (rect.x, rect.y))
        
        # Hover effect - make brighter
        if is_hovered:
            hover_overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            hover_overlay.fill((255, 255, 255, 60))
            game.screen.blit(hover_overlay, (rect.x, rect.y))
        
        # Draw text over the button
        text_surf = game.small_font.render(text, True, WHITE)
        text_rect = text_surf.get_rect(center=rect.center)
        game.screen.blit(text_surf, text_rect)
        
    except Exception as e:
        print(f"Button error: {e}")
        draw_ui_button_simple(game, rect, text, is_hovered)

def draw_ui_button_simple(game, rect, text, is_hovered=False):
    """Simple button without assets (fallback)"""
    if is_hovered:
        pygame.draw.rect(game.screen, (100, 90, 70), rect)
        pygame.draw.rect(game.screen, YELLOW, rect, 2)
    else:
        pygame.draw.rect(game.screen, (60, 50, 40), rect)
        pygame.draw.rect(game.screen, LIGHT_GRAY, rect, 2)
    
    text_surf = game.small_font.render(text, True, WHITE)
    text_rect = text_surf.get_rect(center=rect.center)
    game.screen.blit(text_surf, text_rect)


