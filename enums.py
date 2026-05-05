from enum import Enum


class GameState(Enum):
    MAIN_MENU = 0
    EXPLORATION = 1
    COMBAT = 2
    INVENTORY = 3
    PAUSED = 4
    GAME_OVER = 5
    VICTORY = 6
    SHOP = 7
    OPTIONS = 8
    CONTROLS = 9

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
    FOOD = 3
    SANITY = 4
    TORCH = 5

class BodyPart(Enum):
    HEAD = 0
    TORSO = 1
    LEFT_ARM = 2
    RIGHT_ARM = 3
    LEFT_LEG = 4
    RIGHT_LEG = 5
    