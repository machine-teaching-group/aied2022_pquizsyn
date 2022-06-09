import random
import json
import os
import copy
from code.step2_struct2code.get_concrete_code_for_minimal_code import CodeGen_from_minimal_code
from code.utils.ast import ASTNode, get_max_block_size, json_to_ast, ast_to_json
from code.step2_struct2code.sym_ast import convert_to_json, add_if_else_node, AST, tree_edit_distance_symast, get_hash_code_of_symast, get_size_of_symast
from code.step2_struct2code.minimal_code_to_symcode import GenerateSymASTfromCode
from code.step3_code2task.run_random import run_random_with_quality_only, run_random_with_quality_only_no_shortcut
from code.step3_code2task.utils.parser import convert_json_to_python
from code.step2_struct2code.delta_debugging import get_delta_debugged_validity
from code.step4_intervention.config import DATA_TEMP



def get_set_with_distance_to_sol_code(progs:list, solution_code:AST):
    all_progs = []
    for p in progs:
        d = tree_edit_distance_symast(p, solution_code)
        all_progs.append([p, d])
        # group them by size
    sorted_codes = sorted(all_progs, key=lambda x: x[1], reverse=True)
    final_codes = [c[0] for c in sorted_codes]

    return final_codes



def quick_run_task_gen(type:str, code_set:list, temp_folder=DATA_TEMP, verbose=False):
    '''

    :param type:
    :param code_set:
    :param verbose:
    :return: Given a list of codes (AST), runs task synthesis for 1000 iters for each and returns flag
    '''
    task_iters = 1000
    mask_list = []
    for code in code_set:
        json_code = code[0].to_json()
        with open(temp_folder + 'quick_run_code.json', 'w') as fp:
            json.dump(json_code, fp, indent=4)
        jsoncodefilename = temp_folder + 'quick_run_code.json'
        pythonfilename = 'quick_run_code'
        _ = convert_json_to_python(jsoncodefilename, temp_folder, pythonfilename)
        python_code_file = temp_folder + pythonfilename + '_input.py'
        # cond-flag
        if code[0]._n_if > 0 or code[0]._n_while > 0 or code[0]._n_else > 0 or code[0]._n_repeat_until_goal > 0:
            cond_flag = True
        else:
            cond_flag = False
            task_iters = 60
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

        task, start_karel_world, end_karel_world, task_score = run_random_with_quality_only_no_shortcut(type, task_iters,
                                                                                            python_code_file,
                                                                                            jsoncodefilename,
                                                                                            task_dims,
                                                                                            quality_score_thresh=0)
        if task is None:
            mask_list.append(False)
        else:
            mask_list.append(True)


    return mask_list



