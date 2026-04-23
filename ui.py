import pygame

from config import COLOR_BLACK, WHITE, LIGHT_GRAY, DARK_GRAY


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

