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

    def distance_to_player(self, player):

        dx = self.x - player.x
        dy = self.y - player.y

        return (dx * dx + dy * dy) ** 0.5

    def interact(self, game):


        if self.role == "healer":
            game.awaiting_heal_choice = True
            game.healer_npc = self
            if game.player.hp >= game.player.max_hp:
                game.combat_log.append(f"{self.name}: Want me to heal you? Y/N")
            else:
                game.combat_log.append(f"{self.name}: You are wounded. Let me heal you? Y/N")

            return
        if self.role == "merchant":
            game.state = GameState.SHOP
            game.shop_npc = self

            if not hasattr(self, "shop_items"):
                possible_items = [
                    (HealthPotion("Health Potion", 30), 30),
                    (Food("Bread", 30), 20),
                    (SanityPotion("Sanity Potion", 30), 40),
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
            game.combat_log.append(f"{self.name}: {random.choice(self.lines)}")
            return

        if self.role == "quest":
            if not hasattr(self, "quest_goal"):
                self.quest_goal = random.choice([3, 5])
                self.quest_reward_xp = self.quest_goal * 25
                self.quest_finished = False
                self.quest_refused = False

            if self.quest_finished or self.quest_refused:
                return

            if not game.quest_active and not game.quest_completed:
                game.awaiting_quest_choice = True
                game.quest_giver = self
                game.quest_goal = self.quest_goal
                game.combat_log.append(
                    f"{self.name}: Defeat {self.quest_goal} enemies? Press Y to accept or N to refuse."
                )
                return

            if game.quest_completed and game.quest_giver == self:
                game.combat_log.append(
                    f"{self.name}: Well done. Take {self.quest_reward_xp} XP."
                )
                game.player.xp += self.quest_reward_xp
                #game.player.add_item(HealthPotion("Health Potion", 30))

                reward = random.choice([
                    HealthPotion("Health Potion", 30),
                    Torch(),
                    Armor("Leather Armor", 5, "Quest reward armor"),
                ])
                if game.player.add_item(reward):
                    game.combat_log.append(f"Quest reward: {reward.name}")
                else:
                    game.combat_log.append("Inventory full! Could not take reward.")

                game.remove_npc(self)

                self.quest_finished = True
                game.quest_active = False
                game.quest_completed = False
                game.quest_kills = 0
                game.quest_goal = 0
                game.quest_giver = None
                return

            if game.quest_active and game.quest_giver == self:
                game.combat_log.append(
                    f"{self.name}: Progress {game.quest_kills}/{game.quest_goal} enemies."
                )
                return

            game.combat_log.append(f"{self.name}: Finish your other quest first.")
            return

    def draw(self, screen, camera_x, camera_y, assets):
        sx = int(self.x - camera_x) - TILE_SIZE // 2
        sy = int(self.y - camera_y) - TILE_SIZE // 2
        if self.role == "merchant":
            screen.blit(assets.npc_merchant, (sx, sy))  # Male1

        elif self.role == "healer":

            screen.blit(assets.npc_healer, (sx, sy))  # also Male1


        elif self.role == "guide":
            screen.blit(assets.npc_guide, (sx, sy))     # Male2
        elif self.role == "quest":
            screen.blit(assets.npc_quest, (sx, sy))     # also Male2
        else:
            pygame.draw.rect(screen, (180, 80, 220),
                            pygame.Rect(sx, sy, TILE_SIZE, TILE_SIZE))