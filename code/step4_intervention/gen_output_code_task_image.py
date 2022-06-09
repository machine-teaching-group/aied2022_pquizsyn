import json
import os
import copy
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




def parse_ast_blank_for_json(code_json: dict, type='hoc'):

    clean_arr = get_string_from_json_for_json(code_json)
    c_arr = check_token_arr_for_json(clean_arr)
    c_arr.reverse()
    # print(c_arr)

    id_of_last_child = 0
    id_of_end_of_child = 0

    for i, ele in enumerate(c_arr):
        if ele == ']':
            id_of_last_child = i

        if ele == 'children[':
            id_of_end_of_child = i
            break
    # print('Id: ', len(c_arr) - id_of_last_child-2)
    if id_of_end_of_child == id_of_last_child + 1:
        return c_arr.reverse()
    else:
        c_arr.reverse()
        # print(c_arr[len(c_arr) - id_of_last_child-2])

    mcq_sol = c_arr[len(c_arr) - id_of_last_child - 2]
    if type == 'karel': #changing the type of blank to pick dropdown menu later
        c_arr[len(c_arr) - id_of_last_child - 2] = '?' # change the token to `blank'
    else:
        c_arr[len(c_arr) - id_of_last_child - 2] = '?'  # change the token to `blank'


    # convert the array into string again
    # print("JSON String:", c_arr)


    return c_arr, mcq_sol



def check_token_arr_for_json(arr: list):
    '''checks the token arr for incomplete program constructs,
    and adds empty children if needed'''
    new_arr = []
    for i in range(len(arr)-1):
        ele = arr[i]
        nele = arr[i+1]
        new_arr.append(ele)
        if 'run' in ele:
            if 'children[' not in nele:
                new_arr.append('children[')
                new_arr.append(']')
            else:
                continue

        if 'repeat' in ele and 'repeat_until_goal' not in ele:
            if 'children[' not in nele:
                new_arr.append('children[')
                new_arr.append(']')
            else:
                continue

        if 'repeat_until_goal' in ele:
            if 'children[' not in nele:
                new_arr.append('children[')
                new_arr.append(']')
            else:
                continue

        if 'while' in ele:
            if 'children[' not in nele:
                new_arr.append('children[')
                new_arr.append(']')
            else:
                continue

        if 'do' in ele:
            if 'children[' not in nele:
                new_arr.append('children[')
                new_arr.append(']')
            else:
                continue

        if 'else' in ele:
            if 'children[' not in nele:
                new_arr.append('children[')
                new_arr.append(']')
            else:
                continue


    if 'run' in arr[-1] or 'repeat' in arr[-1] or 'while' in arr[-1] or \
        'repeat_until_goal' in arr[-1] or 'do' in arr[-1] or 'else' in arr[-1]:
        new_arr.append(arr[-1])
        new_arr.append('children[')
        new_arr.append(']')
    else:
        new_arr.append(arr[-1])

    return new_arr



def get_string_from_json_for_json(json_obj: dict):
    '''works only for my json type!!'''
    json_string = json.dumps(json_obj)
    # print("Original JSON String:", json_string)
    arr = json_string.split(' ')
    # print("JSON String in arr:", arr)
    clean_arr = []
    for ele in arr:
        if '"type"' in ele:
            continue
        elif ele == '"children":':
            clean_arr.append('children[')
        elif '"run"' in ele:
            clean_arr.append('run')
        elif '"move"' in ele:
            clean_arr.append('move')
        elif '"turn_left"' in ele:
            clean_arr.append('turn_left')
        elif '"turn_right"' in ele:
            clean_arr.append('turn_right')
        elif '"pick_marker"' in ele:
            clean_arr.append('pick_marker')
        elif '"put_marker"' in ele:
            clean_arr.append('put_marker')
        elif '"A"' in ele:
            clean_arr.append('A')
        elif '"do"' in ele:
            clean_arr.append('do')
        elif '"else"' in ele and '"ifelse"' not in ele and '"if_else"' not in ele:
            clean_arr.append('else')
        else:
            if '}' in ele:
                mele = ele.split('}')
                clean_arr.append(mele[0][1:-1])
            else:
                clean_arr.append(ele[1:-2])
        if ']' in ele:
            c = ele.count(']')
            for i in range(c):
                clean_arr.append(']')

    return clean_arr


def find_pairs (array:list, n=2):
    result_pairs = []
    prev = idx = 0
    count = 1
    for i in range (0, len(array)):
        if(i > 0):
            if(array[i] == prev and array[i] == "]}"):
                count += 1
            else:
                if(count >= n):
                    result_pairs.append((idx, i))
                else:
                    prev = array[i]
                    idx = i
                count = 1
        else:
            prev = array[i]
            idx = i
    return result_pairs



