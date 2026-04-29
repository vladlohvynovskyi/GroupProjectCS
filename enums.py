from enum import Enum


class GameState(Enum):
    EXPLORATION = 0
    COMBAT = 1
    INVENTORY = 2
    PAUSED = 3
    GAME_OVER = 4
    VICTORY = 5
    MAIN_MENU = 6
    OPTIONS = 7
    CONTROLS = 8

class Element(Enum):
    NORMAL = 0
    FIRE = 1
    WATER = 2
    EARTH = 3
    HOLY = 4
    DARK = 5

class ItemType(Enum):
    WEAPON = 0
    HEALTH = 1
    ARMOR = 2
    TORCH = 3
