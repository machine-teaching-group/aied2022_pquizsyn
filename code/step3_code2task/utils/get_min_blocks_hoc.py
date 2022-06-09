import networkx as nx
import csv
import numpy as np
from code.step3_code2task.github_stanfordkarel.stanfordkarel.karel_world import KarelWorld, Direction, Wall

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






def read_grid_from_file(filename):
    '''

    :param filename: name of grid file
    :return: task_type, gridsz, start loc, direction, end loc, grid_blocks
    '''

    tsv_file = open(filename)
    read_tsv = csv.reader(tsv_file, delimiter="\t") # saves each row as a list
    end = []
    for row in read_tsv:
        if 'type' in row:
            task_type = row[1] # specific to tsv file format
        if 'gridsz' in row:
            gridsize = eval(row[1])
        if 'agentloc' in row:
            start = eval(row[1])
            start = (start[1]-1, start[0]-1)
        if 'agentdir' in row:
            direction = row[1]
        if 'pregrid' in row:
            if row[-1] != str(gridsize[0]):
                print("Check the grid specs.")
                return -1
            mat = np.zeros((int(row[-1]), int(row[-1])), dtype = np.int64)
        if '+' in row:
            y_coord = int(row[0])
            x_coord = row.index('+')
            mat[y_coord-1, x_coord-1] = 2
            end.append((y_coord-1, x_coord-1))

        if '#' in row:
            y_coord = int(row[0])
            for i in range(1,len(row)):
                if row[i] == "#":
                    mat[y_coord-1, i-1] = 1
                if row[i] == "+":
                    mat[y_coord-1, i-1] = 2 # 2 is the symbol of goal

    return task_type, gridsize, start, direction, end, mat


def get_neighbors(x_coord, y_coord, direction, grid, gridsize = 12):

    neighbors = []
    if grid[x_coord, y_coord] == 1:
        return neighbors
    if direction == 1: # east
        dx = 0
        dy = 1
    if direction == 2: # south
        dx = 1
        dy = 0
    if direction == 3: # west
        dx = 0
        dy = -1
    if direction == 4: # north
        dx = -1
        dy = 0
    else:
        assert "Invalid direction encountered"


    for i in range(1,5): # add all the directions in the same loc
        if i == direction:
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
        neighbors.append([new_x_coord, new_y_coord, direction])
        return neighbors


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
        all_shortest_paths.append(shortest_blocks)

    return all_shortest_paths


def get_turns_to_next_loc(init_loc, next_loc):

    action = []
    if init_loc[0] == next_loc[0] and init_loc[1] == next_loc[1]:
       dir_pair = str(init_loc[2]) + str(next_loc[2])
       action.extend(dir_dict[dir_pair])
    else:
        action.append('move')

    return action


def get_blocks_from_path(path):
    blocks = []
    for i in range(len(path)-1):
        state = eval(path[i])
        state = [int(ele) for ele in state]
        next_state = eval(path[i+1])
        next_state = [int(ele) for ele in next_state]

        blocks.extend(get_turns_to_next_loc(state, next_state))

    return blocks



def get_grid_mat(karelworld_start: KarelWorld, karelworld_end: KarelWorld):

    gridsize_start = (karelworld_start.num_avenues, karelworld_start.num_streets)

    karelstart = [gridsize_start[1]-karelworld_start.karel_start_location[1], karelworld_start.karel_start_location[0]-1]
    karelstart_dir = karelworld_start.karel_start_direction

    gridsize_end = (karelworld_end.num_avenues, karelworld_end.num_streets)
    karelend = [gridsize_end[1]- karelworld_end.karel_start_location[1], karelworld_end.karel_start_location[0]-1]


    if gridsize_start != gridsize_end:
        assert "Check the dimensions of the start and end worlds!"
        return -1



    mat_pregrid = np.zeros((gridsize_start[0], gridsize_start[1]), dtype=np.int64)



    for ele, value in karelworld_start.beepers.items():
        if value>0:
            mat_pregrid[gridsize_start[1]-ele[1], ele[0]-1] = 2 #goal state

    # mat_pregrid[karelend[0], karelend[1]] = 2
    for ele in karelworld_start.walls:
            mat_pregrid[abs(gridsize_start[1]-ele.street), ele.avenue-1] = 1

    task_type = 'hoc'
    return task_type, gridsize_start, karelstart, karelstart_dir, [karelend], mat_pregrid




def prune_using_shortest_path_hoc(start_karel_world, end_karel_world, maxnumblocks, verbose = 0):
    # task_type, sz, start, direction, end, grid = read_grid_from_file(taskfilepath)
    task_type, sz, start, direction, end, grid = get_grid_mat(start_karel_world, end_karel_world)
    if verbose == 1:
        if task_type != 'hoc':
            assert "Invalid program task_type encountered."
            return False
        print("sz:", sz)
        print("start:", start)
        print("direction:", direction)
        print("end:", end)
        print("grid:", grid)
        exit(0)

    g, inv_vertice_map, vertice_dict, edge_list = construct_graph_from_grid(grid)
    start_state = [start[0], start[1], dir_to_num[direction]]
    all_shortest_paths = {}
    for ele in end:
        all_shortest_paths[str(ele)] = get_shortest_path(g, start_state, ele, vertice_dict, inv_vertice_map)
    #block_paths = []
    min_count = np.inf
    min_block_seq = []
    min_path = []
    for ele in end:
        for path in all_shortest_paths[str(ele)]:
            blocks = get_blocks_from_path(path)
            if len(blocks) < min_count:
                min_count = len(blocks)
                min_block_seq = blocks
                min_path = path
    min_count += 1 # adding the additional element for RUN in the min-block seq (as code block seq also has RUN in the size count)
    if verbose == 1:
        print("Number of blocks:", min_count)
        print("Path:", min_block_seq)
        print("Node seq:", min_path)

    if min_count < maxnumblocks:
        return "lesser"
    elif min_count == maxnumblocks:
        return "equal"
    else:
        return "greater"