def convert_token_arr_to_json(token_arr:list):
    conversion_dict = {
        'run': '"run",',
        'blank': '"blank", "children":[]},',
        'children[': '"children":',
        'repeat_until_goal(bool_goal)': '"repeat_until_goal(bool_goal)",',
        'repeat(2)': '"repeat(2)",',
        'repeat(3)': '"repeat(3)",',
        'repeat(4)': '"repeat(4)",',
        'repeat(5)': '"repeat(5)",',
        'repeat(6)': '"repeat(6)",',
        'repeat(7)': '"repeat(7)",',
        'repeat(8)': '"repeat(8)",',
        'repeat(9)': '"repeat(9)",',
        'if(bool_path_left)': '"if(bool_path_left)",',
        'if(bool_path_ahead)': '"if(bool_path_ahead)",',
        'if(bool_path_right)': '"if(bool_path_right)",',
        'if(bool_no_path_left)': '"if(bool_no_path_left)",',
        'if(bool_no_path_right)': '"if(bool_no_path_right)",',
        'if(bool_no_path_ahead)': '"if(bool_no_path_ahead)",',
        'if(bool_no_marker)': '"if(bool_no_marker)",',
        'if(bool_marker)': '"if(bool_marker)",',
        'while(bool_path_left)': '"while(bool_path_left)",',
        'while(bool_path_ahead)': '"while(bool_path_ahead)",',
        'while(bool_path_right)': '"while(bool_path_right)",',
        'while(bool_no_path_left)': '"while(bool_no_path_left)",',
        'while(bool_no_path_right)': '"while(bool_no_path_right)",',
        'while(bool_no_path_ahead)': '"while(bool_no_path_ahead)",',
        'while(bool_no_marker)': '"while(bool_no_marker)",',
        'while(bool_marker)': '"while(bool_marker)",',
        'ifelse(bool_path_left)': '"ifelse(bool_path_left)",',
        'ifelse(bool_path_ahead)': '"ifelse(bool_path_ahead)",',
        'ifelse(bool_path_right)': '"ifelse(bool_path_right)",',
        'ifelse(bool_no_path_left)': '"ifelse(bool_no_path_left)",',
        'ifelse(bool_no_path_right)': '"ifelse(bool_no_path_right)",',
        'ifelse(bool_no_path_ahead)': '"ifelse(bool_no_path_ahead)",',
        'ifelse(bool_no_marker)': '"ifelse(bool_no_marker)",',
        'ifelse(bool_marker)': '"ifelse(bool_marker)",',
        'do': '"do",',
        'else': '"else",',
        'move': '"move"},',
        'turn_left': '"turn_left"},',
        'turn_right': '"turn_right"},',
        'pick_marker': '"pick_marker"},',
        'put_marker': '"put_marker"},',
        '?': '"?"},',

    }

    new_arr = []
    last_token = None
    for ele in token_arr:
        if ele == 'children[':
            new_arr.append(conversion_dict[ele])
            last_token = 'children'
        elif ele == ']':
            new_arr.append(']}')
            last_token = None
        else: # run, hoc_actions, karel_actions, repeat, repeat_until_goal, if, ifelse, while
            if last_token == 'children':
                new_arr.append('[{"type":')
            else:
                new_arr.append('{"type":')
            new_arr.append(conversion_dict[ele])
            last_token = None



    # print("Updated json arr:", new_arr)
    # combine the last few elements, and remove the final ","
    json_arr = copy.deepcopy(new_arr)
    new_arr.reverse()
    final_token = None
    count = 0
    final_closing_string = ''
    for ele in new_arr:
        if ele == "]}":
            count += 1
            final_closing_string += ele
        else:
            final_token = ele
            break

    json_arr_new = copy.deepcopy(json_arr[:-count])
    # print(json_arr_new)
    # print("Final closing string:", final_closing_string)
    json_arr_new[-1] = final_token[:-1] # remove the final comma
    if final_closing_string is not None:
        json_arr_new[-1] = json_arr_new[-1] + final_closing_string

    # print("Final Updated json arr:", json_arr_new)

    # further combine all the ']}' occurring in between to one string and combine it with last normal token
    indices_to_be_combined = find_pairs(json_arr_new)
    indices_dict = {ele[0]:ele[1] for ele in indices_to_be_combined}
    json_arr_mod = []
    all_indices =  [[i for i in range(ele[0], ele[1])] for ele in indices_to_be_combined]
    all_indices_flat = [ele for sublist in all_indices for ele in sublist]
    for i in range(len(json_arr_new)):
        if i in indices_dict.keys():
            bracket_string = ''.join(json_arr_new[i:indices_dict[i]])
            if i!= 0:
                prev_token = json_arr_new[i-1]
                if prev_token[-1] == ",":
                    json_arr_mod.append(prev_token[:-1] + bracket_string + ',')
                else:
                    json_arr_mod.append(prev_token + bracket_string)
        elif i+1 in indices_dict.keys():
            pass
        elif i in all_indices_flat:
            pass
        else:
            json_arr_mod.append(json_arr_new[i])


    # print("Final processing of arr:", json_arr_mod)

    # combine all the singletons "]}" left with the prev token
    final_code_arr = []
    for i in range(len(json_arr_mod)-1):
        if json_arr_mod[i+1] == "]}":
            prev_token = json_arr_mod[i]
            comma_token = prev_token[-1]
            if comma_token == ',':
                final_code_arr.append(prev_token[:-1] + json_arr_mod[i+1] + ",")
            else:
                final_code_arr.append(prev_token + json_arr_mod[i+1])
        elif json_arr_mod[i] == "]}":
            pass
        else:
            final_code_arr.append(json_arr_mod[i])

    # add the last element
    final_code_arr.append(json_arr_mod[-1])
    # print("Removed singletons:", final_code_arr)

    return final_code_arr





