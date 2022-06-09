import json
import os
import time
import argparse
import shutil
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
from code.step1_hintpolicy.hintpolicy_struct_multihop import get_sketch_multihop_2
from code.step1_hintpolicy.hintpolicy_struct_multihop import get_all_substructures
from code.step4_intervention.wrapper_gen_substructures import get_single_minimal_code_from_set
from code.step4_intervention.config import SUBSTRUCTURE_CODEFILE_PREFIX
from code.step2_struct2code.get_task_code_pair import get_single_task_code_pair_from_minimal_code
from code.step4_intervention.gen_output_code_task_image import gen_output_code_mcq_images, get_blank_token_in_json, get_blank_token_in_json, parse_ast_blank, gen_output_mcq_script



def get_substructures_subcodes(sketch:SketchNode):
    substructures = [

        SketchNode('run', None, []),

        SketchNode('run', None, [
            SketchNode('repeat_until_goal', 'bool_cond', [])
        ]),

        SketchNode('run', None, [
            SketchNode('repeat_until_goal', 'bool_cond', [
                SketchNode('if_else', 'bool_cond', [
                    SketchNode('do', 'bool_cond', []),
                    SketchNode('else', 'bool_cond', []),
                ])
            ])
        ]),

        SketchNode('run', None, [
            SketchNode('repeat_until_goal', 'bool_cond', [
                SketchNode('if_else', 'bool_cond', [
                    SketchNode('do', 'bool_cond', []),
                    SketchNode('else', 'bool_cond', [
                        SketchNode('if_else', 'bool_cond', [
                            SketchNode('do', 'bool_cond', []),
                            SketchNode('else', 'bool_cond', []),
                        ])
                    ]),
                ])
            ])
        ])

    ]
    if sketch == substructures[0]:
        codes = [
            ASTNode('run', None, [
                ASTNode('move')
            ]),
            # ASTNode('run', None, [
            #     ASTNode('turn_right')
            # ]),
            # ASTNode('run', None, [
            #     ASTNode('turn_left')
            # ])

        ]
    elif sketch == substructures[1]:
        codes = [
            ASTNode('run', None, [
                ASTNode('repeat_until_goal', 'bool_goal', [
                    ASTNode('move'),
                ]),

            ]),

            ASTNode('run', None, [
                ASTNode('repeat_until_goal', 'bool_goal', [
                    ASTNode('turn_left')
                ]),
            ]),

            ASTNode('run', None, [
                ASTNode('repeat_until_goal', 'bool_goal', [
                    ASTNode('turn_right')
                ]),
            ])
        ]
    elif sketch == substructures[2]:
        codes = [
            ASTNode('run', None,
                    [ASTNode('repeat_until_goal', 'bool_goal', [
                        ASTNode('ifelse', 'bool_path_ahead',
                        [
                        ASTNode('do', 'bool_path_ahead', [ASTNode('move')]),
                        ASTNode('else', 'bool_path_ahead', [ASTNode('turn_left')])

                        ])

                    ])
                ]),

            ASTNode('run', None,
                    [ASTNode('repeat_until_goal', 'bool_goal', [
                        ASTNode('ifelse', 'bool_path_ahead',
                                [
                                    ASTNode('do', 'bool_path_ahead', [ASTNode('move')]),
                                    ASTNode('else', 'bool_path_ahead', [ASTNode('turn_right')])

                                ])

                    ])
                     ])
        ]

    elif sketch == substructures[3]:
        codes = [

            ASTNode('run', None, [
                ASTNode('repeat_until_goal', 'bool_goal', [ASTNode('ifelse', 'bool_path_ahead',
                                                                   [ASTNode('do', 'bool_path_ahead',
                                                                            [ASTNode('move')]),
                                                                    ASTNode('else', 'bool_path_ahead',
                                                                            [ASTNode('ifelse',
                                                                                     'bool_path_right',
                                                                                     [ASTNode('do',
                                                                                              'bool_path_right',
                                                                                              [
                                                                                                  ASTNode(
                                                                                                      'turn_right')]),
                                                                                      ASTNode('else',
                                                                                              'bool_path_right',
                                                                                              [
                                                                                                  ASTNode(
                                                                                                      'turn_left')])
                                                                                      ])])
                                                                    ])])])

        ]

    else:
        assert "Substructure does not belong to solution code!"
        return None

    return codes



