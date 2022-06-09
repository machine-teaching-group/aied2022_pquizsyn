import json
import numpy as np
from pandas import *
from code.step3_code2task.github_stanfordkarel.stanfordkarel.karel_world import KarelWorld as KarelWorld, Direction
from code.step3_code2task.github_stanfordkarel.stanfordkarel.karel_ascii import AsciiKarelWorld as AsciiKarelWorld

bool_conversions = {
    'bool_no_path_ahead': 'front_is_blocked()',
    'bool_no_path_right': 'right_is_blocked()',
    'bool_no_path_left': 'left_is_blocked()',
    'bool_path_ahead': 'front_is_clear()',
    'bool_path_right': 'right_is_clear()',
    'bool_path_left': 'left_is_clear()',
    'bool_marker': 'beepers_present()',
    'bool_no_marker': 'no_beepers_present()',
    #'bool_goal': 'no_beepers_present()',
    '2': '2',
    '3': '3',
    '4': '4',
    '5': '5',
    '6': '6',
    '7': '7',
    '8': '8',
    '9': '9'
}

direction_dict = {
    Direction.NORTH: "north",
    Direction.EAST: "east",
    Direction.WEST: "west",
    Direction.SOUTH: "south"
}


def get_string_from_json(json_obj: dict):
    json_string = json.dumps(json_obj)
    #print(json_string)
    arr = json_string.split(' ')
    #print(arr)
    clean_arr = []
    for ele in arr:
        if '"type"' in ele:
            continue
        elif ele == '"children":':
            clean_arr.append('children[')
        elif '"run"' in ele:
            clean_arr.append('run')
        elif '"move"' in ele:
            clean_arr.append('move()\n')
        elif '"turn_left"' in ele:
            clean_arr.append('turn_left()\n')
        elif '"turn_right"' in ele:
            clean_arr.append('turn_right()\n')
        elif '"pick_marker"' in ele:
            clean_arr.append('pick_beeper()\n')
        elif '"put_marker"' in ele:
            clean_arr.append('put_beeper()\n')
        elif '"do"' in ele:
            clean_arr.append('do')
        elif '"else"' in ele and '"ifelse"' not in ele and '"if_else"' not in ele:
            clean_arr.append('else\n')
        else:
            if '}' in ele:
                mele = ele.split('}')
                clean_arr.append(mele[0][1:-1])
            else:
                clean_arr.append(ele[1:-2])
        if ']' in ele:
            c = ele.count(']')
            for i in range(c):
                clean_arr.append(']')

    return clean_arr


