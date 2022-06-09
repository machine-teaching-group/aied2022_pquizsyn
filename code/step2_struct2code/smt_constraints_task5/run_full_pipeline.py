import random
import json
import argparse
import os
import matplotlib.pyplot as plt
import time
import copy
from code.step3_code2task.run_random import run_random_with_quality_only, run_random_with_quality_only_no_shortcut
from code.step3_code2task.utils.parser import convert_json_to_python
from code.step2_struct2code.smt_constraints_task5.delta_debugging_task5 import get_delta_debugged_validity
from code.utils.ast import ASTNode, json_to_ast, ast_to_json, get_size, tree_edit_distance, valid_ASTNode


DATA_INPUT_FOLDER = 'data/output/task-5/substructure-2/all-mutations/'
DATA_OUTPUT_FOLDER = 'data/output/task-5/substructure-2/'
TYPE = 'karel'
CODE_BUCKETS = {
    "9": list(range(1,16)),
    "10_1": list(range(1,221)),
    "10_2": list(range(221, 341)),
    "10_3": list(range(341,509)),
    "11_1": list(range(1, 201)),
    "11_2": list(range(201, 401)),
    "11_3": list(range(401, 601)),
    "11_4": list(range(601, 801)),
    "11_5": list(range(801, 1193))
}


def get_solution_code_AST():
    code = ASTNode('run', None, [
        ASTNode('while', 'bool_no_path_ahead', [
            ASTNode('if', 'bool_marker', [
                ASTNode('do', 'bool_marker', [ASTNode('pick_marker')])
            ]),
            ASTNode('turn_left'), ASTNode('move'), ASTNode('turn_right'), ASTNode('move')
        ]),
        ASTNode('pick_marker')
    ])

    return code, code._size

def get_codes_from_bucket(bucket_id:str):
    code_set = []
    code_prefix = "code_mutation_"
    if bucket_id == "9":
        codename = code_prefix + str(9) + "_"
        for ele in CODE_BUCKETS[bucket_id]:
            final_codename = codename + str(ele)+'.json'
            with open(DATA_INPUT_FOLDER + final_codename, 'r') as fp:
                code_dict = json.load(fp)
                code_astnode = json_to_ast(code_dict)
                code_set.append([code_astnode, code_astnode._size])

        return code_set, len(code_set)

    elif bucket_id == "10_1" or bucket_id == "10_2" or bucket_id == "10_3":
        codename = code_prefix + str(10) + "_"
        for ele in CODE_BUCKETS[bucket_id]:
            final_codename = codename + str(ele) + '.json'
            with open(DATA_INPUT_FOLDER + final_codename, 'r') as fp:
                code_dict = json.load(fp)
                code_astnode = json_to_ast(code_dict)
                code_set.append([code_astnode, code_astnode._size])

        return code_set, len(code_set)

    elif bucket_id == "11_1" or bucket_id == "11_2" or bucket_id == "11_3" or bucket_id == "11_4" or bucket_id == "11_5":
        codename = code_prefix + str(11) + "_"
        for ele in CODE_BUCKETS[bucket_id]:
            final_codename = codename + str(ele) + '.json'
            with open(DATA_INPUT_FOLDER + final_codename, 'r') as fp:
                code_dict = json.load(fp)
                code_astnode = json_to_ast(code_dict)
                code_set.append([code_astnode, code_astnode._size])

        return code_set, len(code_set)


    else:
        print("Unknown code bucket encountered...Exiting..")
        exit(0)



def quick_run_task_gen(type:str, code_set:list, temp_folder, verbose=False):
    '''

    :param type:
    :param code_set:
    :param verbose:
    :return: Given a list of codes (AST), runs task synthesis for 1000 iters for each and returns flag
    '''
    ## create the temp folder
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

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
        if code[0]._n_if_only > 0 or code[0]._n_while > 0 or code[0]._n_if_else > 0 or code[0]._n_repeat_until > 0:
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



