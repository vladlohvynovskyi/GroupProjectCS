import pygame

from config import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, YELLOW, GRAY, LIGHT_GRAY


BUTTON_W = 320
BUTTON_H = 64
BUTTON_GAP = 18


class MenuButton:
    def __init__(self, rect, label, action):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.action = action
        self.hover = False

    def update_hover(self, mouse_pos):
        self.hover = self.rect.collidepoint(mouse_pos)

    def clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

    def draw(self, screen, game):
        img = game.assets.ui_button if self.hover else game.assets.ui_button_alt
        scaled = pygame.transform.smoothscale(img, self.rect.size)
        screen.blit(scaled, self.rect.topleft)

        color = YELLOW if self.hover else WHITE
        text_surf = game.medium_font.render(self.label, True, color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)


class Slider:
    def __init__(self, rect, value=0.8):
        self.rect = pygame.Rect(rect)
        self.value = max(0.0, min(1.0, value))
        self.dragging = False

    def _knob_x(self):
        return self.rect.x + int(self.value * self.rect.width)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            hit = self.rect.inflate(0, 24).collidepoint(event.pos)
            if hit:
                self.dragging = True
                self._set_from_x(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._set_from_x(event.pos[0])

    def _set_from_x(self, x):
        frac = (x - self.rect.x) / max(1, self.rect.width)
        self.value = max(0.0, min(1.0, frac))

    def draw(self, screen, game):
        track = pygame.transform.smoothscale(
            game.assets.ui_slider_track, self.rect.size
        )
        screen.blit(track, self.rect.topleft)

        knob_size = self.rect.height + 18
        knob = pygame.transform.smoothscale(
            game.assets.ui_slider_knob, (knob_size, knob_size)
        )
        knob_rect = knob.get_rect(center=(self._knob_x(), self.rect.centery))
        screen.blit(knob, knob_rect.topleft)


def _draw_panel(game, panel_rect, panel_image):
    scaled = pygame.transform.smoothscale(panel_image, panel_rect.size)
    game.screen.blit(scaled, panel_rect.topleft)


def _draw_title_bar(game, center_x, y, width, label, color=YELLOW):
    bar_rect = pygame.Rect(0, 0, width, 56)
    bar_rect.center = (center_x, y)
    bar = pygame.transform.smoothscale(game.assets.ui_title_bar, bar_rect.size)
    game.screen.blit(bar, bar_rect.topleft)
    text = game.title_font.render(label, True, color)
    text_rect = text.get_rect(center=bar_rect.center)
    game.screen.blit(text, text_rect)


def _dim_background(game, alpha=160):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, alpha))
    game.screen.blit(overlay, (0, 0))


def build_main_menu_buttons():
    cx = SCREEN_WIDTH // 2
    start_y = 300
    labels_actions = [
        ("START GAME", "start"),
        ("OPTIONS", "options"),
        ("CONTROLS", "controls"),
        ("QUIT", "quit"),
    ]
    buttons = []
    for i, (label, action) in enumerate(labels_actions):
        rect = pygame.Rect(0, 0, BUTTON_W, BUTTON_H)
        rect.center = (cx, start_y + i * (BUTTON_H + BUTTON_GAP))
        buttons.append(MenuButton(rect, label, action))
    return buttons


def build_pause_menu_buttons():
    cx = SCREEN_WIDTH // 2
    start_y = 260
    labels_actions = [
        ("RESUME", "resume"),
        ("OPTIONS", "options"),
        ("CONTROLS", "controls"),
        ("MAIN MENU", "main_menu"),
        ("QUIT", "quit"),
    ]
    buttons = []
    for i, (label, action) in enumerate(labels_actions):
        rect = pygame.Rect(0, 0, BUTTON_W, BUTTON_H)
        rect.center = (cx, start_y + i * (BUTTON_H + BUTTON_GAP))
        buttons.append(MenuButton(rect, label, action))
    return buttons


