import json
import os
import sys
import collections
sys.path.append("..")


import json
import os
import sys
import copy
import collections
sys.path.append("..")
from code.utils.ast import ASTNode as ASTNode
from code.utils.ast import get_hash_code_of_ast, ast_to_json
from code.utils.code2richsketch import GenerateRichSketch
from code.utils.code2richsketch import get_hash_code_of_sketch
from code.utils.ast import json_to_ast as json_to_ast
from code.utils.rich_sketch import RichSketchNode as RichSketchNode
from code.utils.rich_sketch import generate_nbs_with_node_anywhere as generate_nbs_with_node_anywhere
from code.utils.rich_sketch import json_to_sketch as json_to_sketch
from code.utils.rich_sketch import sketch_to_json as sketch_to_json
from code.utils.rich_sketch import generate_neighbors as generate_neighbors
from code.utils.rich_sketch import generate_unique_neighbors as generate_unique_neighbors
from code.utils.rich_sketch import tree_edit_distance as tree_edit_distance, tree_edit_distance_modified
from code.utils.rich_sketch import get_astnode_from_sketch, add_missing_do_else_nodes
from code.utils.ast import tree_edit_distance as ast_tree_edit_distance
from code.utils.ast import generate_unique_neighbors_with_basic_action_only, tree_equality


MAX_NUM = 1000


def remove_action_nodes(sketch: RichSketchNode):
    # remove A_BLOCK nodes
    queue = collections.deque([sketch])
    while len(queue):
        for i in range(len(queue)):
            node = queue.popleft()
            delete_indices = []
            for j in range(len(node._children)):
                if node._children[j]._type == 'A':
                    delete_indices.append(j)
                # if node._children[j]._type == 'do':
                #     delete_indices.append(j)
                # if node._children[i]._type == 'else':
                #     delete_indices.append(j)

            if len(delete_indices) != 0:
                for k in sorted(delete_indices, reverse=True):
                    # node = node.with_removed_child(k)
                    node._children.pop(k)
                    # print("Node", node)

            for child in node._children:
                queue.append(child)
            # print("Queue:", queue)

    # print("Sketch:", sketch)
    sketch._hash = get_hash_code_of_sketch(sketch)
    sketch_json = sketch_to_json(sketch)
    sketch = json_to_sketch(sketch_json)
    return sketch


def get_counts_of_token(node: RichSketchNode, token_type):
    token_count = 0
    for c in node.children():
        token_count += get_counts_of_token(c, token_type)

    if node._type == token_type:
        token_count += 1

    return token_count


def break_ties(hint_list: list, stusketch: RichSketchNode):
    if len(hint_list) == 1:
        return hint_list[0]
    same_depth = {}
    for ele in hint_list:
        if ele.depth() not in same_depth.keys():
            same_depth[ele.depth()] = [ele]
        else:
            same_depth[ele.depth()].append(ele)

    # get the elements with the min depth
    min_depth = min(same_depth.keys())
    min_depth_sketch = same_depth[min_depth]
    if len(min_depth_sketch) == 1:
        print("Broke ties based on depth of tree")
        return min_depth_sketch[0]

    # if tie still exists get the counts of the tokens and break ties according to the order:
    # repeat > repeat_until_goal > while > if_only > if_else
    token_based_ties = {'repeat': [], 'repeat_until_goal': [], 'while': [], 'if_only': [], 'if_else': []}
    for ele in min_depth_sketch:
        tokencounts_ele = {
                        'repeat': max(-stusketch._n_repeat+ele._n_repeat,0),
                        'repeat_until_goal': max(-stusketch._n_repeat_until_goal+ele._n_repeat_until_goal,0),
                        'while': max(-stusketch._n_while+ele._n_while,0),
                        'if_only': max(-stusketch._n_if_only+ele._n_if_only,0),
                        'if_else': max(-stusketch._n_if_else+ele._n_if_else,0)
                        }
        print(ele, ele._n_repeat, tokencounts_ele)
        max_token = max(tokencounts_ele.values())
        for key, value in tokencounts_ele.items():
            if max_token == value:
                token_based_ties[key].append(ele)

    print(token_based_ties)
    for key in token_based_ties.keys():
        if len(token_based_ties[key]) == 0:
            continue
        else:
            print("Broke ties based on node type")
            return token_based_ties[key][0]

    return None