def check_token_arr(arr: list):
    '''checks the token arr for incomplete program constructs,
    and adds empty children if needed'''
    new_arr = []
    flag_list = []
    count = 1
    prev = -1
    for i in range(len(arr)-1):
        ele = arr[i]
        nele = arr[i+1]
        if prev !=-1:
            pele = arr[prev]
        else:
            pele = None
        new_arr.append(ele)
        if 'run' in ele:
            if 'children[' not in nele:
                new_arr.append('children[')
                new_arr.append(']')
            # else:
            #     continue

        if 'repeat' in ele and 'repeat_until_goal' not in ele:
            cond = ele.split("(")[1][:-1]
            cond = bool_conversions[cond]
            new_arr.pop(-1)
            new_arr.append('for rparam in range('+ cond+'):\n')
            if 'children[' not in nele:
                new_arr.append('children[')
                new_arr.append(']')
            # else:
            #     continue

        if 'repeat_until_goal' in ele:
            new_arr.pop(-1)
            new_arr.append('while(no_beepers_present()):\n')
            if 'children[' not in nele:
                new_arr.append('children[')
                new_arr.append('flag_'+str(count)+"=True\n")
                flag_list.append('flag_'+str(count))
                count +=1
                new_arr.append(']')
            # else:
            #     continue

        if 'while' in ele:
            cond = ele.split("(")[1][:-1]
            cond = bool_conversions[cond]
            new_arr.pop(-1)
            new_arr.append('while('+cond+'):\n')
            if 'children[' not in nele:
                new_arr.append('children[')
                new_arr.append('flag_' + str(count) + "=True\n")
                flag_list.append('flag_' + str(count))
                count += 1
                new_arr.append(']')
            # else:
            #     continue

        if 'if' in ele:
            cond = ele.split("(")[1][:-1]
            cond = bool_conversions[cond]
            new_arr.pop(-1)
            new_arr.append('if(' + cond + '):\n')


        if 'do' in ele:
            if 'children[' not in nele:
                new_arr.append('children[')
                new_arr.append('flag_' + str(count) + "=True\n")
                flag_list.append('flag_' + str(count))
                count += 1
                new_arr.append(']')
            # else:
            #     continue

        if 'else' in ele and 'ifelse' not in ele:
            new_arr.pop(-1)
            new_arr.append('else:\n')
            if 'children[' not in nele:
                new_arr.append('children[')
                new_arr.append('flag_' + str(count) + "=True\n")
                flag_list.append('flag_' + str(count))
                count += 1
                new_arr.append(']')
            # else:
            #     continue

        if pele is not None and 'children[' in ele and 'repeat_until_goal' in pele:
            new_arr.append('flag_' + str(count) + "=True\n")
            flag_list.append('flag_' + str(count))
            count += 1

        if pele is not None and 'children[' in ele and 'while' in pele:
            new_arr.append('flag_' + str(count) + "=True\n")
            flag_list.append('flag_' + str(count))
            count += 1

        if pele is not None and 'children[' in ele and 'do' in pele:
            new_arr.append('flag_' + str(count) + "=True\n")
            flag_list.append('flag_' + str(count))
            count += 1


        if pele is not None and 'children[' in ele and ('else' in pele and 'ifelse' not in pele):
            new_arr.append('flag_' + str(count) + "=True\n")
            flag_list.append('flag_' + str(count))
            count += 1


        prev += 1 # update prev index


    if 'run' in arr[-1] or 'repeat' in arr[-1]:
        new_arr.append(arr[-1])
        new_arr.append('children[')
        new_arr.append(']')
    elif 'while' in arr[-1] \
            or 'do' in arr[-1] or 'else' in arr[-1]:
        new_arr.append(arr[-1])
        new_arr.append('children[')
        new_arr.append('flag_' + str(count) + "=True\n")
        flag_list.append('flag_' + str(count))
        count += 1
        new_arr.append(']')
    elif 'repeat_until_goal' in arr[-1]:
        new_arr.append('while(no_beepers_present()):\n')
        new_arr.append('children[')
        new_arr.append('flag_' + str(count) + "=True\n")
        flag_list.append('flag_' + str(count))
        count += 1
        new_arr.append(']')

    else:
        new_arr.append(arr[-1])


    return new_arr, flag_list


def get_code_script(t_arr: list):

    brac_arr = []
    quad_arr = []
    script = []
    space = ''

    for i, ele in enumerate(t_arr):
        if ele == 'children[':
            if 'ifelse' in t_arr[i-1] or 'if_else' in t_arr[i-1] or 'if_only' in t_arr[i-1] or 'if' in t_arr[i-1]:
                script.append('')
                brac_arr.append('')
                quad_arr.append(space)
                space = quad_arr[-1]
            else:
                script.append('\n')
                brac_arr.append(space + '\n')
                quad_arr.append(space + '\t')
                space = quad_arr[-1]
        elif ele == ']':
            brac = brac_arr.pop()
            script.append(brac)
            quad_arr.pop()
            if len(quad_arr) == 0:
                space = ''
            else:
                space = quad_arr[-1]
        elif ele == 'run':
             continue

        elif ele == 'move()\n' or ele == 'turn_left()\n' or \
                ele == 'turn_right()\n' or ele == 'pick_beeper()\n' or \
                ele == 'put_beeper()\n' or 'flag' in ele:
            script.append(space + ele)
        elif 'ifelse' in ele or 'if_else' in ele or 'if_only' in ele or 'do' in ele:
            continue
        else:
            script.append(space + ele)

    return script


