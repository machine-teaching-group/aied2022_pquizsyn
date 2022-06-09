from __future__ import absolute_import
from code.step3_code2task.sym_world import SymWorld
from code.step3_code2task.sym_code import SymApplication


"""
The following function definitions are defined as stubs so that IDEs can recognize
the function definitions in student code. These names are re-bound upon program
execution to asscoiate their behavior to the one particular Karel object located
in a given world.
"""


def move() -> None:
    pass


def turn_left() -> None:
    pass

def turn_right() -> None:
    pass

def put_beeper() -> None:
    pass


def pick_beeper() -> None:
    pass


def front_is_clear() -> bool:
    pass

#
def front_is_blocked() -> bool:
    pass


def left_is_clear() -> bool:
    pass


def left_is_blocked() -> bool:
    pass


def right_is_clear() -> bool:
    pass


def right_is_blocked() -> bool:
    pass


def beepers_present() -> bool:
    pass

#
def no_beepers_present() -> bool:
    pass
#
#
# def beepers_in_bag() -> bool:
#     pass
#
#
# def no_beepers_in_bag() -> bool:
#     pass
#
#
# def facing_north() -> bool:
#     pass
#
#
# def not_facing_north() -> bool:
#     pass
#
#
# def facing_east() -> bool:
#     pass
#
#
# def not_facing_east() -> bool:
#     pass
#
#
# def facing_west() -> bool:
#     pass
#
#
# def not_facing_west() -> bool:
#     pass
#
#
# def facing_south() -> bool:
#     pass
#
#
# def not_facing_south() -> bool:
#     pass
#
#
# def paint_corner(color: str) -> None:
#     del color
#
#
# def corner_color_is(color: str) -> bool:
#     del color
#     return True

def run_symbolic_execution(code_file:str, json_code_file:str, task_dimensions:dict, prob_front=0.5, prob_left=0.5, prob_right=0.5, prob_beepers=0.5, init_config_flag=False, init_config_file=''):

    sym_world = SymWorld(task_dimensions, prob_front, prob_left, prob_right, prob_beepers, init_config_flag=init_config_flag, init_config_file=init_config_file)
    sym_app = SymApplication(sym_world, code_file, json_code_file)
    # print("Before:", sym_app.karel.karel_seq, sym_app.karel.direction)
    try:
        sym_app.run_program()
    except:
        # print("Initial run has issues:", sym_app.karel.karel_start_location)
        return None


    # print("After:", sym_app.karel.karel_seq)
    # ## create the Karel Worlds
    # start_world = sym_app.karel.create_karel_world()
    # end_world = sym_app.karel.create_karel_world(post_world_flag=True)
    # start_world.walls = end_world.walls
    # # run the concrete Karel-code on this
    # try:
    #     print("Running concrete karel code:")
    #     # print(AsciiKarelWorld(start_world, start_world.karel_start_location[1], start_world.karel_start_location[0]))
    #     # print(start_world.karel_start_direction)
    #     # print(AsciiKarelWorld(end_world, end_world.karel_start_location[1], end_world.karel_start_location[0]))
    #     # print("Final sequence to generate task:", sym_app.karel.karel_seq)
    #     final_seq = sym_app.run_karel_program(start_world)
    # except:
    #     print("Concrete run has issues")
    #     return None
    #
    # if final_seq is None:
    #     return None
    # else:
    #     sym_app.karel.concrete_seq = copy.deepcopy(final_seq)



    return [sym_app]



def run_symbolic_execution_parallel(id:int, code_file:str, json_code_file:str, task_dimensions:dict, prob_front=0.5, prob_left=0.5, prob_right=0.5, prob_beepers=0.5, init_config_flag=False, init_config_file=''):

    sym_world = SymWorld(task_dimensions, prob_front, prob_left, prob_right, prob_beepers, init_config_flag=init_config_flag, init_config_file=init_config_file)
    sym_app = SymApplication(sym_world, code_file, json_code_file)
    # print("Before:", sym_app.karel.karel_seq, sym_app.karel.direction)
    try:
        sym_app.run_program()
    except:
        # print("Initial run has issues:", sym_app.karel.karel_start_location)
        return None

    return sym_app








