import json
import code.step4_intervention.config as config
import os
from code.utils.ast import get_max_block_size, json_to_ast
from code.step0_inputdata.gen_input_task0 import get_solution_code_symast_format as get_solution_code_symast_format_0
from code.step0_inputdata.gen_input_task1 import get_solution_code_symast_format as get_solution_code_symast_format_1
from code.step0_inputdata.gen_input_task2 import get_solution_code_symast_format as get_solution_code_symast_format_2
from code.step0_inputdata.gen_input_task3 import get_solution_code_symast_format as get_solution_code_symast_format_3
from code.step0_inputdata.gen_input_task4 import get_solution_code_symast_format as get_solution_code_symast_format_4
from code.step0_inputdata.gen_input_task5 import get_solution_code_symast_format as get_solution_code_symast_format_5
from code.step0_inputdata.gen_input_task6 import get_solution_code_symast_format as get_solution_code_symast_format_6
from code.step2_struct2code.get_task_code_pair import get_task_code_pair_from_minimal_code
from code.step4_intervention.gen_output_code_task_image import parse_ast_blank
from code.utils.gen_task_image import gen_task_script

'''
This function ties all 3 parts together, and takes as input the task_id,  student attempt(json-file), and the solution code(json-file)
'''




def full_run(task_ids:list, substructure_ids:list, bucket_sample_size = 3, sampling_size=50, verbose=False):

    display_dict = {}
    for tid in task_ids:
        type = tid[1]
        sol_code_symast, sol_code_size = eval(config.INPUT_CODE_DICT[str(tid[0])])()

        for sid in substructure_ids:
            print("Running task:"+ str(tid[0]) + ", substructure:" + str(sid))

            data_output = config.DATA_OUTPUT + 'task-' + str(tid[0]) + '/' + \
                          'substructure-' + str(sid) + '/'

            # get the minimal code for the task-substructure
            with open(data_output+'subcode.json', 'r') as fp:
                mincode_dict = json.load(fp)
            mincode = json_to_ast(mincode_dict)
            max_blk_size = 2 # fixed to 2


            total_codes, display_ids = get_task_code_pair_from_minimal_code(type, str(tid[0]), mincode, max_blk_size, sol_code_symast, bucket_sample_size=bucket_sample_size, delta_debugging_sample_size=sampling_size, output_folder = data_output, verbose=verbose)
            if total_codes is None and display_ids is None:
                display_dict[str([tid, sid])] = [0, [0]]
            else:
                display_dict[str([tid, sid])] = [total_codes, display_ids]

            # save the display IDs in a separate text file
            with open(data_output+'display_ids.txt', 'w') as fp:
                fp.write("Total codes after delta-debugging: "+str(total_codes)+'\n')
                fp.write(str(display_ids))

            print("-"*20)




    return total_codes, display_dict




def gen_output_images_task(tid, sid, aid, taskfile, outputfolder, taskfilename, inputfolder = 'data/output/temp_misc/'):

    task_script = gen_task_script(taskfile)
    with open(inputfolder + 'task.tex', 'w') as fp:
        fp.write("%s" % task_script)

    # generate the image file
    input_path = inputfolder + 'task.tex'
    os.system("pdflatex -interaction=nonstopmode -output-directory data/output/temp_misc %s" % (input_path))
    output_path = outputfolder + taskfilename+'.jpg'
    print("Generated task image:", output_path)
    os.system("convert -density 1200 -quality 100 data/output/temp_misc/task.pdf %s" % output_path)


    return 0


def gen_output_code_mcq_images(tid, sid, aid, codefile, outputfolder, codefilename, inputfolder = 'data/output/temp_misc/'):
    with open(codefile, 'r') as fp:
        code_json = json.load(fp)

    code_script, mcq_sol = parse_ast_blank(code_json)
    with open(inputfolder + 'code.tex', 'w') as fp:
        fp.write("%s" % code_script)

    # save the mcq answer in a separate file
    with open(outputfolder + codefilename + '_sol.txt', 'w') as fp:
        fp.write("%s" % mcq_sol)


    # generate the image file
    input_path = inputfolder + 'code.tex'
    os.system("pdflatex -interaction=nonstopmode -output-directory data/output/temp_misc %s" % (input_path))
    output_path = outputfolder + codefilename+'.jpg'
    print("Generated output-code image with blank:", output_path)
    os.system("convert -density 1200 -quality 100 data/output/temp_misc/code.pdf %s" % output_path)




    return 0




if __name__ == "__main__":

    # # run full_run
    task_ids_dict = {
                "0": [0, 'hoc'],
                "1": [1, 'hoc'],
                "2": [2, 'hoc'],
                "3": [3, 'hoc'],
                "4": [4, 'karel'],
                "5": [5, 'karel'],
                "6": [6, 'karel'] # newly added Karel Task
    }

    task_ids = [task_ids_dict["0"], task_ids_dict["1"], task_ids_dict["2"], task_ids_dict["3"], task_ids_dict["4"], task_ids_dict["5"], task_ids_dict["6"]]
    substructure_ids_dict = {
                   "0": [0,1,2],
                   "1": [0,1,2],
                   "2": [0,1,2],
                   "3": [0,1,2], # substructure ID 3 treated separately for additional code constraints.
                   "4": [0,1,2],
                   "5": [0,1], # substructure ID 2 treated separately for additional code constraints. Also runtime is higher than all others
                   "6": [0,1] # newly added Karel Task

                }

    for key in task_ids_dict.keys():
        print("Running Task:", key)
        sub_ids = substructure_ids_dict[key]
        bucket_code_samples = 3
        sample_size = 2000
        #### generate all the task-code pairs
        total_codes, display_dict = full_run(task_ids, sub_ids, bucket_sample_size=bucket_code_samples, sampling_size=sample_size, verbose=False)
        if total_codes is None:
            print("Unable to create all task-code pairs!")
            exit(0)











