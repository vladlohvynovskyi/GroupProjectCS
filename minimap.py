import pygame

from config import (
    SCREEN_WIDTH,
    MAP_COLS, MAP_ROWS,
    MINIMAP_TILE, MINIMAP_MARGIN,
    TILE_FLOOR, TILE_WALL, TILE_DOOR, TILE_CHEST,
    TILE_TRAP, TILE_CAMPFIRE, TILE_STAIR,
    COLOR_FLOOR, COLOR_WALL, COLOR_DOOR, COLOR_CHEST,
    COLOR_TRAP, COLOR_CAMPFIRE, COLOR_STAIR, COLOR_PLAYER,
    RED,
)


def draw_minimap(game):
    mw = MAP_COLS * MINIMAP_TILE
    mh = MAP_ROWS * MINIMAP_TILE
    mx = SCREEN_WIDTH  - mw - MINIMAP_MARGIN
    my = MINIMAP_MARGIN

    # Semi-transparent background
    bg = pygame.Surface((mw, mh), pygame.SRCALPHA)
    bg.fill((0, 0, 0, 160))
    game.screen.blit(bg, (mx, my))

    # Tile colors on the minimap (Show locked doors differently?)
    color_map = {
        TILE_FLOOR:    COLOR_FLOOR,
        TILE_WALL:     COLOR_WALL,
        TILE_DOOR:     COLOR_DOOR,
        TILE_CHEST:    COLOR_CHEST,
        TILE_TRAP:     COLOR_TRAP,
        TILE_CAMPFIRE: COLOR_CAMPFIRE,
        TILE_STAIR:    COLOR_STAIR,
    }

    for y in range(MAP_ROWS):
        for x in range(MAP_COLS):
            if not game.revealed[y][x]:
                continue
            color = color_map.get(game.dungeon.tiles[y][x])
            if color is None:
                continue
            rect = pygame.Rect(mx + x * MINIMAP_TILE, my + y * MINIMAP_TILE, MINIMAP_TILE, MINIMAP_TILE)
            pygame.draw.rect(game.screen, color, rect)

    # Player dot
    px = mx + game.player.tile_x() * MINIMAP_TILE + MINIMAP_TILE // 2
    py = my + game.player.tile_y() * MINIMAP_TILE + MINIMAP_TILE // 2
    pygame.draw.rect(game.screen, COLOR_PLAYER, pygame.Rect(px - 1, py - 1, 3, 3))


    for enemy in game.dungeon.enemies:
        if enemy.hp > 0:
            # Only show enemies in revealed tiles
            if game.revealed[enemy.current_tile_y][enemy.current_tile_x]:
                ex = mx + enemy.current_tile_x * MINIMAP_TILE + MINIMAP_TILE // 2
                ey = my + enemy.current_tile_y * MINIMAP_TILE + MINIMAP_TILE // 2
                pygame.draw.rect(game.screen, RED,
                                 pygame.Rect(ex - 1, ey - 1, 3, 3))
                
    #NPC's quest dot
    if game.quest_giver is not None and (game.quest_active or game.quest_completed):
        qx = game.quest_giver.tile_x
        qy = game.quest_giver.tile_y

        # Only show if the quest giver tile is revealed
        if game.revealed[qy][qx]:
            dot_x = mx + qx * MINIMAP_TILE + MINIMAP_TILE // 2
            dot_y = my + qy * MINIMAP_TILE + MINIMAP_TILE // 2

            pygame.draw.rect(
                game.screen,
                (0, 150, 255), #Blue
                pygame.Rect(dot_x - 1, dot_y - 1, 3, 3)
            )


