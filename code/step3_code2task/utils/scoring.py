from scipy.spatial import distance
import numpy as np
from itertools import groupby


from code.step3_code2task.sym_world import SymWorld
from code.step3_code2task.sym_code import SymApplication
from code.step3_code2task.utils.get_min_blocks import prune_using_shortest_path_karel
from code.step3_code2task.utils.get_min_blocks_hoc import prune_using_shortest_path_hoc
from code.step3_code2task.github_stanfordkarel.stanfordkarel.karel_world import KarelWorld, Direction

def qual_score(karel_world:SymWorld):
    grid_size = karel_world.num_streets
    counts = [[k, len(list(v))] for k, v in groupby(karel_world.karel_seq)]
    moves_count = 0
    turns_count = 0
    short_seg = 0
    long_seg = 0
    pick_count = 0
    put_count = 0
    for ele in counts:
        if ele[0] == 'move':
            moves_count += ele[1]
            if ele[1] > 2:
                short_seg += 1
            if ele[1] > 4:
                long_seg += 1
        if ele[0] == 'turn_left' or ele[0] == 'turn_right':
            turns_count += ele[1]
        if ele[0] == 'pick_beeper':
            pick_count += ele[1]
        if ele[0] == 'put_beeper':
            put_count += ele[1]

    if karel_world.type != 'hoc':
        return 0.75*0.25*(float(moves_count/(2*grid_size)) + float(turns_count/grid_size) + float(short_seg/(grid_size/2)) +
                      float(long_seg/(grid_size/3))) + 0.25*0.5*(float(pick_count/grid_size)+float(put_count/grid_size))
    else:
        return  0.25 * (float(moves_count / (2 * grid_size)) + float(turns_count / grid_size) + float(
            short_seg / (grid_size / 2)) +
                              float(long_seg / (grid_size / 3)))


def cut_score(sym_world: SymWorld, start_karel_world:KarelWorld, end_karel_world:KarelWorld, maxblocks:int, basic_action_flag:bool, type='hoc'):
    # try :
    if type!='hoc':
        flag = prune_using_shortest_path_karel(start_karel_world, end_karel_world, maxblocks, verbose=0)
    else:
        flag = prune_using_shortest_path_hoc(start_karel_world, end_karel_world, maxblocks, verbose=0)
    # except:
    #     #     print("Start Direction:", sym_world.karel_start_direction)
    #     #     print("Sym Seq:", sym_world.karel_seq)
    #     #     print(AsciiKarelWorld(start_karel_world, start_karel_world.karel_start_location[1], start_karel_world.karel_start_location[0]))
    #     #     print(AsciiKarelWorld(end_karel_world, end_karel_world.karel_start_location[1], end_karel_world.karel_start_location[0]))
    #     #     exit(0)

    if not basic_action_flag: # code has other structures.
        if( flag == "greater"): # keep codes whose basic action seq solution is strictly greater than the current code size
            return 1
        else:
            return 0  # remove codes whose basic action seq solution is less than or equal to the current code size
    else: # code only has basic actions
        if (flag == "greater" or flag == "equal"):  # keep codes whose basic action seq solution is less than/ equal to the current code size
            return 1
        else:
            return 0



def coverage_score(sym_application:SymApplication):
    if sym_application.cov:
        return 1
    else:
        return 0


def dissimilarity_score(input_world:dict, output_world:SymWorld, type:str):

    input_preloc = input_world['pre_loc']
    output_preloc = output_world.karel_start_location
    preloc_score = score_agent_location(input_preloc, output_preloc, output_world.num_streets)

    input_predir = input_world['pre_dir']
    output_predir = output_world.karel_start_direction
    predir_score = direction_agent(input_predir, output_predir)

    input_postloc = input_world['post_loc']
    output_postloc = (output_world.avenue, output_world.street)
    postloc_score = score_agent_location(input_postloc, output_postloc, output_world.num_streets)

    input_postdir = input_world['post_dir']
    output_postdir = output_world.direction
    postdir_score = direction_agent(input_postdir, output_postdir)

    world_score = world_level_dissimilarity(input_world, output_world)
    if type == "hoc":
        return (float(1/3)*preloc_score*postloc_score + float(1/3)*predir_score + float(1/3)*world_score)
    else:
        return (float(1 / 3) * preloc_score * postloc_score + float(1 / 3) * predir_score * postdir_score + float(
            1 / 3) * world_score)



