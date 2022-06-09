import json
import os

#### latex dictionary
latex_dict = {
    'run': '\\textcode{def }\DSLRun\\textcode{()}',
    'if_only': 'if_only',
    'ifelse': 'ifelse',
    'if_else': 'if_else',
    'if':'if',
    'do': '\DSLIf',
    'else': '\DSLElse',
    'while': '\DSLWhile',
    'repeat': '\DSLRepeat',
    'repeat_until_goal': '\DSLRepeatUntil',
    'bool_path_ahead': '\DSLBoolPathAhead',
    'bool_no_path_ahead': '\DSLBoolNoPathAhead',
    'bool_path_left': '\DSLBoolPathLeft',
    'bool_no_path_left': '\DSLBoolNoPathLeft',
    'bool_path_right': '\DSLBoolPathRight',
    'bool_no_path_right': '\DSLBoolNoPathRight',
    'bool_marker': '\DSLBoolMarker',
    'bool_no_marker': '\DSLBoolNoMarker',
    'bool_goal': '\DSLBoolGoal',
    'X': '\SDSLIter',
    '2': '2',
    '3': '3',
    '4': '4',
    '5': '5',
    '6': '6',
    '7': '7',
    '8': '8',
    '9': '9',
    'A': '\SDSLAction\\\\',
    'bool_cond': '\SDSLBoolCond',
    'move': '\DSLMove\\\\',
    'turn_right': '\DSLTurnRight\\\\',
    'turn_left': '\DSLTurnLeft\\\\',
    'pick_marker': '\DSLPickMarker\\\\',
    'put_marker': '\DSLPutMarker\\\\'
}
mcq_sol_dict = {
    'move': '\DSLMove',
    'turnleft': '\DSLTurnLeft',
    'turnright': '\DSLTurnRight',
    'pickmarker': '\DSLPickMarker',
    'putmarker': '\DSLPutMarker'
}


MACROS = "macros_code.txt"

def get_macros(macros_file = MACROS):
    script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in
    rel_path = macros_file
    abs_file_path = os.path.join(script_dir, rel_path)
    with open(abs_file_path, 'r') as f:
        data = f.read()
    return data


def get_string_from_json(json_obj: dict):
    json_string = json.dumps(json_obj)
    #print(json_string)
    arr = json_string.split(' ')
    #print(arr)
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


def check_token_arr(arr: list):
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






def get_arr_with_tokens(arr: list, fill_in_blank=False):
    tokens_arr = []
    mcq_sol = ''
    for i, ele in enumerate(arr):
        if 'repeat' in ele or 'ifelse' in ele or 'while' in ele  or \
                'repeat_until_goal' in ele or 'if_only' in ele or 'if_else' in ele or 'if' in ele:
            if 'deleted!' not in ele and 'added!' not in ele and 'replaced!' not in ele:
                s = ele.split('(')
                t = s[0]
                t_latex = latex_dict[t]
                cond = s[1].split(')')
                cond_latex = latex_dict[cond[0]]
                tokens_arr.append(t_latex+'\\textcode{('+cond_latex+')}')
            else:
                if 'deleted!' in ele:
                    if 'deleted!' in ele:
                        tokens_arr.append('\\framebox[1.0\width]{\\textcolor{red}{*token-deleted*}}\\\\')
                else:
                    split_ = ele.split('!')
                    s = split_[1].split('(')
                    t = s[0]
                    t_latex = latex_dict[t]
                    cond = s[1].split(')')
                    cond_latex = latex_dict[cond[0]]
                    tokens_arr.append('\\framebox[1.0\width]{\\textcolor{red}{' + t_latex + '\\textcode{(' + cond_latex + ')}}}')

        elif ele == 'children[':
            tokens_arr.append(ele)
        elif ele == ']':
            tokens_arr.append(ele)
        elif 'do' in ele:
            if 'deleted!' not in ele and 'added!' not in ele and 'replaced!' not in ele:
                t_latex = latex_dict[ele]
                s_parent = arr[i-2]
                s = s_parent.split('(')
                cond = s[1].split(')')
                cond_latex = latex_dict[cond[0]]
                tokens_arr.append(t_latex + '\\textcode{(' + cond_latex + ')}')
            else:
                if 'deleted!' in ele:
                    if 'deleted!' in ele:
                        tokens_arr.append('\\framebox[1.0\width]{\\textcolor{red}{*token-deleted*}}\\\\')
                else:
                    split_ = ele.split('!')
                    t_latex = latex_dict[split_[1]]
                    s_parent = arr[i - 2]
                    s = s_parent.split('(')
                    cond = s[1].split(')')
                    cond_latex = latex_dict[cond[0]]
                    tokens_arr.append('\\framebox[1\width]{\\textcolor{red}{' + t_latex + '\\textcode{(' + cond_latex + ')}}}')
        else:
            if 'blank_' in ele:
                mcq_sol = ele.split('_')[1:]
                mcq_sol =  ''.join(mcq_sol)
                ## add the latex script for a empty box with '?'
                if fill_in_blank:
                    token_filled = mcq_sol_dict[mcq_sol]
                    tokens_arr.append('\\framebox[1.5\width]{' + token_filled + '}\\\\')
                else:
                    tokens_arr.append('\\framebox[8.0\width]{?}\\\\')
            elif 'deleted!' in ele or 'added!' in ele or 'replaced!' in ele:
                token = ele.split('!')
                if 'deleted!' in ele:
                    tokens_arr.append('\\framebox[1.0\width]{\\textcolor{red}{*token-deleted*}}\\\\')
                else:
                    tokens_arr.append('\\framebox[1.5\width]{\\textcolor{red}{' + latex_dict[token[1]][:-2] + '}}\\\\')
            else:
                tokens_arr.append(latex_dict[ele])

    return tokens_arr, mcq_sol