def generate_tasks_for_code_set(type, code_set:list, solution_code:ASTNode, output_folder):
    mask_2 = []
    filtered_list = []
    n = 1

    ## create the temp folder
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for c in code_set:
        # get the task dimensions
        if c._n_if_only > 0 or c._n_while > 0 or c._n_if_else > 0 or c._n_repeat_until > 0:
            cond_flag = True
            task_iters = 20000
            qual_thresh = 0.1 # changed to 0.1 for Task-4 (repeat(if)--Karel E)
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


        jsoncodefilename = output_folder + 'code_run_' + str(n) + '.json'
        jsoncode = ast_to_json(c)
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
            filtered_list.append([c, c._size, task, start_karel_world, end_karel_world, tree_edit_distance(c, solution_code)])



    return mask_2, filtered_list


def wrapper_quick_gen(bucket_id:str):
    # obtain the code_set to run the full pipeline
    code_set, num_codes = get_codes_from_bucket(bucket_id)
    print("Initial mutation codes to be processed:", num_codes)
    # print the size buckets
    codes_by_size = {}
    size_bucket_without_cons = {}
    for ele in code_set:
        if ele[1] not in codes_by_size.keys():
            codes_by_size[ele[1]] = [ele[0]]
        else:
            codes_by_size[ele[1]].append(ele[0])
    for key, value in codes_by_size.items():
        size_bucket_without_cons[key] = len(value)
    print("Total number of codes generated purely based on code constraints:", size_bucket_without_cons)

    # carry out fast-task-gen for first level filtering
    # temp-folder
    temp_folder_name = DATA_OUTPUT_FOLDER + "bucket-" + str(bucket_id) + "/temp_misc/"
    mask_1 = quick_run_task_gen(TYPE, code_set, temp_folder_name)
    # filtered codes
    filtered_codes_1 = [code_set[i] for i in range(len(code_set)) if mask_1[i]]

    # sort the codes into the buckets (by size)
    filtered_codes_1 = [ele[0] for ele in filtered_codes_1]
    filtered_codes_1 = list(set(filtered_codes_1))  # remove repeated codes if-any
    print("Filtered codes after quick task generation:", len(filtered_codes_1))
    filtered_codes_1 = [[ele, get_size(ele)] for ele in filtered_codes_1]
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
    sampled_codes = [c[0] for c in filtered_codes_1]
    print("Sampled codes for full task-gen:", len(sampled_codes))
    return sampled_codes, len(sampled_codes)


def wrapper_full_task_gen(bucket_id:str):
    solution_code_ast, sol_code_size = get_solution_code_AST()
    # after pruning level 1
    sampled_codes, num_codes = wrapper_quick_gen(bucket_id)

    # carry out full task synthesis for sampled codes
    temp_folder_name =  DATA_OUTPUT_FOLDER + "bucket-" + str(bucket_id) + "/temp_misc/"
    # run the second layer of filtering: mask_2 is applied to all_codes to get filtered_codes
    mask_2, filtered_list = generate_tasks_for_code_set(TYPE, sampled_codes, solution_code_ast,
                                                        output_folder=temp_folder_name)
    print("Sampled codes for task-generation after shortcut:", len(filtered_list))
    # print by size
    size_bucket_after_shortcut = {}
    codes_by_size_after_shortcut = {}
    for ele in filtered_list:
        if ele[1] not in codes_by_size_after_shortcut.keys():
            codes_by_size_after_shortcut[ele[1]] = [ele[0]]
        else:
            codes_by_size_after_shortcut[ele[1]].append(ele[0])
    for key, value in codes_by_size_after_shortcut.items():
        size_bucket_after_shortcut[key] = len(value)
    print("Sampled codes for task-generation after shortcut:", size_bucket_after_shortcut)

    # final delta-debugging step
    mask_3 = [get_delta_debugged_validity(TYPE, c[0], c[3], c[4], temp_folder=temp_folder_name) for c in
              filtered_list]
    final_list_of_task_codes = [[filtered_list[i][0], filtered_list[i][1], filtered_list[i][2], filtered_list[i][3],
                                 filtered_list[i][4], filtered_list[i][5]] for i in range(len(filtered_list)) if
                                mask_3[i]]
    print("Final list of codes, after delta debugging pruning:", len(final_list_of_task_codes))


    size_bucket_after_delta_debugging = {}
    codes_by_size = {}
    for ele in final_list_of_task_codes:
        if ele[1] not in codes_by_size.keys():
            codes_by_size[ele[1]] = [ele[0]]
        else:
            codes_by_size[ele[1]].append(ele[0])
    for key, value in codes_by_size.items():
        size_bucket_after_delta_debugging[key] = len(value)
    print("Final list of codes, after delta debugging pruning:", size_bucket_after_delta_debugging)

    print("Sampled codes for task-generation after shortcut (before delta-debugging):", len(filtered_list))
    if final_list_of_task_codes is None or len(final_list_of_task_codes) == 0:
        print("No valid codes generated!")
        return None, 0

    return final_list_of_task_codes, len(final_list_of_task_codes)



