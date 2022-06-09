from z3 import *
import json
from code.utils.ast import ASTNode, json_to_ast
from code.step2_struct2code.minimal_code_to_symcode import GenerateSymASTfromCode
from code.step2_struct2code.sym_ast import AST, remove_null_nodes, valid_prog, get_ast_size, tree_edit_distance_symast, \
    add_if_else_node, get_hash_code_of_symast, get_size_of_symast, filter_codes_with_repeat_nodes
from code.step2_struct2code.z3_constraints_for_minimal_code import get_vars, get_fwdC, get_valuesC, get_condC, \
    get_elseC, get_elseC_alt, get_elimination_seq, get_conditional_seq, get_repeatC, get_prefix_suffix_betweenC, get_repeatuntilC
from code.step2_struct2code.z3_solver import gen_all


def get_set_with_distance_to_sol_code(progs: list, solution_code: AST):
    all_progs = []
    for p in progs:
        d = tree_edit_distance_symast(p, solution_code)
        all_progs.append([p, d])
        # group them by size
    grouped_codes = {}
    for c, s in all_progs:
        grouped_codes.setdefault(s, []).append((c))
    code_counts = {}
    for key in grouped_codes.keys():
        code_counts[key] = len(grouped_codes[key])

    return grouped_codes



def fill_assigns(prog, assigns, type='hoc'):
    name = prog.name
    if name in assigns:
        name = assigns[name]

    return AST(name, [fill_assigns(child, assigns)
                      for child in prog.children], type=type)


def CodeGen_from_minimal_code(prog, size_threshold:int, mincode:ASTNode, solution_code:AST, additional_vars = None, type='hoc', verbose=False):
    if additional_vars is None:
        additional_vars = {}

    names = prog.get_names_with_fixed_vals()

    X, vars_map = get_vars(names)  # Create SAT vars
    values_c = get_valuesC(X)  # And value constraints
    size_c = get_prefix_suffix_betweenC(prog, vars_map, additional_vars, type=type)
    fwds_c = get_fwdC(prog, vars_map)
    conds_c = get_condC(prog, vars_map)
    else_c = get_elseC_alt(prog, vars_map) # changed to get_elseC_alt! -- the other version: get_elseC is not compatible with get_condC
    repeat_c = get_repeatC(prog, vars_map)
    repeatuntil_c = get_repeatuntilC(prog, vars_map)
    elimnation_c = get_elimination_seq(prog, vars_map)
    conditional_if_seq, conditional_while_seq = get_conditional_seq(prog, vars_map)

    # print("Conditional constraints:", conds_c)
    # # print("Else constraints:", else_c)
    # exit(0)
    if verbose:
        print('values_c: ', values_c)
        print('size_c:', size_c)
        print('forwardInLoop_c: ', fwds_c)
        print('conditional_c: ', conds_c)
        print('else_c: ', else_c)
        print('repeat_c:', repeat_c)
        print('elimination_c:', elimnation_c)
        print('conditional seq:', conditional_if_seq, conditional_while_seq)
        print('repeat_until_c:', repeatuntil_c)
        # exit(0)


    solver = z3.Solver()  # Create solver
    solver.add(
               values_c
               + size_c
               + fwds_c
               + conds_c
               + else_c
               + repeat_c
               + repeatuntil_c
               + elimnation_c
               + conditional_if_seq
               + conditional_while_seq
               )


    values = gen_all(solver, X)  # Fetch all assigns
    print('Found {} #sat values'.format(len(values)))  # Print count
    all_valid_progs = []
    solution_code_json = solution_code.to_json()
    solution_code_str = json.dumps(solution_code_json)
    mincode_json = mincode.to_json()
    mincode_str = json.dumps(mincode_json)
    for assigns in values:
        newProg = fill_assigns(prog, assigns, type=type)
        # print(assigns)
        newProg = remove_null_nodes(newProg)
        newProg = add_if_else_node(newProg)
        # compute the hash map of the codes again due to added if-else nodes
        newProg._hash = get_hash_code_of_symast(newProg)
        # recompute the size of the obtained code
        newProg._size = get_size_of_symast(newProg)
        newProg_str = json.dumps(newProg.to_json())
        if newProg_str == solution_code_str: # removes the solution code from the set of codes
            continue
        if newProg_str == mincode_str: # remove the minimal code among generated codes
            continue
        if valid_prog(newProg, type=type) and newProg._size <= size_threshold and newProg_str != solution_code_str\
                and filter_codes_with_repeat_nodes(newProg) and newProg_str != mincode_str:
            if [newProg, newProg._size] not in all_valid_progs:
                all_valid_progs.append([newProg, newProg._size])

    return all_valid_progs




def save_codes(code_set:dict, code_id:str, output_folder='temp/'):

    for key, val in code_set.items():
        count = 1
        for ele in val:
            c_name = 'code-' + code_id + '_' + str(key) + '-' + str(count) + '.json'
            count += 1
            c_json = ele.to_json()
            with open(output_folder + c_name, 'w') as fp:
                json.dump(c_json, fp, indent=4)



def compare_code_sets(code_set_new:list, code_set_old:list):

    code_set_new_str = [json.dumps(ele.to_json()) for ele in code_set_new]
    code_set_old_str = [json.dumps(ele.to_json()) for ele in code_set_old]
    diff_new = list(set(code_set_new_str)-set(code_set_old_str))
    diff_old = list(set(code_set_old_str)-set(code_set_new_str))

    return diff_new, diff_old, len(diff_new), len(diff_old)
