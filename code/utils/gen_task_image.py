import json
import os


MACROS = "macros_task.txt"

def get_macros(macros_file = MACROS):
    script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in
    rel_path = macros_file
    abs_file_path = os.path.join(script_dir, rel_path)
    with open(abs_file_path, 'r') as f:
        data = f.read()
    return data




def parse_task_file(task_file:str):
    with open(task_file, 'r') as f:
        data = f.read()

    task_type = data.split('\n', 1)[0].split('\t')[1]
    gridsz =  eval(data.split('\n', 2)[1].split('\t')[1])

    ## read the next gridsz lines

    if task_type == 'karel':
        grid = data.split('\n', gridsz[0] + 3 + gridsz[0] + 7)
    else:
        grid = data.split('\n', gridsz[0] + 6)

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




    ## if task-type is karel, will have to return the post grid and agent loc
    if task_type == 'karel':
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


        if task_type == 'karel':
            return task_type, [agent_loc,post_agent_loc], [agent_dir,post_agent_dir] , [grid_mat, post_grid_mat]

    return task_type, [agent_loc], [agent_dir], [grid_mat]




def gen_latex_script(type:str, agent_loc: tuple, agent_dir: tuple, grid_mat:tuple, macros_file=MACROS):
    macros = get_macros(macros_file)

    ### beginning script
    begin_script = "\n\\begin{document}\n" \
             "\\tikzset{\n" \
             "box/.style={" \
             "rectangle, draw=black, minimum size=0.25cm}" \
             "}\n" \
             "\centering\n" \
             "\\begin{tikzpicture}[\n" \
             "box/.style={rectangle,draw=black,minimum size=0.25cm" \
             "}\n]" \
             "\n%%%%% GRID\n"
    ### ending script
    if type == 'hoc':
        end_script = "\draw[draw=black, thick] (-0.15,-0.15) rectangle (2.40,2.40);\n" \
                     "\end{tikzpicture}\n" \
                     "\end{document}"
    elif type == 'karel':
        end_script = "\draw[draw=black, thick] (-0.15,-0.15) rectangle (2.40,2.40);\n" \
                     "\draw[draw=black, thick] (2.6,-0.15) rectangle (5.15,2.4);\n"\
                      "%%%%% adding the transition arrow\n"\
                    "\draw[-{Latex[scale=1.0]}] (2.4, 1.15) -- (2.6,1.15);\n"\
                     "\end{tikzpicture}\n" \
                     "\end{document}"
    else:
        print("Unknown task type encountered")
        return None


    ### create the task-grid with colors
    all_grid_colors = []
    y_max = len(grid_mat[0])-1
    grid_color = []
    goal_flag = False
    for ridx, row in enumerate(grid_mat[0]):
        for cidx, cell in enumerate(row):
            if(cell == '#'):
                grid_color.append('\\node[box, fill=gray!40] at '+str((cidx*0.25, (y_max-ridx)*0.25))+"{};\n")
            elif(cell == '.'):
                grid_color.append('\\node[box, fill=white] at ' + str((cidx * 0.25, (y_max - ridx) * 0.25)) + "{};\n")
            elif(cell == "+"):
                goal_flag = True
                goal_grid = '\\node[draw, fill=red, star, star points=5, inner sep=0pt, minimum size=6pt] at '+str((cidx * 0.25, (y_max - ridx) * 0.25))+"{};\n"
                grid_color.append(goal_grid)
            elif (cell == 'x'):
                if type == 'hoc':
                    goal_flag = True
                    goal_grid = '\\node[draw, fill=red, star, star points=5, inner sep=0pt, minimum size=6pt] at ' + str(
                        (cidx * 0.25, (y_max - ridx) * 0.25)) + "{};\n"
                    grid_color.append(goal_grid)
                else:
                    grid_color.append(
                        '\\node[box, fill=white] at ' + str((cidx * 0.25, (y_max - ridx) * 0.25)) + "{};\n")
                    grid_color.append(
                        '\\node[draw, fill=yellow, diamond, inner sep=1.75pt,minimum size=0.75pt] at' + str(
                            (cidx * 0.25, (y_max - ridx) * 0.25)) + "{};\n"
                    )
            else:
                continue

    # add the goal state sign for HOC-tasks if not added
    if type == 'hoc' and not goal_flag:
        goal_grid = '\\node[draw, fill=red, star, star points=5, inner sep=0pt, minimum size=6pt] at ' + str(
            (agent_loc[1][0] * 0.25, (y_max - agent_loc[1][1]) * 0.25)) + "{};\n"
        grid_color.append(goal_grid)

    all_grid_colors.append(grid_color)

    if agent_dir[0] == "east":
        dart_dir = 0
    elif agent_dir[0] == "north":
        dart_dir = 90
    elif agent_dir[0] == "south":
        dart_dir = -90
    else:
        dart_dir = 180

    all_agents_pos = []
    all_agents_pos.append("\\node[draw, fill=blue!50, dart, rotate="+str(dart_dir)+" ,inner sep=0.01pt, minimum size=4.4pt] at "+str((agent_loc[0][0]* 0.25, (y_max - agent_loc[0][1]) * 0.25))+"{};\n")

    ## If task type is karel, add additional post grid code
    if type == 'karel':
        postgridscript = "\n%%%%% POSTGRID\n" \
                         "[\nbox/.style={rectangle,draw=black,minimum size=0.25cm" \
                        "}\n]"
        ### create the task-grid with colors
        y_max = len(grid_mat[1]) - 1
        grid_color = []
        for ridx, row in enumerate(grid_mat[1]):
            for cidx, cell in enumerate(row):
                if (cell == '#'):
                    grid_color.append(
                        '\\node[box, fill=gray!40] at ' + str(((cidx * 0.25)+2.75, (y_max - ridx) * 0.25)) + "{};\n")
                elif (cell == '.'):
                    grid_color.append(
                        '\\node[box, fill=white] at ' + str(((cidx * 0.25)+2.75, (y_max - ridx) * 0.25)) + "{};\n")
                elif (cell == "+"):
                    goal_grid = '\\node[draw, fill=red, star, star points=5, inner sep=0pt, minimum size=6pt] at ' + str(
                        ((cidx * 0.25)+2.75, (y_max - ridx) * 0.25)) + "{};\n"
                    grid_color.append(goal_grid)
                elif (cell == 'x'):
                    grid_color.append(
                        '\\node[box, fill=white] at ' + str(((cidx * 0.25)+2.75, (y_max - ridx) * 0.25)) + "{};\n")
                    grid_color.append(
                        '\\node[draw, fill=yellow, diamond, inner sep=1.75pt,minimum size=0.75pt] at' + str(
                            ((cidx * 0.25)+2.75, (y_max - ridx) * 0.25)) + "{};\n")
                else:
                    continue

        all_grid_colors.append(grid_color)
        if agent_dir[1] == "east":
            dart_dir = 0
        elif agent_dir[1] == "north":
            dart_dir = 90
        elif agent_dir[1] == "south":
            dart_dir = -90
        else:
            dart_dir = 180

        all_agents_pos.append("\\node[draw, fill=blue!50, dart, rotate=" + str(
            dart_dir) + " ,inner sep=0.01pt, minimum size=4.4pt] at " + str(
            ((agent_loc[1][0] * 0.25)+2.75, (y_max - agent_loc[1][1]) * 0.25)) + "{};\n")


        ### combine the whole script
        script = macros + begin_script
        for ele in all_grid_colors[0]: # pregrid
            script = script + ele
        script = script + all_agents_pos[0] # pre-agent pos
        for ele in all_grid_colors[1]: # post grid
            script = script + ele
        script = script + all_agents_pos[1] + end_script # post-agent pos
        return script



    ### combine the whole script
    script = macros+ begin_script
    for ele in all_grid_colors[0]:
        script = script + ele
    script = script + all_agents_pos[0] + end_script

    return script

def gen_task_script(task_file, macros_file = MACROS):

    type, loc, dir, mat = parse_task_file(task_file)
    script = gen_latex_script(type, loc, dir, mat, macros_file)

    return script


def get_task_image(taskfile:str, taskfolder:str, taskimg: str):

    task_script = gen_task_script(taskfile)
    with open(taskfolder + '/' + taskimg + '.tex', 'w') as fp:
        fp.write("%s" % task_script)

    # generate the image file
    input_path = taskfolder + '/' + taskimg + '.tex'
    os_cmd = "pdflatex -interaction=nonstopmode -output-directory " +  taskfolder + " %s"
    os.system(os_cmd % (input_path))
    output_path = taskfolder + "/" + taskimg + '.jpg'
    os_cmd = "convert -density 1200 -quality 100 " + taskfolder + "/" + taskimg + ".pdf %s"
    os.system(os_cmd % (output_path))

    print("Generated task image")
    return 0