def get_minimal_code_from_sketch(sketch:SketchNode, sol_sketch:SketchNode):
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

    all_minimal_codes = get_substructures_subcodes(sketch)

    return all_minimal_codes




def get_task():
    '''

    :return: the string representation of the task
    '''

    task_string = "type\thoc\ngridsz\t(12,12)\n" \
                  "\npregrid\t1\t2\t3\t4\t5\t6\t7\t8\t9\t10\t11\t12\n" \
                  "1\t#\t#\t#\t#\t#\t#\t#\t#\t#\t#\t#\t#\n" \
                  "2\t#\t#\t#\t#\t#\t#\t#\t#\t#\t#\t#\t#\n" \
                  "3\t#\t#\t#\t#\t#\t#\t#\t#\t#\t#\t#\t#\n" \
                  "4\t#\t#\t#\t#\t#\t+\t#\t#\t#\t#\t#\t#\n" \
                  "5\t#\t#\t#\t#\t#\t.\t.\t.\t.\t#\t#\t#\n" \
                  "6\t#\t#\t#\t#\t#\t#\t#\t#\t.\t#\t#\t#\n" \
                  "7\t#\t#\t#\t#\t.\t.\t.\t#\t.\t#\t#\t#\n" \
                  "8\t#\t#\t#\t#\t.\t#\t.\t.\t.\t#\t#\t#\n" \
                  "9\t#\t#\t#\t#\t.\t#\t#\t#\t#\t#\t#\t#\n" \
                  "10\t#\t#\t#\t#\t#\t#\t#\t#\t#\t#\t#\t#\n" \
                  "11\t#\t#\t#\t#\t#\t#\t#\t#\t#\t#\t#\t#\n" \
                  "12\t#\t#\t#\t#\t#\t#\t#\t#\t#\t#\t#\t#\n" \
                  "agentloc\t(5,9)\n" \
                  "agentdir\tnorth\n"

    return task_string


def get_solution_code():
    '''

    :return: the solution code of the task
    '''

    code = ASTNode('run', None, [
        ASTNode('repeat_until_goal', 'bool_goal', [ASTNode('ifelse', 'bool_path_ahead',
                                                           [ASTNode('do', 'bool_path_ahead',
                                                                    [ASTNode('move')]),
                                                            ASTNode('else', 'bool_path_ahead',
                                                                    [ASTNode('ifelse',
                                                                             'bool_path_right',
                                                                             [ASTNode('do',
                                                                                      'bool_path_right',
                                                                                      [
                                                                                          ASTNode(
                                                                                              'turn_right')]),
                                                                              ASTNode('else',
                                                                                      'bool_path_right',
                                                                                      [
                                                                                          ASTNode(
                                                                                              'turn_left')])
                                                                              ])])
                                                            ])])])
    sketch = GenerateSketch(code, type='hoc')
    type = 'hoc'
    return code, sketch._sketch_without_A, type

def get_solution_code_symast_format():
    '''

    :return: the solution code in AST format
    '''
    code = AST('run', [
        AST('while(bool_goal)', [
        AST('ifelse(bool_path_ahead)', [
            AST('do', [AST('move')]),
            AST('else', [
                AST('ifelse(bool_path_right)', [
                    AST('do', [AST('turn_right')]),
                    AST('else', [AST('turn_left')])
                ])
            ])
        ])

    ])
        ])

    return code, code.size()


