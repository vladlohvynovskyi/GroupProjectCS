import os

import pygame

from config import TILE_SIZE, ASSET_DIR, UI_DIR


def load_sprite(filename, width=TILE_SIZE, height=TILE_SIZE):
    path = os.path.join(ASSET_DIR, filename)
    img = pygame.image.load(path).convert_alpha()
    return pygame.transform.scale(img, (width, height))


def load_ui(filename, size=None):
    path = os.path.join(UI_DIR, filename)
    img = pygame.image.load(path).convert_alpha()
    if size is not None:
        img = pygame.transform.smoothscale(img, size)
    return img


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

        # UI assets
        self.ui_panel_tall   = load_ui("Menu01.png")
        self.ui_panel_wide   = load_ui("Menu02.png")
        self.ui_panel_settings = load_ui("PanelSettings.png")
        self.ui_title_bar    = load_ui("Menu_Button.png")
        self.ui_button       = load_ui("Button02.png")
        self.ui_button_alt   = load_ui("Button03.png")
        self.ui_close        = load_ui("Menu_Close.png")
        self.ui_slider_track = load_ui("PanelSettings_Slider.png")
        self.ui_slider_knob  = load_ui("PanelSettings_Slider_B.png")