def get_all_codes_for_task_generation(type:str, minimal_code:ASTNode, max_blk_size:int, solution_code:AST, bucket_sample_size=3, delta_debugging_sample_size=50, output_folder= DATA_TEMP,verbose=False):

    all_codes = []
    symcode_obj = GenerateSymASTfromCode(minimal_code, max_blk_size, type=type)
    symcode = symcode_obj.sym_code
    max_size = solution_code._size + 2 * max_blk_size
    if verbose:
        print("SymCode:", symcode)
        print("Max size:", max_size)

    codes = CodeGen_from_minimal_code(symcode, max_size, minimal_code, solution_code, additional_vars=symcode_obj.additional_actions, type=type, verbose=verbose)
    all_codes.extend(codes)
    all_codes = [ele[0] for ele in all_codes]
    all_codes = list(set(all_codes))
    all_codes = [[ele, get_size_of_symast(ele)]  for ele in all_codes]
    print("Total number of codes generated purely based on code constraints:", len(all_codes))

    # print the size buckets
    codes_by_size = {}
    size_bucket_without_cons = {}
    for ele in all_codes:
        if ele[1] not in codes_by_size.keys():
            codes_by_size[ele[1]] = [ele[0]]
        else:
            codes_by_size[ele[1]].append(ele[0])
    for key,value in codes_by_size.items():
        size_bucket_without_cons[key] = len(value)
    print("Total number of codes generated purely based on code constraints:", size_bucket_without_cons)


    # First filtering to eliminate obvious bad codes
    if not os.path.exists(output_folder + 'temp_misc/'):
        os.makedirs(output_folder + 'temp_misc/')
    mask_1 = quick_run_task_gen(type, all_codes, temp_folder=output_folder+'temp_misc/')
    # filtered codes
    filtered_codes_1 = [all_codes[i] for i in range(len(all_codes)) if mask_1[i]]


    # sort the codes into the buckets (by size)
    filtered_codes_1 = [ele[0] for ele in filtered_codes_1]
    filtered_codes_1 = list(set(filtered_codes_1)) # remove repeated codes if-any
    print("Filtered codes after quick task generation:", len(filtered_codes_1))
    filtered_codes_1 = [[ele, get_size_of_symast(ele)]  for ele in filtered_codes_1]
    filtered_codes_1 = sorted(filtered_codes_1, key=lambda x: x[1])
    if len(filtered_codes_1) == 0 or filtered_codes_1 is None:
        assert "No valid codes generated!"
        return None, 0

    grouped_codes = {}
    for c, s in filtered_codes_1:
        grouped_codes.setdefault(s, []).append((c))
    code_counts = {}
    for key in grouped_codes.keys():
        code_counts[key] = len(grouped_codes[key])

    print("Filtered codes after quick task generation:", code_counts)


    ## sampled codes for delta debugging and full task-generation
    sampled_codes = []
    bucket_counts = 1
    total_codes = 0
    for key, value in grouped_codes.items():
        if bucket_counts > 3:
            break
        code_list = copy.deepcopy(value)
        sampled_list = random.sample(code_list, min(len(code_list), delta_debugging_sample_size))
        sampled_codes.extend(sampled_list)
        bucket_counts += 1
        total_codes += len(sampled_list)

    print("Number of codes sampled for task-generation:", len(sampled_codes))
    # print the distribution of sampled codes
    code_size = [[c, c._size] for c in sampled_codes]
    size_bucket_sampled = {}
    codes_by_size_sampled = {}
    for ele in code_size:
        if ele[1] not in codes_by_size_sampled.keys():
            codes_by_size_sampled[ele[1]] = [ele[0]]
        else:
            codes_by_size_sampled[ele[1]].append(ele[0])
    for key, val in codes_by_size_sampled.items():
        size_bucket_sampled[key] = len(val)
    print("Number of codes sampled for task-generation:", size_bucket_sampled)

    return sampled_codes, total_codes




def generate_tasks_for_code_set(type, code_set:list, solution_code:AST, output_folder=DATA_TEMP):
    mask_2 = []
    filtered_list = []
    n = 1
    for c in code_set:
        # get the task dimensions
        if c._n_if > 0 or c._n_while > 0 or c._n_else > 0 or c._n_repeat_until_goal > 0:
            cond_flag = True
            task_iters = 20000
            if type != 'hoc': # for karel tasks lowering quality
                qual_thresh = 0.1 # changed to 0.1 for Task-4 (repeat(if)--Karel E)
            else:
                qual_thresh = 0.2
        else:
            cond_flag = False
            task_iters = 30
            qual_thresh = 0

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

        ## create the temp folder
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        jsoncodefilename = output_folder + 'code_run_' + str(n) + '.json'
        curr_code = add_if_else_node(c)
        jsoncode = convert_to_json(curr_code, type)
        with open(jsoncodefilename, 'w') as f:  # json code file
            json.dump(jsoncode, f, indent=4)
        pythonfilename = 'code_run_' + str(n)
        _ = convert_json_to_python(jsoncodefilename, output_folder, pythonfilename)
        python_code_file = output_folder + pythonfilename + '_input.py'
        # generate the task

        task, start_karel_world, end_karel_world, task_score = run_random_with_quality_only(type, task_iters, python_code_file,
                                                                                                jsoncodefilename,
                                                                                                task_dims,
                                                                                               quality_score_thresh=qual_thresh)

        n += 1
        if task is None:
            mask_2.append(False)
        else:
            mask_2.append(True)
            filtered_list.append([c, c._size, task, start_karel_world, end_karel_world, tree_edit_distance_symast(c, solution_code)])
            # print("Task for code:", c, task.karel)


    return mask_2, filtered_list




