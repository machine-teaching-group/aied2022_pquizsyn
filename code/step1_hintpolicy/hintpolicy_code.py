import json
import os
import sys
sys.path.append("..")
from code.utils.ast import ASTNode as ASTNode
from code.utils.ast import json_to_ast as json_to_ast
from code.utils.ast import ast_to_json as ast_to_json
from code.utils.ast import generate_neighbors as generate_neighbors
from code.utils.ast import generate_unique_neighbors as generate_unique_neighbors
from code.utils.ast import generate_unique_neighbors_with_basic_action_only
from code.utils.ast import tree_edit_distance as tree_edit_distance
from code.utils.ast import with_deleted_node as with_deleted_node

MAX_NUM = 1000

def get_shortest_path_code_edit(student_code: ASTNode, solution_code: ASTNode, type= 'hoc'):
    ## get the immediate neighbors of the student code
    neighbors = generate_unique_neighbors(student_code, type)
    all_nbs = []
    for ele in neighbors:
        if tree_edit_distance(student_code, ele) < 2:
            all_nbs.append(ele)

    all_nbs.append(student_code)
    # print(all_nbs)


    ## compute the tree-edit distance for each neighbor and return the node with the minimum distance
    min_distance = MAX_NUM
    hint_code = student_code
    for ele in all_nbs:
        d = tree_edit_distance(ele, solution_code)
        if d <= min_distance:
            min_distance = d
            hint_code = ele

    return hint_code



def get_basic_action_edit(student_code, solution_code, type='hoc'):
    ## get the immediate neighbors of the student code
    neighbors = generate_unique_neighbors_with_basic_action_only(student_code, type)
    all_nbs = []
    for ele in neighbors:
        if tree_edit_distance(student_code, ele) < 2:
            all_nbs.append(ele)

    all_nbs.append(student_code)
    # print(all_nbs)

    ## compute the tree-edit distance for each neighbor and return the node with the minimum distance
    min_distance = MAX_NUM
    hint_code = student_code
    for ele in all_nbs:
        d = tree_edit_distance(ele, solution_code)
        if d <= min_distance:
            min_distance = d
            hint_code = ele

    return hint_code






