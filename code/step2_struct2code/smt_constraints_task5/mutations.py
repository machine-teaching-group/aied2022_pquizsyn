import json
import os

from code.step2_struct2code.smt_constraints_task5.utils_ast_smt import ASTNode, json_to_ast, ast_to_json
from code.step2_struct2code.smt_constraints_task5.z3_constraints import generate_assignments, get_p_star, generate_ast_nodes_from_assignments


def get_all_mutations(thresh=2, type='karel'):
    # get the solution code
    sol_code = get_p_star()
    # get the assignments from z3
    mutations_smt = generate_assignments(thresh=thresh, id=type)
    mutations_ast = generate_ast_nodes_from_assignments(mutations_smt)
    mutations_ast = list(set(mutations_ast))
    print("Total number of mutations:", len(mutations_ast))
    # remove the solution code
    if sol_code in mutations_ast:
        mutations_ast.remove(sol_code)
    print("Total number of mutations without the solution code:", len(mutations_ast))
    # sort the mutations by size
    codes_by_size = [[ele, ele._size] for ele in mutations_ast]
    grouped_by_size = {}
    for ele in codes_by_size:
        if ele[1] not in grouped_by_size.keys():
            grouped_by_size[ele[1]] = [ele[0]]
        else:
            grouped_by_size[ele[1]].append(ele[0])
    codes_by_size_dict = {}
    for key, val in grouped_by_size.items():
        codes_by_size_dict[key] = len(val)

    print("Size dict:", codes_by_size_dict)

    return grouped_by_size, len(mutations_ast)




if __name__ == "__main__":

    output_folder = 'data/output/task-5/substructure-2/all-mutations/'
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    mut_ast, num_mutations = get_all_mutations()
    print("Total number of mutations:", num_mutations)
    ######### save the mutation codes in the folder
    code_prefix = 'code_mutation_'
    for key, val in mut_ast.items():
        codename = code_prefix + str(key+1) + "_"
        count = 1
        for ele in val:
            filename = codename + str(count) + '.json'
            json_dict = ast_to_json(ele)
            with open(output_folder+filename, 'w') as fp:
                json.dump(json_dict, fp, indent=4)
            count += 1





