from __future__ import annotations
from __future__ import absolute_import
from typing import Dict, Tuple


from code.step3_code2task.github_stanfordkarel.stanfordkarel.karel_world import Direction
from code.step3_code2task.sym_world import SymWorld

CHAR_WIDTH = 5
HORIZONTAL, VERTICAL = "─", "│"
SPACING = 10
BEEPER_COORDS = Dict[Tuple[int, int], int]


class Tile:  # pylint: disable=too-few-public-methods
    def __init__(self, value: str = "?") -> None:
        self.value = value
        self.walls: list[Direction] = []
        self.beepers = 0
        self.color = ""

    def __repr__(self) -> str:
        result = ""
        if self.value == "K" and self.beepers > 0:
            result = "<K>"
        elif self.beepers > 0:
            result = f"<{self.beepers}>"
        else:
            result = self.value
        return result.center(CHAR_WIDTH)


class AsciiSymWorld:
    def __init__(self, world: SymWorld, beepers: dict, karel_street: int, karel_avenue: int) -> None:
        num_sts, num_aves = world.num_streets, world.num_avenues
        # Initialize Tiles
        self.world_arr = [[Tile() for _ in range(num_aves)] for _ in range(num_sts)]

        # Add Karel
        self.world_arr[num_sts - karel_street][karel_avenue - 1].value = "K"
        for (avenue, street), count in beepers.items():
            self.world_arr[num_sts - street][avenue - 1].beepers = count

        # Add the unkown cells
        for ele in world.empty_cells:
            self.world_arr[num_sts - ele[1]][ele[0] - 1].value = "."

        # Add Walls
        # for wall in world.walls:
        #     avenue, street, direction = wall.avenue, wall.street, wall.direction
        #     self.world_arr[num_sts - street][avenue - 1].walls.append(direction)

        for wall in world.walls:
            avenue, street= wall.avenue, wall.street
            self.world_arr[num_sts - street][avenue - 1].value = "#"

        self.num_streets = num_sts
        self.num_avenues = num_aves

    def __repr__(self) -> str:
        avenue_widths = HORIZONTAL * ((CHAR_WIDTH + 1) * self.num_avenues + 1)
        result = f"┌{avenue_widths}┐\n"
        for r in range(self.num_streets):
            next_line = VERTICAL
            result += VERTICAL
            next_block_start = " "
            for c in range(self.num_avenues):
                tile = self.world_arr[r][c]
                line, next_block_start = self.get_next_line(r, c, next_block_start)
                next_line += line
                # result += (
                #     VERTICAL if self.tile_pair_has_wall(r, c, Direction.WEST) else " "
                # ) + str(tile)
                result += (
                              VERTICAL if self.tile_has_wall(r, c) else " "
                          ) + str(tile)

            result += f" {VERTICAL}\n"
            if r == self.num_streets - 1:
                result += f"└{avenue_widths}┘\n"
            else:
                result += f"{next_line} {VERTICAL}\n"
        return result

    def tile_has_wall(self, r: int, c: int) -> bool:
        if 0 <= r < self.num_streets and 0 <= c < self.num_avenues:
            tile = self.world_arr[r][c]
            if tile == "#":
                return True
            # return direction in tile.walls
        return False



    def get_next_line(self, r: int, c: int, next_block_start: str) -> tuple[str, str]:
        """ Given a tile, figures out the lower line of the ASCII art. """

        if self.tile_has_wall(r, c):
            if (
                    next_block_start == HORIZONTAL
                    and self.tile_has_wall(r, c)
                    and self.tile_has_wall(r + 1, c)
            ):
                next_block_start = "#"
            elif (
                    next_block_start == " "
                    and self.tile_has_wall(r, c)
                    and self.tile_has_wall(r + 1, c)
            ):
                next_block_start = "#"
            elif self.tile_has_wall(r + 1, c):
                next_block_start = "#"
            elif self.tile_has_wall(r, c):
                next_block_start = "#"
            next_line = next_block_start + HORIZONTAL * CHAR_WIDTH
            next_block_start = HORIZONTAL
        else:
            if (
                    next_block_start == HORIZONTAL
                    and self.tile_has_wall(r, c)
                    and self.tile_has_wall(r + 1, c)
            ):
                next_block_start = "#"
            elif next_block_start == HORIZONTAL and self.tile_has_wall(
                    r + 1, c
            ):
                next_block_start = "#"
            elif next_block_start == HORIZONTAL and self.tile_has_wall(
                    r, c
            ):
                next_block_start = "#"
            elif self.tile_has_wall(
                    r, c
            ) and self.tile_has_wall(r + 1, c):
                next_block_start = VERTICAL

            next_line = next_block_start + " " * CHAR_WIDTH
            next_block_start = " "
        return next_line, next_block_start


def display_current_sym_world(sym_world: SymWorld):

    begin_world = AsciiSymWorld(sym_world, sym_world.beepers, sym_world.karel_start_location[1], sym_world.karel_start_location[0])
    print(begin_world)
    end_world = AsciiSymWorld(sym_world, sym_world.post_beepers, sym_world.street, sym_world.avenue)
    print("end_world")
    print(end_world)
