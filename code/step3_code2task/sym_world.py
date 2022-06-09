from __future__ import absolute_import
import os
import collections
import random
import copy
import re
import numpy as np
from typing import Any as Any


from code.step3_code2task.github_stanfordkarel.stanfordkarel.karel_world import Wall as Wall
from code.step3_code2task.github_stanfordkarel.stanfordkarel.karel_world import KarelWorld
from code.step3_code2task.github_stanfordkarel.stanfordkarel.karel_ascii import AsciiKarelWorld
from code.step3_code2task.github_stanfordkarel.stanfordkarel.karel_world import Direction as Direction
from code.step3_code2task.github_stanfordkarel.stanfordkarel.karel_world import INFINITY as INFINITY
from code.step3_code2task.github_stanfordkarel.stanfordkarel.karel_program import DIRECTION_DELTA_MAP, NEXT_DIRECTION_MAP, NEXT_DIRECTION_MAP_RIGHT, KarelException



VALID_WORLD_KEYWORDS = [
    "dimension",
    "wall",
    "beeper",
    "empty",
]

KEYWORD_DELIM = ":"
PARAM_DELIM = ";"
direction_dict = {
    Direction.NORTH: "north",
    Direction.EAST: "east",
    Direction.WEST: "west",
    Direction.SOUTH: "south",
    Direction.UNK: "unknown"
}

MAX_LEN_EXECUTION_TRACE = 10000