def world_level_dissimilarity(input_world:dict, output_world:SymWorld):

    # process the output world to generate a string
    input_pregrid = input_world['pregrid']
    # output_pregrid = np.empty([2*output_world.num_avenues+1, 2*output_world.num_streets+1], dtype=str)
    # output_pregrid[:] = "."

    output_pregrid = np.empty([output_world.num_avenues , output_world.num_streets], dtype=str)
    output_pregrid[:] = "."

    input_postgrid = input_world['postgrid']
    # output_postgrid = np.empty([2*output_world.num_avenues+1, 2*output_world.num_streets+1], dtype=str)
    # output_postgrid[:] = "."
    output_postgrid = np.empty([output_world.num_avenues, output_world.num_streets], dtype=str)
    output_postgrid[:] = "."


    for ele in output_world.walls:
        # if ele.direction == Direction.NORTH:
        #     output_pregrid[2 * abs(output_world.num_streets - ele.street), 2 * ele.avenue - 1] = "#"
        #     output_postgrid[2 * abs(output_world.num_streets - ele.street), 2 * ele.avenue - 1] = "#"
        # if ele.direction == Direction.SOUTH:
        #     output_pregrid[2 * abs(output_world.num_streets - ele.street + 1), 2 * ele.avenue - 1] = "#"
        #     output_postgrid[2 * abs(output_world.num_streets - ele.street + 1), 2 * ele.avenue - 1] = "#"
        # if ele.direction == Direction.EAST:
        #     output_pregrid[2 * abs(output_world.num_streets - ele.street) + 1, 2 * ele.avenue] = "#"
        #     output_postgrid[2 * abs(output_world.num_streets - ele.street) + 1, 2 * ele.avenue] = "#"
        # if ele.direction == Direction.WEST:
        #     output_postgrid[2 * abs(output_world.num_streets - ele.street) + 1, 2 * (ele.avenue - 1)] = "#"
        #     output_pregrid[2 * abs(output_world.num_streets - ele.street) + 1, 2 * (ele.avenue - 1)] = "#"
        output_postgrid[abs(output_world.num_streets - ele.street), (ele.avenue - 1)] = "#"
        output_pregrid[abs(output_world.num_streets - ele.street), (ele.avenue - 1)] = "#"


    for ele,val in output_world.beepers.items():
        if val == 0:
            continue
        elif val == 1:
            # output_pregrid[2*abs(ele[1]-output_world.num_streets)+1][2*ele[0]-1] = "x"
            output_pregrid[abs(ele[1] - output_world.num_streets)][ele[0]-1] = "x"

        else:
            # output_pregrid[2 * abs(ele[1] - output_world.num_streets) + 1][2 * ele[0] - 1] = str(val)
            output_pregrid[abs(ele[1] - output_world.num_streets)][ele[0] - 1] = str(val)


    for ele, val in output_world.post_beepers.items():
        if val == 0:
            continue
        elif val == 1:
            # output_postgrid[2*abs(ele[1]-output_world.num_streets)+1][2*ele[0]-1] = "x"
            output_postgrid[abs(ele[1] - output_world.num_streets)][ele[0] - 1] = "x"
        else:
            # output_postgrid[2 * abs(ele[1] - output_world.num_streets) + 1][2 * ele[0] - 1] = str(val)
            output_postgrid[abs(ele[1] - output_world.num_streets)][ele[0] - 1] = str(val)

    # compute the hamming distance
    # pad the input matrix:
    # mod_input_pregrid = np.empty([2*input_pregrid.shape[1]+1, 2*input_pregrid.shape[0]+1], dtype=str)
    # mod_input_pregrid[:] = "#"
    # mid_x = int(input_pregrid.shape[1])
    # mid_y = int(input_pregrid.shape[0])
    # for i in range(input_pregrid.shape[1]):
    #     for j in range(input_pregrid.shape[0]):
    #         mod_input_pregrid[i + mid_x][j + mid_y] = input_pregrid[i][j]
    # mod_input_pregrid = mod_input_pregrid.flatten()
    output_pregrid = output_pregrid.flatten()
    # hamming_distance_pregrid = distance.hamming(mod_input_pregrid, output_pregrid)
    hamming_distance_pregrid = distance.hamming(input_pregrid.flatten(), output_pregrid)


    # compute the hamming distance
    # pad the input matrix:
    # mod_input_postgrid = np.empty([2 * input_postgrid.shape[1] + 1, 2 * input_postgrid.shape[0] + 1], dtype=str)
    # mod_input_postgrid[:] = "#"
    # mid_x = int(input_postgrid.shape[1])
    # mid_y = int(input_postgrid.shape[0])
    # for i in range(input_postgrid.shape[1]):
    #     for j in range(input_postgrid.shape[0]):
    #         mod_input_postgrid[i + mid_x][j + mid_y] = input_postgrid[i][j]
    # mod_input_postgrid = mod_input_postgrid.flatten()
    output_postgrid = output_postgrid.flatten()
    # hamming_distance_postgrid = distance.hamming(mod_input_postgrid, output_postgrid)
    hamming_distance_postgrid = distance.hamming(input_postgrid.flatten(), output_postgrid)

    min_distance = min(hamming_distance_pregrid, hamming_distance_postgrid)
    return norm_score(2 * min_distance, 1)


def norm_score(val, good_val):
    return min(1, val/good_val)



def get_quadrant(x, y, gridsz):
    '''This gridsz includes padding'''
    if( (x<=gridsz/2) and (y<=gridsz/2) ):
        quad = "top_left"
    elif( (x>gridsz/2) and (y<=gridsz/2) ):
        quad = "top_right"
    elif( (x<=gridsz/2) and (y>gridsz/2) ):
        quad = "bottom_left"
    else:
        quad = "bottom_right"
    # ordering to check quadrants is important,
    # first check four corners then check centre
    if( gridsz == 8 ):
        if( (x>=3) and (x<=4) and (y>=3) and (y<=4) ):
            quad = "centre"
    elif( gridsz == 12 ):
        if( (x>=4) and (x<=7) and (y>=4) and (y<=7) ):
            quad = "centre"
    elif( gridsz == 14 ):
        if( (x>=5) and (x<=9) and (y>=5) and (y<=9) ):
            quad = "centre"
    elif( gridsz == 16 ):
        if( (x>=5) and (x<=11) and (y>=5) and (y<=11) ):
            quad = "centre"

    return quad

def direction_agent(input_agent_dir, output_agent_dir):
    if( input_agent_dir == output_agent_dir):
        return 0
    else:
        # higher score if dissimilar
        return 1

def score_agent_location(input_agent_loc: tuple, output_agent_loc: tuple, gridsz: int):

    input_quad = get_quadrant(input_agent_loc[0], input_agent_loc[1], gridsz)
    output_quad = get_quadrant(output_agent_loc[0], output_agent_loc[1], gridsz)

    if (input_quad == output_quad):
        return 0
    else:
        # higher score if dissimilar
        return 1


