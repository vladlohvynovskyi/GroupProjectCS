from enum import Enum

class StatusType(Enum):
    ATK_UP = "atk_up"
    DEF_UP = "def_up"
    SPD_UP = "spd_up"
    ATK_DOWN = "atk_down"
    DEF_DOWN = "def_down"
    STUN = "stun"
    POISON = "poison"
    REGEN = "regen"

class StatusEffect:
    def __init__(self, effect_type, duration, value=0):
        self.type = effect_type
        self.duration = duration
        self.value = value  # For percentage modifiers or damage/heal amounts
    
    def tick(self):
        """Decrease duration by 1, return True if expired"""
        self.duration -= 1
        return self.duration <= 0
    
    def get_damage_modifier(self):
        """Return damage multiplier for ATK/DEF effects"""
        if self.type == StatusType.ATK_UP:
            return 1.25
        elif self.type == StatusType.ATK_DOWN:
            return 0.75
        return 1.0
    
    def get_defense_modifier(self):
        """Return defense multiplier"""
        if self.type == StatusType.DEF_UP:
            return 0.75  # Take 25% less damage
        elif self.type == StatusType.DEF_DOWN:
            return 1.25  # Take 25% more damage
        return 1.0