def get_neighbors_within_one_hop(sketch: RichSketchNode, type='hoc'):
    ## get the immediate neighbors of the student sketch
    neighbors = generate_unique_neighbors(sketch, type)
    #print("Neighbors:", neighbors)
    # ## prune the elements to combine the 'A' nodes after routine
    # pruned_neighbors = [prune_blocks(s) for s in neighbors]
    # pruned_neighbors = list(set(pruned_neighbors))
    ## neighbors within 1-hop of sketch
    #one_hop_nbs = [s for s in neighbors if tree_edit_distance(s, sketch) < 4]
    one_hop_nbs = [s for s in neighbors]

    return one_hop_nbs



def get_all_min_hop_sketch(student_sketch: RichSketchNode, solution_sketch: RichSketchNode, type= 'hoc'):
    ## get the immediate neighbors of the student sketch
    neighbors = get_neighbors_within_one_hop(student_sketch, type)
    if student_sketch == solution_sketch:
         neighbors.append(student_sketch)

    ## compute the tree-edit distance for each neighbor and return the node with the minimum distance
    dist_dict = {}
    hint_code = student_sketch
    for ele in neighbors:
        d = tree_edit_distance(ele, solution_sketch)
        if d not in dist_dict.keys():
            dist_dict[d] = [ele]
        else:
            dist_dict[d].append(ele)
        # if d <= min_distance:
        #     min_distance = d
        #     hint_code = ele

    # get all the neighbors with the minimum distance
    min_distance = min(dist_dict.keys())
    all_valid_hints = dist_dict[min_distance]

    return all_valid_hints

def get_sketch_one_hop(student_sketch: RichSketchNode, solution_sketch: RichSketchNode, type= 'hoc'):

    all_valid_hints = get_all_min_hop_sketch(student_sketch, solution_sketch, type)
    one_hint = break_ties(all_valid_hints, student_sketch)

    return one_hint