def wrapper_get_all_codes_for_task_generation(mcode:ASTNode, solution_code_ast:AST, max_blk_size:int, bucket_sample_size=3, delta_debugging_sample_size=50, output_folder='', type='hoc', verbose=False):


    # get all the codes from the minimal code, and first layer of filtering
    all_codes, num_codes = get_all_codes_for_task_generation(type, mcode, max_blk_size, solution_code_ast, bucket_sample_size=bucket_sample_size, delta_debugging_sample_size=delta_debugging_sample_size, output_folder=output_folder,verbose=verbose)
    # run the second layer of filtering: mask_2 is applied to all_codes to get filtered_codes
    mask_2, filtered_list = generate_tasks_for_code_set(type, all_codes, solution_code_ast, output_folder=output_folder+'temp_misc/')
    print("Sampled codes for task-generation after shortcut:", len(filtered_list))



    # print by size bucket: [c, c._size, task, start_karel_world, end_karel_world, tree_edit_distance_symast(c, solution_code)]
    size_bucket_after_shortcut= {}
    codes_by_size_after_shortcut = {}
    for ele in filtered_list:
        if ele[1] not in codes_by_size_after_shortcut.keys():
            codes_by_size_after_shortcut[ele[1]] = [ele[0]]
        else:
            codes_by_size_after_shortcut[ele[1]].append(ele[0])
    for key, value in codes_by_size_after_shortcut.items():
        size_bucket_after_shortcut[key] = len(value)
    print("Sampled codes for task-generation after shortcut:", size_bucket_after_shortcut)


    # run delta_debugging on the final list of codes: mask_3 is apllied to filtered_List
    mask_3 = [get_delta_debugged_validity(type, c[0], c[3], c[4], temp_folder=output_folder+'temp_misc/') for c in filtered_list]
    final_list_of_task_codes = [[filtered_list[i][0], filtered_list[i][1], filtered_list[i][2], filtered_list[i][3],
                                 filtered_list[i][4], filtered_list[i][5]] for i in range(len(filtered_list)) if mask_3[i]]
    print("Final list of codes, after delta debugging pruning:", len(final_list_of_task_codes))

    # print by size bucket: [c, c._size, task, start_karel_world, end_karel_world, tree_edit_distance_symast(c, solution_code)]
    size_bucket_after_delta_debugging = {}
    codes_by_size = {}
    for ele in final_list_of_task_codes:
        if ele[1] not in codes_by_size.keys():
            codes_by_size[ele[1]] = [ele[0]]
        else:
            codes_by_size[ele[1]].append(ele[0])
    for key,value in codes_by_size.items():
        size_bucket_after_delta_debugging[key] = len(value)
    print("Final list of codes, after delta debugging pruning:", size_bucket_after_delta_debugging)


    print("Sampled codes for task-generation after shortcut (before delta-debugging):", len(filtered_list))
    if final_list_of_task_codes is None or len(final_list_of_task_codes) == 0:
        print("No valid codes generated!")
        # print(mcode)
        return None, 0

    return final_list_of_task_codes, len(final_list_of_task_codes)