def get_all_task_code_pairs(bucket_id:str):
    final_task_code_set, num_codes = wrapper_full_task_gen(bucket_id)

    # save the obtained codes
    if final_task_code_set is None:
        print("No valid codes generated!")
        return None, None

        # sort this set based on distance and distance to solution code
    sorted_codes = sorted(final_task_code_set, key=lambda x: x[1])

    grouped_codes = {}
    for ele in sorted_codes:
        if ele[1] in grouped_codes.keys():
            grouped_codes[ele[1]].append(ele)
        else:
            grouped_codes[ele[1]] = [ele]

        # sort each list based on distance to solution code
    sorted_codes_by_ast_dist = []
    sorted_dict = {}
    indices = []
    sizes = []
    start_id = 1
    for key, val in grouped_codes.items():
        # val_copy = copy.deepcopy(val)
        codes = sorted(val, key=lambda x: x[5], reverse=True)
        sorted_dict[key] = codes
        sorted_codes_by_ast_dist.extend(codes)
        sizes.append(len(codes))
        indices.append([start_id, start_id + len(codes)])
        start_id = start_id + len(codes)

    print("Double check the number of task-codes generated:", len(sorted_codes_by_ast_dist))

    # save all the valid task-code pairs
    output_folder = DATA_OUTPUT_FOLDER + 'bucket-' + str(bucket_id) + "/"
    for key, value in grouped_codes.items():
        codes = sorted(value, key=lambda x: x[5], reverse=True)
        code_num = 1
        # save the task-code file
        for ele in codes:
            taskname = 'task_' + str(key) + '_' + str(code_num)
            codename = 'code_' + str(key) + '_' + str(code_num)
            _ = save_task_code_pair(TYPE, ele[0], ele[2], ele[3], ele[4], output_folder, codename, taskname)
            code_num += 1




def save_task_code_pair(type:str, final_code:ASTNode, final_task, final_start_world, final_end_world, data_output:str, output_codename:str, output_taskname:str):

    if final_code is not None and final_task is not None:
        final_jsoncode = ast_to_json(final_code)
        # save the json code file

        # create the output folder if it doesn't exist
        if not os.path.exists(data_output):
            os.makedirs(data_output)

        with open(data_output + output_codename + '_output.json', 'w') as f:  # json code file
            json.dump(final_jsoncode, f, indent=4)
        # save the task text file
        final_task.karel.save_task_grid_to_file(final_start_world, final_end_world,
                                                final_end_world.karel_start_location,
                                                final_end_world.karel_start_direction,
                                                data_output,
                                                output_taskname)



    else:  # save the text files saying no valid task-code pair generated.
        # create the output folder if it doesn't exist
        print("Invalid task, code pair generated!---", final_code)
        if not os.path.exists(data_output):
            os.makedirs(data_output)

        if final_code is None:
            with open(data_output + output_codename + '_output.json', 'w') as f:  # json code file
                f.write('No valid task-code pair generated.')
                f.close()
        else:
            final_jsoncode = ast_to_json(final_code)
            with open(data_output + output_codename + '_output.json', 'w') as f:
                json.dump(final_jsoncode, f, indent=4)

        if final_task is None:
            with open(data_output + output_taskname + '_output.txt', 'w') as f:  # json code file
                f.write('No valid task generated.')
                f.close()

    return 0


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--bucket_id', type=str, default="9",
                            help='Bucket-ID to run pipeline for TASK-5 only')
    args = arg_parser.parse_args()
    bucket_id =  args.bucket_id

    get_all_task_code_pairs(bucket_id)


