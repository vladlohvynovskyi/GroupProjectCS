import pygame

from config import (
    TILE_SIZE, MAP_COLS, MAP_ROWS,
    TILE_FLOOR, TILE_CAMPFIRE, TILE_TRAP, TILE_STAIR,
)
from enums import Element, ItemType
from items import Weapon, HealthPotion, Armor
from status import StatusEffect

class Player:
    SIZE  = TILE_SIZE - 12
    SPEED = 300

    IDLE_FRAME_DURATION = 0.15  # seconds per idle frame
    RUN_FRAME_DURATION  = 0.09  # seconds per run frame

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.keys: set = set()
        self.max_hp = 100
        self.hp = 100
        self.xp = 0
        self.level = 1

        # Animation state
        self.anim_frame = 0
        self.anim_timer = 0.0
        self.is_moving  = False
        self.facing_left = False

        self.escape_timer = 0.0  # seconds of post-escape invincibility

        # Active torch state (light bonus that decays over time)
        self.torch_time_left = 0.0
        self.torch_radius_bonus = 0

        # Inventory
        self.inventory = []
        self.max_inventory = 12
        self.equipped_weapon = None
        self.equipped_armor = None

        self.status_effects = []  # List of StatusEffect objects
        self.poison_tick_timer = 0
        self.regen_tick_timer = 0
        # Starting equipment
        self._setup_starting_gear()

        #Crystal bag
        self.crystal_bag = 0
        self.crystal_bag_max = 0

        # Hunger system
        self.max_hunger = 100
        self.hunger = 100
        self.hunger_timer = 0.0
        self.starvation_timer = 0.0

        #Sanity
        self.max_sanity = 100 
        self.sanity = 100 

        #self.sanity_timer = 0.0
        self.sanity_hunger_timer = 0.0
        self.darkness_timer =0.0

        self.combat_stress = 0
        self.last_combat_time = 0.0
       
       
      
    def _setup_starting_gear(self):
        """Give player starting items"""
        starter_sword = Weapon("Wooden Sword", Element.NORMAL, 15, "A basic wooden sword")
        starter_armor = Armor("Cloth Armor", 2, "Basic protection")
        health_potion = HealthPotion("Health Potion", 30)
        
        self.add_item(starter_sword)
        self.add_item(starter_armor)
        self.add_item(health_potion)
        self.equip_weapon(starter_sword)
        self.equip_armor(starter_armor)

    def add_item(self, item):
        if len(self.inventory) < self.max_inventory:
            self.inventory.append(item)
            return True
        return False

    def remove_item(self, item):
        if item in self.inventory:
            self.inventory.remove(item)
            return True
        return False

    def equip_weapon(self, weapon):
        if weapon.type == ItemType.WEAPON and weapon in self.inventory:
            self.equipped_weapon = weapon

    def equip_armor(self, armor):
        if armor.type == ItemType.ARMOR and armor in self.inventory:
            self.equipped_armor = armor

    def take_damage(self, damage, reduce_hunger = True):
            # Apply defense multiplier from status effects
            defense_mult = self.get_defense_multiplier()
            damage = int(damage * defense_mult)
            # Armor reduces damage
            if self.equipped_armor:
                damage = max(1, damage - self.equipped_armor.defense)
            self.hp -= damage

            # Damage causes hunger loss
            if reduce_hunger:
                hunger_loss = max(1, damage //4)
                self.hunger = max(0, self.hunger - hunger_loss)
           # self.hp -= damage
            #self.hunger = max(0, self.hunger - damage)

            # Big damage causes sanity loss
            if damage >= 20:
                sanity_loss = max(8, damage //4)
                self.sanity = max(0, self.sanity - sanity_loss)

            return self.hp <= 0

    def heal(self, amount):
        if self.sanity <= 20:
            amount = int(amount * 0.5)
        elif self.sanity <= 40:
            amount = int(amount * 0.75)

        self.hp = min(self.max_hp, self.hp + amount)

    def light_torch(self, torch):
        # Stack remaining time so a fresh torch refreshes the light source
        self.torch_time_left = max(self.torch_time_left, 0.0) + torch.duration
        self.torch_radius_bonus = max(self.torch_radius_bonus, torch.radius_bonus)

    def gain_xp(self, amount):
        self.xp += amount
        # Level up every 100 XP
        if self.xp >= self.level * 100:
            self.level += 1

            self.max_hp += 10
            #self.max_hp += 20

            self.hp = min(self.max_hp, self.hp + 10)
            return True
        return False

    def calculate_damage(self, enemy_element):
        # Critical hit chance (10%)
        #if random.random() < 0.1:
        #    return int(base_damage * multiplier * 2)
        if not self.equipped_weapon:
            base_damage = 5
        else:
            base_damage = self.equipped_weapon.damage + (self.level * 2)
        
        # Apply status effect modifiers
        damage_multiplier = self.get_damage_multiplier()
        base_damage = int(base_damage * damage_multiplier)
        
        # Element multiplier
        multiplier = self.equipped_weapon.get_damage_multiplier(enemy_element) if self.equipped_weapon else 1.0
        
        return int(base_damage * multiplier)

 

    def tile_x(self) -> int:
        return int(self.x) // TILE_SIZE

    def tile_y(self) -> int:
        return int(self.y) // TILE_SIZE

    def can_move(self, tiles, x: float, y: float) -> bool:
        walkable = [TILE_FLOOR, TILE_CAMPFIRE, TILE_TRAP, TILE_STAIR]
        half = self.SIZE // 2

        # Check all four corners of the player's bounding box
        corners = [
            (x - half, y - half),  # top-left
            (x + half, y - half),  # top-right
            (x - half, y + half),  # bottom-left
            (x + half, y + half),  # bottom-right
        ]

        for corner_x, corner_y in corners:
            # Convert pixel to tile
            tile_x = int(corner_x) // TILE_SIZE
            tile_y = int(corner_y) // TILE_SIZE

            # Out of bounds check
            if tile_x < 0 or tile_x >= MAP_COLS or tile_y < 0 or tile_y >= MAP_ROWS:
                return False

            # Check if not walkable (not floor tile)
            if tiles[tile_y][tile_x] not in walkable:
                return False

        return True

    def update(self, keys_pressed, dt: float, tiles) -> None:
        dx, dy = 0, 0
        if keys_pressed[pygame.K_w] or keys_pressed[pygame.K_UP]:
            dy = -1
        if keys_pressed[pygame.K_s] or keys_pressed[pygame.K_DOWN]:
            dy = 1
        if keys_pressed[pygame.K_a] or keys_pressed[pygame.K_LEFT]:
            dx = -1
        if keys_pressed[pygame.K_d] or keys_pressed[pygame.K_RIGHT]:
            dx = 1

        self.is_moving = dx != 0 or dy != 0
        if dx < 0:
            self.facing_left = True
        elif dx > 0:
            self.facing_left = False

        if self.is_moving:
            speed = self.SPEED * self.get_hunger_speed_multiplier()
            
            new_x = self.x + dx * speed * dt
            new_y = self.y + dy * speed * dt

            if self.can_move(tiles, new_x, self.y):
                self.x = new_x
            if self.can_move(tiles, self.x, new_y):
                self.y = new_y

        if self.escape_timer > 0:
            self.escape_timer = max(0.0, self.escape_timer - dt)

        if self.torch_time_left > 0:
            self.torch_time_left = max(0.0, self.torch_time_left - dt)
            if self.torch_time_left == 0.0:
                self.torch_radius_bonus = 0

        frame_duration = self.RUN_FRAME_DURATION if self.is_moving else self.IDLE_FRAME_DURATION
        self.anim_timer += dt
        if self.anim_timer >= frame_duration:
            self.anim_timer -= frame_duration
            self.anim_frame = (self.anim_frame + 1) % 4

    def add_status(self, effect_type, duration, value=0):
        """Add a status effect to the player"""
        # Check if already has this effect - refresh duration
        for effect in self.status_effects:
            if effect.type == effect_type:
                effect.duration = max(effect.duration, duration)
                return
        self.status_effects.append(StatusEffect(effect_type, duration, value))

    def remove_status(self, effect_type):
        """Remove a specific status effect"""
        self.status_effects = [e for e in self.status_effects if e.type != effect_type]

    def has_status(self, effect_type):
        """Check if player has a specific status effect"""
        return any(e.type == effect_type for e in self.status_effects)

    def get_damage_multiplier(self):
        """Calculate total damage multiplier from status effects"""
        multiplier = 1.0
        for effect in self.status_effects:
            multiplier *= effect.get_damage_modifier()
        return multiplier

    def get_defense_multiplier(self):
        """Calculate total defense multiplier from status effects"""
        multiplier = 1.0
        for effect in self.status_effects:
            multiplier *= effect.get_defense_modifier()
        return multiplier

    def update_status_effects(self):
        """Update all status effects (call at end of turn)"""
        expired = []
        for effect in self.status_effects[:]:
            if effect.tick():
                expired.append(effect.type)
                self.status_effects.remove(effect)
        return expired 
    def get_hunger_speed_multiplier(self):
        #Low hunger slows the player
        if self.hunger <= 0:
            return 0.45
        elif self.hunger <=10:
            return 0.55
        elif self.hunger <=25:
            return 0.75
        elif self.hunger <=50:
            return 0.9
        return 1.0

    def update_survival_hunger(self, dt):
        self.hunger_timer += dt
        #Hunger drops every 20 seconds
        if self.hunger_timer >= 20: 
            self.hunger = max(0, self.hunger - 1)
            self.hunger_timer = 0

        # Low hunger slowly damage health
        if self.hunger <= 20:
            self.starvation_timer += dt

            if self.hunger == 0:
                damage_interval = 5
                damage_amount = 2

            elif self.hunger <= 10:
                damage_interval = 10
                damage_amount = 1
            else:
                damage_interval = 20
                damage_amount = 1



            if self.starvation_timer >= damage_interval:
                self.take_damage(damage_amount, reduce_hunger = False)
                self.starvation_timer = 0
        
        else:
            self.starvation_timer = 0

    
    def restore_hunger(self, amount):
        self.hunger = min(self.max_hunger, self.hunger + amount)

    def draw(self, screen, camera_x: float, camera_y: float, assets) -> None:
        frames = assets.player_run if self.is_moving else assets.player_idle
        frame = frames[self.anim_frame]
        if self.facing_left:
            frame = pygame.transform.flip(frame, True, False)
        screen.blit(frame, (
            int(self.x - camera_x) - TILE_SIZE // 2,
            int(self.y - camera_y) - TILE_SIZE // 2,
        ))

    def update_sanity(self, dt):

        #Very low hunger slowly drops sanity
        if self.hunger <= 40:
            self.sanity_hunger_timer += dt

            if self.sanity_hunger_timer >= 10:
                self.sanity = max(0, self.sanity - 3)
                self.sanity_hunger_timer = 0

        # elif self.hunger <= 10:
        #     self.sanity_hunger_timer += dt
        #     if self.sanity_hunger_timer >= 10:
        #         self.sanity = max(0, self.sanity - 1)
        #         self.sanity_hunger_timer = 0
        # else:
            self.sanity_hunger_timer = 0
        
        #Darkness sanity loss : No Torch for 20 seconds
        if self.torch_time_left <= 0:
            self.darkness_timer += dt
            if self.darkness_timer >= 20:
                self.sanity = max(0, self.sanity - 4)
                self.darkness_timer = 0
        else:
            self.darkness_timer = 0
        

    def record_combat_stress(self):
        current_time = pygame.time.get_ticks()

        if current_time - self.last_combat_time <= 15000:
            self.combat_stress +=1
        else:
            self.combat_stress = 1
        self.last_combat_time = current_time

        if self.combat_stress == 3:
            self.sanity = max(0, self.sanity - 5)
        elif self.combat_stress >3:
            self.sanity = max(0, self.sanity - 10)
        

        
    def restore_sanity(self, amount):
            self.sanity = min(self.max_sanity, self.sanity + amount)


    