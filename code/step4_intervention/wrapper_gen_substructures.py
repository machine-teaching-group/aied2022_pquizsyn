import json
import os
from code.step4_intervention.config import DATA_TEMP, DATA_OUTPUT, DATA_INPUT, SUBSTRUCTURE_FILE_PREFIX, SUBSTRUCTURE_CODEFILE_PREFIX, SUBSTRUCTURE_TASKFILE_PREFIX
from code.step1_hintpolicy.hintpolicy_struct_multihop import get_all_substructures
from code.utils.sketch import SketchNode, sketch_to_json
from code.utils.ast import ASTNode, ast_to_json
from code.step0_inputdata.gen_input_task0 import get_substructures as get_substructures_0
from code.step0_inputdata.gen_input_task0 import get_solution_code as get_solution_code_0
from code.step0_inputdata.gen_input_task0 import get_substructures_subcodes as get_substructures_subcodes_0
from code.step0_inputdata.gen_input_task1 import get_substructures as get_substructures_1
from code.step0_inputdata.gen_input_task1 import get_solution_code as get_solution_code_1
from code.step0_inputdata.gen_input_task1 import get_substructures_subcodes as get_substructures_subcodes_1
from code.step0_inputdata.gen_input_task2 import get_substructures as get_substructures_2
from code.step0_inputdata.gen_input_task2 import get_solution_code as get_solution_code_2
from code.step0_inputdata.gen_input_task2 import get_substructures_subcodes as get_substructures_subcodes_2
from code.step0_inputdata.gen_input_task3 import get_substructures as get_substructures_3
from code.step0_inputdata.gen_input_task3 import get_solution_code as get_solution_code_3
from code.step0_inputdata.gen_input_task3 import get_substructures_subcodes as get_substructures_subcodes_3
from code.step0_inputdata.gen_input_task4 import get_substructures as get_substructures_4
from code.step0_inputdata.gen_input_task4 import get_solution_code as get_solution_code_4
from code.step0_inputdata.gen_input_task4 import get_substructures_subcodes as get_substructures_subcodes_4
from code.step0_inputdata.gen_input_task5 import get_substructures as get_substructures_5
from code.step0_inputdata.gen_input_task5 import get_solution_code as get_solution_code_5
from code.step0_inputdata.gen_input_task5 import get_substructures_subcodes as get_substructures_subcodes_5
from code.step0_inputdata.gen_input_task6 import get_substructures as get_substructures_6
from code.step0_inputdata.gen_input_task6 import get_solution_code as get_solution_code_6
from code.step0_inputdata.gen_input_task6 import get_substructures_subcodes as get_substructures_subcodes_6
from code.step3_code2task.utils.parser import convert_json_to_python
from code.step3_code2task.run_random import run_random_with_quality_only
'''This is a wrapper that saves the substructure, and the minimal codes for each substructure for all tasks'''


def get_solution_sketch(tid:str):
    if tid == 0:
        _, sketch, type = get_solution_code_0()
    elif tid == 1:
        _, sketch, type = get_solution_code_1()
    elif tid == 2:
        _, sketch, type = get_solution_code_2()
    elif tid == 3:
        _, sketch, type = get_solution_code_3()
    elif tid == 4:
        _, sketch, type = get_solution_code_4()
    elif tid == 5:
        _, sketch, type = get_solution_code_5()
    elif tid == 6:
        _, sketch, type = get_solution_code_6()
    else:
        assert "Task ID not found!"
        return None, None

    return sketch, type


def get_all_substructures_for_task(tid:str):
    '''This routine gets all the substructure sketches for the solution code of the task, presaved in the input-gen files'''
    if tid == 0:
        all_sketches = get_substructures_0()
    elif tid == 1:
        all_sketches = get_substructures_1()
    elif tid == 2:
        all_sketches = get_substructures_2()
    elif tid == 3:
        all_sketches = get_substructures_3()
    elif tid == 4:
        all_sketches = get_substructures_4()
    elif tid == 5:
        all_sketches = get_substructures_5()
    elif tid == 6:
        all_sketches = get_substructures_6()
    else:
        assert "Task ID not found!"
        return None

    return all_sketches