def get_student_attempt():

    #### Basic blocks
    stu_0 = ASTNode('run', None, [
        ASTNode('move'), ASTNode('move'), ASTNode('move'),
        ASTNode('turn_right'),
        ASTNode('move'), ASTNode('move'), ASTNode('move'),
        ASTNode('turn_left'),
        ASTNode('move'), ASTNode('move'), ASTNode('move'),
        ASTNode('turn_right'),
        ASTNode('move'), ASTNode('move'), ASTNode('move'), ASTNode('move'),
        ASTNode('turn_left'),
        ASTNode('move'), ASTNode('move'), ASTNode('move'), ASTNode('move'),
        ASTNode('turn_right'),
        ASTNode('move'), ASTNode('move')
    ])
    sketch_0 = GenerateSketch(stu_0, type='hoc')
    return stu_0, sketch_0._sketch_without_A

def generate_input(inputfolder = 'data/demo/fig1/', inputfolder_temp = 'data/demo/fig1/temp_latex/'):
    task= get_task()
    solcode, solsketch, type = get_solution_code()
    stuattempt, stusketch = get_student_attempt()

    # generate the input task, code, and student attempt (txt, json format)
    # create the folder if it does not exist
    if not os.path.exists(inputfolder):
        os.makedirs(inputfolder)
    with open(inputfolder + 'task_Tin.txt', 'w') as fp:
        fp.write("{}".format(task))
    fp.close()
    # save the sol-code file
    solcode_json = ast_to_json(solcode)
    with open(inputfolder + 'code_Cin_solution.json', 'w', encoding='utf-8') as fp:
        json.dump(solcode_json, fp, ensure_ascii=False, indent=4)
    solsketch_json = sketch_to_json(solsketch)
    # with open(inputfolder + 'code_struct.json', 'w', encoding='utf-8') as fp:
    #     json.dump(solsketch_json, fp, ensure_ascii=False, indent=4)

    stujson = ast_to_json(stuattempt)
    stusketch_json = sketch_to_json(stusketch)
    filename = 'code_Cin_student'
    with open(inputfolder + filename + '.json', 'w', encoding='utf-8') as fp:
        json.dump(stujson, fp, ensure_ascii=False, indent=4)


    return task, solcode, solsketch, stuattempt, stusketch


def get_sketch_hint(student_sketch, solution_sketch, type='hoc'):
    sketch_hint = get_sketch_multihop_2(student_sketch, solution_sketch, type=type)
    return sketch_hint




