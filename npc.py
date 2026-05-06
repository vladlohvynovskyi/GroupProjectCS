import pygame
import random


from config import TILE_SIZE
from items import HealthPotion, Food, SanityPotion, Torch, Armor
from enums import GameState
class NPC:
    def __init__(self, tile_x, tile_y, name, lines, role="guide"):
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.x = tile_x * TILE_SIZE + TILE_SIZE // 2
        self.y = tile_y * TILE_SIZE + TILE_SIZE // 2
        self.name = name
        self.lines = lines
        self.role = role
        self.dialogue_index = 0
        self.has_interacted = False

        #NPC animation healer
        self.anim_frame = 0
        self.anim_timer = 0.0
        self.is_moving = False
        self.facing_left = False
        self.current_tile_x = tile_x
        self.current_tile_y = tile_y
        self.target_tile_x = tile_x
        self.target_tile_y = tile_y
        self.spawn_tile_x = tile_x
        self.spawn_tile_y = tile_y

        self.move_timer = 0.0
        self.move_delay = random.uniform(1.0, 2.5)
        self.move_progress = 1.0
        self.move_range = 4

    def distance_to_player(self, player):

        dx = self.x - player.x
        dy = self.y - player.y

        return (dx * dx + dy * dy) ** 0.5

    def interact(self, game):


        if self.role == "healer":
            game.dialogue_npc = self

            if game.player.hp >= game.player.max_hp:
                game.dialogue_text = "You look healthy already. Do you still seek my help?"
            else:
                game.dialogue_text = "You are wounded. Do you want me to heal you?"

            game.dialogue_buttons = [
                {"text": "Yes", "action": "heal_yes", "rect": pygame.Rect(0, 0, 160, 50)},
                {"text": "No", "action": "heal_no", "rect": pygame.Rect(0, 0, 160, 50)},
            ]

            self.is_moving = False
            return
        if self.role == "merchant":
            game.state = GameState.SHOP
            game.shop_npc = self

            if not hasattr(self, "shop_items"):
                possible_items = [
                    (HealthPotion("Health Potion", 30), 30),
                    (Food("Bread", random.randint(20, 40)), 20),
                    (SanityPotion("Sanity Potion", random.randint(25, 40)), 40),
                    (Torch(), 25),
                    (Armor("Leather Armor", 5, "Better protection"), 50),
                ]

                self.shop_items = []
                self.shop_prices = []

                stock_count = random.randint(1, 4)

                for _ in range(stock_count):
                    item, price = random.choice(possible_items)
                    self.shop_items.append(item)
                    self.shop_prices.append(price)

            game.shop_items = self.shop_items
            game.shop_prices = self.shop_prices
            game.selected_shop_index = 0
            game.combat_log.append(f"{self.name}: Take a look.")
            return

        if self.role == "guide":
            game.dialogue_npc = self
            game.dialogue_text = random.choice(self.lines)
            game.dialogue_buttons = [
                {"text": "Finish Dialogue", "action": "finish", "rect": pygame.Rect(0, 0, 240, 50)}
            ]
            self.is_moving = False
            return
        if self.role == "quest":
            if not hasattr(self, "quest_goal"):
                self.quest_type = random.choice(["kill", "collect"])
                self.quest_goal = random.choice([3, 5])
                self.quest_reward_xp = self.quest_goal * 25
                self.quest_finished = False

            game.dialogue_npc = self
            self.is_moving = False

            if game.quest_active and game.quest_giver != self:
                game.dialogue_text = "Looks like you are already doing another quest. Come back later."
                game.dialogue_buttons = [
                    {"text": "Finish Dialogue", "action": "finish", "rect": pygame.Rect(0, 0, 240, 50)}
                ]
                return

            if game.quest_completed and game.quest_giver == self:
                reward = random.choice([
                    HealthPotion("Health Potion", 30),
                    Food("Bread", random.randint(20, 40)),
                    SanityPotion("Sanity Potion", random.randint(25, 40)),
                    Torch(),
                    Armor("Leather Armor", 5, "Quest reward armor"),
                ])

                game.player.xp += self.quest_reward_xp

                if game.player.add_item(reward):
                    game.dialogue_text = f"Well done. Here is your reward: {reward.name}, and {self.quest_reward_xp} XP."
                else:
                    game.dialogue_text = f"Well done. You gained {self.quest_reward_xp} XP, but your inventory is full."

                self.quest_finished = True
                game.quest_active = False
                game.quest_completed = False
                game.quest_kills = 0
                game.quest_goal = 0
                game.quest_type = None
                game.quest_giver = None
                game.player.crystal_bag = 0
                game.player.crystal_bag_max = 0

                game.remove_npc(self)

                game.dialogue_buttons = [
                    {"text": "Finish Dialogue", "action": "finish", "rect": pygame.Rect(0, 0, 240, 50)}
                ]
                return

            if game.quest_active and game.quest_giver == self:
                if game.quest_type == "kill":
                    game.dialogue_text = f"Your quest is not finished yet. Progress: {game.quest_kills}/{game.quest_goal} enemies."
                else:
                    game.dialogue_text = f"Your quest is not finished yet. Progress: {game.player.crystal_bag}/{game.player.crystal_bag_max} crystals."

                game.dialogue_buttons = [
                    {"text": "Finish Dialogue", "action": "finish", "rect": pygame.Rect(0, 0, 240, 50)}
                ]
                return

            if self.quest_type == "kill":
                game.dialogue_text = f"Will you defeat {self.quest_goal} enemies for me?"
            else:
                game.dialogue_text = f"Will you collect {self.quest_goal} magic crystals for me?"

            game.dialogue_buttons = [
                {"text": "Yes", "action": "quest_yes", "rect": pygame.Rect(0, 0, 160, 50)},
                {"text": "No", "action": "quest_no", "rect": pygame.Rect(0, 0, 160, 50)},
            ]
            return

    def draw(self, screen, camera_x, camera_y, assets):
        sx = int(self.x - camera_x) - TILE_SIZE // 2
        sy = int(self.y - camera_y) - TILE_SIZE // 2

        if self.role == "merchant":
            frames = assets.npc_merchant_run if self.is_moving else assets.npc_merchant_idle
            frame = frames[self.anim_frame]

            if self.facing_left:
                frame = pygame.transform.flip(frame, True, False)

            screen.blit(frame, (sx, sy))

        elif self.role == "healer":
            frames = assets.npc_healer_run if self.is_moving else assets.npc_healer_idle
            frame = frames[self.anim_frame]

            if self.facing_left:
                frame = pygame.transform.flip(frame, True, False)

            screen.blit(frame, (sx, sy))

        elif self.role == "guide":
            frames = assets.npc_guide_run if self.is_moving else assets.npc_guide_idle
            frame = frames[self.anim_frame]

            if self.facing_left:
                frame = pygame.transform.flip(frame, True, False)

            screen.blit(frame, (sx, sy))   
        elif self.role == "quest":
            frames = assets.npc_quest_run if self.is_moving else assets.npc_quest_idle
            frame = frames[self.anim_frame]

            if self.facing_left:
                frame = pygame.transform.flip(frame, True, False)

            screen.blit(frame, (sx, sy))   
        else:
            pygame.draw.rect(screen, (180, 80, 220),
                            pygame.Rect(sx, sy, TILE_SIZE, TILE_SIZE))
            
    def can_stand_on_tile(self, dungeon, x, y):
        #NPC can only stand on the flor
        if dungeon.tiles[y][x] != 1:
            return False
        #NPC  cannot stand too close to the doors, chest and stairs
        blocked_nearby_tiles = [3, 4, 7]

        for dy in range(-2, 3):
            for dx in range(-2, 3):
                nx = x + dx
                ny = y + dy

                if 0 <= ny < len(dungeon.tiles) and 0 <= nx < len(dungeon.tiles[0]):
                    if dungeon.tiles[ny][nx] in blocked_nearby_tiles:
                        return False
        return True
            
    def update(self, dt, dungeon):
        self.anim_timer += dt
        frame_duration = 0.09 if self.is_moving else 0.15

        if self.anim_timer >= frame_duration:
            self.anim_timer = 0
            self.anim_frame = (self.anim_frame + 1) % 4
        if self.is_moving:
            self.move_progress += dt * 2.0

            if self.move_progress >= 1.0:
                self.move_progress = 1.0
                self.is_moving = False
                self.current_tile_x = self.target_tile_x
                self.current_tile_y = self.target_tile_y
                self.x = self.current_tile_x * TILE_SIZE + TILE_SIZE // 2
                self.y = self.current_tile_y * TILE_SIZE + TILE_SIZE // 2
            else:
                start_x = self.current_tile_x * TILE_SIZE + TILE_SIZE // 2
                start_y = self.current_tile_y * TILE_SIZE + TILE_SIZE // 2
                end_x = self.target_tile_x * TILE_SIZE + TILE_SIZE // 2
                end_y = self.target_tile_y * TILE_SIZE + TILE_SIZE // 2

                self.x = start_x + (end_x - start_x) * self.move_progress
                self.y = start_y + (end_y - start_y) * self.move_progress
            return

        self.move_timer += dt
        if self.move_timer < self.move_delay:
            return

        self.move_timer = 0
        self.move_delay = random.uniform(1.0, 2.5)
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        random.shuffle(directions)

        for dx, dy in directions:
            nx = self.current_tile_x + dx
            ny = self.current_tile_y + dy
            if abs(nx - self.spawn_tile_x) > self.move_range:
                continue
            if abs(ny - self.spawn_tile_y) > self.move_range:
                continue
            if not dungeon._is_in_room(nx, ny):
                continue

            # if dungeon.tiles[ny][nx] != 1:
            #     continue
            if not self.can_stand_on_tile(dungeon, nx, ny):
                continue

            self.target_tile_x = nx
            self.target_tile_y = ny
            self.is_moving = True
            self.move_progress = 0.0
            if dx < 0:
                self.facing_left = True
            elif dx > 0:
                self.facing_left = False
            break