def get_blank_token_in_json(json_code:dict, type='hoc'):

    code_with_blank_arr, mcq_option = parse_ast_blank_for_json(json_code, type=type)
    # json parsing
    parse_arr = convert_token_arr_to_json(code_with_blank_arr)
    # print("After json parsing:", parse_arr)
    # convert back to json
    combined_string = " ".join(parse_arr)
    # print("Modified json code string:", combined_string)
    modified_json_code = json.loads(combined_string)
    # print("Final Json code:", modified_json_code)

    # og_json_code_string = json.dumps(json_code)
    # # print("Original code string:", og_json_code_string)
    # print("Original JSON:", json.loads(og_json_code_string))

    return modified_json_code, mcq_option



def parse_ast_blank(code_json: dict, fill_in_blank = False):

    clean_arr = get_string_from_json(code_json)
    # print(clean_arr)
    c_arr = check_token_arr(clean_arr)
    c_arr.reverse()
    # print(c_arr)

    id_of_last_child = 0
    id_of_end_of_child = 0

    for i, ele in enumerate(c_arr):
        if ele == ']':
            id_of_last_child = i

        if ele == 'children[':
            id_of_end_of_child = i
            break
    # print('Id: ', len(c_arr) - id_of_last_child-2)
    if id_of_end_of_child == id_of_last_child + 1:
        return c_arr.reverse()
    else:
        c_arr.reverse()
        # print(c_arr[len(c_arr) - id_of_last_child-2])

    c_arr[len(c_arr) - id_of_last_child - 2] = 'blank_' +  c_arr[len(c_arr) - id_of_last_child - 2]
    # print(c_arr)

    t_arr, mcq_sol = get_arr_with_tokens(c_arr, fill_in_blank=fill_in_blank)
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

    return final_script, mcq_sol




def gen_output_mcq_script(task_type):
    macros = get_macros_mcq()
    if task_type == 'karel':
        script = "\n\\begin{document}\n" \
                 "\\begin{boxcode}{5cm}{0.65}{1.0}\n" \
                 "\quad \\textcode{Q.} \\text{Fill in the blank from: }\\\\\n" \
                 "\quad \quad \\tikz\draw[black,fill=none] (0,0) circle (.5ex); \DSLMove\\\\\n" \
                 "\quad \quad \\tikz\draw[black,fill=none] (0,0) circle (.5ex); \DSLTurnLeft\\\\\n" \
                 "\quad \quad \\tikz\draw[black,fill=none] (0,0) circle (.5ex); \DSLTurnRight\\\\\n" \
                 "\quad \quad \\tikz\draw[black,fill=none] (0,0) circle (.5ex); \DSLPutMarker\\\\\n" \
                 "\quad \quad \\tikz\draw[black,fill=none] (0,0) circle (.5ex); \DSLPickMarker\\\\\n" \
                 "\\\n" \
                 "\end{boxcode}\n" \
                 "\end{document}"

    else:
        script = "\n\\begin{document}\n" \
                 "\\begin{boxcode}{5cm}{0.65}{1.0}\n" \
                 "\quad \\textcode{Q.} \\text{Fill in the blank from: }\\\\\n" \
                 "\quad \quad \\tikz\draw[black,fill=none] (0,0) circle (.5ex); \DSLMove\\\\\n" \
                 "\quad \quad \\tikz\draw[black,fill=none] (0,0) circle (.5ex); \DSLTurnLeft\\\\\n" \
                 "\quad \quad \\tikz\draw[black,fill=none] (0,0) circle (.5ex); \DSLTurnRight\\\\\n" \
                 "\\\n" \
                 "\end{boxcode}\n" \
                 "\end{document}"


    return macros + script


def gen_output_code_mcq_images(codefile, outputfolder, type = 'hoc', inputfolder = '../../data/temp/'):

    with open(codefile, 'r') as fp:
        code_json = json.load(fp)

    code_script,_ = parse_ast_blank(code_json)
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


def wrapper_call_image(task_id, student_id, alg_id, outputfolder):

    if task_id == '4' or task_id == '5':
        type = 'karel'
    else:
        type = 'hoc'


    outputpath = outputfolder + 'task-' + task_id + '/student-' + student_id + '/alg-' + alg_id + '/'
    codefile = outputpath + 'code.json'

    err_code = gen_output_code_mcq_images(codefile, outputpath, type = type)

    return err_code


