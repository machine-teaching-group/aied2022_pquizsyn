import networkx as nx
import numpy as np
import ast
from code.step3_code2task.github_stanfordkarel.stanfordkarel.karel_world import KarelWorld, Direction, Wall
from code.step3_code2task.github_stanfordkarel.stanfordkarel.karel_ascii import AsciiKarelWorld


dir_to_num = {
    Direction.EAST: 1,
    Direction.SOUTH: 2,
    Direction.WEST: 3,
    Direction.NORTH: 4

}


dir_dict = {
    '11': [],
    '13': ['turn_right', 'turn_right'],
    '14': ['turn_left'],
    '12': ['turn_right'],

    '33': [],
    '31': ['turn_left', 'turn_left'],
    '34': ['turn_right'],
    '32': ['turn_left'],

    '44': [],
    '42': ['turn_right', 'turn_right'],
    '41': ['turn_right'],
    '43': ['turn_left'],

    '22': [],
    '24': ['turn_left', 'turn_left'],
    '21': ['turn_left'],
    '23': ['turn_right']
}



def get_grid_mat(karelworld_start: KarelWorld, karelworld_end: KarelWorld):

    gridsize_start = (karelworld_start.num_avenues, karelworld_start.num_streets)
    #karelstart = [2*abs(gridsize_start[1]-karelworld_start.karel_start_location[1])+1, 2*karelworld_start.karel_start_location[0]-1]
    karelstart = [gridsize_start[1]-karelworld_start.karel_start_location[1], karelworld_start.karel_start_location[0]-1]
    karelstart_dir = karelworld_start.karel_start_direction

    gridsize_end = (karelworld_end.num_avenues, karelworld_end.num_streets)
    #karelend = [2*abs(gridsize_end[1]- karelworld_end.karel_start_location[1])+1, 2*karelworld_end.karel_start_location[0]-1]
    karelend = [gridsize_end[1]- karelworld_end.karel_start_location[1], karelworld_end.karel_start_location[0]-1]
    karelend_dir = karelworld_end.karel_start_direction

    if gridsize_start != gridsize_end:
        assert "Check the dimensions of the start and end worlds!"
        return -1

    # mat_pregrid = np.zeros((2*gridsize_start[0]+1, 2*gridsize_start[1]+1), dtype = np.int64)
    # mat_postgrid = np.zeros((2*gridsize_end[0]+1, 2*gridsize_end[1]+1), dtype = np.int64)

    mat_pregrid = np.zeros((gridsize_start[0], gridsize_start[1]), dtype=np.int64)
    mat_postgrid = np.zeros((gridsize_end[0], gridsize_end[1]), dtype=np.int64)

    ## fill in the matrix
    # for ele, value in karelworld_start.beepers.items():
    #     if value>0:
    #         mat_pregrid[2*abs(gridsize_start[1]-ele[1])+1, 2*ele[0]-1] = 2
    # for ele, value in karelworld_end.beepers.items():
    #     if value>0:
    #         mat_postgrid[2*abs(gridsize_end[1]-ele[1])+1, 2*ele[0]-1] = 2
    # for ele in karelworld_start.walls:
    #     if ele.direction == Direction.NORTH:
    #         mat_pregrid[2*abs(gridsize_start[1]-ele.street), 2*ele.avenue-1] = 1
    #         mat_postgrid[2*abs(gridsize_end[1]-ele.street), 2*ele.avenue-1] = 1
    #     if ele.direction == Direction.SOUTH:
    #         mat_pregrid[2*abs(gridsize_start[1]-ele.street+1),  2*ele.avenue-1] = 1
    #         mat_postgrid[2*abs(gridsize_start[1]-ele.street+1),  2*ele.avenue-1] = 1
    #     if ele.direction == Direction.EAST:
    #         mat_pregrid[ 2*abs(gridsize_start[1]-ele.street)+1, 2*ele.avenue] = 1
    #         mat_postgrid[2*abs(gridsize_start[1]-ele.street)+1, 2*ele.avenue] = 1
    #     if ele.direction == Direction.WEST:
    #         mat_postgrid[2*abs(gridsize_start[1]-ele.street)+1, 2 * (ele.avenue - 1)] = 1
    #         mat_pregrid[2*abs(gridsize_start[1]-ele.street)+1, 2 * (ele.avenue - 1)] = 1

    for ele, value in karelworld_start.beepers.items():
        if value>0:
            mat_pregrid[gridsize_start[1]-ele[1], ele[0]-1] = 2

    for ele, value in karelworld_end.beepers.items():
        if value>0:
            mat_postgrid[abs(gridsize_end[1]-ele[1]), ele[0]-1] = 2

    for ele in karelworld_start.walls:
            mat_pregrid[abs(gridsize_start[1]-ele.street), ele.avenue-1] = 1
            mat_postgrid[abs(gridsize_end[1]-ele.street), ele.avenue-1] = 1


    ######## Find the difference of the 2 mats: post_grid-pregrid
    subgoals = []
    mat_diff = np.where(mat_pregrid != mat_postgrid)
    listOfCoordinates = list(zip(mat_diff[0], mat_diff[1]))
    # diff = np.zeros((2*gridsize_start[0]+1, 2*gridsize_start[1]+1), dtype=np.int64)
    diff = np.zeros((gridsize_start[0], gridsize_start[1]), dtype=np.int64)
    for coord in listOfCoordinates:
        subgoals.append(coord)
        diff[coord[0], coord[1]] = 3

    return gridsize_start, karelstart, karelstart_dir, mat_pregrid, karelend, karelend_dir, mat_postgrid, subgoals, diff




