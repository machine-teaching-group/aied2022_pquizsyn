import json
import os
import sys
import shutil
sys.path.append("..")
from code.utils.ast import ASTNode as ASTNode
from code.step2_struct2code.sym_ast import AST
from code.utils.ast import json_to_ast as json_to_ast
from code.utils.ast import ast_to_json as ast_to_json
from code.utils.code2sketch import GenerateSketch as GenerateSketch
from code.utils.sketch import sketch_to_json, SketchNode
from code.utils.sketch import sketch_to_json as sketch_to_json
from code.utils.gen_task_image import parse_task_file as parse_task_file
from code.utils.gen_task_image import gen_latex_script as gen_latex_script_task
from code.utils.gen_code_image import get_full_latex_script as gen_latex_script_code


def get_task():
    '''

    :return: the string representation of the task
    '''

    task_string = "type\tkarel\ngridsz\t(12,12)\n" \
                  "\npregrid\t1\t2\t3\t4\t5\t6\t7\t8\t9\t10\t11\t12\n" \
                  "1\t#\t#\t#\t#\t#\t#\t#\t#\t#\t#\t#\t#\n" \
                  "2\t#\t.\t.\t.\t.\t.\t.\t.\t.\t.\t.\t#\n" \
                  "3\t#\t.\t.\t.\t.\t.\t.\t.\t.\t.\t.\t#\n" \
                  "4\t#\t.\t.\t.\t.\t.\t.\t.\t.\t.\t.\t#\n" \
                  "5\t#\t.\t.\t.\t.\t.\t.\t.\t.\t.\t.\t#\n" \
                  "6\t#\t.\t.\t.\t.\t.\t.\t.\t.\t.\t.\t#\n" \
                  "7\t#\t.\t.\t.\t.\t.\t.\t.\t.\t.\t.\t#\n" \
                  "8\t#\t.\t.\t.\t.\t.\t.\t.\t.\t.\t.\t#\n" \
                  "9\t#\t.\t.\t.\t.\t.\t.\t.\t.\t.\t.\t#\n" \
                  "10\t#\t.\t.\t.\t.\t.\t.\t.\t.\t.\t.\t#\n" \
                  "11\t#\t.\t.\t.\t.\t.\t.\t.\t.\t.\t.\t#\n" \
                  "12\t#\t#\t#\t#\t#\t#\t#\t#\t#\t#\t#\t#\n" \
                  "agentloc\t(2,11)\n" \
                  "agentdir\teast\n" \
                  "\npostgrid\t" \
                  "1\t2\t3\t4\t5\t6\t7\t8\t9\t10\t11\t12\n" \
                  "1\t#\t#\t#\t#\t#\t#\t#\t#\t#\t#\t#\t#\n" \
                  "2\t#\t.\t.\t.\t.\t.\t.\t.\t.\t.\tx\t#\n" \
                  "3\t#\t.\t.\t.\t.\t.\t.\t.\t.\tx\t.\t#\n" \
                  "4\t#\t.\t.\t.\t.\t.\t.\t.\tx\t.\t.\t#\n" \
                  "5\t#\t.\t.\t.\t.\t.\t.\tx\t.\t.\t.\t#\n" \
                  "6\t#\t.\t.\t.\t.\t.\tx\t.\t.\t.\t.\t#\n" \
                  "7\t#\t.\t.\t.\t.\tx\t.\t.\t.\t.\t.\t#\n" \
                  "8\t#\t.\t.\t.\tx\t.\t.\t.\t.\t.\t.\t#\n" \
                  "9\t#\t.\t.\tx\t.\t.\t.\t.\t.\t.\t.\t#\n" \
                  "10\t#\t.\tx\t.\t.\t.\t.\t.\t.\t.\t.\t#\n" \
                  "11\t#\tx\t.\t.\t.\t.\t.\t.\t.\t.\t.\t#\n" \
                  "12\t#\t#\t#\t#\t#\t#\t#\t#\t#\t#\t#\t#\n" \
                  "agentloc\t(11,2)\n" \
                  "agentdir\teast\n"

    return task_string


def get_solution_code():
    '''

    :return: the solution code of the task
    '''

    code = ASTNode('run', None, [
        ASTNode('put_marker'),
        ASTNode('while', 'bool_path_ahead', [

            ASTNode('move'), ASTNode('turn_left'),
            ASTNode('move'), ASTNode('turn_right'),
            ASTNode('put_marker')
        ]),

    ])
    type = 'karel'
    sketch = GenerateSketch(code, type=type)



    return code, sketch._sketch_without_A, type