def generate_all_images(inputfolder='data/demo/fig1/', inputfolder_temp='data/demo/fig1/temp_latex/'):

    # create the temo_latex folder if it doesn't exist
    if not os.path.exists(inputfolder_temp):
        os.makedirs(inputfolder_temp)

    # generate the input code  image
    code_script = gen_latex_script_code(inputfolder + 'code_Cin_solution.json')
    with open(inputfolder_temp + 'code_Cin_solution.tex', 'w') as fp:
        fp.write("%s" % code_script)

    # generate the image file
    input_path = inputfolder_temp + 'code_Cin_solution.tex'
    os.system("pdflatex -interaction=nonstopmode -output-directory data/demo/fig1/temp_latex %s" % (input_path))
    output_path = inputfolder_temp + 'code_Cin_solution.pdf'
    shutil.copyfile(output_path, 'data/demo/fig1/code_Cin_solution.pdf')
    # os.system("convert -density 1200 -quality 100 data/demo/fig1/temp_latex/code_Cin_solution.pdf %s" % output_path)

    # generate the input student code image
    code_script = gen_latex_script_code(inputfolder + 'code_Cin_student.json')
    with open(inputfolder_temp + 'code_Cin_student.tex', 'w') as fp:
        fp.write("%s" % code_script)

    # generate the image file
    input_path = inputfolder_temp + 'code_Cin_student.tex'
    os.system("pdflatex -interaction=nonstopmode -output-directory data/demo/fig1/temp_latex %s" % (input_path))
    output_path = inputfolder_temp + 'code_Cin_student.pdf'
    shutil.copyfile(output_path, 'data/demo/fig1/code_Cin_student.pdf')
    # os.system("convert -density 1200 -quality 100 data/demo/fig1/temp_latex/code_Cin_student.pdf %s" % output_path)


    # generate the output code img
    # generate the input code  image
    code_script = gen_latex_script_code(inputfolder + 'code_Cquiz.json')
    with open(inputfolder_temp + 'code_Cquiz.tex', 'w') as fp:
        fp.write("%s" % code_script)

    # generate the image file
    input_path = inputfolder_temp + 'code_Cquiz.tex'
    os.system("pdflatex -interaction=nonstopmode -output-directory data/demo/fig1/temp_latex %s" % (input_path))
    output_path = inputfolder_temp + 'code_Cquiz.pdf'
    shutil.copyfile(output_path, 'data/demo/fig1/code_Cquiz.pdf')
    # os.system("convert -density 1200 -quality 100 data/demo/fig1/temp_latex/code_Cquiz.pdf %s" % output_path)


    # generates the output code + mcq image
    with open(inputfolder + 'code_Cquiz.json', 'r') as fp:
        code_json = json.load(fp)

    code_script,_ = parse_ast_blank(code_json)
    with open(inputfolder_temp + 'code_Cquiz_with_blank.tex', 'w') as fp:
        fp.write("%s" % code_script)

    # generate the image file
    input_path = inputfolder_temp + 'code_Cquiz_with_blank.tex'
    os.system("pdflatex -interaction=nonstopmode -output-directory data/demo/fig1/temp_latex %s" % (input_path))
    output_path = inputfolder_temp + 'code_Cquiz_with_blank.pdf'
    shutil.copyfile(output_path, 'data/demo/fig1/code_Cquiz_with_blank.pdf')
    # os.system("convert -density 1200 -quality 100 data/demo/fig1/temp_latex/code_Cquiz_with_blank.pdf %s" % output_path)

    ## MCQ image file
    mcq_script = gen_output_mcq_script('hoc')
    with open(inputfolder_temp + 'quiz_options.tex', 'w') as fp:
        fp.write("%s" % mcq_script)

    # generate the image file
    input_path = inputfolder_temp + 'quiz_options.tex'
    os.system("pdflatex -interaction=nonstopmode -output-directory data/demo/fig1/temp_latex %s" % (input_path))
    output_path = inputfolder_temp + 'quiz_options.pdf'
    shutil.copyfile(output_path, 'data/demo/fig1/quiz_options.pdf')
    # os.system("convert -density 1200 -quality 100 data/demo/fig1/temp_latex/quiz_options.pdf %s" % output_path)


    ## generates the input task img
    # add the task.tex file
    type, loc, dir, mat = parse_task_file(inputfolder + 'task_Tin.txt')
    task_script = gen_latex_script_task(type, loc, dir, mat)
    ## save it in a file
    with open(inputfolder_temp + 'task_Tin.tex', 'w') as fp:
        fp.write("%s" % task_script)
    # run the command to generate the pdf files, jpg files
    input_path = inputfolder_temp + 'task_Tin.tex'
    os.system("pdflatex -output-directory data/demo/fig1/temp_latex %s" % (input_path))
    output_path = inputfolder_temp + 'task_Tin.pdf'
    shutil.copyfile(output_path, 'data/demo/fig1/task_Tin.pdf')
    # os.system("convert -density 1200 -quality 100 data/demo/fig1/temp_latex/task_Tin.pdf %s" % output_path)

    ### generates the task image
    # add the task.tex file
    type, loc, dir, mat = parse_task_file(inputfolder + 'task_Tquiz.txt')
    task_script = gen_latex_script_task(type, loc, dir, mat)
    ## save it in a file
    with open(inputfolder_temp + 'task_Tquiz.tex', 'w') as fp:
        fp.write("%s" % task_script)
    # run the command to generate the pdf files, jpg files
    input_path = inputfolder_temp + 'task_Tquiz.tex'
    os.system("pdflatex -output-directory data/demo/fig1/temp_latex %s" % (input_path))
    output_path = inputfolder_temp + 'task_Tquiz.pdf'
    shutil.copyfile(output_path, 'data/demo/fig1/task_Tquiz.pdf')
    # os.system("convert -density 1200 -quality 100 data/demo/fig1/temp_latex/task_Tquiz.pdf %s" % output_path)

    return 0