def obtain_code_from_sketchhint(student_sketch_true: RichSketchNode, hint_true: RichSketchNode, type='hoc'):
    queue = collections.deque([[student_sketch_true, hint_true]])
    # assumption for this routine is that the student_sketch, solution_sketch contains all the node_vals, boolean_vals with it
    while len(queue):
        for i in range(len(queue)):
            all_sketches = queue.popleft()
            student_sketch = all_sketches[0]
            hint =  all_sketches[1]
            if student_sketch is None or hint is None:
                pass
            else:
                student_children = [ele._type for ele in student_sketch._children]
                student_children_without_A = [[k,ele] for k, ele in enumerate(student_children) if ele != "A"]
                student_only_types = [ele[1] for ele in student_children_without_A ]
                hint_children = [ele._type for ele in hint._children]
                if len(student_only_types) > len(hint_children): # node deleted for sure
                    missing_ele = set(student_only_types) - set(hint_children)
                    all_id = []
                    for ele in missing_ele:
                        id = student_only_types.index(ele) # id of node to be deleted
                        all_id.append(id)
                    for index in sorted(all_id, reverse=True):
                        student_only_types.pop(index)
                        k_id = student_children_without_A[index][0]
                        student_children_without_A.pop(index)
                        student_children.pop(k_id)
                        student_sketch._children.pop(k_id)

                    return student_sketch_true


                else: #node added: hint_children >= student_only_types
                    if len(hint_children) > len(student_only_types): # child added
                        missing_ele = set(hint_children) - set(student_only_types)
                        all_id = []
                        for ele in missing_ele:
                            id = hint_children.index(ele)  # id of node to be deleted
                            all_id.append([id, ele])
                        for index in sorted(all_id, reverse=True):
                            student_only_types.insert(index[0], index[1])
                            # k_id = student_children_without_A[index[0]][0]
                            student_children_without_A.insert(-1, index[1])
                            student_children.insert(-1, index[1])
                            if index[1] == "repeat":
                                # node_type_str, node_type_condition=None, children=[], node_type_enum=None, conditional_val=None, node_val=[]
                                cond_val = "3"
                                new_node = RichSketchNode(index[1], node_type_condition="X", conditional_val=cond_val)
                            elif index[1] == "if_else" or index[1]._type == "if_only" or index[1]._type == "while":
                                cond_val = "bool_path_ahead"
                                new_node = RichSketchNode(index[1], node_type_condition="bool_cond", conditional_val=cond_val)
                            else: # repeat_until_goal
                                cond_val = "bool_goal"
                                new_node = RichSketchNode(index[1], node_type_condition="bool_cond", conditional_val=cond_val)
                            student_sketch._children.insert(-1, new_node)
                        return student_sketch_true
                    else: # sizes are equal
                        compare_all = all(map(lambda x, y: x == y, hint_children, student_only_types))
                        if compare_all:
                            for i in range(len(student_children_without_A)):
                                kid = student_children_without_A[i][0]
                                queue.append([student_sketch._children[kid], hint._children[i]])
                        else: # assuming only single element and different -- hint has a new node
                            missing_ele = set(hint_children) - set(student_only_types)
                            all_id = []
                            for ele in missing_ele:
                                id = hint_children.index(ele)  # id of node to be replaced
                                all_id.append([id, ele])
                            for index in sorted(all_id, reverse=True):
                                student_only_types[index[0]] =  index[1] # replace the node type
                                k_id = student_children_without_A[index[0]][0]
                                new_children = [student_sketch._children[k_id]]
                                student_children_without_A[index[0]] = [index[0], index[1]]
                                student_children[k_id] = index[1]
                                if index[1] == "repeat":
                                    # node_type_str, node_type_condition=None, children=[], node_type_enum=None, conditional_val=None, node_val=[]
                                    cond_val = "3"
                                    new_node = RichSketchNode(index[1], node_type_condition="X", children=new_children,
                                                              conditional_val=cond_val)
                                elif index[1] == "if_else" or index[1] == "if_only" or index[1] == "while":
                                    cond_val = "bool_path_ahead"
                                    new_node = RichSketchNode(index[1], node_type_condition="bool_cond", children=new_children,
                                                              conditional_val=cond_val)
                                else:  # repeat_until_goal
                                    cond_val = "bool_goal"
                                    new_node = RichSketchNode(index[1], node_type_condition="bool_cond", children=new_children,
                                                              conditional_val=cond_val)
                                student_sketch._children[k_id] = new_node
                                return student_sketch_true
                                # for i in range(len(student_children_without_A)):
                                #     kid = i[0]
                                #     queue.append([student_sketch._children[kid], hint._children[i]])
                                #
                                #
                                #
    return student_sketch_true



# returns the final ASTNode for one-hop-action hint
def get_astnode_from_sketchhint(modified_sketch: RichSketchNode, type='hoc', id='18'):
    astnode = get_astnode_from_sketch(modified_sketch, type=type, id=id)

    return astnode


def get_basic_action_hint(student_code: ASTNode, solution_code: ASTNode, type='hoc'):
    ## get the immediate neighbors of the student code
    neighbors = generate_unique_neighbors_with_basic_action_only(student_code, type)
    print("All neighbors:", neighbors)
    all_nbs = []
    for ele in neighbors:
        if ast_tree_edit_distance(student_code, ele) < 2:
            all_nbs.append(ele)

    all_nbs.append(student_code)
    # print(all_nbs)


    ## compute the tree-edit distance for each neighbor and return the node with the minimum distance
    min_distance = MAX_NUM
    hint_code = student_code
    for ele in all_nbs:
        d = ast_tree_edit_distance(ele, solution_code)
        if d <= min_distance:
            min_distance = d
            print("Min distance:", d, ele)
            hint_code = ele

    return hint_code


def obtain_code_from_sketchhint_2(student_sketch: RichSketchNode, sketch_hint: RichSketchNode, type='hoc'):
    # get the neighbors of the student sketch
    ## get the immediate neighbors of the student code
    neighbors = list(generate_unique_neighbors(student_sketch, type))
    print("All neighbors:", neighbors)
    min_distance = MAX_NUM
    hint_code = student_sketch
    sketch_hint_mod = add_missing_do_else_nodes(sketch_hint)
    for ele in neighbors:
        d = ast_tree_edit_distance(ele, sketch_hint_mod)
        if d <= min_distance:
            min_distance = d
            hint_code = ele

    return hint_code