def save_task_code_pair(type:str, final_code:AST, final_task, final_start_world, final_end_world,
                        data_output:str, output_codename:str, output_taskname:str, code_num,
                        final_code_size_flag=True, demo_file=False):

    if final_code is not None and final_task is not None:
        final_code = add_if_else_node(final_code)
        # get the size of the final code
        final_code_size = get_size_of_symast(final_code)
        final_jsoncode = convert_to_json(final_code, type)
        if not final_code_size_flag:
            final_code_size =''
        # save the json code file

        # create the output folder if it doesn't exist
        if not os.path.exists(data_output):
            os.makedirs(data_output)
        codefilename = data_output + output_codename
        if final_code_size != '':
            codefilename = codefilename + '-' + str(final_code_size)
        if code_num != '':
            codefilename = codefilename + '-' + str(code_num)
        if not demo_file:
            codefilename = codefilename + '_code.json'
        else:
            codefilename = codefilename + '.json'

        with open(codefilename, 'w') as f:  # json code file
            json.dump(final_jsoncode, f, indent=4)
        taskname = output_taskname
        if final_code_size != '':
            taskname = taskname + '-' + str(final_code_size)
        if code_num != '':
            taskname = taskname + '-' + str(code_num)
        if not demo_file:
            taskname = taskname + '_task.txt'
        else:
            taskname = taskname + '.txt'
        # save the task text file
        final_task.karel.save_task_grid_to_file(final_start_world, final_end_world,
                                                final_end_world.karel_start_location,
                                                final_end_world.karel_start_direction,
                                                data_output,
                                                taskname)



    else:  # save the text files saying no valid task-code pair generated.
        # create the output folder if it doesn't exist
        print("Invalid task, code pair generated!---", final_code)
        if not os.path.exists(data_output):
            os.makedirs(data_output)

        if final_code is None:
            final_code_size = 0
            codefilename = data_output + output_codename
            if final_code_size != '':
                codefilename = codefilename + '-' + str(final_code_size)
            if code_num != '':
                codefilename = codefilename + '-' + str(code_num)
            if not demo_file:
                codefilename = codefilename + '_code.json'
            else:
                codefilename = codefilename + '.json'

            with open(codefilename, 'w') as f:  # json code file
                f.write('No valid task-code pair generated.')
                f.close()
        else:
            final_code = add_if_else_node(final_code)
            final_code_size = get_size_of_symast(final_code)
            final_jsoncode = convert_to_json(final_code, type)
            codefilename = data_output + output_codename
            if final_code_size != '':
                codefilename = codefilename + '-' + str(final_code_size)
            if code_num != '':
                codefilename = codefilename + '-' + str(code_num)
            if not demo_file:
                codefilename = codefilename + '_code.json'
            else:
                codefilename = codefilename + '.json'

            with open(codefilename, 'w') as f:
                json.dump(final_jsoncode, f, indent=4)

        if final_task is None:
            taskfilename = data_output + output_taskname
            if final_code_size != '':
                taskfilename = taskfilename + '-' + str(final_code_size)
            if code_num != '':
                taskfilename = taskfilename + '-' + str(code_num)
            if not demo_file:
                taskfilename = taskfilename + '_task.txt'
            else:
                taskfilename = taskfilename + '.txt'

            with open(taskfilename, 'w') as f:  # json code file
                f.write('No valid task generated.')
                f.close()

    return 0



def get_task_code_pair_from_minimal_code(type:str, task_id:int, mincode:ASTNode, max_blk_size:int, solution_code_ast:AST, bucket_sample_size=3, delta_debugging_sample_size=50, output_folder = '', verbose=False):
    all_codes, num_codes = wrapper_get_all_codes_for_task_generation(mincode, solution_code_ast,
                                                                     max_blk_size,
                                                                     bucket_sample_size=bucket_sample_size,
                                                                     delta_debugging_sample_size=delta_debugging_sample_size,
                                                                     output_folder=output_folder, type=type,
                                                                     verbose=verbose)

    if all_codes is None:
        print("No valid codes generated!")
        return None, None

    # save all the task-code pairs in this set
    # sort this set based on distance and distance to solution code
    sorted_codes = sorted(all_codes, key=lambda x: x[1])

    # task_id to alphabet dictionary
    task_id_to_str = {
        '0': 'D',
        '1': 'G',
        '2': 'H',
        '3': 'I',
        '4': 'E',
        '5': 'J',
        '6': 'F'
    }

    grouped_codes = {}
    for ele in sorted_codes:
        if ele[1] in grouped_codes.keys():
            grouped_codes[ele[1]].append(ele)
        else:
            grouped_codes[ele[1]] = [ele]

    # check that we have exactly 3 buckets in the sorted code list
    print("Number of size buckets:", len(grouped_codes))
    # sort each list based on distance to solution code
    sorted_codes_by_ast_dist = []
    sorted_dict = {}
    indices = []
    sizes = []
    start_id = 1
    for key, val in grouped_codes.items():
        # val_copy = copy.deepcopy(val)
        codes = sorted(val,key=lambda x: x[5], reverse=True)
        sorted_dict[key] = codes
        sorted_codes_by_ast_dist.extend(codes)
        sizes.append(len(codes))
        indices.append([start_id, start_id+len(codes)])
        start_id = start_id + len(codes)

    print("Double check the number of task-codes generated:", len(sorted_codes_by_ast_dist))

    # save all the valid task-code pairs
    for key,value in grouped_codes.items():
        codes = sorted(value,key=lambda x: x[5], reverse=True)
        code_num = 1
        # save the task-code file
        for ele in codes:
            if type == 'hoc':
                taskname = 'out-pquizs-in-hoc-' + task_id_to_str[str(task_id)]
                codename = 'out-pquizs-in-hoc-' + task_id_to_str[str(task_id)]
            else:
                taskname = 'out-pquizs-in-karel-' + task_id_to_str[str(task_id)]
                codename = 'out-pquizs-in-karel-' + task_id_to_str[str(task_id)]
            _ = save_task_code_pair(type, ele[0], ele[2], ele[3],ele[4], output_folder, codename, taskname, code_num)
            code_num += 1

    # obtain the bucketed list for display (3 from each size bucket)
    display_codes = []
    i = 0
    for key, val in sorted_dict.items():
        codes = val
        ids = list(range(indices[i][0], indices[i][1]))
        if len(codes) < bucket_sample_size:
            ids_ = copy.deepcopy(ids)
            while len(ids_) < bucket_sample_size:
                j = random.sample(ids, 1)
                ids_.extend(j)
        else:
            ids_ = ids[:bucket_sample_size]

        display_codes.extend(ids_)
        i = i+1

    # print(sizes)
    # print(indices)
    # print(display_codes)
    # exit(0)


    return len(sorted_codes_by_ast_dist), display_codes



