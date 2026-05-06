from enums import Element, ItemType
from elements import EFFECTIVENESS



class Item:
    """Base item class with element-aware damage multiplier."""
    def __init__(self, name, item_type, element=Element.NORMAL,
                 value=0, damage=0, defense=0, description=""):
        self.name = name
        self.type = item_type
        self.element = element
        self.value = value
        self.damage = damage
        self.defense = defense
        self.description = description

    def get_damage_multiplier(self, enemy_element):
        if self.type != ItemType.WEAPON:
            return 1.0
        return EFFECTIVENESS.get((self.element, enemy_element), 1.0)


class Weapon(Item):
    def __init__(self, name, element, damage, description=""):
        super().__init__(name, ItemType.WEAPON, element, damage, damage, 0, description)


class HealthPotion(Item):
    def __init__(self, name, heal_amount):
        super().__init__(name, ItemType.HEALTH, Element.NORMAL,
                         heal_amount, 0, 0, f"Heals {heal_amount} HP")


class Armor(Item):
    def __init__(self, name, defense, description=""):
        super().__init__(name, ItemType.ARMOR, Element.NORMAL, 0, 0, defense, description)


class Torch(Item):
    def __init__(self, name="Torch", duration=120.0, radius_bonus=160):
        super().__init__(name, ItemType.TORCH, Element.NORMAL,
                         int(duration), 0, 0,
                         f"Lights the area for {int(duration)}s")
        self.duration = float(duration)
        self.radius_bonus = int(radius_bonus)

class Food(Item):
    def __init__(self, name, hunger_amount):
        super().__init__(name, ItemType.FOOD, Element.NORMAL,
                         hunger_amount, 0, 0, f"Restores {hunger_amount} hunger")

class SanityPotion(Item):
    def __init__(self, name, restore_amount):
        super().__init__(name, ItemType.SANITY, Element.NORMAL,
                         restore_amount, 0, 0, f"Restores {restore_amount} sanity")

class MagicCrystal(Item):
   def __init__(self):
       super().__init__("Magic Crystal", ItemType.QUEST, Element.NORMAL, 0, 0, 0, "crystal")