if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Run Demo for Code.org task: HOC20.')
    parser.add_argument('-i', '--latex_images_flag', help='Boolean flag to generate images for the quiz: 0 --> do not generate img; 1 --> generate img', required=True, type=int)
    args = vars(parser.parse_args())
    # img flag
    if args['latex_images_flag'] == 0:
        img_flag = False
    else:
        img_flag = True



    # output data folder
    data_output = 'data/demo/fig1/'
    if not os.path.exists(data_output):
        os.makedirs(data_output)
    if not os.path.exists(data_output + 'temp_misc/'):
        os.makedirs(data_output + 'temp_misc/')
    # generate input data
    task, solcode, solsketch, stuattempt, stusketch = generate_input()
    sol_code_symast, sol_size = get_solution_code_symast_format()

    # generate a popquiz
    # get the sketch hint
    sketch_hint = get_sketch_hint(stusketch, solsketch)
    print("******************************************************* Stage 1: Generating the Pop Quiz Sketch Squiz")
    print("Sketch Hint Squiz:")
    print(sketch_hint)

    # get the minimal code and save it
    print("******************************************************* Stage 2: Synthesizing (Tquiz, Cquiz) from Squiz")
    print("Obtaining minimal code for Squiz.... (this may take upto a minute!).....")
    min_code_set = get_minimal_code_from_sketch(sketch_hint, solsketch)
    min_code, _, min_task, min_start_karel_world, min_end_karel_world, = get_single_minimal_code_from_set(min_code_set,
                                                                                                          data_output,
                                                                                                          type='hoc')
    # save the min_code
    min_code_name = SUBSTRUCTURE_CODEFILE_PREFIX
    min_code_json = ast_to_json(min_code)
    print("Minimal JSON code from Squiz:", min_code_json)
    with open(data_output + 'temp_misc/' + min_code_name + '.json', 'w') as fp:
        json.dump(min_code_json, fp, indent=4)

    # generate all the task-codes
    # get the minimal code for the task-substructure
    with open(data_output + '/temp_misc/subcode.json', 'r') as fp:
        mincode_dict = json.load(fp)
    mincode = json_to_ast(mincode_dict)
    max_blk_size = 2  # fixed to 2

    # this routine also saves the task-code pair
    print("Synthesizing a task-code pair from minimal code...(this may take a couple of minutes!).....")
    total_codes = get_single_task_code_pair_from_minimal_code('hoc', 3, mincode, max_blk_size,
                                                                    sol_code_symast,
                                                                    bucket_sample_size=1,
                                                                    delta_debugging_sample_size=1,
                                                                    output_folder=data_output,
                                                              verbose=False)




    # generate the code with blank
    print("******************************************************* Stage 3: Generating Multi-Choice Question from (Tquiz, Cquiz)")
    with open('data/demo/fig1/code_Cquiz.json', 'r') as f:
        code_cquiz = json.load(f)
    code_with_blank, mcq_option = get_blank_token_in_json(code_cquiz, type='hoc')
    with open('data/demo/fig1/code_Cquiz_with_blank.json', 'w') as f:
        json.dump(code_with_blank, f, indent=4)

    print("(Tquiz, Cquiz) generated.")
    # generate the images for the popquiz
    if img_flag:
        print("******************************************************* Popquiz Image: Generating Images for the popquiz: (Tquiz, Cquiz)")
        time.sleep(10)
        _ = generate_all_images()