def get_neighbors(x_coord, y_coord, dir, grid, gridsize = 12):

    neighbors = []
    if grid[x_coord, y_coord] == 1:
        return neighbors
    if dir == 1: # east
        dx = 0
        dy = 1
    if dir == 2: # south
        dx = 1
        dy = 0
    if dir == 3: # west
        dx = 0
        dy = -1
    if dir == 4: # north
        dx = -1
        dy = 0
    else:
        assert "Invalid dir encountered"


    for i in range(1,5): # add all the directions in the same loc
        if i == dir:
            continue
        neighbors.append([x_coord, y_coord, i])
    # add the neighbor for the move option
    new_x_coord = x_coord + dx
    new_y_coord = y_coord + dy

    if new_x_coord > gridsize-1 or new_y_coord > gridsize-1:
        return neighbors
    elif new_x_coord < 0 or new_y_coord < 0:
        return neighbors

    elif grid[new_x_coord, new_y_coord] == 1:
        return neighbors

    else:
        neighbors.append([new_x_coord, new_y_coord, dir])
        return neighbors



############ OLD
# def get_neighbors(x_coord, y_coord, dir, grid, gridsize = 12):
#
#     neighbors = []
#     if grid[x_coord, y_coord] == 1:
#         return neighbors
#     if x_coord%2 == 0 or y_coord%2 == 0:
#         return neighbors
#
#     if dir == 1: # east
#         dx = 0
#         dy = 1
#     if dir == 2: # south
#         dx = 1
#         dy = 0
#     if dir == 3: # west
#         dx = 0
#         dy = -1
#     if dir == 4: # north
#         dx = -1
#         dy = 0
#     else:
#         assert "Invalid dir encountered"
#
#
#     for i in range(1,5): # add all the directions in the same loc
#         if i == dir:
#             continue
#         neighbors.append([x_coord, y_coord, i])
#     # add the neighbor for the move option
#     new_x_coord = x_coord + dx
#     new_y_coord = y_coord + dy
#
#     if grid[new_x_coord, new_y_coord] == 1:
#         return neighbors
#
#     if new_x_coord%2 == 0:
#         new_x_coord = new_x_coord + dx
#         if new_x_coord % 2 ==0:
#             return neighbors
#         else:
#             if new_x_coord > gridsize - 1 or new_y_coord > gridsize - 1:
#                 return neighbors
#             elif new_x_coord < 0 or new_y_coord < 0:
#                 return neighbors
#
#             elif grid[new_x_coord, new_y_coord] == 1:
#                 return neighbors
#
#             else:
#                 neighbors.append([new_x_coord, new_y_coord, dir])
#                 return neighbors
#
#     elif new_y_coord%2 == 0:
#         new_y_coord = new_y_coord + dy
#         if new_y_coord % 2 == 0:
#             return neighbors
#         else:
#             if new_x_coord > gridsize - 1 or new_y_coord > gridsize - 1:
#                 return neighbors
#             elif new_x_coord < 0 or new_y_coord < 0:
#                 return neighbors
#
#             elif grid[new_x_coord, new_y_coord] == 1:
#                 return neighbors
#
#             else:
#                 neighbors.append([new_x_coord, new_y_coord, dir])
#                 return neighbors
#
#     else:
#         if new_x_coord > gridsize-1 or new_y_coord > gridsize-1:
#             return neighbors
#         elif new_x_coord < 0 or new_y_coord < 0:
#             return neighbors
#
#         elif grid[new_x_coord, new_y_coord] == 1:
#             return neighbors
#
#         else:
#             neighbors.append([new_x_coord, new_y_coord, dir])
#             return neighbors


