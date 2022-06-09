import json
import os
import sys
import collections
sys.path.append("..")

from code.utils.sketch import SketchNode as SketchNode
from code.utils.sketch import generate_nbs_with_node_anywhere as generate_nbs_with_node_anywhere
from code.utils.sketch import json_to_sketch as json_to_sketch
from code.utils.sketch import sketch_to_json as sketch_to_json
from code.utils.sketch import generate_neighbors as generate_neighbors
from code.utils.sketch import generate_unique_neighbors as generate_unique_neighbors
from code.utils.sketch import tree_edit_distance as tree_edit_distance
from code.utils.sketch import with_deleted_node as with_deleted_node


MAX_NUM = 1000


def get_counts_of_token(node: SketchNode, token_type):
    token_count = 0
    for c in node.children():
        token_count += get_counts_of_token(c, token_type)

    if node._type == token_type:
        token_count += 1

    return token_count


def break_ties(hint_list: list, stusketch: SketchNode):
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





def get_neighbors_within_one_hop(sketch: SketchNode, type='hoc'):
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



def get_all_min_hop_sketch(student_sketch: SketchNode, solution_sketch: SketchNode, type= 'hoc'):
    ## get the immediate neighbors of the student sketch
    neighbors = get_neighbors_within_one_hop(student_sketch, type)
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

def get_sketch_one_hop(student_sketch: SketchNode, solution_sketch: SketchNode, type= 'hoc'):

    all_valid_hints = get_all_min_hop_sketch(student_sketch, solution_sketch, type)
    one_hint = break_ties(all_valid_hints, student_sketch)

    return one_hint
