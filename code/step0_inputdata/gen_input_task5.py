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
                  "5\t#\t.\t.\t.\t.\t.\t.\tx\t.\t.\t.\t#\n" \
                  "6\t#\t.\t.\t.\t.\t.\tx\t#\t.\t.\t.\t#\n" \
                  "7\t#\t.\t.\t.\t.\t.\t#\t.\t.\t.\t.\t#\n" \
                  "8\t#\t.\t.\t.\tx\t#\t.\t.\t.\t.\t.\t#\n" \
                  "9\t#\t.\t.\t.\t#\t.\t.\t.\t.\t.\t.\t#\n" \
                  "10\t#\t.\tx\t#\t.\t.\t.\t.\t.\t.\t.\t#\n" \
                  "11\t#\tx\t#\t.\t.\t.\t.\t.\t.\t.\t.\t#\n" \
                  "12\t#\t#\t#\t#\t#\t#\t#\t#\t#\t#\t#\t#\n" \
                  "agentloc\t(2,11)" \
                  "\nagentdir\teast\n" \
                  "\npostgrid\t1\t2\t3\t4\t5\t6\t7\t8\t9\t10\t11\t12\n" \
                  "1\t#\t#\t#\t#\t#\t#\t#\t#\t#\t#\t#\t#\n" \
                  "2\t#\t.\t.\t.\t.\t.\t.\t.\t.\t.\t.\t#\n" \
                  "3\t#\t.\t.\t.\t.\t.\t.\t.\t.\t.\t.\t#\n" \
                  "4\t#\t.\t.\t.\t.\t.\t.\t.\t.\t.\t.\t#\n" \
                  "5\t#\t.\t.\t.\t.\t.\t.\t.\t.\t.\t.\t#\n" \
                  "6\t#\t.\t.\t.\t.\t.\t.\t#\t.\t.\t.\t#\n" \
                  "7\t#\t.\t.\t.\t.\t.\t#\t.\t.\t.\t.\t#\n" \
                  "8\t#\t.\t.\t.\t.\t#\t.\t.\t.\t.\t.\t#\n" \
                  "9\t#\t.\t.\t.\t#\t.\t.\t.\t.\t.\t.\t#\n" \
                  "10\t#\t.\t.\t#\t.\t.\t.\t.\t.\t.\t.\t#\n" \
                  "11\t#\t.\t#\t.\t.\t.\t.\t.\t.\t.\t.\t#\n" \
                  "12\t#\t#\t#\t#\t#\t#\t#\t#\t#\t#\t#\t#\n" \
                  "agentloc\t(8,5)\n" \
                  "agentdir\teast\n"

    return task_string


def get_solution_code():
    '''

    :return: the solution code of the task
    '''

    code = ASTNode('run', None, [
        ASTNode('while', 'bool_no_path_ahead', [
            ASTNode('if', 'bool_marker', [
                ASTNode('do', 'bool_marker', [ASTNode('pick_marker')])
            ]),
            ASTNode('turn_left'), ASTNode('move'), ASTNode('turn_right'), ASTNode('move')
        ]),
        ASTNode('pick_marker')
    ])
    type = 'karel'
    sketch = GenerateSketch(code, type=type)
    return code, sketch._sketch_without_A, type


def get_solution_code_symast_format():
    '''

    :return: the solution code in AST format
    '''
    code = AST('run', [
        AST('while(bool_no_path_ahead)', [
        AST('if(bool_marker)', [
            AST('do', [AST('pick_marker')]),
        ]),
            AST('turn_left'), AST('move'), AST('turn_right'), AST('move')

    ]),
        AST('pick_marker')
    ], type='karel')

    return code, code.size()