def get_single_task_code_pair_from_minimal_code(type:str, task_id:int, mincode:ASTNode, max_blk_size:int, solution_code_ast:AST, bucket_sample_size=3, delta_debugging_sample_size=50, output_folder = '', verbose=False):

    all_codes, num_codes = wrapper_get_all_codes_for_task_generation(mincode, solution_code_ast,
                                                                     max_blk_size,
                                                                     bucket_sample_size=bucket_sample_size,
                                                                     delta_debugging_sample_size=delta_debugging_sample_size,
                                                                     output_folder=output_folder, type=type,
                                                                     verbose=verbose)
    max_counter = 100
    while all_codes is None and max_counter >0:
        print("No valid codes generated! -- sampling again")
        all_codes, num_codes = wrapper_get_all_codes_for_task_generation(mincode, solution_code_ast,
                                                                         max_blk_size,
                                                                         bucket_sample_size=bucket_sample_size,
                                                                         delta_debugging_sample_size=delta_debugging_sample_size,
                                                                         output_folder=output_folder, type=type, verbose=verbose)


        max_counter-= 1
        if max_counter <= 0:
            print("No valid codes generated in 100 samples! Exiting process...")
            return None, None


    # save all the task-code pairs in this set
    # sort this set based on distance and distance to solution code
    sorted_codes = sorted(all_codes, key=lambda x: x[1])

    # task_id to alphabet dictionary
    task_id_to_str = {
        '0': 'D',
        '1': 'G',
        '2': 'H',
        '3': 'I',
        '4': 'E',
        '5': 'J',
        '6': 'F'
    }

    grouped_codes = {}
    for ele in sorted_codes:
        if ele[1] in grouped_codes.keys():
            grouped_codes[ele[1]].append(ele)
        else:
            grouped_codes[ele[1]] = [ele]

    # check that we have exactly 3 buckets in the sorted code list
    print("Number of size buckets:", len(grouped_codes))
    # sort each list based on distance to solution code
    sorted_codes_by_ast_dist = []
    sorted_dict = {}
    indices = []
    sizes = []
    start_id = 1
    for key, val in grouped_codes.items():
        # val_copy = copy.deepcopy(val)
        codes = sorted(val,key=lambda x: x[5], reverse=True)
        sorted_dict[key] = codes
        sorted_codes_by_ast_dist.extend(codes)
        sizes.append(len(codes))
        indices.append([start_id, start_id+len(codes)])
        start_id = start_id + len(codes)

    # print("Double check the number of task-codes generated:", len(sorted_codes_by_ast_dist))
    # randomly pick one of the obtained task-code pairs
    final_task_code_pair = random.choice(sorted_codes_by_ast_dist)
    # save the task-code pair
    taskname = 'task_Tquiz'
    codename = 'code_Cquiz'
    _ = save_task_code_pair(type, final_task_code_pair[0], final_task_code_pair[2], final_task_code_pair[3],
                            final_task_code_pair[4],
                            output_folder, codename, taskname, '',
                            final_code_size_flag=False, demo_file=True)



    return len(sorted_codes_by_ast_dist)