def convert_json_to_python(codefile:str, folder:str, filename:str):

    # get the json dict from the codefile
    with open(codefile, 'r') as fp:
        jsondict = json.load(fp)

    # python filename
    # filename = codefile.split('/')[-1]
    # filename = filename.split('.')[0]
    filename = filename + '_input.py'

    begin_script = "from stanfordkarel import *\n" \
                   "def main():\n"
                   # "\tdef turn_right():\n" \
                   # "\t\tturn_left()\n" \
                   # "\t\tturn_left()\n" \
                   # "\t\tturn_left()\n"

    end_script = "\n\n\nif __name__ == \"__main__\":\n"\
                 "\trun_karel_program()\n"


    token_arr = get_string_from_json(jsondict)
    token_arr, flag_list = check_token_arr(token_arr)
    token_arr = get_code_script(token_arr)

    if len(flag_list) > 0:
        flag_script = '\t'
        for ele in flag_list:
            flag_script += ele
            flag_script += "=False\n"
            flag_script += "\t"
        begin_script = begin_script + flag_script

    code_script = begin_script
    for ele in token_arr:
        code_script = code_script + ele

    if len(flag_list) >0:
        flag_script = '\treturn ('
        for ele in flag_list:
            flag_script += ele
            flag_script += " and "
        flag_script += "True)\n"
    else:
        flag_script = "\treturn True"


    code_script += flag_script
    code_script = code_script + end_script

    # save the python file
    with open(folder+filename, 'w') as fp:
        fp.write("% s" % code_script)

    return code_script

def parse_task_file(task_file:str):
    with open(task_file, 'r') as f:
        data = f.read()

    task_type = data.split('\n', 1)[0].split('\t')[1]
    gridsz =  eval(data.split('\n', 2)[1].split('\t')[1])


    ## read the next gridsz lines
    if task_type == 'karel' or task_type == 'hoc':
        grid = data.split('\n', gridsz[0] + 3 + gridsz[0] + 7)
    else:
        print("Incorrect world encountered!")
        return None
        #grid = data.split('\n', gridsz[0] + 6)

    ## first line of grid
    grid_headings = grid[3].split('\t')
    if('pregrid' not in grid_headings):
        print("Task doesn't contain pregrid.")
        return None
    grid_mat = []
    for ele in grid[5:5+gridsz[0]-2]:
        row = ele.split('\t')[2:gridsz[0]]
        grid_mat.append(row)


    ## agentloc, dir
    agent_loc = eval(grid[gridsz[0] + 4].split('\t')[1])
    agent_loc = (agent_loc[0]-2, agent_loc[1]-2)
    agent_dir = grid[gridsz[0] + 5].split('\t')[1]

    ## if task-type is karel,hoc will have to return the post grid and agent loc
    if task_type == 'karel' or task_type == 'hoc':
        post_grid_title = grid[gridsz[0] + 7].split('\t')
        if('postgrid' not in post_grid_title):
            print("Task doesn't contain the postgrid")
            return None
        post_grid_mat = []
        for ele in grid[gridsz[0] + 9:9 + gridsz[0] + gridsz[0] - 2]:
            row = ele.split('\t')[2:gridsz[0]]
            post_grid_mat.append(row)

        ## final agentloc, dir
        post_agent_loc = eval(grid[gridsz[0] + 3 + gridsz[0] + 5].split('\t')[1])
        post_agent_loc = (post_agent_loc[0] - 2, post_agent_loc[1] - 2)
        post_agent_dir = grid[gridsz[0] + 3 + gridsz[0] + 6].split('\t')[1]

        gridsz = (gridsz[0] - 2, gridsz[1] - 2)
        return task_type, [agent_loc,post_agent_loc], [agent_dir,post_agent_dir] , [grid_mat, post_grid_mat], gridsz

    gridsz = (gridsz[0] - 2, gridsz[1] - 2)
    return task_type, [agent_loc], [agent_dir], [grid_mat], gridsz



