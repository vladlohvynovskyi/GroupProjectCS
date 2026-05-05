from enum import Enum


class GameState(Enum):
    EXPLORATION = 0
    COMBAT = 1
    INVENTORY = 2
    PAUSED = 3
    GAME_OVER = 4
    VICTORY = 5

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

class BodyPart(Enum):
    HEAD = 0
    TORSO = 1
    LEFT_ARM = 2
    RIGHT_ARM = 3
    LEFT_LEG = 4
    RIGHT_LEG = 5