def get_substructures_subcodes(sketch:SketchNode):
    substructures = [
        SketchNode('run', None, []),

        SketchNode('run', None, [
            SketchNode('while', 'bool_cond', [])
        ]),

        SketchNode('run', None, [
            SketchNode('while', 'bool_cond', [
                SketchNode('if_only', 'bool_cond', [
                    SketchNode('do', 'bool_cond', [])

                ])
            ])
        ])


    ]

    if sketch == substructures[0]:
        codes = [
            ASTNode('run', None, [
                ASTNode('pick_marker')
            ]),

            ASTNode('run', None, [
                ASTNode('turn_left'),
                ASTNode('move'),
                ASTNode('turn_right'),
                ASTNode('move'),
                ASTNode('pick_marker'),

            ]),

            ASTNode('run', None, [
                ASTNode('pick_marker'),
                ASTNode('turn_left'),
                ASTNode('move'),
                ASTNode('turn_right'),
                ASTNode('move'),
                ASTNode('pick_marker'),

            ])
        ]
    elif sketch == substructures[1]:
        codes = [
            ASTNode('run', None, [
                ASTNode('while', 'bool_no_path_ahead', [
                    ASTNode('turn_left'),
                    ASTNode('move'),
                    ASTNode('turn_right'),
                    ASTNode('move'),
                ]),
                ASTNode('pick_marker')
            ]),

            ASTNode('run', None, [
                ASTNode('while', 'bool_no_path_ahead', [
                    ASTNode('pick_marker'),
                    ASTNode('turn_left'),
                    ASTNode('move'),
                    ASTNode('turn_right'),
                    ASTNode('move'),
                ]),
                ASTNode('pick_marker')
            ])

        ]

    elif sketch == substructures[2]:
        codes = [
            ASTNode('run', None, [
                ASTNode('while', 'bool_no_path_ahead', [
                    ASTNode('if', 'bool_marker', [
                        ASTNode('do', 'bool_marker', [ASTNode('pick_marker')])
                    ]),
                    ASTNode('turn_left'), ASTNode('move'), ASTNode('turn_right'), ASTNode('move')
                ]),
                ASTNode('pick_marker')
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
        ]),

        SketchNode('run', None, [
            SketchNode('while', 'bool_cond', [
                SketchNode('if_only', 'bool_cond', [
                    SketchNode('do', 'bool_cond', [])

                ])
            ])
        ])

    ]

    return substructures





def get_student_attempts():
    '''

    :return: student attempts, and number of student attempts
    '''

    all_attempts = []
    all_sketches = []

    ########### Student attempts
    #### Basic blocks
    stu_0 = ASTNode('run', None, [
        ASTNode('pick_marker'),
        ASTNode('turn_left'), ASTNode('move'), ASTNode('turn_right'), ASTNode('move'),
        ASTNode('pick_marker'),
        ASTNode('turn_left'), ASTNode('move'), ASTNode('move'), ASTNode('turn_right'), ASTNode('move'), ASTNode('move'),
        ASTNode('pick_marker'),
        ASTNode('turn_left'), ASTNode('move'), ASTNode('move'), ASTNode('turn_right'), ASTNode('move'), ASTNode('move'),
        ASTNode('pick_marker'),
        ASTNode('turn_left'), ASTNode('move'), ASTNode('turn_right'), ASTNode('move'), ASTNode('pick_marker'),
    ])
    sketch_0 = GenerateSketch(stu_0, type='karel')
    all_sketches.append(sketch_0._sketch_without_A)
    all_attempts.append(stu_0)

    ##### Sub-structure
    stu_1 = ASTNode('run', None, [
        ASTNode('while', 'bool_no_path_ahead', [
            ASTNode('pick_marker'),
            ASTNode('turn_left'),
            ASTNode('move'),
            ASTNode('turn_right'),
            ASTNode('move'),
            ASTNode('move')
        ])
    ])
    sketch_1 = GenerateSketch(stu_1, type='karel')
    all_sketches.append(sketch_1._sketch_without_A)
    all_attempts.append(stu_1)

    ###### Same-structure
    stu_2 = ASTNode('run', None, [
        ASTNode('while', 'bool_marker', [
            ASTNode('if', 'bool_path_left', [
                ASTNode('do', 'bool_path_left', [
                    ASTNode('pick_marker'), ASTNode('turn_left'), ASTNode('move'), ASTNode('turn_right'), ASTNode('move')
                ])
            ]),
        ]),
        ASTNode('pick_marker')
    ])
    sketch_2 = GenerateSketch(stu_2, type='karel')
    all_sketches.append(sketch_2._sketch_without_A)
    all_attempts.append(stu_2)

    ####### Complex-structure (nested repeat)
    stu_3 = ASTNode('run', None, [
        ASTNode('if', 'bool_marker', [
            ASTNode('do', 'bool_marker', [
                ASTNode('pick_marker'),
                ASTNode('while', 'bool_no_path_ahead', [
                    ASTNode('turn_right'), ASTNode('move'), ASTNode('turn_left'), ASTNode('move'),
                    ASTNode('if', 'bool_marker', [
                        ASTNode('do', 'bool_marker', [ASTNode('pick_marker')])
                    ])
                ])
            ])
        ])
    ])
    sketch_3 = GenerateSketch(stu_3, type='karel')
    all_sketches.append(sketch_3._sketch_without_A)
    all_attempts.append(stu_3)

    return all_attempts, all_sketches, len(all_attempts)