def generate_world(type:str, agent_loc: tuple, agent_dir: tuple, grid_mat:tuple, gridsz:tuple):


    ### ending script
    if type == 'karel' or type == 'hoc':
        end_script = "Speed: 0.75\n" \
                     "BeeperBag: INFINITY\n"
    else:
        print("Unknown task type encountered")
        return None


    ### create the task-grid with colors
    all_grids = []
    #y_max = len(grid_mat[0])-1
    grid_start = []
    for ridx, row in enumerate(grid_mat[0]):
        for cidx, cell in enumerate(row):
            if(cell == '#'):
                grid_start.append("Wall: ("+ str(abs(cidx)+1) + "," + str(abs(gridsz[0]-ridx)) + ")\n")
            elif(cell == '.'):
                continue
            elif (cell == 'x'):
                grid_start.append("Beeper: (" + str(abs(cidx)+1) + "," + str(abs(gridsz[0]-ridx)) + "); 1\n")
            else:
                continue


    all_grids.append(grid_start)
    all_agents_pos = []
    all_agents_pos.append("Karel: ("+ str(abs(agent_loc[0][0]+1)) + "," + str(gridsz[0]-agent_loc[0][1]) + "); " + agent_dir[0] + "\n")
    # print(all_agents_pos)
    ## If task type is karel, add additional post grid code
    if type == 'karel' or type == 'hoc':
        ### create the task-grid with colors
        #y_max = len(grid_mat[1]) - 1
        grid_end = []
        for ridx, row in enumerate(grid_mat[1]):
            for cidx, cell in enumerate(row):
                if (cell == '#'):
                    grid_end.append("Wall: (" + str(abs(cidx)+1) + "," + str(abs(gridsz[0]-ridx)) + ")\n")
                elif (cell == '.'):
                    continue
                elif (cell == 'x'):
                    grid_end.append("Beeper: (" + str(abs(cidx)+1) + "," + str(abs(gridsz[0]-ridx)) + "); 1\n")
                else:
                    continue

        all_grids.append(grid_end)

        all_agents_pos.append("Karel: (" + str(abs(agent_loc[1][0]+1)) + "," + str(gridsz[0]-agent_loc[1][1]) + "); " + agent_dir[1] + "\n")
        # print(all_agents_pos)

        ### combine the whole script into start and end worlds
        script_begin = "Dimension: (" + str(gridsz[0]) + "," + str(gridsz[1]) + ")\n"
        for ele in all_grids[0]: # pregrid
            script_begin = script_begin + ele
        script_begin = script_begin + all_agents_pos[0] # pre-agent pos
        script_begin = script_begin + end_script
        script_end = "Dimension: (" + str(gridsz[0]) + "," + str(gridsz[1]) + ")\n"
        for ele in all_grids[1]: # post grid
            script_end = script_end + ele
        script_end = script_end + all_agents_pos[1] + "BeeperBag: INFINITY\n" # post-agent pos

        return script_begin, script_end


    return None



def convert_task_to_world(taskfile: str, temp_outputfolder:str):

    task_name = taskfile.split('/')
    task_name = task_name[-1]
    task_name = task_name.split('.')
    task_name = task_name[0]

    tasktype, agent_loc, agent_dir, grid_mat, gridsz = parse_task_file(taskfile)
    begin_world, end_world = generate_world(tasktype, agent_loc, agent_dir, grid_mat, gridsz)


    try:
        with open(temp_outputfolder+task_name+'_pre.w', 'w') as fp:
            fp.write(begin_world)
        begin_karel_world = KarelWorld(temp_outputfolder+task_name+'_pre.w')
        begin_ascii_world = AsciiKarelWorld(begin_karel_world, begin_karel_world.karel_start_location[1], begin_karel_world.karel_start_location[0])
        print("Beginning world:\n")
        print(begin_ascii_world)
        with open(temp_outputfolder + task_name + "_post.w", 'w') as fp:
            fp.write(end_world)
        end_karel_world = KarelWorld(temp_outputfolder + task_name + "_post.w")
        end_ascii_world = AsciiKarelWorld(end_karel_world, end_karel_world.karel_start_location[1], end_karel_world.karel_start_location[0])
        print("Ending world:\n")
        print(end_ascii_world)
        print("Worlds generated in temp/ folder.")
    except:
        print("Error in writing task into a world file")
        return None

    return (temp_outputfolder+task_name+'_pre.w', temp_outputfolder+task_name+'_post.w')