def get_latex_code(t_arr: list):

    brac_arr = []
    quad_arr = []
    script = []
    space = ''
    for i, ele in enumerate(t_arr):
        if ele == 'children[':
            if 'ifelse' in t_arr[i-1] or 'if_else' in t_arr[i-1] or 'if_only' in t_arr[i-1] or 'if' in t_arr[i-1]:
                script.append('')
                brac_arr.append('')
                quad_arr.append(space)
                space = quad_arr[-1]
            else:
                script.append('\\textcode{\{}\\\\'+'\n')
                brac_arr.append(space + '\\textcode{\}}\\\\' + '\n')
                quad_arr.append(space + '\quad')
                space = quad_arr[-1]
        elif ele == ']':
            brac = brac_arr.pop()
            script.append(brac)
            quad_arr.pop()
            if len(quad_arr) == 0:
                space = ''
            else:
                space = quad_arr[-1]
        elif ele == '\DSLMove\\\\' or ele == '\DSLTurnLeft\\\\' or \
                ele == '\DSLTurnRight\\\\' or ele == '\DSLPickMarker\\\\' or \
                ele == '\DSLPutMarker\\\\' or ele == '\SDSLAction\\\\' or ele == '\\framebox[8.0\width]{?}\\\\':
            script.append(space + ele + '\n')
        elif 'ifelse' in ele or 'if_else' in ele or 'if_only' in ele or 'if' in ele:
            continue
        else:
            script.append(space + ele)

    return script



def get_full_latex_script(code_file, macros_file = MACROS):

    macros = get_macros(macros_file)
    ### beginning script
    begin_script = "\n\\begin{document}\n" \
                   "\\begin{boxcode}{5cm}{0.75}{0.58}\n"

    ### ending script
    end_script = "\\\\\n" \
                 "\end{boxcode}\n" \
                 "\end{document}"

    with open(code_file, 'r') as f:
        code_json = json.load(f)

    clean_arr = get_string_from_json(code_json)
    c_arr = check_token_arr(clean_arr)
    t_arr, _ = get_arr_with_tokens(c_arr)

    code_script = get_latex_code(t_arr)
    final_script = macros + begin_script
    for ele in code_script:
        final_script = final_script + ele
    final_script = final_script + end_script

    return final_script


def get_code_image(jsoncodefile:str, codefolder:str, codeimg:str):
    script = get_full_latex_script(codefile)

    with open(codefolder + "/" + codeimg + '.tex', 'w') as fp:
        fp.write("%s" % script)

        # generate the image file
    input_path = codefolder + '/' + codeimg + '.tex'
    os_cmd = "pdflatex -interaction=nonstopmode -output-directory " + codefolder + " %s"
    os.system(os_cmd % (input_path))
    output_path = codefolder + "/" + codeimg + '.jpg'
    os_cmd = "convert -density 1200 -quality 100 " + codefolder + "/" + codeimg + ".pdf %s"
    os.system(os_cmd % (output_path))

    print("Generated code image")
    return 0