def construct_graph_from_grid(grid):

    node_dict = {}

    k = 0
    # add all the elements in the node dictionary
    for i in range(grid.shape[0]):
        for j in range(grid.shape[1]):
            if [i,j,1] not in node_dict.values():
                node_dict[k] = str([i,j,1])
                k += 1
            if [i, j, 2] not in node_dict.values():
                node_dict[k] = str([i,j,2])
                k += 1
            if [i, j, 3] not in node_dict.values():
                node_dict[k] = str([i,j,3])
                k += 1
            if [i, j, 4] not in node_dict.values():
                node_dict[k] = str([i,j,4])
                k += 1

    inv_node_map = {v: k for k, v in node_dict.items()}

    # generate the edge list
    edge_list = []
    for k, item in node_dict.items():
        tuple = eval(item)
        tuple = [int(ele) for ele in tuple]

        nbs = get_neighbors(tuple[0], tuple[1], tuple[2], grid, gridsize=grid.shape[0])
        nbs = [str(ele) for ele in nbs]

        edge_node_1 = inv_node_map[item]
        for ele in nbs:
            edge_node_2 = inv_node_map[ele]
            edge_list.append((edge_node_1, edge_node_2))



    # construct the graph from edge list
    G = nx.DiGraph()
    G.add_edges_from(edge_list)

    return G, inv_node_map, node_dict, edge_list


def get_shortest_path(g, start, goal, node_dict, inv_node_map):

    all_shortest_paths = []
    start_node = inv_node_map[str(start)]
    for i in range(1,5): # get paths to all the orientations in the goal state
        goal_o = str([goal[0], goal[1], i])
        goal_node = inv_node_map[str(goal_o)]
        shortest_path = nx.shortest_path(g,source=start_node,target=goal_node)

        shortest_blocks = [node_dict[ele] for ele in shortest_path]
        all_shortest_paths.append([i,shortest_blocks])

    return all_shortest_paths

def get_turns_to_next_loc(init_loc, next_loc):

    action = []
    if init_loc[0] == next_loc[0] and init_loc[1] == next_loc[1]:
       dir_pair = str(init_loc[2]) + str(next_loc[2])
       action.extend(dir_dict[dir_pair])
    else:
        action.append('move')

    return action

def prune_path_to_remove_walking_over_walls(path):
    new_path = []
    for ele in path:
        nele = ast.literal_eval(ele)
        if int(nele[0]) % 2 == 0:
            continue
        elif int(nele[1]) % 2 == 0:
            continue
        else:
            new_path.append(ele)

    return new_path


def get_blocks_from_path(path):
    blocks = []
    # prune the path to avoid additional moves
    # pruned_path  = prune_path_to_remove_walking_over_walls(path)
    pruned_path = path
    for i in range(len(pruned_path)-1):
        state = eval(pruned_path[i])
        state = [int(ele) for ele in state]
        next_state = eval(pruned_path[i+1])
        next_state = [int(ele) for ele in next_state]

        blocks.extend(get_turns_to_next_loc(state, next_state))

    return blocks

