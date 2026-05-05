import os

import pygame

from config import TILE_SIZE, ASSET_DIR, SCRIPT_DIR


def load_sprite(filename, width=TILE_SIZE, height=TILE_SIZE):
    path = os.path.join(ASSET_DIR, filename)
    img = pygame.image.load(path).convert_alpha()
    return pygame.transform.scale(img, (width, height))


class Assets:
    def __init__(self):
        self.floor     = load_sprite("floor_1.png")
        self.floor_2   = load_sprite("floor_2.png")
        self.floor_3   = load_sprite("floor_3.png")
        self.wall  = load_sprite("wall_mid.png")
        self.door      = load_sprite("doors_leaf_closed.png")
        self.chest     = load_sprite("chest_full_open_anim_f0.png")
        self.trap      = load_sprite("floor_spikes_anim_f0.png")
        self.stairs    = load_sprite("floor_ladder.png")
        self.player_idle = [
            load_sprite(f"knight_m_idle_anim_f{i}.png", TILE_SIZE, TILE_SIZE)
            for i in range(4)
        ]
        self.player_run = [
            load_sprite(f"knight_m_run_anim_f{i}.png", TILE_SIZE, TILE_SIZE)
            for i in range(4)
        ]
        self.floor_tiles = [self.floor, self.floor_2, self.floor_3]
        
        #Combat UI assets
        self.ui_menu = None
        self.ui_health = None
        self.ui_dialog = None
        self.ui_title = None
        self.combat_bg = None
        
        self._load_ui_assets()

    def _load_ui_assets(self):
        """Load UI assets from Angria pack"""
        # Fix the path - go directly to assets/images/UI
        ui_dir = os.path.join(SCRIPT_DIR, "assets", "images", "UI")
        print(f"Looking for UI assets in: {ui_dir}")
        
        try:
            self.ui_menu = pygame.image.load(os.path.join(ui_dir, "UI-Menu and Buttons.png")).convert_alpha()
            self.ui_health = pygame.image.load(os.path.join(ui_dir, "UI-Life-and-mana-Sheet.png")).convert_alpha()
            self.ui_dialog = pygame.image.load(os.path.join(ui_dir, "UI-Dialog-box2.png")).convert_alpha()
            self.ui_title = pygame.image.load(os.path.join(ui_dir, "UI-Title-screen2.png")).convert_alpha()
            self.combat_bg = pygame.image.load(os.path.join(ui_dir, "OldDungeon.png")).convert_alpha()
            print("UI assets loaded successfully!")
        except Exception as e:
            print(f"UI assets not found: {e}")
            self.ui_menu = None
            self.ui_health = None
            self.ui_dialog = None

    def draw_ui_panel(game, x, y, width, height):
        """Draw decorative panel with corners"""
        # Border
        pygame.draw.rect(game.screen, (40, 35, 45), (x, y, width, height))
        pygame.draw.rect(game.screen, (80, 70, 90), (x, y, width, height), 2)
        # Inner dark area
        pygame.draw.rect(game.screen, (20, 18, 25), (x+4, y+4, width-8, height-8))
        # Corner decorations
        for cx, cy in [(x, y), (x+width-10, y), (x, y+height-10), (x+width-10, y+height-10)]:
            pygame.draw.line(game.screen, (120, 100, 80), (cx, cy), (cx+10, cy), 2)
            pygame.draw.line(game.screen, (120, 100, 80), (cx, cy), (cx, cy+10), 2)

    def draw_ui_dialog_box(game, x, y, width, height):
        """Draw a dialog box for combat log"""
        pygame.draw.rect(game.screen, (25, 22, 30), (x, y, width, height))
        pygame.draw.rect(game.screen, (100, 80, 60), (x, y, width, height), 2)
        # Decorative top bar
        pygame.draw.rect(game.screen, (60, 45, 35), (x+2, y+2, width-4, 18))
