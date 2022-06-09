import json
import os
from code.utils.gen_code_image import get_macros as get_macros
from code.utils.gen_code_image import get_string_from_json as get_string_from_json
from code.utils.gen_code_image import check_token_arr as check_token_arr
from code.utils.gen_code_image import get_arr_with_tokens as get_arr_with_tokens
from code.utils.gen_code_image import get_latex_code as get_latex_code


MACROS = '../utils/macros_mcq.txt'
def get_macros_mcq(macros_file = MACROS):
    script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in
    rel_path = macros_file
    abs_file_path = os.path.join(script_dir, rel_path)
    with open(abs_file_path, 'r') as f:
        data = f.read()
    return data




def parse_ast_edit(hint_code_json: dict, stu_code_json: dict):

    clean_arr_hint = get_string_from_json(hint_code_json)
    # print(clean_arr_hint)
    clean_arr_stu = get_string_from_json(stu_code_json)
    # print(clean_arr_stu)
    c_arr_hint = check_token_arr(clean_arr_hint)
    # print("Hint:", c_arr_hint)
    c_arr_stu = check_token_arr(clean_arr_stu)
    # print("Student:", c_arr_stu)

    if len(c_arr_hint) < len(c_arr_stu): # code token deleted
        if c_arr_hint[-1] != c_arr_stu[-1]:
            c_arr_hint.append('deleted!' + c_arr_stu[-1])
        else:
            for i in range(len(c_arr_stu)):
                if c_arr_hint[i] == c_arr_stu[i]:
                    continue
                else:
                    id = i
                    ele = c_arr_stu[i]
                    break
            c_arr_hint.insert(id, 'deleted!' + ele)

    elif len(c_arr_hint) > len(c_arr_hint): # code token added
        if c_arr_hint[-1] != c_arr_stu[-1]:
            c_arr_hint.append('added!' + c_arr_hint[-1])
        else:
            for i in range(len(c_arr_hint)):
                if c_arr_hint[i] == c_arr_stu[i]:
                    continue
                else:
                    id = i
                    ele = c_arr_hint[i]
                    c_arr_hint[id] = 'added!' + ele

    elif len(c_arr_hint) == len(c_arr_stu): # code token replaced
        for i in range(len(c_arr_hint)):
            if c_arr_hint[i] == c_arr_stu[i]:
                continue
            else:
                c_arr_hint[i] = 'replaced!' + c_arr_hint[i]
                break
    else:
        pass

    # print("Edited code hint arr:", c_arr_hint)
    t_arr = get_arr_with_tokens(c_arr_hint)
    script = get_latex_code(t_arr)

    # create the full script
    macros = get_macros()
    ### beginning script
    begin_script = "\n\\begin{document}\n" \
                   "\\begin{boxcode}{5cm}{0.75}{0.58}\n"

    ### ending script
    end_script = "\\\\\n" \
                 "\end{boxcode}\n" \
                 "\end{document}"

    final_script = macros + begin_script
    for ele in script:
        final_script = final_script + ele
    final_script = final_script + end_script

    return final_script



def gen_output_mcq_script(task_type):
    macros = get_macros_mcq()
    script = "\n\\begin{document}\n" \
             "\\begin{boxcode}{5cm}{0.65}{1.0}\n" \
             "\quad \\text{Edit suggested on student code.}\\\\\n" \
             "\quad \\text{See the edit marked in red.}\\\\\n" \
             "\\\n" \
             "\end{boxcode}\n" \
             "\end{document}"


    return macros + script


def gen_output_code_mcq_images(hintcodefile, stucodefile, outputfolder, type = 'hoc', inputfolder = '../../data/temp/'):

    with open(hintcodefile, 'r') as fp:
        hintcode_json = json.load(fp)
    with open(stucodefile, 'r') as fp:
        stucode_json = json.load(fp)

    code_script = parse_ast_edit(hintcode_json, stucode_json)
    with open(inputfolder + 'code.tex', 'w') as fp:
        fp.write("%s" % code_script)

    # generate the image file
    input_path = inputfolder + 'code.tex'
    os.system("pdflatex -interaction=nonstopmode -output-directory ../../data/temp %s" % (input_path))
    output_path = outputfolder + 'code.jpg'
    os.system("convert -density 1200 -quality 100 ../../data/temp/code.pdf %s" % output_path)

    print("Generated output-code image with blank")

    ## MCQ image file
    mcq_script = gen_output_mcq_script(type)
    with open(inputfolder + 'mcq.tex', 'w') as fp:
        fp.write("%s" % mcq_script)

    # generate the image file
    input_path = inputfolder + 'mcq.tex'
    os.system("pdflatex -interaction=nonstopmode -output-directory ../../data/temp %s" % (input_path))
    output_path = outputfolder + 'mcq.jpg'
    os.system("convert -density 1200 -quality 100 ../../data/temp/mcq.pdf %s" % output_path)

    print("Generated output-mcq image")

    return 0


def wrapper_call_image(task_id, student_id, alg_id, outputfolder, inputfolder):

    if task_id == '4' or task_id == '5':
        type = 'karel'
    else:
        type = 'hoc'

    outputpath = outputfolder + 'task-' + task_id + '/student-' + student_id + '/alg-' + alg_id + '/'
    hintcodefile = outputpath + 'code.json'
    stucodefile = inputfolder + 'task-' + task_id + '/student-' + student_id + '.json'


    err_code = gen_output_code_mcq_images(hintcodefile, stucodefile, outputpath, type = type)

    return err_code