def get_dict_from_task(task_file: str):
    task_dict = {}
    task_type, agent_locs, agent_dirs, grid_mats, gridsz = parse_task_file(task_file)
    task_dict['type'] = task_type

    task_dict['pre_loc'] = agent_locs[0]
    task_dict['post_loc'] = agent_locs[1]

    task_dict['pre_dir'] = agent_dirs[0]
    task_dict['post_dir'] = agent_locs[1]

    task_dict['pregrid'] = np.array(grid_mats[0])
    task_dict['postgrid'] = np.array(grid_mats[1])

    return task_dict


def convert_world_to_grid(karel_start_world: KarelWorld, karel_end_world: KarelWorld, taskfilename: str, type: str, outputfolder:str):


    pregridworld = np.empty([karel_start_world.num_streets, karel_start_world.num_avenues], dtype=str)
    pregridworld[:] = "."
    postgridworld = np.empty([karel_end_world.num_streets, karel_end_world.num_avenues], dtype=str)
    postgridworld[:] = "."

    grid_size = (karel_start_world.num_streets + 2, karel_start_world.num_avenues + 2)

    task_file = outputfolder + taskfilename + '.txt'
    f = open(task_file, "w")
    f.write("type\t" + str(type) + "\n")
    f.write("gridsz\t" + str(grid_size) + "\n\n")
    f.write("pregrid\t")

    for i in range(1, karel_start_world.num_avenues + 3):
        f.write(str(i) + "\t")
    f.write("\n")
    f.write("1\t")
    for i in range(1, karel_start_world.num_avenues + 3):
        f.write("#\t")
    f.write("\n")

    for wall in sorted(karel_start_world.walls):
        pregridworld[karel_start_world.num_streets - wall.street, wall.avenue - 1] = "#"
        postgridworld[karel_start_world.num_streets - wall.street, wall.avenue - 1] = "#"

    for loc, count in sorted(karel_start_world.beepers.items()):
        if count == 1:
            pregridworld[karel_start_world.num_streets - loc[1], loc[0] - 1] = "x"
        elif count > 1:
            pregridworld[karel_start_world.num_streets - loc[1], loc[0] - 1] = str(count)
        else:
            continue

    for loc, count in sorted(karel_end_world.beepers.items()):
        if count == 1:
            postgridworld[karel_end_world.num_streets - loc[1], loc[0] - 1] = "x"
        elif count > 1:
            postgridworld[karel_end_world.num_streets - loc[1], loc[0] - 1] = str(count)
        else:
            continue

    ####### Store the pregrid
    j = 1
    for i in range(pregridworld.shape[0]):
        j += 1
        f.write(str(j) + "\t#\t")
        for k in range(pregridworld.shape[1]):
            f.write(pregridworld[i, k] + "\t")
        f.write("#\n")

    f.write(str(j + 1) + "\t")
    for i in range(1, karel_start_world.num_avenues + 3):
        f.write("#\t")
    f.write("\n")

    ##### Agent loc
    f.write("agentloc\t" + str((karel_start_world.karel_start_location[0] + 1, karel_start_world.num_streets - karel_start_world.karel_start_location[1] + 2)))
    f.write("\n")
    #### Agent direction
    f.write("agentdir\t" + str((direction_dict[karel_start_world.karel_start_direction])))
    f.write("\n\n")

    ####### Store the postgrid
    f.write("postgrid\t")

    for i in range(1, karel_end_world.num_avenues + 3):
        f.write(str(i) + "\t")
    f.write("\n")
    f.write("1\t")
    for i in range(1, karel_end_world.num_avenues + 3):
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
    for i in range(1, karel_end_world.num_avenues + 3):
        f.write("#\t")
    f.write("\n")

    ##### Agent loc
    f.write("agentloc\t" + str((karel_end_world.karel_start_location[0] + 1, karel_end_world.num_streets - karel_end_world.karel_start_location[1] + 2)))
    f.write("\n")
    #### Agent direction
    if type == "hoc":
        f.write("agentdir\t" + str("unknown"))
    else:
        f.write("agentdir\t" + str((direction_dict[karel_end_world.karel_start_direction])))
    f.write("\n\n")

    f.close()