def build_back_button():
    rect = pygame.Rect(0, 0, BUTTON_W, BUTTON_H)
    rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80)
    return MenuButton(rect, "BACK", "back")


def draw_main_menu(game):
    game.screen.fill((10, 8, 12))

    panel_rect = pygame.Rect(0, 0, 520, 560)
    panel_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20)
    _draw_panel(game, panel_rect, game.assets.ui_panel_tall)

    _draw_title_bar(game, SCREEN_WIDTH // 2, 140, 560, "DEPTH OF DREAD")

    subtitle = game.small_font.render(
        "A dungeon crawler of elemental dread", True, LIGHT_GRAY
    )
    game.screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_WIDTH // 2, 200)))

    mouse_pos = pygame.mouse.get_pos()
    for button in game.main_menu_buttons:
        button.update_hover(mouse_pos)
        button.draw(game.screen, game)

    hint = game.small_font.render(
        "Use the mouse to navigate, or press ENTER to start", True, GRAY
    )
    game.screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40)))


def draw_pause_menu(game):
    # Keep the exploration view dimmed in the background for context.
    _dim_background(game, alpha=180)

    panel_rect = pygame.Rect(0, 0, 480, 560)
    panel_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30)
    _draw_panel(game, panel_rect, game.assets.ui_panel_tall)

    _draw_title_bar(game, SCREEN_WIDTH // 2, 160, 420, "PAUSED")

    mouse_pos = pygame.mouse.get_pos()
    for button in game.pause_menu_buttons:
        button.update_hover(mouse_pos)
        button.draw(game.screen, game)


def draw_options(game):
    _dim_background(game, alpha=200)

    panel_rect = pygame.Rect(0, 0, 720, 520)
    panel_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    _draw_panel(game, panel_rect, game.assets.ui_panel_settings)

    _draw_title_bar(game, SCREEN_WIDTH // 2, 150, 420, "OPTIONS")

    # Volume labels (to the left of sliders)
    labels = [
        ("Master Volume", game.master_slider),
        ("Music Volume", game.music_slider),
        ("SFX Volume", game.sfx_slider),
    ]
    for label, slider in labels:
        text = game.medium_font.render(label, True, WHITE)
        game.screen.blit(text, (slider.rect.x, slider.rect.y - 34))
        slider.draw(game.screen, game)

        pct = game.small_font.render(f"{int(slider.value * 100)}%", True, YELLOW)
        game.screen.blit(
            pct,
            (slider.rect.right + 20, slider.rect.centery - pct.get_height() // 2),
        )

    game.options_back_button.update_hover(pygame.mouse.get_pos())
    game.options_back_button.draw(game.screen, game)


def draw_controls(game):
    _dim_background(game, alpha=200)

    panel_rect = pygame.Rect(0, 0, 720, 560)
    panel_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    _draw_panel(game, panel_rect, game.assets.ui_panel_settings)

    _draw_title_bar(game, SCREEN_WIDTH // 2, 140, 420, "CONTROLS")

    bindings = [
        ("Move",           "W A S D  /  Arrow Keys"),
        ("Interact",       "E"),
        ("Open Inventory", "I"),
        ("Pause Menu",     "Esc"),
        ("Confirm / Use",  "Enter"),
        ("Navigate List",  "Up / Down"),
        ("Attack",         "Click ATTACK"),
        ("Run from Fight", "Click RUN"),
        ("Restart (dead)", "Space"),
    ]

    start_x = SCREEN_WIDTH // 2 - 260
    start_y = 230
    row_h = 38
    for i, (action, keys) in enumerate(bindings):
        y = start_y + i * row_h
        a_surf = game.medium_font.render(action, True, WHITE)
        k_surf = game.medium_font.render(keys, True, YELLOW)
        game.screen.blit(a_surf, (start_x, y))
        game.screen.blit(k_surf, (start_x + 260, y))

    game.controls_back_button.update_hover(pygame.mouse.get_pos())
    game.controls_back_button.draw(game.screen, game)
