import os

import pygame

from config import TILE_SIZE, ASSET_DIR, UI_DIR, SCRIPT_DIR


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
        self.trap_frames = [
            load_sprite(f"floor_spikes_anim_f{i}.png", TILE_SIZE, TILE_SIZE)
            for i in range(4)
        ]
        self.stairs    = load_sprite("floor_ladder.png")

        # Campfire animation 
        campfire_path = os.path.join(SCRIPT_DIR, "assets", "images", "dungeon", "32px fireplace.png")
        campfire_sheet = pygame.image.load(campfire_path).convert_alpha()
        self.campfire_frames = [
            pygame.transform.scale(
                campfire_sheet.subsurface((i * 32, 0, 32, 32)),
                (TILE_SIZE, TILE_SIZE),
            )
            for i in range(6)
        ]
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

        # Healer NPC
        healer_path = os.path.join(SCRIPT_DIR, "assets", "images", "npcs", "monk.png")
        healer_sheet = pygame.image.load(healer_path).convert_alpha()
        healer_frame = healer_sheet.subsurface((0, 0, 32, 32))
        self.npc_healer = pygame.transform.scale(healer_frame, (TILE_SIZE, TILE_SIZE))

        # Merchant NPC
        merchant_path = os.path.join(SCRIPT_DIR, "assets", "images", "npcs", "Male1.png")
        merchant_sheet = pygame.image.load(merchant_path).convert_alpha()
        merchant_frame = merchant_sheet.subsurface((0, 0, 32, 32))
        self.npc_merchant = pygame.transform.scale(merchant_frame, (TILE_SIZE, TILE_SIZE))

        # Guide NPC
        guide_path = os.path.join(SCRIPT_DIR, "assets", "images", "npcs", "Male2.png")
        guide_sheet = pygame.image.load(guide_path).convert_alpha()
        guide_frame = guide_sheet.subsurface((0, 0, 32, 32))
        self.npc_guide = pygame.transform.scale(guide_frame, (TILE_SIZE, TILE_SIZE))

        # Quest NPC
        quest_path = os.path.join(SCRIPT_DIR, "assets", "images", "npcs", "Necromancer_creativekind-Sheet.png")
        quest_sheet = pygame.image.load(quest_path).convert_alpha()
        quest_frame = quest_sheet.subsurface((0, 0, 128, 128))
        self.npc_quest = pygame.transform.scale(quest_frame, (TILE_SIZE, TILE_SIZE))

        # Dark tint
        self.npc_merchant.fill((180, 180, 180), special_flags=pygame.BLEND_RGB_MULT)