def get_shortest_block_seq_to_subgoal(g, vertice_dict, inv_vertice_map, edge_list, start_state, end_loc):


    all_shortest_paths = {}
    for ele in end_loc:
        all_shortest_paths[str(ele)] = get_shortest_path(g, start_state, ele, vertice_dict, inv_vertice_map)

    min_count = np.inf
    min_block_seq = []
    min_path = []
    for ele in end_loc:
        for path in all_shortest_paths[str(ele)]:
            blocks = get_blocks_from_path(path[1])
            if len(blocks) < min_count:
                min_count = len(blocks)
                min_block_seq = blocks
                min_path = path
                dir = path[0]

    return min_count, min_block_seq, min_path, dir


def prune_using_shortest_path_karel(start_world:KarelWorld, end_world:KarelWorld, maxnumblocks, verbose = 0):

    gridsz, start_loc, start_dir, pregrid, end_loc, end_dir, postgrid, subgoals, diff = \
        get_grid_mat(start_world, end_world)



    if verbose == 1:
        print("Gridsize:", gridsz)
        print("Start:", start_loc, start_dir)
        print("End:", end_loc, end_dir)
        print("pregrid:", pregrid)
        print("postgrid:", postgrid)
        print("diff:", diff)
        print("subgoals:", subgoals)


    g, inv_vertice_map, vertice_dict, edge_list = construct_graph_from_grid(pregrid)


    completed_goals = []
    start_state = [start_loc[0], start_loc[1], dir_to_num[start_dir]]
    start_xy = start_loc
    total_steps = 0
    full_path = []
    full_block_seq = []
    for i in range(len(subgoals)):
        goals_remaining = list(set(subgoals)-set(completed_goals))
        # get the subgoal with minimum distance
        dists = []
        for ele in goals_remaining:
            dists.append(abs(start_xy[0]-ele[0])+ abs(start_xy[1]-ele[1]))
        goal = goals_remaining[np.argmin(dists)]

        if verbose == 1:
            print("Next goal:", goal)

        completed_goals.append(goal)
        min_count, min_block_seq, min_path, dir = get_shortest_block_seq_to_subgoal(g, vertice_dict, inv_vertice_map, edge_list, start_state, [goal])

        if verbose == 1:
            print("Shortest Path:", min_block_seq)


        total_steps = total_steps + min_count + 1 # +1 for marker activity
        full_path.extend(min_path[1] + ['marker_act'])
        full_block_seq.extend(min_block_seq+['marker_act'])

        start_state = [goal[0], goal[1], dir]
        start_xy = goal


    ####### Add the final path to the goal state
    if verbose == 1:
        print("End state:", end_loc, end_dir)
    min_count, min_block_seq, min_path, dir = get_shortest_block_seq_to_subgoal(g, vertice_dict, inv_vertice_map, edge_list,
                                                                                start_state, [end_loc])
    if verbose == 1:
        print("Shortest Path:", min_block_seq)

    if dir != dir_to_num[end_dir]:
        key = str(dir) + str(dir_to_num[end_dir])
        add_actions = dir_dict[key]

        total_steps = total_steps + min_count + len(add_actions)
        full_path.extend(min_path[1] + ['turn'+str(k) for k in range(len(add_actions))])

        full_block_seq.extend(min_block_seq)
        full_block_seq.extend(add_actions)
    else:
        total_steps = total_steps + min_count
        full_path.extend(min_path[1])

        full_block_seq.extend(min_block_seq)

    if verbose == 1:
        print("Total steps:", total_steps)
        print("Full Path:", full_path)
        print("Full block sequence:", full_block_seq)
    total_steps += 1  # adding the additional element for RUN in the min-block seq (as code block seq also has RUN in the size count)
    if total_steps < maxnumblocks:
        return "lesser"
    elif total_steps == maxnumblocks:
        #print("Shortest path:", full_path)
        return "equal"
    else:
        #print("Shortest path:", full_path)
        return "greater"



