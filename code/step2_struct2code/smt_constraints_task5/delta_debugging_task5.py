import json
import copy
import collections
import os
from step4_intervention.config import DATA_TEMP
from step3_code2task.stanford_based.full_code.code.utils.parser import convert_json_to_python
from utils.ast import ASTNode, valid_ASTNode, get_hash_code_of_ast
from step3_code2task.stanford_based.full_code.code.utils.run_testcases import solves_karel_task
from step3_code2task.stanford_based.full_code.code.run_random import run_random_with_quality_only


def run_delta_set_on_task(type:str, code:ASTNode, start_karel_world, end_karel_world, temp_folder=DATA_TEMP):
    '''

    :param type:
    :param code:
    :param start_karel_world:
    :param end_karel_world:
    :param temp_folder:
    :return: False --> if code solves task, True --> if code does not solve task
    '''
    # get the python code file from the code
    json_code = code.to_json()
    with open(temp_folder + 'delta_code.json', 'w') as fp:
        json.dump(json_code, fp, indent=4)
    jsoncodefilename = temp_folder + 'delta_code.json'
    pythonfilename =  'delta_code'
    _ = convert_json_to_python(jsoncodefilename, temp_folder, pythonfilename)
    python_code_file = temp_folder + pythonfilename + '_input.py'

    ### get the .w files for the start/end karel worlds
    start_karel_world.save_to_file(os.path.join(temp_folder, "start_world.w"))
    start_task_file = temp_folder + 'start_world.w'
    end_karel_world.save_to_file(os.path.join(temp_folder, "end_world.w"))
    end_task_file = temp_folder + 'end_world.w'

    # check if code solves the task
    solved_flag = solves_karel_task(python_code_file, start_task_file, end_task_file, type=type)

    # print("Code solves task:", code, solved_flag)
    return not solved_flag





# temporary routine to validate the delta debugging routine
def get_tasks_for_code(type:str, code:ASTNode, temp_folder = DATA_TEMP, task_iters=10000):
    # get the json code file, python code file
    json_code = code.to_json()
    with open(temp_folder + 'test_code.json', 'w') as fp:
        json.dump(json_code, fp, indent=4)
    jsoncodefilename = temp_folder + 'test_code.json'
    pythonfilename = 'test_code'
    _ = convert_json_to_python(jsoncodefilename, temp_folder, pythonfilename)
    python_code_file = temp_folder + pythonfilename + '_input.py'

    # cond-flag
    if code._n_if_only > 0 or code._n_while > 0 or code._n_if_else > 0 or code._n_repeat_until > 0:
        cond_flag = True
    else:
        cond_flag = False


    # TASK-DIM
    task_dims = {
        'type': type,
        'num_streets': 10,
        'num_avenues': 10,
        'random_init': True,
        'cond_flag': cond_flag,
        'init_loc_flag': True,
        'ref_task': {},
        'ref_task_file': ''
    }

    task, start_karel_world, end_karel_world, task_score = run_random_with_quality_only(type, task_iters,
                                                                                         python_code_file,
                                                                                         jsoncodefilename,
                                                                                         task_dims,
                                                                                         quality_score_thresh=0)
    if task is None:
        return None, None, None, 0
    else:
        return task, start_karel_world, end_karel_world, task_score



def remove_single_node_from_ast(root:ASTNode):

    new_ast_nodes = []
    queue = collections.deque([root])
    while len(queue):
        for i in range(len(queue)):
            node = queue.popleft()
            node_children = [child._type for child in node._children]
            if 'move' or 'turn_left' or 'turn_right' or 'put_marker' or 'pick_marker' in node_children:
                if len(node_children)>1:
                    indices = [i for i, x in enumerate(node_children) if x == "move"]
                    indices.extend([i for i, x in enumerate(node_children) if x == "turn_left"])
                    indices.extend([i for i, x in enumerate(node_children) if x == "turn_right"])
                    indices.extend([i for i, x in enumerate(node_children) if x == "put_marker"])
                    indices.extend([i for i, x in enumerate(node_children) if x == "pick_marker"])

                    if len(indices) != 0:
                        for i in indices:
                            c = node._children.pop(i)
                            new_node = copy.deepcopy(root)
                            new_node._hash = get_hash_code_of_ast(new_node)
                            new_ast_nodes.append(new_node)
                            node._children.insert(i, c)


            for child in node._children:
                queue.append(child)

    return new_ast_nodes


def get_delta_codes(code:ASTNode):
    delta_set = list(set(remove_single_node_from_ast(code)))
    # remove the invalid nodes
    delta_set = [ele for ele in delta_set if valid_ASTNode(ele)]
    delta_set = list(set(delta_set))

    return delta_set


def get_delta_debugged_validity(type:str, code:ASTNode, start_task, end_task, temp_folder=DATA_TEMP):
    '''

    :param type:
    :param code:
    :param start_task:
    :param end_task:
    :return: True --> if code valid, False --> if code is invalid
    '''
    delta_set = get_delta_codes(code)
    mask_list = []
    for ele in delta_set:
        d_flag = run_delta_set_on_task(type, ele, start_task, end_task, temp_folder=temp_folder)
        mask_list.append(d_flag)


    # print(mask_list)
    '''if delta-set is empty then, all([]) always returns True.'''
    return all(mask_list)