def get_minimal_code_from_sketch(tid:str, sketch:SketchNode, sol_sketch:SketchNode):
    '''

    :param tid:
    :param sketch:
    :param sol_sketch:
    :return: All the minimal code candidates for the given sketch, solution sketch
    '''
    # generate all the substructures from the solution code
    all_substructures = get_all_substructures(sol_sketch)

    if sketch not in all_substructures:
        assert "Substructure not part of solution code."
        return None

    all_minimal_codes = []

    if tid == 0:
        all_minimal_codes = get_substructures_subcodes_0(sketch)
    elif tid == 1:
        all_minimal_codes = get_substructures_subcodes_1(sketch)
    elif tid == 2:
        all_minimal_codes = get_substructures_subcodes_2(sketch)
    elif tid == 3:
        all_minimal_codes = get_substructures_subcodes_3(sketch)
    elif tid == 4:
        all_minimal_codes = get_substructures_subcodes_4(sketch)
    elif tid == 5:
        all_minimal_codes = get_substructures_subcodes_5(sketch)
    elif tid == 6:
        all_minimal_codes = get_substructures_subcodes_6(sketch)
    else:
        assert "Task ID not found!"
        return None



    return all_minimal_codes





def get_single_minimal_code_from_set(minimal_codes:list, output_folder='', type='hoc'):
    '''

    :param minimal_codes:
    :param output_folder:
    :param type:
    :return: One single minimal code from the set of minimal codes based on the task-quality
    '''

    if len(minimal_codes) == 1:
        return minimal_codes[0], 0, None, None, None
    else: # generate the task for each code, and pick that code with highest quality
        min_code_set = []
        for i, code in enumerate(minimal_codes):
            ## create the temp folder
            if not os.path.exists(output_folder + 'temp_misc'):
                os.makedirs(output_folder + 'temp_misc')
            jsoncode = code.to_json()
            jsoncodefilename = output_folder + 'temp_misc/mincode_' + str(i) + '.json'
            # convert each of code files into python codes
            with open(jsoncodefilename, 'w') as f:  # json code file
                json.dump(jsoncode, f, indent=4)
            pythonfilename = 'mincode_' + str(i)
            _ = convert_json_to_python(jsoncodefilename, output_folder + 'temp_misc/', pythonfilename)
            python_code_file = output_folder + 'temp_misc/' + pythonfilename + '_input.py'

            # check if the code has conditionals
            if code._n_if_only > 0 or code._n_if_else > 0 or code._n_while> 0 or code._n_repeat_until > 0:
                cond_flag = True
                task_iters = 20000
            else:
                cond_flag = False
                task_iters = 30

            # task dimensions
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
                # print("No valid task generated from minimal code routine!", code)
                task_score = 0
            min_code_set.append([code, task_score, task, start_karel_world, end_karel_world])
            # also save the task corresponding to the minimal code




        # return that code with the highest task quality score
        # sort the codes based on task quality and return the code with highest quality
        sorted_min_code_set = sorted(min_code_set, key=lambda x: x[1], reverse=True)
        return sorted_min_code_set[0][0], sorted_min_code_set[0][1], sorted_min_code_set[0][2], sorted_min_code_set[0][3], sorted_min_code_set[0][4]


def wrapper_gen_all_substructures_and_subcodes(tid, subid=None):
    print("Running substructures routine for Task:", tid)
    # get the substructures and save the sketch json
    substructures = get_all_substructures_for_task(tid)
    # save the sketch in a json file
    data_output_prefix = DATA_OUTPUT + 'task-' + str(tid) + '/substructure-'
    # obtain the solution sketch for the task
    sol_sketch, type = get_solution_sketch(tid)


    for i,ele in enumerate(substructures):
        print("Running substructure:", i)
        data_output = data_output_prefix + str(i) + '/'
        # create the output directory if it doesn't exist
        if not os.path.exists(data_output):
            os.makedirs(data_output)
        sketchname = SUBSTRUCTURE_FILE_PREFIX
        ele_json = sketch_to_json(ele)
        # save the sketch
        with open(data_output+sketchname+'.json', 'w') as fp:
            json.dump(ele_json, fp, indent=4)

        # generate the subcode from the sketch, from the available options
        min_code_set = get_minimal_code_from_sketch(tid, ele, sol_sketch)
        # print("Min code set:", min_code_set)
        min_code, _, min_task, min_start_karel_world, min_end_karel_world,  = get_single_minimal_code_from_set(min_code_set, data_output, type=type)
        # save the min_code
        min_code_name = SUBSTRUCTURE_CODEFILE_PREFIX
        min_code_json = ast_to_json(min_code)
        print("Minimal JSON code for sketch:", min_code_json)
        with open(data_output+min_code_name+'.json', 'w') as fp:
            json.dump(min_code_json, fp, indent=4)
        # # save the min_task
        # min_task_name = SUBSTRUCTURE_TASKFILE_PREFIX
        # with open(data_output + min_task_name + '.txt', 'w') as fp:





    return 0




if __name__ == "__main__":

    tids = [0,1,2,3,4,5,6]
    for t in tids:
        _ = wrapper_gen_all_substructures_and_subcodes(t)
