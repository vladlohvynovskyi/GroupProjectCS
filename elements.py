from enums import Element


# Damage multiplier table: (attacker_element, defender_element) -> multiplier
EFFECTIVENESS = {
    (Element.FIRE, Element.EARTH): 1.5,
    (Element.WATER, Element.FIRE): 1.5,
    (Element.EARTH, Element.WATER): 1.5,
    (Element.EARTH, Element.FIRE): 0.5,
    (Element.FIRE, Element.WATER): 0.5,
    (Element.WATER, Element.EARTH): 0.5,
    (Element.HOLY, Element.FIRE): 2.0,
    (Element.HOLY, Element.EARTH): 2.0,
    (Element.HOLY, Element.WATER): 2.0,
    (Element.DARK, Element.HOLY): 2.5,
}

ELEMENT_COLORS = {
    Element.NORMAL: (255, 255, 255),
    Element.FIRE: (200, 0, 0),
    Element.WATER: (0, 100, 200),
    Element.EARTH: (0, 200, 0),
    Element.HOLY: (255, 255, 0),
    Element.DARK: (50, 50, 50),
}

