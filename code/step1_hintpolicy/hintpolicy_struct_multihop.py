import json
import os
import time
import copy
import sys
import collections
sys.path.append("..")

from code.utils.sketch import SketchNode as SketchNode, tree_edit_distance
from code.step1_hintpolicy.hintpolicy_struct_hop import get_sketch_one_hop, get_neighbors_within_one_hop
from code.utils.sketch import generate_nbs_with_node_anywhere as generate_nbs_with_node_anywhere
from code.utils.sketch import json_to_sketch as json_to_sketch
from code.utils.sketch import sketch_to_json as sketch_to_json
from code.utils.sketch import generate_neighbors as generate_neighbors
from code.utils.sketch import generate_unique_neighbors as generate_unique_neighbors
from code.utils.sketch import tree_edit_distance as tree_edit_distance
from code.utils.sketch import with_deleted_node as with_deleted_node





# removes ALL leaves of a tree, and returns it
def removeLeaf(root:SketchNode, empty_list:list):
    if (len(root._children) == 0): return None  # if root itself is leaf return None
    # if root.children is a leaf node
    # then delete it from children vector
    i = 0
    while i < len(root._children):
        child = root._children[i]
        # if it is  a leaf
        if (len(child._children) == 0):
            # shifting the vector to left
            # after the point i
            for j in range(i, len(root._children) - 1):
                root._children[j] = root._children[j + 1]
                empty_list.append(root)


            # delete the last element
            root._children.pop()


            i -= 1
        i += 1

    # Remove all leaf node
    # of children of root
    for i in range(len(root._children)):
        # call function for root.children
        root._children[i] = removeLeaf(root._children[i], empty_list)


    return root


def copy_tree(root:SketchNode, mask):
    def recur(node:SketchNode):
        nonlocal mask
        if not node._children:
            # Extract the next bit from the mask and let it determine whether
            # to create the leaf copy or not:
            keep = mask & 1
            mask >>= 1
            if not keep:
                return
        # Get the children through recursion and remove None returns
        filtered_children = list(filter(None, map(recur, node._children)))
        return SketchNode(node._type, node._condition, filtered_children)

    return recur(root)


def get_trimmed_trees(root:SketchNode):
    leaf_count = sum(1 for _ in get_leaves(root))
    # Iterate all possible mask numbers (except the one that keeps all leaves)
    return [copy_tree(root, mask) for mask in range(2 ** leaf_count - 1)]





def get_leaves(node:SketchNode):  # Depth first traversal yielding all leaves

    if node._children:
        for child in node._children:
            yield from get_leaves(child)
    else:
        yield node


# checks if the sketch id valid: ifelse nodes have both do/else
def get_valid_sketch(sketch: SketchNode):
    if sketch._type == 'if_else':
        if len(sketch._children) != 2: # do,else nodes
            return False
    if sketch._type == 'if_only':
        if len(sketch._children) != 1: # do node only
            return False

    for c in sketch._children:
        flag = get_valid_sketch(c)
        if flag is False:
            return False

    return True


def get_all_substructures(sketch:SketchNode):
    depth_sketch = sketch.depth()
    # Obtain all the trees without 1/more leaves
    all_substructures = [sketch]
    for i in range(depth_sketch):
        for ele in all_substructures:
            subsketches = get_trimmed_trees(ele)
            # remove the repeated sketches
            subsketches = list(set(subsketches))
            # remove the None elements
            subsketches = [s for s in subsketches if s is not None]
            all_substructures.extend(subsketches)

    # finally remove all the repeated structures once again
    all_substructures = list(set(all_substructures))
    # remove sketches which are incomplete
    filtered = filter(lambda s: get_valid_sketch(s), all_substructures)
    all_substructures = list(filtered)

    # # remove the empty structure from the list of substructures, if the original sketch is not empty
    # if sketch != SketchNode('run', None, []):
    #     all_substructures.remove(SketchNode('run', None, []))

    return all_substructures



# def get_sketch_multihop_old(student_sketch:SketchNode, solution_sketch:SketchNode, type='hoc'):
#     # get all the substructures of the solution sketch
#     valid_substructues = get_all_substructures(solution_sketch)
#     # get the distance of the student_sketch from the solution_substructures
#     all_distances = []
#     for s in valid_substructues:
#         d = tree_edit_distance(student_sketch, s)
#         all_distances.append((s,d))
#     # sort all the substructures based on the distance to student sketch and pick the one that is closest
#     all_distances.sort(key=lambda x: x[1])
#
#     return all_distances[0][0]


def intersection(lst1, lst2):
    return list(set(lst1) & set(lst2))


def get_sketch_multihop(student_sketch:SketchNode, solution_sketch:SketchNode, type='hoc'):
    # get all the valid substructures of the solutino sketch
    valid_substructues = get_all_substructures(solution_sketch)
    # intersection of valid substructures and one-hop
    intersection_set = []
    start_nbs_old = [student_sketch]
    start_nbs = [student_sketch]
    while len(intersection_set) == 0:
        # get the neighbors of the student-sketch
        all_nbs = []
        for ele in start_nbs:
            one_hop_nbs = get_neighbors_within_one_hop(ele, type=type)
            one_hop_nbs.append(ele)
            all_nbs.extend(one_hop_nbs)
        # get the intersection with the common substructures
        start_nbs = list(set(all_nbs)-set(start_nbs_old))
        print("Neighbors:", len(start_nbs))
        start_nbs_old = start_nbs
        intersection_set = intersection(all_nbs, valid_substructues)


    if len(intersection_set) == 1:
        return intersection_set[0]
    elif len(intersection_set) == 0:
        print("No valid sketch hint found!")
        return None
    else: # multiple candidates for sketch-hint
        all_distances = []
        for s in intersection_set:
            d = tree_edit_distance(solution_sketch, s)
            all_distances.append((s,d))
        # sort all the substructures based on the distance to student sketch and pick the one that is closest
        all_distances.sort(key=lambda x: x[1])
        return all_distances[0][0]



def get_sketch_multihop_2(student_sketch:SketchNode, solution_sketch:SketchNode, type='hoc'):
    # get all the valid substructures of the solutino sketch
    valid_substructues = get_all_substructures(solution_sketch)
    # intersection of valid substructures and one-hop
    dist_thresh = 1
    indices = []
    while len(indices) == 0:
        all_dist = [tree_edit_distance(student_sketch, s) for s in valid_substructues]
        for i, d in enumerate(all_dist):
            if d <= dist_thresh:
                indices.append(i)
        dist_thresh += 1

    intersection_set = [valid_substructues[i] for i in indices]
    # print(dist_thresh-1)
    if len(intersection_set) == 1:
        return intersection_set[0]
    else:
        all_distances = []
        for s in intersection_set:
            d = tree_edit_distance(solution_sketch, s)
            all_distances.append((s, d))
        # sort all the substructures based on the distance to solution sketch and pick the one that is closest
        all_distances.sort(key=lambda x: x[1])
        return all_distances[0][0]