def obtain_code_from_sketchhint_3(student_sketch: RichSketchNode, sketch_hint: RichSketchNode, type='hoc'):
    # get the neighbors of the student sketch
    ## get the immediate neighbors of the student code
    print("Student sketch:", student_sketch)
    neighbors = list(generate_unique_neighbors(student_sketch, type, debug_flag=False))
    print("All neighbors:", neighbors)
    hint_code = student_sketch
    sketch_hint_mod = add_missing_do_else_nodes(sketch_hint)

    # send all the neighbors to the new routine to check whose structures match that of the sketch hint
    candidate_sketches = obtain_compact_sketch_and_compare(neighbors, sketch_hint_mod, student_sketch)
    print("All candidate states:", candidate_sketches)
    # [first_sketch_with_A, first_sketch_without_A, sketch_hint]
    hint_code = candidate_sketches[0][0] # take the first element

    return hint_code



### main routine that will generate the codehint
def get_code_hint(student_code: ASTNode, solution_code: ASTNode, type='hoc', id='18'):
    '''

    :param student_code: ASTNode
    :param solution_code: ASTNode
    :param type: hoc/karel
    :return: final ASTNode code-hint
    '''
    stusketch = GenerateRichSketch(student_code)._sketch_without_A
    stusketch_with_A = GenerateRichSketch(student_code)._raw_sketch
    solsketch = GenerateRichSketch(solution_code)._sketch_without_A
    # solsketch_with_A = GenerateRichSketch(solution_code)._raw_sketch

    if stusketch == solsketch: # give simple basic action-based hint
        print("Obtaining basic action hint as structures match")
        hint = get_basic_action_hint(student_code, solution_code, type=type)
    else: # give the one-hop sketch based hint
        sketch_hint = get_sketch_one_hop(stusketch, solsketch, type=type) # uses all sketches without A
        print("One-hop sketch hint:", sketch_hint)

        ########### OLD
        # modified_sketch = obtain_code_from_sketchhint(stusketch_with_A, sketch_hint, type=type) # use student sketch with A
        # print("Modified Sketch hint:", modified_sketch)
        # modified_sketch = obtain_code_from_sketchhint_2(stusketch_with_A, sketch_hint, type=type) # use student sketch with A
        # print("Modified Sketch hint:", modified_sketch)

        print("Student sketch:", stusketch_with_A)
        modified_sketch = obtain_code_from_sketchhint_3(stusketch_with_A, sketch_hint, type=type)
        print("Modified Sketch hint:", modified_sketch)
        hint = get_astnode_from_sketchhint(modified_sketch, type=type, id=id)

    return hint


def obtain_compact_sketch_and_compare(all_sketches:list, sketch_hint:RichSketchNode, student_sketch:RichSketchNode):
    '''

    :param all_sketches: contains A
    :param sketch_hint: No A
    :param student_sketch: contains A
    :return: single sketch from all_sketches
    '''

    # get the hash map of the sketch_hint
    sketch_hint._hash = get_hash_code_of_sketch(sketch_hint)
    student_sketch_copy = copy.deepcopy(student_sketch)
    student_sketch_without_A = remove_action_nodes(student_sketch_copy)
    candidate_sketches = []
    for ele in all_sketches:
        # remove the A nodes from ele
        ele_copy = copy.deepcopy(ele)
        ele_without_A = remove_action_nodes(ele_copy)
        if ele_without_A == sketch_hint:
            candidate_sketches.append([ele, ele_without_A, sketch_hint])


    if len(candidate_sketches) == 0: # to ensure that there is atleast one element -- by default the student's code as a hint
        candidate_sketches.append([student_sketch, student_sketch_without_A, sketch_hint])

    return candidate_sketches

def wrapper_get_code_hint(studentcode_json:dict, solutioncode_json:dict, type='hoc', id='18'):
    # get the student astnode
    student_code = json_to_ast(studentcode_json)
    solution_code = json_to_ast(solutioncode_json)

    # get the code hint
    hint = get_code_hint(student_code, solution_code, type=type, id=id)
    # convert the hint into json
    hint_json = ast_to_json(hint)
    return hint_json