class SymWorld:
    def __init__(self, args, prob_front_is_clear=0.5, prob_left_is_clear=0.5, prob_right_is_clear=0.5, prob_beepers_present=0.5,init_config_flag=False, init_config_file='', max_len_execution_trace=MAX_LEN_EXECUTION_TRACE):
        # Dimensions of the world
        self.type = args['type']
        self.num_streets = args['num_streets'] #y
        self.num_avenues = args['num_avenues'] #x
        self.max_len_execution_trace = max_len_execution_trace

        self.beepers: dict[tuple[int, int], int] = collections.defaultdict(int)
        self.post_beepers: dict[tuple[int, int], int] = collections.defaultdict(int)
        self.walls: set[Wall] = set() # Wall has attributes: avenue, street, direction
        self.empty_cells: set[tuple[int, int]] = set()
        self.unknown_cells: set[tuple[int, int]] = set()
        self.locked_cells: set[tuple[int, int]] = set()
        # AFTER DEBUG: ADDED to track all the cells on which beeper decisions have been made (to keep empty or add a beeper)
        self.all_beeper_decision_cells: set[tuple[int, int]] = set()

        for i in range(1,self.num_avenues+1):
            for j in range(1,self.num_streets+1):
                self.unknown_cells.add((i,j))

        self.prob_front_is_clear = 0.5
        self.prob_left_is_clear = 0.5
        self.prob_right_is_clear = 0.5
        self.prob_beepers_present = 0.5
        self.conditionals_hit = {'front_is_clear':0, 'left_is_clear':0, 'right_is_clear':0, 'beepers_present':0,
                                 'front_is_blocked': 0, 'left_is_blocked':0, 'right_is_blocked':0, 'no_beepers_present':0}

        # Initial Karel state saved to enable world reset
        self.karel_start_location = (1, 1)
        self.karel_start_direction = Direction.EAST
        self.karel_start_beeper_count = INFINITY
        self.empty_cells.add(self.karel_start_location)
        self.locked_cells.add(self.karel_start_location)
        self.init_config_file_flag = init_config_flag

        self.random_init = args['random_init']
        self.specify_cond = args['cond_flag']
        self.init_loc_flag = args['init_loc_flag']
        if self.random_init:
            self.set_init_world(prob_front_is_clear, prob_left_is_clear, prob_right_is_clear, prob_beepers_present, cond_flag = self.specify_cond, init_loc= self.init_loc_flag)

        if self.init_config_file_flag:
            self.init_config_file = init_config_file
            self.load_from_file()

        self.avenue = self.karel_start_location[0]
        self.street = self.karel_start_location[1]
        self.direction = self.karel_start_direction
        self.num_beepers = self.karel_start_beeper_count
        self.karel_seq = []
        self.karel_locations = [(self.karel_start_location[0], self.karel_start_location[1], self.direction, self.beepers[(self.avenue, self.street)])]
        self.karel_locations_without_direction = [(self.karel_start_location[0], self.karel_start_location[1], self.beepers[(self.avenue, self.street)])]
        self.concrete_seq  = []

        self.ref_task = args['ref_task'] # dict
        self.ref_task_file = args['ref_task_file']
        self.file_name = self.ref_task_file.split('/')
        self.file_name = self.file_name[-1].split('.')[0]




    def set_init_world(self, front_cond, left_cond, right_cond, beepers_present, cond_flag = False, init_loc=True):

        init_loc_fixed = [(2,2), (2, self.num_avenues-1), (self.num_streets-1, 2), (self.num_streets-1, self.num_streets-1),
                          (int((self.num_streets+2)/2),int((self.num_avenues+2)/2) )] # changed the middle coordinate to (6,6)


        rand_loc_fixed = random.randint(0,4)
        if init_loc:
            self.karel_start_location = init_loc_fixed[rand_loc_fixed]
        else:
            rand_x = random.randint(1,self.num_streets)
            rand_y = random.randint(1, self.num_avenues)
            self.karel_start_location = (rand_x, rand_y)


        dir = {0:Direction.EAST, 1:Direction.NORTH, 2:Direction.WEST, 3:Direction.SOUTH}
        rand_dir = random.randint(0,3)
        self.karel_start_direction = dir[rand_dir]
        self.empty_cells = set()
        self.locked_cells = set()
        # AFTER DEBUG: ADDED
        self.all_beeper_decision_cells = set()
        self.empty_cells.add(self.karel_start_location)
        self.locked_cells.add(self.karel_start_location)

        self.remove_cell(self.karel_start_location[0], self.karel_start_location[1])

        self.avenue = self.karel_start_location[0]
        self.street = self.karel_start_location[1]
        self.direction = self.karel_start_direction
        self.num_beepers = self.karel_start_beeper_count
        self.karel_seq = []
        self.karel_locations = [(self.karel_start_location[0], self.karel_start_location[1], self.direction, self.beepers[(self.avenue, self.street)])]
        self.karel_locations_without_direction = [(self.karel_start_location[0], self.karel_start_location[1], self.beepers[(self.avenue, self.street)])]

        if cond_flag:
            self.prob_front_is_clear = front_cond
            self.prob_left_is_clear = left_cond
            self.prob_right_is_clear = right_cond
            self.prob_beepers_present = beepers_present




    def move(self) -> None:
        """
        This function moves Karel forward one space in the direction that it is
        currently facing. If Karel's front is not clear (blocked by wall or boundary
        of world) then a KarelException will be raised).

        Parameters: None
        Returns: None
        """
        delta_avenue, delta_street = DIRECTION_DELTA_MAP[self.direction]
        next_avenue = self.avenue + delta_avenue
        next_street = self.street + delta_street

        # front is not clear if we are about to go out of bounds
        if not self.in_bounds(next_avenue, next_street):
            raise KarelException(
                next_avenue,
                next_street,
                self.direction,
                "Karel attempted to move, but its front was blocked.--1 "+str(self.karel_start_location)+str(self.karel_start_direction),
            )

        # front is not clear if wall exists in same direction we're currently facing: in the current location
        if self.wall_exists(self.avenue, self.street):
            raise KarelException(
                self.avenue,
                self.street,
                self.direction,
                "Karel attempted to move, but its front was blocked.--2",
            )

        delta_avenue, delta_street = DIRECTION_DELTA_MAP[self.direction]
        self.avenue += delta_avenue
        self.street += delta_street

        # front is not clear if wall exists in same direction we're currently facing: after the move
        if self.wall_exists(self.avenue, self.street):
            raise KarelException(
                self.avenue,
                self.street,
                self.direction,
                "Karel attempted to move, but its front was blocked.--3",
            )

        # do not allow backtracking
        if self.type != "karel":
            if (self.avenue, self.street, self.direction, self.beepers[(self.avenue, self.street)]) in self.karel_locations:
                # print("circular move:", self.karel_locations)
                raise KarelException(
                    self.avenue,
                    self.street,
                    self.direction,
                    "Karel attempted circular path.",
                )
            # do not allow same location to come up in move action
            if ( self.avenue, self.street) in self.locked_cells:
                # print("circular move:", self.karel_locations)
                raise KarelException(
                    self.avenue,
                    self.street,
                    self.direction,
                    "Karel attempted circular path.",
                )

        self.empty_cells.add((self.avenue, self.street))
        self.locked_cells.add((self.avenue, self.street))
        self.remove_cell(self.avenue, self.street)
        self.karel_seq.append('move')
        self.concrete_seq.append('move')
        if len(self.karel_seq) > self.max_len_execution_trace:
            raise KarelException(
                self.avenue,
                self.street,
                self.direction,
                "Karel exceeded execution trace len: Due to infinite loop.",
            )

        self.karel_locations.append(
            (self.avenue, self.street, self.direction, self.beepers[(self.avenue, self.street)]))
        self.karel_locations_without_direction.append(
            (self.avenue, self.street, self.beepers[(self.avenue, self.street)]))



    def turn_left(self) -> None:
        """
        This function turns Karel 90 degrees counterclockwise.

        Parameters: None
        Returns: None
        """
        self.direction = NEXT_DIRECTION_MAP[self.direction]

        if self.type != "karel":
            if (self.avenue, self.street, self.direction, self.beepers[(self.avenue, self.street)]) in self.karel_locations:
                raise KarelException(
                    self.avenue,
                    self.street,
                    self.direction,
                    "Karel attempted circular path.",
            )


        # else:
        self.karel_seq.append('turn_left')
        self.concrete_seq.append('turn_left')
        if len(self.karel_seq) > self.max_len_execution_trace:
            raise KarelException(
                self.avenue,
                self.street,
                self.direction,
                "Karel exceeded execution trace len: Due to infinite loop.",
            )
        self.karel_locations.append(
            (self.avenue, self.street, self.direction, self.beepers[(self.avenue, self.street)]))
        self.karel_locations_without_direction.append(
            (self.avenue, self.street, self.beepers[(self.avenue, self.street)]))



    def turn_right(self) -> None:
        """
                This function turns Karel 90 degrees clockwise.

                Parameters: None
                Returns: None
                """
        self.direction = NEXT_DIRECTION_MAP_RIGHT[self.direction]

        if self.type != "karel":
            if (self.avenue, self.street, self.direction, self.beepers[(self.avenue, self.street)]) in self.karel_locations:
                raise KarelException(
                    self.avenue,
                    self.street,
                    self.direction,
                    "Karel attempted circular path.",
                )
            # if (self.avenue, self.street, self.beepers[(self.avenue, self.street)]) in self.karel_locations_without_direction:


        # else:
        self.karel_seq.append('turn_right')
        self.concrete_seq.append('turn_right')
        if len(self.karel_seq) > self.max_len_execution_trace:
            raise KarelException(
                self.avenue,
                self.street,
                self.direction,
                "Karel exceeded execution trace len: Due to infinite loop.",
            )
        self.karel_locations.append((self.avenue, self.street, self.direction, self.beepers[(self.avenue, self.street)]))
        self.karel_locations_without_direction.append(
            (self.avenue, self.street, self.beepers[(self.avenue, self.street)]))



    def put_beeper(self) -> None:
        """
        This function places a beeper on the corner that Karel is currently standing
        on in the post-world and increases Karel's beeper count by 1. If Karel has no more beepers in its
        beeper bag, then this function raises a KarelException.

        Parameters: None
        Returns: None
        """
        if self.num_beepers == 0:
            raise KarelException(
                self.avenue,
                self.street,
                self.direction,
                "Karel attempted to put a beeper, but it had none left in its bag.",
            )

        if self.num_beepers != INFINITY:
            self.num_beepers += 1

        # flag = self.post_beepers[(self.avenue, self.street)] != 0
        # if not flag:
        if self.type != "karel":
            if (self.avenue, self.street, self.direction, self.post_beepers[(self.avenue, self.street)]) in self.karel_locations:
                # print("circular put marker:", self.karel_locations)
                raise KarelException(
                    self.avenue,
                    self.street,
                    self.direction,
                    "Karel attempted circular path.",
                )


        # ##################### TO ALLOW MORE THAN 1 BEEPER IN A LOCATION CHANGE add_beeper() routine
        self.add_beeper(self.post_beepers, self.avenue, self.street)
        self.empty_cells.add((self.avenue, self.street))
        self.locked_cells.add((self.avenue, self.street))
        # AFTER DEBUG: ADDED
        self.all_beeper_decision_cells.add((self.avenue, self.street))
        self.remove_cell(self.avenue, self.street)
        self.karel_seq.append('put_beeper')
        self.concrete_seq.append('put_beeper')
        if len(self.karel_seq) > self.max_len_execution_trace:
            raise KarelException(
                self.avenue,
                self.street,
                self.direction,
                "Karel exceeded execution trace len: Due to infinite loop.",
            )
        self.karel_locations.append(
            (self.avenue, self.street, self.direction, self.post_beepers[(self.avenue, self.street)]))
        self.karel_locations_without_direction.append(
            (self.avenue, self.street, self.post_beepers[(self.avenue, self.street)]))
        # print("After put marker:", self.karel_locations)

        # print("Concrete seq:", self.karel_seq)


    def pick_beeper(self) -> None:
        """
        This function adds a beeper from the corner that Karel is currently
        standing on. If there are no beepers
        on Karel's current corner, then this function raises a KarelException.

        Parameters: None
        Returns: None
        """
        # if not self.beepers_present():
        #     raise KarelException(
        #         self.avenue,
        #         self.street,
        #         self.direction,
        #         "Karel attempted to pick up a beeper, "
        #         "but there were none on the current corner.",
        #     )
        #
        # if self.beepers_present():
        #     self.remove_beeper(self.post_beepers, self.avenue, self.street)
        #     flag = True

        # # else:# flag = self.beepers[(self.avenue, self.street)] != 0
        #else:
        if self.type != "karel":
            if (self.avenue, self.street, self.direction, self.beepers[(self.avenue, self.street)]) in self.karel_locations:
                # print("circular pick marker:", self.karel_locations)
                raise KarelException(
                    self.avenue,
                    self.street,
                    self.direction,
                    "Karel attempted circular path.",
                )

        ################ TO ALLOW FOR MORE THAN 1-BEEPER IN A GRID CELL CHANGE THE add_beeper() routine
        if len(self.concrete_seq) == 0 or self.concrete_seq[-1] != "beeper_added":
            self.add_beeper(self.beepers, self.avenue, self.street)
            self.empty_cells.add((self.avenue, self.street))
            self.locked_cells.add((self.avenue, self.street))
            # AFTER DEBUG: ADDED
            self.all_beeper_decision_cells.add((self.avenue, self.street))
            self.remove_cell(self.avenue, self.street)
            if self.post_beepers[(self.avenue, self.street)] != 0:
                self.post_beepers[(self.avenue, self.street)] -= 1
            # if not flag:
        else:
            if self.post_beepers[(self.avenue, self.street)] != 0:
                self.post_beepers[(self.avenue, self.street)] -= 1

            self.empty_cells.add((self.avenue, self.street))
            self.locked_cells.add((self.avenue, self.street))
            self.remove_cell(self.avenue, self.street)
            # AFTER DEBUG: ADDED
            self.all_beeper_decision_cells.add((self.avenue, self.street))

        self.karel_seq.append('pick_beeper')
        self.concrete_seq.append('pick_beeper')
        if len(self.karel_seq) > self.max_len_execution_trace:
            raise KarelException(
                self.avenue,
                self.street,
                self.direction,
                "Karel exceeded execution trace len: Due to infinite loop.",
            )
        self.karel_locations.append(
            (self.avenue, self.street, self.direction, self.beepers[(self.avenue, self.street)]))
        self.karel_locations_without_direction.append(
            (self.avenue, self.street, self.beepers[(self.avenue, self.street)]))
        # # print("After pick marker:", self.karel_locations)


    def front_is_clear(self) -> bool:
        """
        This function returns a boolean indicating whether or not there is a wall
        in front of Karel.

        Parameters: None
        Returns:
            is_clear (Bool) - True if there is no wall in front of Karel
                              False otherwise
        """
        flag = self.direction_is_clear(self.direction, self.prob_front_is_clear)
        if flag:
            self.conditionals_hit['front_is_clear'] += 1
           # print(self.conditionals_hit['front_is_clear'])
            self.concrete_seq.append('front_is_clear')
        else:
            self.conditionals_hit['front_is_blocked'] += 1
            self.concrete_seq.append('front_is_blocked')

        return flag

    def front_is_blocked(self) -> bool:
        """
        This function returns a boolean indicating whether there is a wall
        in front of Karel.

        Parameters: None
        Returns:
            is_blocked (Bool) - True if there is a wall in front of Karel
                                  False otherwise
        """
        flag = self.direction_is_clear(self.direction, 1-self.prob_front_is_clear)


        if not flag:
            self.conditionals_hit['front_is_blocked'] += 1
            self.concrete_seq.append('front_is_blocked')
        else:
            self.conditionals_hit['front_is_clear'] += 1
            self.concrete_seq.append('front_is_clear')

        # print("Concrete seq:", self.karel_seq)

        return not flag


    def left_is_clear(self) -> bool:
        """
        This function returns a boolean indicating whether or not there is a wall
        to the left of Karel.

        Parameters: None
        Returns:
            is_clear (Bool) - True if there is no wall to the left of Karel
                              False otherwise
        """
        flag = self.direction_is_clear(NEXT_DIRECTION_MAP[self.direction], self.prob_left_is_clear)
        if flag:
            self.conditionals_hit['left_is_clear'] += 1
            self.concrete_seq.append('left_is_clear')
        else:
            self.conditionals_hit['left_is_blocked'] += 1
            self.concrete_seq.append('left_is_blocked')

        return flag

    def left_is_blocked(self) -> bool:
        """
        This function returns a boolean indicating whether there is a wall
        to the left of Karel.

        Parameters: None
        Returns:
            is_blocked (Bool) - True if there is a wall to the left of Karel
                                  False otherwise
        """
        flag = self.direction_is_clear(NEXT_DIRECTION_MAP[self.direction], 1-self.prob_left_is_clear)
        if not flag:
            self.conditionals_hit['left_is_blocked'] += 1
            self.concrete_seq.append('left_is_blocked')
        else:
            self.conditionals_hit['left_is_clear'] += 1
            self.concrete_seq.append('left_is_clear')

        return not flag

    def right_is_clear(self) -> bool:
        """
        This function returns a boolean indicating whether or not there is a wall
        to the right of Karel.

        Parameters: None
        Returns:
            is_clear (Bool) - True if there is no wall to the right of Karel
                              False otherwise
        """
        flag = self.direction_is_clear(NEXT_DIRECTION_MAP_RIGHT[self.direction], self.prob_right_is_clear)
        if flag:
            self.conditionals_hit['right_is_clear'] += 1
            self.concrete_seq.append('right_is_clear')
        else:
            self.conditionals_hit['right_is_blocked'] += 1
            self.concrete_seq.append('right_is_blocked')

        return flag

    def right_is_blocked(self) -> bool:
        """
        This function returns a boolean indicating whether there is a wall
        to the right of Karel.

        Parameters: None
        Returns:
            is_blocked (Bool) - True if there is a wall to the right of Karel
                                  False otherwise
        """
        flag = self.direction_is_clear(NEXT_DIRECTION_MAP_RIGHT[self.direction], 1-self.prob_right_is_clear)
        if not flag:
            self.conditionals_hit['right_is_blocked'] += 1
            self.concrete_seq.append('right_is_blocked')
        else:
            self.conditionals_hit['right_is_clear'] += 1
            self.concrete_seq.append('right_is_clear')

        return not flag

    def wall_exists(self, avenue: int, street: int) -> bool:
        wall = Wall(avenue, street)
        return wall in self.walls

    def in_bounds(self, avenue: int, street: int) -> bool:
        return 0 < avenue <= self.num_avenues and 0 < street <= self.num_streets


    def direction_is_clear(self, direction: Direction, prob: float) -> bool:
        """
        This is a helper function that returns a boolean indicating whether
        or not there is a barrier in the specified direction of Karel.

        Parameters:
            direction (Direction[Enum]) - The direction in which to check for a barrier

        Returns:
            is_clear (Bool) - True if there is no barrier in the specified direction
                              False otherwise
        """
        delta_avenue, delta_street = DIRECTION_DELTA_MAP[direction]
        next_avenue = self.avenue + delta_avenue
        next_street = self.street + delta_street

        # front is not clear if we are about to go out of bounds
        if not self.in_bounds(next_avenue, next_street):
            return False

        # front is not clear if wall exists in same direction we're currently facing
        if self.wall_exists(self.avenue, self.street):
            return False

        # must also check for alternate possible representation of wall
        # opposite_direction = NEXT_DIRECTION_MAP[NEXT_DIRECTION_MAP[direction]]
        if self.wall_exists(next_avenue, next_street):
            return False

        # DEBUGGED HERE:
        if (next_avenue, next_street) in self.empty_cells:
            return True

        # If all previous conditions checked out, then the front is clear with self.prob_front_is_clear
        if random.random() < prob:
            self.empty_cells.add((next_avenue, next_street))
            self.remove_cell(next_avenue, next_street)
            return True
        else:
            # if (next_avenue, next_street) not in self.empty_cells:
            #     self.add_wall(Wall(next_avenue, next_street))
            #     self.remove_cell(next_avenue, next_street)
            if (next_avenue, next_street) not in self.empty_cells:
                self.add_wall(Wall(next_avenue, next_street))
                self.remove_cell(next_avenue, next_street)
                self.locked_cells.add((next_avenue, next_street))
            return False

    def beepers_present(self) -> bool:
        """
        This function returns a boolean indicating whether or not there is
        a beeper on Karel's current corner.

        Parameters: None
        Returns:
            beepers_on_corner (Bool) - True if there's at least one beeper
                                       on Karel's current corner, False otherwise
        """
        if self.beepers[(self.avenue, self.street)] != 0:
            self.conditionals_hit['beepers_present'] += 1
            self.concrete_seq.append('beepers_present')
            return True

        # AFTER DEBUG: added to prevent cells which are already marked empty from containing markers/or not
        if (self.avenue, self.street) in self.all_beeper_decision_cells:
            if self.beepers[(self.avenue, self.street)] == 0:
                self.conditionals_hit['no_beepers_present'] += 1
                self.concrete_seq.append('no_beeper_present')
                return False

        if random.random() < self.prob_beepers_present:
            # # added to prevent circular paths in mazes
            # if (self.avenue, self.street) in self.empty_cells:
            #     return False
            self.add_beeper(self.beepers, self.avenue, self.street)
            self.add_beeper(self.post_beepers, self.avenue, self.street)
            self.empty_cells.add((self.avenue, self.street))
            self.locked_cells.add((self.avenue, self.street))
            # AFTER DEBUG: ADDED
            self.all_beeper_decision_cells.add((self.avenue, self.street))
            self.remove_cell(self.avenue, self.street)
            self.conditionals_hit['beepers_present'] += 1
            self.concrete_seq.append('beeper_added')
            return True
        else:
            flag = self.beepers[(self.avenue, self.street)] != 0
            if flag:
                self.conditionals_hit['beepers_present'] += 1
                self.concrete_seq.append('beeper_present')
            else:
                self.conditionals_hit['no_beepers_present'] += 1
                self.concrete_seq.append('no_beeper_present')
                self.locked_cells.add((self.avenue, self.street))
                # AFTER DEBUG: ADDED
                self.all_beeper_decision_cells.add((self.avenue, self.street))
                self.remove_cell(self.avenue, self.street)
            return flag


    def no_beepers_present(self) -> bool:

        if self.beepers[(self.avenue, self.street)] != 0:
            self.conditionals_hit['beepers_present'] += 1
            self.concrete_seq.append('beeper_present')
            return False

        # AFTER DEBUG:: added to prevent cells which are already marked empty from containing markers/or not
        if (self.avenue, self.street) in self.all_beeper_decision_cells:
            if self.beepers[(self.avenue, self.street)] == 0:
                self.conditionals_hit['no_beepers_present'] += 1
                self.concrete_seq.append('no_beeper_present')
                return True



        if random.random() < 1-self.prob_beepers_present:
            self.conditionals_hit['no_beepers_present'] += 1
            self.concrete_seq.append('no_beeper_present')
            self.empty_cells.add((self.avenue, self.street))
            self.locked_cells.add((self.avenue, self.street))
            self.remove_cell(self.avenue, self.street)
            # AFTER DEBUG: ADDED
            self.all_beeper_decision_cells.add((self.avenue, self.street))
            return True
        else:
            # if self.beepers[(self.avenue, self.street)] == 0:
            #     self.conditionals_hit['no_beepers_present'] += 1
            #     self.concrete_seq.append('no_beeper_present')
            #     return True
            self.add_beeper(self.beepers, self.avenue, self.street)
            self.add_beeper(self.post_beepers, self.avenue, self.street)
            self.empty_cells.add((self.avenue, self.street))
            self.locked_cells.add((self.avenue, self.street))
            # AFTER DEBUG: ADDED
            self.all_beeper_decision_cells.add((self.avenue, self.street))
            self.remove_cell(self.avenue, self.street)
            self.conditionals_hit['beepers_present'] += 1
            self.concrete_seq.append('beeper_added')
            return False

    def remove_cell(self, avenue:int, street:int):
        if (avenue, street) in self.unknown_cells:
            self.unknown_cells.remove((avenue, street))


    def add_beeper(self, beeper_dict: dict, avenue: int, street: int) -> None:
        if beeper_dict[(avenue, street)] == 0:
            beeper_dict[(avenue, street)] += 1
        else:
            raise KarelException(
                self.avenue,
                self.street,
                self.direction,
                "Karel attempted to put multiple beepers in one location.",
            )


    def remove_beeper(self, beeper_dict: dict, avenue: int, street: int) -> None:
        if beeper_dict[(avenue, street)] > 0:
            beeper_dict[(avenue, street)] -= 1


    def add_wall(self, wall: Wall) -> None:
        # alt_wall = self.get_alt_wall(wall)
        if wall not in self.walls:
            #and alt_wall not in self.walls:
            self.walls.add(wall)
            self.locked_cells.add((wall.avenue, wall.street))

    def remove_wall(self, wall: Wall) -> None:
        # alt_wall = self.get_alt_wall(wall)
        if wall in self.walls:
            self.walls.remove(wall)
        # if alt_wall in self.walls:
        #     self.walls.remove(alt_wall)




    def create_karel_world(self, post_world_flag = False):

        karel_world = KarelWorld(None)
        if post_world_flag:
            karel_world.beepers = self.post_beepers
            karel_world.karel_start_location = (self.avenue, self.street)
            karel_world.karel_start_direction = self.direction
        else:
            karel_world.beepers = self.beepers
            karel_world.karel_start_location = self.karel_start_location
            karel_world.karel_start_direction = self.karel_start_direction

        walls = copy.deepcopy(self.walls)
        if self.type !=  "karel":
            for i in range(1,self.num_avenues+1):
                for j in range(1,self.num_streets+1):
                    if (i,j) not in self.empty_cells:
                        # walls.add(Wall(i,j,Direction.NORTH))
                        # walls.add(Wall(i,j, Direction.WEST))
                        walls.add(Wall(i,j))


        karel_world.walls = walls
        karel_world.num_streets = self.num_streets
        karel_world.num_avenues = self.num_avenues
        karel_world.karel_start_beeper_count = self.karel_start_beeper_count

        return karel_world

    def __repr__(self):
        karelworld_start = self.create_karel_world()
        karelworld_end = self.create_karel_world(post_world_flag=True)
        karelworld_start.walls = karelworld_end.walls
        return str(AsciiKarelWorld(karelworld_start, self.karel_start_location[1], self.karel_start_location[0])) + "\n" + str(AsciiKarelWorld(karelworld_end, self.street, self.avenue))

    @staticmethod
    def parse_parameters(keyword: str, param_str: str):
        params: dict[str, Any] = {}
        for param in param_str.split(PARAM_DELIM):
            param = param.strip()

            # check to see if parameter encodes a location
            coordinate = re.match(r"\((\d+),\s*(\d+)\)", param)
            if coordinate:
                # avenue, street
                params["location"] = int(coordinate.group(1)), int(coordinate.group(2))
                continue

            # check to see if the parameter is a direction value
            if param in (d.value for d in Direction):
                params["direction"] = Direction(param)

            else:
                raise ValueError(f"Error: {param} is invalid parameter for {keyword}.")
        return params

    # for loading initial gird parameters form a file
    def load_from_file(self) -> None:

        if self.init_config_file == '':
            print("No initial config file provided.")
            exit(0)

        with open(self.init_config_file) as f:
            for i, line in enumerate(f):
                # Ignore blank lines and lines with no comma delineator
                line = line.strip()
                if not line:
                    continue

                if KEYWORD_DELIM not in line:
                    print(f"Incorrectly formatted - ignoring line {i} of file: {line}")
                    continue

                keyword, param_str = line.lower().split(KEYWORD_DELIM)

                # only accept valid keywords as defined in world file spec
                # TODO: add error detection for keywords with insufficient parameters
                params = self.parse_parameters(keyword, param_str)

                # handle all different possible keyword cases
                if keyword == "dimension":
                    # set world dimensions based on location values
                    self.num_avenues, self.num_streets = params["location"]

                elif keyword == "wall":
                    # build a wall at the specified location
                    (avenue, street) = (
                        params["location"]
                        #params["direction"],
                    )
                    self.walls.add(Wall(avenue, street))
                    self.remove_cell(avenue, street)

                elif keyword == "beeper":
                    # add the specified number of beepers to the world
                    self.beepers[params["location"]] += params["val"]
                    self.remove_cell(params["location"][0], params["location"][1])

                elif keyword == "empty":
                    # add the empty cells to the world
                    self.empty_cells.add(params["location"])
                    self.remove_cell(params['location'][0], params['location'][1])

                else:
                    print(f"Invalid keyword - ignoring line {i} of world file: {line}")


    def save_to_file(self, filename: str, beeper_dict: dict, karel_location: tuple, karel_direction: Direction) -> None:

        with open(filename, "w") as f:
            # First, output dimensions of world
            f.write(f"Dimension: ({self.num_avenues}, {self.num_streets})\n")

            # Next, output all walls
            for wall in sorted(self.walls):
                # f.write(
                #     f"Wall: ({wall.avenue}, {wall.street}); {wall.direction.value}\n"
                # )
                f.write(
                    f"Wall: ({wall.avenue}, {wall.street})\n"
                )

            # Next, output all beepers
            for loc, count in sorted(beeper_dict.items()):
                f.write(f"Beeper: ({loc[0]}, {loc[1]}); {count}\n")

            for empty_cell in sorted(self.empty_cells):
                f.write(f"Empty: ({empty_cell[0]}, {empty_cell[1]})\n")

            # Next, output Karel information
            f.write(
                f"Karel: {karel_location}; "
                f"{karel_direction.value}\n"
            )

            # Finally, output beeperbag info
            beeper_output = (
                self.karel_start_beeper_count
                if self.karel_start_beeper_count >= 0
                else "INFINITY"
            )
            f.write(f"BeeperBag: {beeper_output}\n")


    def save_current_sym_world_file(self, dir:str, filename:str):

        if not os.path.exists(dir):
            os.makedirs(dir)

        init_world_file = dir+ filename + '_pre.sw'
        self.save_to_file(init_world_file, self.beepers, self.karel_start_location, self.karel_start_direction)

        final_world_file = dir+ filename+ '_post.sw'
        self.save_to_file(final_world_file, self.post_beepers, (self.avenue, self.street), self.direction)


    def save_task_grid_to_file(self, karel_start_world, karel_end_world, karel_loc, karel_dir, outputfolder, filename):

        pregridworld = np.empty([self.num_streets, self.num_avenues], dtype=str)
        pregridworld[:] = "."
        postgridworld = np.empty([self.num_streets, self.num_avenues], dtype=str)
        postgridworld[:] = "."

        grid_size = (self.num_streets + 2, self.num_avenues + 2)

        task_file = outputfolder + filename
        f = open(task_file, "w")
        f.write("type\t" + str(self.type) + "\n")
        f.write("gridsz\t" + str(grid_size) + "\n\n")
        f.write("pregrid\t")

        for i in range(1,self.num_avenues+3):
            f.write(str(i)+"\t")
        f.write("\n")
        f.write("1\t")
        for i in range(1, self.num_avenues + 3):
            f.write("#\t")
        f.write("\n")


        for wall in sorted(karel_start_world.walls):
            pregridworld[self.num_streets-wall.street, wall.avenue-1] = "#"
            postgridworld[self.num_streets-wall.street, wall.avenue-1] = "#"

        for loc, count in sorted(karel_start_world.beepers.items()):
            if count == 1:
                pregridworld[self.num_streets-loc[1], loc[0] - 1] = "x"
            elif count > 1:
                pregridworld[self.num_streets-loc[1], loc[0] - 1] = str(count)
            else:
                continue

        for loc, count in sorted(karel_end_world.beepers.items()):
            if count == 1:
                postgridworld[self.num_streets-loc[1], loc[0] - 1] = "x"
            elif count > 1:
                postgridworld[self.num_streets-loc[1], loc[0] - 1] = str(count)
            else:
                continue

        ####### Store the pregrid
        j = 1
        for i in range(pregridworld.shape[0]):
            j += 1
            f.write(str(j)+"\t#\t")
            for k in range(pregridworld.shape[1]):
                f.write(pregridworld[i,k]+"\t")
            f.write("#\n")

        f.write(str(j+1)+"\t")
        for i in range(1, self.num_avenues + 3):
            f.write("#\t")
        f.write("\n")

        ##### Agent loc
        f.write("agentloc\t" + str((self.karel_start_location[0]+1, self.num_streets - self.karel_start_location[1]+2)))
        f.write("\n")
        #### Agent direction
        f.write("agentdir\t" + str(direction_dict[self.karel_start_direction]))
        f.write("\n\n")

        ####### Store the postgrid
        f.write("postgrid\t")

        for i in range(1, self.num_avenues + 3):
            f.write(str(i) + "\t")
        f.write("\n")
        f.write("1\t")
        for i in range(1, self.num_avenues + 3):
            f.write("#\t")
        f.write("\n")

        j = 1
        for i in range(postgridworld.shape[0]):
            j += 1
            f.write(str(j) + "\t#\t")
            for k in range(postgridworld.shape[1]):
                f.write(postgridworld[i, k] + "\t")
            f.write("#\n")

        f.write(str(j + 1) + "\t")
        for i in range(1, self.num_avenues + 3):
            f.write("#\t")
        f.write("\n")

        ##### Agent loc
        f.write("agentloc\t" + str((karel_loc[0]+1, self.num_streets - karel_loc[1]+2)))
        f.write("\n")
        #### Agent direction
        if self.type == "hoc":
            f.write("agentdir\t" + str("unknown"))
        else:
            f.write("agentdir\t" + str(direction_dict[karel_dir]))

        f.write("\n\n")


        f.close()
