def get_basic_data_for_task(folder='', save = True):

    task = get_task()
    solcode, solsketch, _ = get_solution_code()
    stucodes, stusketches, nstudents = get_student_attempts()

    if save:
        print("Saving the contents of task-5...")
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
        for i,s in enumerate(stucodes):
            s_json = ast_to_json(s)
            s_sketch_json = sketch_to_json(stusketches[i])
            filename = 'student-'+ str(i)
            with open(folder + filename + '.json', 'w', encoding='utf-8') as fp:
                json.dump(s_json, fp, ensure_ascii=False, indent=4)
            with open(folder + filename + '_struct.json', 'w', encoding='utf-8') as fp:
                json.dump(s_sketch_json, fp, ensure_ascii=False, indent=4)

    return task, solcode, stucodes


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


    # add the student tex files
    _, _, nstudents = get_student_attempts()
    for i in range(nstudents):
        s_script = gen_latex_script_code(outputfolder + 'student-' +str(i) + '.json')
        with open(inputfolder + 'student-' +str(i) + '.tex', 'w') as fp:
            fp.write("%s" % s_script)
        s_struct_script = gen_latex_script_code(outputfolder + 'student-' +str(i) + '_struct.json')
        with open(inputfolder + 'student-' +str(i) + '_struct.tex', 'w') as fp:
            fp.write("%s" % s_struct_script)

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


    # student-codes
    for i in range(nstudents):
        student_name = 'student-' + str(i)
        input_path = inputfolder + 'student-' + str(i) + '.tex'
        os.system("pdflatex -interaction=nonstopmode -output-directory data/input/temp_latex %s" % (input_path))
        output_path = outputfolder + 'student-' + str(i) + '.pdf'
        shutil.copyfile('data/input/temp_latex/' + 'student-' + str(i) + '.pdf', output_path)
        # os.system("convert -density 1200 -quality 100 data/input/temp_latex/%s.pdf %s" % (student_name,output_path))

        # struct image
        input_path = inputfolder + 'student-' + str(i) + '_struct.tex'
        os.system("pdflatex -interaction=nonstopmode -output-directory data/input/temp_latex %s" % (input_path))
        output_path = outputfolder + 'student-' + str(i) + '_struct.pdf'
        shutil.copyfile('data/input/temp_latex/' + 'student-' + str(i) + '.pdf', output_path)
        # os.system("convert -density 1200 -quality 100 data/input/temp_latex/%s_struct.pdf %s" % (student_name, output_path))

    return


def get_all_data_for_task(folder='', save=True):
    task, code, stu = get_basic_data_for_task(folder=folder, save=save)
    get_files_for_images(folder)

    print("Generated data and image data")

    return
