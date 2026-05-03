import sys
import random

import pygame

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TILE_SIZE,
    MAP_COLS, MAP_ROWS,
    TILE_DOOR, TILE_CHEST, TILE_STAIR, TILE_FLOOR,
)
from enums import GameState, ItemType
from items import HealthPotion, Torch, Food, SanityPotion
from assets import Assets
from player import Player
from dungeon import DungeonMap
from screens import (
    draw_exploration, draw_combat, draw_inventory,
    draw_shop,
    draw_game_over, draw_victory, 
)
from menus import (
    build_main_menu_buttons, build_pause_menu_buttons, build_back_button,
    Slider,
    draw_main_menu, draw_pause_menu, draw_options, draw_controls,
)
from npc import NPC


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Dreadful Depths")
        self.clock = pygame.time.Clock()
        self.assets = Assets()
        self.font = pygame.font.SysFont(None, 36)
        self.small_font = pygame.font.SysFont(None, 24)
        self.title_font = pygame.font.SysFont(None, 64)
        self.medium_font = pygame.font.SysFont(None, 30)

        # Menu UI (persists across runs)
        self.state = GameState.MAIN_MENU
        self.prev_state = GameState.MAIN_MENU
        self.main_menu_buttons = build_main_menu_buttons()
        self.pause_menu_buttons = build_pause_menu_buttons()
        self.options_back_button = build_back_button()
        self.controls_back_button = build_back_button()

        slider_x = SCREEN_WIDTH // 2 - 180
        slider_w = 360
        self.master_slider = Slider((slider_x, 260, slider_w, 20), value=0.8)
        self.music_slider  = Slider((slider_x, 340, slider_w, 20), value=0.6)
        self.sfx_slider    = Slider((slider_x, 420, slider_w, 20), value=0.7)

        # UI button rectangles (shared between combat/inventory/exploration)
        self.attack_button    = pygame.Rect(640, 480, 220, 52)
        self.run_button       = pygame.Rect(640, 544, 220, 52)
        self.inventory_button = pygame.Rect(640, 608, 220, 52)
        self.use_item_button  = pygame.Rect(100, 500, 150, 40)
        self.drop_item_button = pygame.Rect(300, 500, 150, 40)
        self.back_button      = pygame.Rect(600, 500, 150, 40)

        #NPCs
        #self.npcs = []
        #self.spawn_npc()

        
        self.current_enemy = None
        self.combat_message = ""
        self.combat_turn = "player"
        self.combat_log = []
        self.selected_item_index = 0

        # UI button rectangles
        self.attack_button    = pygame.Rect(640, 480, 220, 52)
        self.run_button       = pygame.Rect(640, 544, 220, 52)
        self.inventory_button = pygame.Rect(640, 608, 220, 52)
        self.use_item_button  = pygame.Rect(100, 500, 150, 40)
        self.drop_item_button = pygame.Rect(300, 500, 150, 40)
        self.back_button      = pygame.Rect(600, 500, 150, 40)

        #Shop Buttons
        self.shop_buy_button = pygame.Rect(250, 500, 160, 45)
        self.shop_back_button = pygame.Rect(500, 500, 160, 45)
        

        #Hallucination
        self.hallucination_timer =0.0
        self.hallucination = None

        #NPCs Quests
        self.quest_active = False
        self.quest_completed = False
        self.quest_kills = 0
        self.quest_goal = 0
        #Accept or Not accept the quest choice
        self.awaiting_quest_choice = False
        self.quest_giver = None

        #Healer NPC
        self.awaiting_heal_choice = False
        self.healer_npc = None

        self._start_new_run()

    def _start_new_run(self):
        """Reset world state for a fresh playthrough."""
        self.floor = 1

        self.dungeon = DungeonMap()
        self.dungeon.generate(self.floor)

        # Fog of war
        self.revealed = [[False] * MAP_COLS for _ in range(MAP_ROWS)]
        self.visited_rooms = set()

        first_room = self.dungeon.rooms[0]
        spawn_x = float(first_room[0] * TILE_SIZE + first_room[2] * TILE_SIZE / 2)
        spawn_y = float(first_room[1] * TILE_SIZE + first_room[3] * TILE_SIZE / 2)
        self.player = Player(spawn_x, spawn_y)
        self.update_fog()

        self.current_enemy = None
        self.combat_message = ""
        self.combat_turn = "player"
        self.combat_log = []
        self.selected_item_index = 0

        self.npcs = []
        self.spawn_npc()

        self.shop_buy_button = pygame.Rect(250, 500, 160, 45)
        self.shop_back_button = pygame.Rect(500, 500, 160, 45)
        self.shop_npc = None

        self.quest_active = False
        self.quest_completed = False
        self.quest_kills = 0
        self.quest_goal = 0
        self.awaiting_quest_choice = False
        self.quest_giver = None

        self.awaiting_heal_choice = False
        self.healer_npc = None

        self.hallucination_timer = 0.0
        self.hallucination = None


    def update_fog(self):
        px, py = self.player.tile_x(), self.player.tile_y()

        # Reveal the current tile and its immediate neighbors (for corridors)
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                nx, ny = px + dx, py + dy
                if 0 <= nx < MAP_COLS and 0 <= ny < MAP_ROWS:
                    self.revealed[ny][nx] = True

        # If player is inside a room, reveal the entire room (+ its walls)
        for i, (rx, ry, rw, rh) in enumerate(self.dungeon.rooms):
            if i in self.visited_rooms:
                continue
            if rx <= px < rx + rw and ry <= py < ry + rh:
                self.visited_rooms.add(i)
                for y in range(ry - 1, ry + rh + 1):
                    for x in range(rx - 1, rx + rw + 1):
                        if 0 <= x < MAP_COLS and 0 <= y < MAP_ROWS:
                            self.revealed[y][x] = True

    def _descend(self):
        self.floor += 1
        print(f"Descending to floor {self.floor}...")
        self.dungeon = DungeonMap()
        self.dungeon.generate(self.floor)

        # Reset fog of war for the new floor
        self.revealed = [[False] * MAP_COLS for _ in range(MAP_ROWS)]
        self.visited_rooms = set()

        first_room = self.dungeon.rooms[0]
        self.player.x = float(first_room[0] * TILE_SIZE + first_room[2] * TILE_SIZE / 2)
        self.player.y = float(first_room[1] * TILE_SIZE + first_room[3] * TILE_SIZE / 2)
        self.player.keys = set()
        self.update_fog()

       
        self.current_enemy = None
        self.combat_log = []

        self.npcs = []
        self.spawn_npc()

    def _handle_interact(self):
        player = self.player
        dungeon = self.dungeon

        closest_npc = None
        closest_distance = 80

        for npc in self.npcs:
            distance = npc.distance_to_player(player)
            if distance < closest_distance:
                closest_distance = distance
                closest_npc = npc

        if closest_npc is not None:
            closest_npc.interact(self)
            return

        for adj_dx, adj_dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            check_x = player.tile_x() + adj_dx
            check_y = player.tile_y() + adj_dy

            if not (0 <= check_x < MAP_COLS and 0 <= check_y < MAP_ROWS):
                continue

            tile = dungeon.tiles[check_y][check_x]

            if tile == TILE_STAIR:
                self._descend()
                break

            elif tile == TILE_DOOR:
                result = dungeon.open_door(check_x, check_y, player.keys)
                if result == "opened":
                    self.combat_log.append("Door opened!")
                elif result == "unlocked":
                    self.combat_log.append("Unlocked and opened!")
                elif result == "locked":
                    needed_key = None
                    for door in dungeon.doors:
                        if door["x"] == check_x and door["y"] == check_y:
                            needed_key = door["key_id"]
                            break

                    self.combat_log.append(f"Door is locked! Need {needed_key}.")
                break

            elif tile == TILE_CHEST:
                found = dungeon.open_chest(check_x, check_y)
                if found is None:
                    break
                print(f"Found: {found}")

                if isinstance(found, str) and found.startswith("key_"):
                    player.keys.add(found)
                    print(f"Picked up {found}. Keys: {sorted(player.keys)}")
                elif found == "smth":
                    potion = HealthPotion("Health Potion", 30)
                    if player.add_item(potion):
                        self.combat_log.append("Found Health Potion!")
                    else:
                        self.combat_log.append("Inventory full!")
                elif found == "torch":
                    torch = Torch()
                    if player.add_item(torch):
                        self.combat_log.append("Found Torch!")
                    else:
                        self.combat_log.append("Inventory full!")
                break

    def _check_traps(self):
        player = self.player
        damage = self.dungeon.trigger_trap(player.tile_x(), player.tile_y())
        if damage is None:
            return
        player.take_damage(damage)
        self.combat_log.append(f"Trap! {damage} damage!")
        print(f"Trap! {damage} damage!")
        if player.hp <= 0:
            self.state = GameState.GAME_OVER

    def _update_enemies(self, dt):
        """Move alive enemies; cull dead ones."""
        for enemy in self.dungeon.enemies:
            if enemy.hp > 0:
                enemy.update_movement(dt, self.dungeon.tiles)
        self.dungeon.enemies = [e for e in self.dungeon.enemies if e.hp > 0]
   
    def _check_combat_trigger(self):
        """Check if player is adjacent to an enemy"""
        if self.state != GameState.EXPLORATION:
            return
        if self.player.escape_timer > 0:
            return
        
        # Use the methods that calculate current tile from pixel position
        player_tile_x = self.player.tile_x()  # This calls the method
        player_tile_y = self.player.tile_y()  # This calls the method
        
        for enemy in self.dungeon.enemies[:]:
            if enemy.hp <= 0:
                continue
                
            # Check if enemy is adjacent to player
            if (abs(enemy.current_tile_x - player_tile_x) <= 1 and 
                abs(enemy.current_tile_y - player_tile_y) <= 1):
                self.state = GameState.COMBAT
                self.current_enemy = enemy
                self.combat_turn = "player"
                self.combat_message = f"Encountered {enemy.name}!"
                self.combat_log.append(f"Encountered {enemy.name}!")
                self.player.record_combat_stress()
                break

    def _open_pause(self):
        self.prev_state = self.state
        self.state = GameState.PAUSED

    def _return_from_submenu(self):
        """Called when 'Back' is pressed from Options/Controls."""
        if self.prev_state == GameState.PAUSED:
            self.state = GameState.PAUSED
        else:
            self.state = GameState.MAIN_MENU

    def handle_main_menu(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for button in self.main_menu_buttons:
                    if not button.clicked(event.pos):
                        continue
                    if button.action == "start":
                        self._start_new_run()
                        self.state = GameState.EXPLORATION
                    elif button.action == "options":
                        self.prev_state = GameState.MAIN_MENU
                        self.state = GameState.OPTIONS
                    elif button.action == "controls":
                        self.prev_state = GameState.MAIN_MENU
                        self.state = GameState.CONTROLS
                    elif button.action == "quit":
                        pygame.event.post(pygame.event.Event(pygame.QUIT))
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._start_new_run()
                    self.state = GameState.EXPLORATION

    def handle_pause(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for button in self.pause_menu_buttons:
                    if not button.clicked(event.pos):
                        continue
                    if button.action == "resume":
                        self.state = GameState.EXPLORATION
                    elif button.action == "options":
                        self.prev_state = GameState.PAUSED
                        self.state = GameState.OPTIONS
                    elif button.action == "controls":
                        self.prev_state = GameState.PAUSED
                        self.state = GameState.CONTROLS
                    elif button.action == "main_menu":
                        self.state = GameState.MAIN_MENU
                    elif button.action == "quit":
                        pygame.event.post(pygame.event.Event(pygame.QUIT))
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.state = GameState.EXPLORATION

    def handle_options(self, events):
        for event in events:
            self.master_slider.handle_event(event)
            self.music_slider.handle_event(event)
            self.sfx_slider.handle_event(event)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.options_back_button.clicked(event.pos):
                    self._return_from_submenu()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._return_from_submenu()

    def handle_controls(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.controls_back_button.clicked(event.pos):
                    self._return_from_submenu()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._return_from_submenu()

    def handle_exploration(self, events):
        """Handle input during exploration state."""
        self._check_combat_trigger()
        self._check_traps()
        for event in events:
            if event.type == pygame.KEYDOWN:

                if self.awaiting_heal_choice:
                    if event.key == pygame.K_y:
                        if self.healer_npc:
                            if self.player.hp >= self.player.max_hp:
                                self.combat_log.append("Healer: Sorry, I can't heal you now.")
                            else:
                                self.player.heal(50)
                                self.combat_log.append("Healer restored 50 HP.")
                                self.remove_npc(self.healer_npc)

                        self.awaiting_heal_choice = False
                        self.healer_npc = None
                        return

                    elif event.key == pygame.K_n:
                        self.combat_log.append("Healing refused.")
                        self.awaiting_heal_choice = False
                        self.healer_npc = None
                        return

                if self.awaiting_quest_choice:
                    if event.key == pygame.K_y:
                        self.quest_active = True
                        self.quest_completed = False
                        self.quest_kills = 0
                        self.combat_log.append("Quest accepted!")
                        self.awaiting_quest_choice = False
                        return

                    elif event.key == pygame.K_n:
                        self.combat_log.append("Quest refused.")

                        #if self.quest_giver:
                            #self.quest_giver.quest_refused = True
                        self.awaiting_quest_choice = False
                        self.quest_giver = None
                        return
                    
                if event.key == pygame.K_e:
                    self._handle_interact()
                elif event.key == pygame.K_i:
                    self.state = GameState.INVENTORY
                    self.combat_log.append("Opened inventory")
                elif event.key == pygame.K_ESCAPE:
                    self._open_pause()
                    return
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.inventory_button.collidepoint(event.pos):
                    self.state = GameState.INVENTORY
                    self.combat_log.append("Opened inventory")

    def handle_combat(self, events):
        """Handle events in combat mode"""
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                # Attack button
                if self.attack_button.collidepoint(mouse_pos) and self.combat_turn == "player":
                    # Player attacks
                    damage = self.player.calculate_damage(self.current_enemy.element)
                    
                    # Check for critical hit (10% chance)
                    is_critical = random.random() < 0.1
                    if is_critical:
                        damage = int(damage * 2)
                    
                    # Apply damage
                    enemy_defeated = self.current_enemy.take_damage(damage)
                    
                    # Add to combat log
                    crit_text = "CRITICAL! " if is_critical else ""
                    if self.player.equipped_weapon:
                        element_text = f"({self.player.equipped_weapon.element.name} vs {self.current_enemy.element.name})"
                    else:
                        element_text = f"(Bare hands vs {self.current_enemy.element.name})"
                    self.combat_log.append(f"{crit_text}You dealt {damage} damage {element_text}")
                    
                    if enemy_defeated:
                        # Victory
                        xp_gained = self.current_enemy.xp_reward
                        leveled_up = self.player.gain_xp(xp_gained)
                        self.combat_log.append(f"Victory! Gained {xp_gained} XP")
                        if leveled_up:
                            self.combat_log.append(f"Level Up! Now level {self.player.level}!")
                        
                        # Quest completed
                        if self.quest_active and not self.quest_completed:
                            self.quest_kills += 1
                            if self.quest_kills >= self.quest_goal:
                                self.quest_completed = True
                                self.combat_log.append("Quest completed!")

                        # Remove enemy from dungeon
                        if self.current_enemy in self.dungeon.enemies:
                            self.dungeon.enemies.remove(self.current_enemy)
                        
                        # Check if all enemies are defeated
                        if not self.dungeon.enemies:
                            self.state = GameState.VICTORY
                        else:
                            self.state = GameState.EXPLORATION
                        self.current_enemy = None
                    else:
                        # Enemy turn
                        self.combat_turn = "enemy"
                        self.combat_message = "Enemy's turn..."
                
                # Run button
                elif self.run_button.collidepoint(mouse_pos) and self.combat_turn == "player":
                    # Attempt to run (50% chance)
                    if random.random() < 0.5:
                        self.player.escape_timer = 3.0
                        self.state = GameState.EXPLORATION
                        self.combat_log.append("You escaped! (invincible for 3s)")
                        self.current_enemy = None
                    else:
                        self.combat_log.append("Couldn't escape!")
                        self.combat_turn = "enemy"
                
                # Inventory button
                elif self.inventory_button.collidepoint(mouse_pos):
                    self.state = GameState.INVENTORY
                    self.combat_log.append("Opened inventory")
        
        # Enemy turn (delayed)
        if self.combat_turn == "enemy" and self.current_enemy:
            damage = self.current_enemy.damage
            player_dead = self.player.take_damage(damage)
            self.combat_log.append(f"{self.current_enemy.name} dealt {damage} damage!")

            if player_dead:
                self.state = GameState.GAME_OVER
                self.combat_message = "You died!"
            else:
                self.combat_turn = "player"
                self.combat_message = "Your turn!"

    def handle_inventory(self, events):
        """Handle events in inventory mode"""
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                # Item selection (click on items)
                for i, item in enumerate(self.player.inventory):
                    item_rect = pygame.Rect(80, 90 + i * 60, 640, 50)
                    if item_rect.collidepoint(mouse_pos):
                        self.selected_item_index = i
                        self.combat_log.append(f"Selected {item.name}")
                
                # Use/Equip button
                if self.use_item_button.collidepoint(mouse_pos):
                    if self.selected_item_index < len(self.player.inventory):
                        item = self.player.inventory[self.selected_item_index]
                        
                        if item.type == ItemType.HEALTH:
                            # Use health potion
                            self.player.heal(item.value)
                            self.player.inventory.pop(self.selected_item_index)
                            self.combat_log.append(f"Used {item.name}, healed {item.value} HP")

                            # Adjust selection if needed
                            if self.selected_item_index >= len(self.player.inventory):
                                self.selected_item_index = max(0, len(self.player.inventory) - 1)

                        elif item.type == ItemType.TORCH:
                            self.player.light_torch(item)
                            self.player.inventory.pop(self.selected_item_index)
                            self.combat_log.append(f"Lit {item.name} ({int(item.duration)}s)")
                            if self.selected_item_index >= len(self.player.inventory):
                                self.selected_item_index = max(0, len(self.player.inventory) - 1)

                        elif item.type == ItemType.WEAPON:
                            # Equip weapon
                            self.player.equip_weapon(item)
                            self.combat_log.append(f"Equipped {item.name}")
                        
                        elif item.type == ItemType.ARMOR:
                            # Equip armor
                            self.player.equip_armor(item)
                            self.combat_log.append(f"Equipped {item.name}")
                
                # Drop button
                elif self.drop_item_button.collidepoint(mouse_pos):
                    if self.selected_item_index < len(self.player.inventory):
                        dropped_item = self.player.inventory.pop(self.selected_item_index)
                        if dropped_item == self.player.equipped_weapon:         
                            self.player.equipped_weapon = None                  
                            self.combat_log.append(f"Unequipped {dropped_item.name}")  
                        elif dropped_item == self.player.equipped_armor:        
                            self.player.equipped_armor = None                   
                            self.combat_log.append(f"Unequipped {dropped_item.name}")  
                        self.combat_log.append(f"Dropped {dropped_item.name}")
                        
                        # Adjust selection if needed
                        if self.selected_item_index >= len(self.player.inventory):
                            self.selected_item_index = max(0, len(self.player.inventory) - 1)
                
                # Back button
                elif self.back_button.collidepoint(mouse_pos):
                    # Return to previous state
                    if self.current_enemy:
                        self.state = GameState.COMBAT
                    else:
                        self.state = GameState.EXPLORATION
                    self.combat_log.append("Closed inventory")
            
            # Keyboard navigation
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_item_index = max(0, self.selected_item_index - 1)
                elif event.key == pygame.K_DOWN:
                    self.selected_item_index = min(len(self.player.inventory) - 1, self.selected_item_index + 1)
                elif event.key == pygame.K_RETURN:
                    # Use selected item
                    if self.selected_item_index < len(self.player.inventory):
                        item = self.player.inventory[self.selected_item_index]
                        if item.type == ItemType.HEALTH:
                            self.player.heal(item.value)
                            self.player.inventory.pop(self.selected_item_index)
                            self.combat_log.append(f"Used {item.name}, healed {item.value} HP")
                            if self.selected_item_index >= len(self.player.inventory):
                                self.selected_item_index = max(0, len(self.player.inventory) - 1)
                        elif item.type == ItemType.TORCH:
                            self.player.light_torch(item)
                            self.player.inventory.pop(self.selected_item_index)
                            self.combat_log.append(f"Lit {item.name} ({int(item.duration)}s)")
                            if self.selected_item_index >= len(self.player.inventory):
                                self.selected_item_index = max(0, len(self.player.inventory) - 1)
                elif event.key == pygame.K_ESCAPE:
                    # Back to previous state
                    if self.current_enemy:
                        self.state = GameState.COMBAT
                    else:
                        self.state = GameState.EXPLORATION
                    self.combat_log.append("Closed inventory")
  

    def run(self):
        """Main game loop"""
        running = True
        
        while running:
            # Calculate delta time
            dt = self.clock.tick(FPS) / 1000.0
            
            # Get events
            events = pygame.event.get()
            
            # Handle quit events
            for event in events:
                if event.type == pygame.QUIT:
                    running = False

                # Global key handlers (per-state handlers own Esc; don't consume it here)
                if event.type == pygame.KEYDOWN:
                    # Restart on game over or victory
                    if self.state in [GameState.GAME_OVER, GameState.VICTORY]:
                        if event.key == pygame.K_SPACE:
                            self._start_new_run()
                            self.state = GameState.EXPLORATION
                        elif event.key == pygame.K_ESCAPE:
                            self.state = GameState.MAIN_MENU

            # Handle states
            if self.state == GameState.MAIN_MENU:
                self.handle_main_menu(events)
                draw_main_menu(self)

            elif self.state == GameState.PAUSED:
                # Keep the last exploration frame as backdrop, then overlay the pause menu.
                draw_exploration(self)
                self.handle_pause(events)
                draw_pause_menu(self)

            elif self.state == GameState.OPTIONS:
                # Draw whichever screen we came from as backdrop.
                if self.prev_state == GameState.PAUSED:
                    draw_exploration(self)
                else:
                    draw_main_menu(self)
                self.handle_options(events)
                draw_options(self)

            elif self.state == GameState.CONTROLS:
                if self.prev_state == GameState.PAUSED:
                    draw_exploration(self)
                else:
                    draw_main_menu(self)
                self.handle_controls(events)
                draw_controls(self)

            elif self.state == GameState.EXPLORATION:
                # Update player movement
                self.player.update(pygame.key.get_pressed(), dt, self.dungeon.tiles)

                # Update fog of war
                
                self.player.update_survival_hunger(dt)
                self.player.update_sanity(dt)
                
                # Update fog of war (kept from main.py)
                self.update_fog()

                # Update enemies
                self._update_enemies(dt)

                # Update animated tiles
                self.dungeon.update(dt)

                # Handle exploration events
                self.handle_exploration(events)

                # Draw exploration
                draw_exploration(self)

            elif self.state == GameState.COMBAT:
                # Handle combat events
                self.handle_combat(events)

                # Draw combat
                draw_combat(self)

            elif self.state == GameState.INVENTORY:
                # Handle inventory events
                self.handle_inventory(events)

                # Draw inventory
                draw_inventory(self)

            elif self.state == GameState.SHOP:
                self.handle_shop(events)
                draw_shop(self)

            elif self.state == GameState.GAME_OVER:
                # Draw game over screen
                draw_game_over(self)

            elif self.state == GameState.VICTORY:
                # Draw victory screen
                draw_victory(self)
            
            # Update display
            pygame.display.flip()
        
        # Quit game
        pygame.quit()
        sys.exit()

    def handle_shop(self, events):
        for event in events:

            if event.type == pygame.KEYDOWN:

                if event.key in [pygame.K_UP, pygame.K_w]:
                    self.selected_shop_index = max(0, self.selected_shop_index - 1)

                elif event.key in [pygame.K_DOWN, pygame.K_s]:
                    self.selected_shop_index = min(len(self.shop_items) - 1, self.selected_shop_index + 1)


                elif event.key == pygame.K_RETURN:

                    self.buy_shop_item()
                elif event.key == pygame.K_ESCAPE:
                    self.state = GameState.EXPLORATION
                    self.combat_log.append("Left shop")
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                # Select item
                for i, item in enumerate(self.shop_items):
                    item_rect = pygame.Rect(150, 120 + i * 70, 600, 55)
                    if item_rect.collidepoint(mouse_pos):
                        self.selected_shop_index = i

                # BUY BUTTON
                if self.shop_buy_button.collidepoint(mouse_pos):
                    self.buy_shop_item()

                # BACK BUTTON
                elif self.shop_back_button.collidepoint(mouse_pos):
                    self.state = GameState.EXPLORATION
                    self.combat_log.append("Left shop")


    def buy_shop_item(self):
        if not self.shop_items:
            self.combat_log.append("Shop is empty.")
            return
        item = self.shop_items[self.selected_shop_index]
        cost = self.shop_prices[self.selected_shop_index]
        if self.player.xp < cost:

            self.combat_log.append(f"Not enough XP! Need {cost} XP.")
            return

        if not self.player.add_item(item):
            self.combat_log.append("Inventory full! Cannot buy item.")
            return
        self.player.xp -= cost
        self.combat_log.append(f"Bought {item.name} for {cost} XP.")

        # Remove bought item from this merchant forever
        self.shop_items.pop(self.selected_shop_index)
        self.shop_prices.pop(self.selected_shop_index)
        if self.selected_shop_index >= len(self.shop_items):
            self.selected_shop_index = max(0, len(self.shop_items) - 1)
            if not self.shop_items and self.shop_npc:
                self.combat_log.append("Merchant has nothing left and leaves.")
                self.remove_npc(self.shop_npc)
                self.shop_npc = None
                self.state = GameState.EXPLORATION
    
    
    def update_hallucination(self, dt):
        if self.player.sanity > 20:
            self.hallucination = None
            self.hallucination_timer = 0.0
            return

        self.hallucination_timer += dt

        if self.hallucination is None and self.hallucination_timer >= 5:
            offset_x = random.choice([-3, -2, 2, 3]) * TILE_SIZE
            offset_y = random.choice([-3, -2, 2, 3]) * TILE_SIZE

            self.hallucination = {
                "x": self.player.x + offset_x,
                "y": self.player.y + offset_y,
                "time": 2.5
            }

            self.hallucination_timer = 0.0

        if self.hallucination is not None:
            self.hallucination["time"] -= dt
            if self.hallucination["time"] <= 0:
                self.hallucination = None


    def spawn_npc(self):
        self.npcs = []

        npc_templates = [
            ("Healer", ["I can heal you."], "healer"),
            ("Merchant", ["Take a look."], "merchant"),
            ("Quest giver", ["Defeat enemies for me."], "quest"),
            ("Guide", ["Stay close to the light.", "Doors may hide danger."], "guide"),
        ]

        npc_count = random.randint(2, 5) #NPC AMOUNT
        #npc_count = min(5, 2 + self.floor // 2) #Another option

        possible_rooms = self.dungeon.rooms[1:]

        safe_rooms = []
        for room in possible_rooms:
            rx, ry, rw, rh = room
            has_enemy = False

            for enemy in self.dungeon.enemies:
                if rx <= enemy.current_tile_x < rx + rw and ry <= enemy.current_tile_y < ry + rh:
                    has_enemy = True
                    break

            if not has_enemy:
                safe_rooms.append(room)

        random.shuffle(safe_rooms)
        rooms_to_use = safe_rooms[:npc_count]

        for room in rooms_to_use:
            role_choice = random.choice(npc_templates)

            placed = False
            attempts = 80

            while not placed and attempts > 0:
                attempts -= 1

                rx, ry, rw, rh = room
                tile_x = random.randint(rx, rx + rw - 1)
                tile_y = random.randint(ry, ry + rh - 1)

                if self.dungeon.tiles[tile_y][tile_x] != TILE_FLOOR:
                    continue

                bad_nearby = False
                for dy in range(-1, 2):
                    for dx in range(-1, 2):
                        nx = tile_x + dx
                        ny = tile_y + dy
                        if 0 <= nx < MAP_COLS and 0 <= ny < MAP_ROWS:
                            if self.dungeon.tiles[ny][nx] in [
                                TILE_DOOR,
                                TILE_CHEST,
                                TILE_STAIR,
                            ]:
                                bad_nearby = True

                if bad_nearby:
                    continue

                name, lines, role = role_choice
                self.npcs.append(NPC(tile_x, tile_y, name, lines, role))
                placed = True

    #TEST THE NPCS
    # def spawn_npc(self):
    #     self.npcs = []

    #     px = self.player.tile_x()
    #     py = self.player.tile_y()

    #     npc_data = [
    #         ("ealer", ["I can eal you."], "ealer", px + 2, py),
    #         ("Mercant", ["Take a look."], "mercant", px - 2, py),
    #         ("Quest giver", ["Defeat enemies for me."], "quest", px, py + 2),
    #         ("Guide", ["Stay close to te light.", "Doors may hide danger."], "guide", px, py - 2),
    #     ]

    #     for name, lines, role, x, y in npc_data:
    #         if 0 <= x < MAP_COLS and 0 <= y < MAP_ROWS:
    #             if self.dungeon.tiles[y][x] == TILE_FLOOR:
    #                 self.npcs.append(NPC(x, y, name, lines, role))

    def remove_npc(self, npc):
        if npc in self.npcs:
            self.npcs.remove(npc)