def get_solution_code_symast_format():
    '''

    :return: the solution code in AST format
    '''
    code = AST('run', [
        AST('put_marker'),
        AST('while(bool_path_ahead)', [
            AST('move'), AST('turn_left'),
            AST('move'), AST('turn_right'),
            AST('put_marker')

    ]),

    ], type='karel')

    return code, code.size()

def get_substructures_subcodes(sketch:SketchNode):
    substructures = [
        SketchNode('run', None, []),

        SketchNode('run', None, [
            SketchNode('while', 'bool_cond', [])
        ]),



    ]

    if sketch == substructures[0]:
        codes = [
            ASTNode('run', None, [
                ASTNode('put_marker'),
                ASTNode('move'), ASTNode('turn_left'),
                ASTNode('move'), ASTNode('turn_right'),
                ASTNode('put_marker')

            ])
        ]

    elif sketch == substructures[1]:
        codes = [
            ASTNode('run', None, [
                ASTNode('put_marker'),
                ASTNode('while', 'bool_path_ahead', [
                    ASTNode('move'), ASTNode('turn_left'),
                    ASTNode('move'), ASTNode('turn_right'),
                    ASTNode('put_marker')
                ]),
            ])

        ]



    else:
        assert "Substructure does not belong to solution code!"
        return None

    return codes





def get_substructures():
    substructures = [

        SketchNode('run', None, []),

        SketchNode('run', None, [
            SketchNode('while', 'bool_cond', [])
        ])
    ]

    return substructures





def get_student_attempts():
    '''

    :return: student attempts, and number of student attempts
    '''

    pass




def get_basic_data_for_task(folder='', save = True):

    task = get_task()
    solcode, solsketch, type = get_solution_code()

    if save:
        print("Saving the contents of task-6...")
        # create the folder if it does not exist
        if not os.path.exists(folder):
            os.makedirs(folder)
        # save the task file
        with open(folder + 'task.txt', 'w') as fp:
            fp.write("{}".format(task))
        fp.close()
        # save the sol-code file
        solcode_json = ast_to_json(solcode)
        with open(folder + 'code.json', 'w', encoding='utf-8') as fp:
            json.dump(solcode_json, fp, ensure_ascii=False, indent=4)
        solsketch_json = sketch_to_json(solsketch)
        with open(folder + 'code_struct.json', 'w', encoding='utf-8') as fp:
            json.dump(solsketch_json, fp, ensure_ascii=False, indent=4)
        # save the student attempts


    return task, solcode


def get_files_for_images(outputfolder, inputfolder='data/input/temp_latex/'):

    if not os.path.exists(inputfolder):
        os.makedirs(inputfolder)

    # add the task.tex file
    type, loc, dir, mat = parse_task_file(outputfolder + 'task.txt')
    task_script = gen_latex_script_task(type, loc, dir, mat)
    ## save it in a file
    with open(inputfolder + 'task.tex', 'w') as fp:
        fp.write("%s" % task_script)

    # add the code.tex file
    code_script = gen_latex_script_code(outputfolder + 'code.json')
    with open(inputfolder + 'code.tex', 'w') as fp:
        fp.write("%s" % code_script)

    # add the code_struct.tex file
    struct_script = gen_latex_script_code(outputfolder + 'code_struct.json')
    with open(inputfolder + 'code_struct.tex', 'w') as fp:
        fp.write("%s" % struct_script)

    print("Image tex files generated")

    # run the command to generate the pdf files, jpg files
    input_path = inputfolder + 'task.tex'
    os.system("pdflatex -output-directory data/input/temp_latex %s" % (input_path))
    output_path = outputfolder + 'task.pdf'
    shutil.copyfile('data/input/temp_latex/task.pdf', output_path)
    # os.system("convert -density 1200 -quality 100 data/input/temp_latex/task.pdf %s" % output_path)

    # code
    input_path = inputfolder + 'code.tex'
    os.system("pdflatex -interaction=nonstopmode -output-directory data/input/temp_latex %s" % (input_path))
    output_path = outputfolder + 'code.pdf'
    shutil.copyfile('data/input/temp_latex/code.pdf', output_path)
    # os.system("convert -density 1200 -quality 100 data/input/temp_latex/code.pdf %s" % output_path)

    # code_struct
    input_path = inputfolder + 'code_struct.tex'
    os.system("pdflatex -interaction=nonstopmode -output-directory data/input/temp_latex %s" % (input_path))
    output_path = outputfolder + 'code_struct.pdf'
    shutil.copyfile('data/input/temp_latex/code_struct.pdf', output_path)
    # os.system("convert -density 1200 -quality 100 data/input/temp_latex/code_struct.pdf %s" % output_path)

    return 0


def get_all_data_for_task(folder='', save=True):
    task, code = get_basic_data_for_task(folder=folder, save=save)
    get_files_for_images(folder)

    print("Generated data and image data")

    return 0
