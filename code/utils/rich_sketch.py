import enum
import json
import copy
import collections
import sys
sys.path.append("..")
from queue import Queue
from utils.definitions import SketchNodeType as SketchNodeType
from utils.definitions import node_str_to_sketch_type as node_str_to_sketch_type
from utils.definitions import sketchnode_to_astnode
from utils.ast import ASTNode, json_to_ast
import zss




MAX_POW = 17
MAX_SIZE = 30
MAX_DEPTH = 10



P = 1000000007
M = 10 ** MAX_POW

#### all node-types for insertion
hoc_types = ['A', 'repeat', 'repeat_until_goal', 'if_only', 'if_else']
karel_types = ['A', 'repeat', 'while', 'if_only', 'if_else']

#### modified node-types for insertion
hoc_types_mod = ['repeat', 'repeat_until_goal', 'if_only', 'if_else']
karel_types_mod = ['repeat', 'while', 'if_only', 'if_else']

def split_list(data, n):
    from itertools import combinations, chain
    for splits in combinations(range(1, len(data)), n-1):
        result = []
        prev = None
        for split in chain(splits, [None]):
            result.append(data[prev:split])
            prev = split
        yield result


def dsamepow10(num, max_pow=MAX_POW): # returns the max pow of max_pow in num
    r = 1
    while num >= max_pow:
        num = int(num // max_pow)
        r *= max_pow
    return r


def join_ints(a, b, max_pow=MAX_POW):
    return a * dsamepow10(b) * max_pow + b


class RichSketchNode:
    ''' A custom Sketch class to represent program sketches '''

    # @staticmethod
    def from_json(json_dict):
        return json_to_sketch(json_dict)

    def to_int(self):
        return self._hash

    def to_json(self):
        return sketch_to_json(self)

    def __init__(self, node_type_str, node_type_condition=None, children=[], node_type_enum=None, conditional_val=None, node_val=[]):

        self._type_enum = node_type_enum or node_str_to_sketch_type[node_type_str]
        self._type = node_type_str
        self._condition = node_type_condition
        self._condition_val = conditional_val # mainly introduced for nodes with conditional parameters X
        self._node_val = node_val # mainly introduced for Node type A: to store its list of action nodes
        self._children = children
        self._size = 0
        self._depth = 0
        self._parent = None


        self._hash = int(self._type_enum)
        if self._condition is not None:
            cond_enum = node_str_to_sketch_type[self._condition]
            self._hash = join_ints(cond_enum, self._hash, max_pow=MAX_POW)

        # counts of the constructs
        self._n_if_only = 0
        self._n_while = 0
        self._n_repeat = 0
        self._n_if_else = 0
        self._n_repeat_until_goal = 0


        for i, child in enumerate(children):
            if child._type != 'phi':
                self._size += child._size
            self._depth = max(self._depth, child._depth)
            if child._type != 'phi':
                self._hash = join_ints(child._hash*(i+1), self._hash, max_pow=MAX_POW)
            self._n_if_else += child._n_if_else
            self._n_while += child._n_while
            self._n_if_only += child._n_if_only
            self._n_repeat += child._n_repeat
            self._n_repeat_until_goal += child._n_repeat_until_goal
            child._parent = self

        if self._type_enum == SketchNodeType.A:
            self._size += 1
        elif self._type_enum == SketchNodeType.WHILE:
            self._size += 1
            self._depth += 1
            self._n_while += 1
        elif self._type_enum == SketchNodeType.REPEAT:
            self._size += 1
            self._depth += 1
            self._n_repeat += 1
        elif self._type_enum == SketchNodeType.IF_ELSE:
            self._size += 1
            self._depth += 1
            self._n_if_else += 1
        elif self._type_enum == SketchNodeType.IF_ONLY:
            self._size += 1
            self._depth += 1
            self._n_if_only += 1
        elif self._type_enum == SketchNodeType.G:
            self._size += 1
            self._depth += 1
            self._n_repeat_until_goal += 1
        elif self._type_enum == SketchNodeType.S_S:
            self._size += 1
            self._depth += 1
        elif self._type_enum == SketchNodeType.IF:
            self._size += 1
            self._depth += 1
        elif self._type_enum == SketchNodeType.ELSE:
            self._size += 1
            self._depth += 1

        else:
            pass




    def size(self):
        return self._size

    def depth(self):
        return self._depth

    def children(self):
        return self._children

    def conditional(self):
        return self._condition

    def get_rev_children(self):
        children = self._children[:]
        children.reverse()
        return children

    def n_children(self):
        return len(self._children)

    def label_print(self):
        label = self._type
        if self._condition is not None:
            label = label + ' ' + self._condition

        if self._node_val is not None:
            if len(self._node_val) == 1:
                node_vals = self._node_val[0]
            else:
                node_vals = '-'.join(self._node_val)
            label = label + ' ' + node_vals
        if self._condition_val is not None:
            label = label + ' ' + self._condition_val

        return label

    def label(self):
        return self._type

    def label_enum(self):
        return self._type_enum

    def with_label(self, label, cond):
        return RichSketchNode(label, cond, self.children())

    def with_ith_child(self, i, child):
        if must_be_last_node(child) and i + 1 != len(self._children) and i != -1:
            return None
        new_children = self._children[:i] + [child]
        if i != -1:
            new_children += self._children[i + 1:]
        return RichSketchNode(self._type, self._condition, new_children, self._type_enum, node_val=self._node_val, conditional_val=self._condition_val)

    def with_inserted_child(self, i, child):

        if i > 0 and must_be_last_node(self.children()[i-1]):
            return None
        if must_be_last_node(child) and i != len(self._children):
            return None
        if self._type == 'if_only' and i == 0:
            return None
        if self._type == 'if_else' and (i == 0 or i == 1):
            return None
        new_children = self.children().copy()
        new_children.insert(i, child)
        return RichSketchNode(self._type, self._condition, new_children, self._type_enum, node_val=self._node_val, conditional_val=self._condition_val)

    def with_inserted_parent(self, node):

        if node._type == 'if_else' or self._type == 'run':
            return None
        elif self._type == 'repeat_until_goal' and node._type == 'repeat_until_goal':
            return None
        elif self._type == 'do' or self._type == 'else':
            return None
        else:
            if node._type == 'repeat':
                return RichSketchNode(node._type, 'X', [self], node_val=self._node_val, conditional_val=self._condition_val)
            elif node._type == 'while':
                return RichSketchNode(node._type, 'bool_cond', [self], node_val=self._node_val, conditional_val=self._condition_val)
            elif node._type == 'repeat_until_goal':
                 RichSketchNode(node._type, 'bool_cond', [self], node_val=self._node_val, conditional_val=self._condition_val)
            elif node._type == 'if_only':
                return RichSketchNode(node._type, 'bool_cond', [
                    RichSketchNode('do', 'bool_cond', [self], node_val=self._node_val, conditional_val=self._condition_val)
                ])
            else:
                return None

    def with_inserted_node_anywhere(self, node):

        if self._type == 'if_only' or self._type == 'if_else':
            return None
        if self.children() is None:
            return None
        children = self.children()
        if len(children) == 0:
            return None
        max_num_splits = len(children)
        cids = list(range(max_num_splits))
        all_insertions = []
        for id in range(1,max_num_splits+1):
            split_children = list(split_list(cids, id))
            for j, schild in enumerate(split_children):
                for k in schild:
                    if node._type == 'repeat':
                        inode_c = [self._children[l] for l in k]
                        inode = RichSketchNode('repeat', 'X', inode_c)
                        old_children = copy.deepcopy(self.children())
                        k.reverse()
                        for l in k:
                            old_children.pop(l)
                        old_children.insert(k[0], inode)
                        all_insertions.append(RichSketchNode(self._type, self._condition, old_children, node_val=self._node_val, conditional_val=self._condition_val))
                    elif node._type == 'while':
                        inode_c = [self._children[l] for l in k]
                        inode = RichSketchNode('while', 'bool_cond', inode_c)
                        old_children = copy.deepcopy(self.children())
                        k.reverse()
                        for l in k:
                            old_children.pop(l)
                        old_children.insert(k[0], inode)
                        all_insertions.append(RichSketchNode(self._type, self._condition, old_children, node_val=self._node_val, conditional_val=self._condition_val))
                    elif node._type == 'repeat_until_goal':
                        inode_c = [self._children[l] for l in k]
                        inode = RichSketchNode('repeat_until_goal', 'bool_cond', inode_c)
                        old_children = copy.deepcopy(self.children())
                        k.reverse()
                        for l in k:
                            old_children.pop(l)
                        old_children.insert(k[0], inode)
                        all_insertions.append(RichSketchNode(self._type, self._condition, old_children, node_val=self._node_val, conditional_val=self._condition_val))
                    elif node._type == 'if_only':
                        inode_c = [self._children[l] for l in k]
                        inode = RichSketchNode('if_only', 'bool_cond', [
                            RichSketchNode('do', 'bool_cond', inode_c)
                        ])
                        old_children = copy.deepcopy(self.children())
                        k.reverse()
                        for l in k:
                            old_children.pop(l)
                        old_children.insert(k[0], inode)
                        all_insertions.append(RichSketchNode(self._type, self._condition, old_children, node_val=self._node_val, conditional_val=self._condition_val))
                    else:
                        continue
        return all_insertions


    def with_removed_child(self, i):
        #print(self._type, i)
        if self._type == 'if_only' or self._type == 'if_else':
            return None
        old_children = self.children()
        if old_children[i]._type == 'repeat' or \
            old_children[i]._type == 'while' or old_children[i]._type == 'repeat_until_goal':
            if len(old_children[i].children()) == 1:
                insert_child = old_children[i].children()[0]
                new_children = copy.deepcopy(old_children)
                new_children[i] = insert_child
                return RichSketchNode(self._type, self._condition, new_children, self._type_enum, node_val=self._node_val, conditional_val=self._condition_val)
            else: #len(old_children's children != 1)
                new_children = copy.deepcopy(old_children[:i])
                new_children = new_children + copy.deepcopy(old_children[i+1:]) # remove the i-th element
                counter = 0
                for ele in old_children[i]._children:
                    new_children.insert(i+counter, ele)
                    counter += 1
                return RichSketchNode(self._type, self._condition, new_children, self._type_enum, node_val=self._node_val, conditional_val=self._condition_val)
        if old_children[i]._type == 'if_only':
            #if len(old_children[i].children()[0].children()) == 1:
            insert_child = old_children[i].children()[0].children()
            new_children = copy.deepcopy(old_children)
            new_children.pop(i) # remove the i-th child
            # add the remaining children of 'do' node
            for j,nn in enumerate(insert_child):
                new_children.insert(i+j, nn)
            return RichSketchNode(self._type, self._condition, new_children, self._type_enum, node_val=self._node_val, conditional_val=self._condition_val)
        if old_children[i]._type == 'if_else':
            if(len(old_children[i].children()[0].children()) == 0 and len(old_children[i].children()[1].children()) == 0):
                new_children = old_children[:i] + old_children[i + 1:]
                return RichSketchNode(self._type, self._condition, new_children, self._type_enum, node_val=self._node_val, conditional_val=self._condition_val)
            if (len(old_children[i].children()[0].children()) == 1 and len(
                    old_children[i].children()[1].children()) == 0):
                if old_children[i].children()[0].children()[0]._type == 'A':
                    new_children = old_children[:i] + old_children[i + 1:]
                    return RichSketchNode(self._type, self._condition, new_children, self._type_enum, node_val=self._node_val, conditional_val=self._condition_val)
                else:
                    return None

            elif (len(old_children[i].children()[0].children()) == 0 and len(
                    old_children[i].children()[1].children()) == 1):
                if old_children[i].children()[1].children()[0]._type == 'A':
                    new_children = old_children[:i] + old_children[i + 1:]
                    return RichSketchNode(self._type, self._condition, new_children, self._type_enum, node_val=self._node_val, conditional_val=self._condition_val)
                else:
                    return None

            elif (len(old_children[i].children()[0].children()) == 1 and len(
                    old_children[i].children()[1].children()) == 1):
                if old_children[i].children()[0].children()[0]._type == 'A' and old_children[i].children()[1].children()[0]._type == 'A':
                    new_children = old_children[:i] + old_children[i + 1:]
                    return RichSketchNode(self._type, self._condition, new_children, self._type_enum,
                                          node_val=self._node_val, conditional_val=self._condition_val)
                else:
                    return None

            else:
                return None

        new_children = old_children[:i] + old_children[i + 1:]
        #print("Children:",new_children)
        return RichSketchNode(self._type, self._condition, new_children, self._type_enum, node_val=self._node_val, conditional_val=self._condition_val)



    def __repr__(self, offset=''):
        cs = offset + self.label_print() + '\n'
        for child in self.children():
            cs += offset + child.__repr__(offset + '   ')
        return cs

    def __eq__(self, other):
        # updating this function because linearization of the tree does not handle a few corner cases
        hash_self = get_hash_code_of_sketch(self)
        hash_other = get_hash_code_of_sketch(other)
        if hash_self == hash_other:
            # check using tree traversal also because linearization does not work for corner cases
            return tree_equality(self, other)
        return hash_self == hash_other
        # return self._hash == other._hash

    def __hash__(self):
        return self._hash

def must_be_last_node(node: RichSketchNode):
    return node.label() == 'repeat_until_goal'


def node_types_for_task(type: str, allow_A=False):
    ''' Generates all available AST node types for a dataset. '''
    if allow_A:
        if type == 'hoc':
            return hoc_types
        elif type == 'karel':
            return karel_types
        else:
            return hoc_types
    else:
        if type == 'hoc':
            return hoc_types_mod
        elif type == 'karel':
            return karel_types_mod
        else:
            return hoc_types_mod


def create_empty_node(node_type: str, parameter=None):
    ''' A shorthand to create a single RichSketchNode of a given type. '''
    children = []
    if node_type == 'if_only':
        children.append(RichSketchNode('do', parameter, [], ))
    if node_type == 'if_else':
        children.append(RichSketchNode('do', parameter, []))
        children.append(RichSketchNode('else', parameter, []))
    return RichSketchNode(node_type, parameter, children)


#### recursive functions to add/delete nodes to RichSketchNode
def with_depth(func):
    ''' A decorator used to automatically maintain node depth when applying
        recursive func function to a tree. '''
    def recursive_with_depth(node, *args, depth=0, **kwargs):
        if node.label() != 'do' and node.label() != 'else':
            depth += 1
        yield from func(node, *args, depth=depth, **kwargs)
    return recursive_with_depth


def generate_recursively(func=None, depth=False):
    if func is None:
        return lambda f : generate_recursively(f, depth)
    ''' A decorator used to apply func recursively to every child of a tree. '''
    def recursive(node, *args, **kwargs):

        continue_recursion = yield from (
            r for r in func(node, *args, **kwargs) if r is not None
        )

        if continue_recursion is False:
            return

        yield from (
            node.with_ith_child(i, new_child)
            for i, child in enumerate(node.children())
            for new_child in recursive(child, *args, **kwargs)
        )

    if depth:
        recursive = with_depth(recursive)
    return recursive

def last_node_check(sketch: RichSketchNode):
    # check if last node is repeat_until_goal for each child in the tree if repeat_until_goal  exists in tree
    queue = collections.deque([sketch])
    while len(queue):
        for i in range(len(queue)):
            node = queue.popleft()
            children = node.children()
            if len(children) == 0:
                continue

            elif len(children) == 1:
                if(children[0]._type == 'repeat_until_goal' and node._type == 'repeat_until_goal'):
                    return False
            else:
                children_types = [c._type for c in children]
                if 'repeat_until_goal' in children_types:
                    if children_types[-1] != 'repeat_until_goal':
                        return False

            for child in node._children:
                queue.append(child)

    return True


def remove_children_after_repeat_until_goal(sketch: RichSketchNode):
    queue = collections.deque([sketch])
    while len(queue):
        for i in range(len(queue)):
            node = queue.popleft()
            children = node.children()
            if len(children) == 0:
                continue

            else:
                children_types = [c._type for c in children]
                if 'repeat_until_goal' in children_types:
                    index_of_repeat_until = children_types.index('repeat_until_goal')
                    new_children = children[:index_of_repeat_until+1]
                    node._children = new_children

            for child in node._children:
                queue.append(child)

    sketch._hash = get_hash_code_of_sketch(sketch)
    return sketch



@generate_recursively
def with_inserted_node(node: RichSketchNode, type: str):
    ''' Generates all possible Sketches obtainable by inserting a new single node
        as a child anywhere in the tree. '''
    if node.label() == 'A' or node.label() == 'if_only' or node.label() == 'if_else':
        return None
    new_nodes = []
    all_node_types = node_types_for_task(type)
    for ele in all_node_types:
        if ele == 'if_only' or ele == 'if_else' or ele == 'while':
            param = ['bool_cond']
        elif ele == 'repeat_until_goal':
            param = ['bool_cond']
        elif ele == 'repeat':
            param = ['X']
        else:
            param = []
            new_nodes.append(create_empty_node(ele))
        for p in param:
            new_nodes.append(create_empty_node(ele, p))

    yield from (
        node.with_inserted_child(i, new_node)
        for new_node in new_nodes
        for i in range(0, node.n_children() + 1)
    )

    #print([node.with_inserted_parent(n) for n in new_nodes])

    # yield from(
    #     node.with_inserted_parent(n)
    #     for n in new_nodes
    # )




@generate_recursively
def with_deleted_node(node: RichSketchNode):
    # if node.label() == 'if_only' or node.label() == 'if_else' or node.label() == 'do' or \
    #         node.label() == 'else' or node.label() == 'while':
    #     return

    yield from (
        node.with_removed_child(i)
        for i in range(0, node.n_children())
    )


def check_size_and_depth(
    node: RichSketchNode,
    max_size=MAX_SIZE,
    max_depth=MAX_DEPTH,
):


    return node.size() <= max_size and node.depth() <= max_depth



def generate_neighbors(
    node: RichSketchNode,
    type: str,
    max_size=MAX_SIZE,
    max_depth=MAX_DEPTH,
    debug_flag = False
):
    if not check_size_and_depth(node, max_size, max_depth):
        return


    #all insertions
    all_nbs_after_insertions = [remove_children_after_repeat_until_goal(ele) for ele in list(with_inserted_node(node, type))]
    yield from (
        neighbor for neighbor in all_nbs_after_insertions
        if (neighbor is not None and check_size_and_depth(neighbor, max_size, max_depth) and last_node_check(neighbor))
    )

    if debug_flag:
        all_nbs = []
        for ele in  list(with_deleted_node(node)):
            new_nb = remove_children_after_repeat_until_goal(ele)
            all_nbs.append(new_nb)
        print("Only deleted nodes:", all_nbs)
        print(list(with_deleted_node(node)))
        exit(0)


    all_nbs_after_deletion = [remove_children_after_repeat_until_goal(ele) for ele in list(with_deleted_node(node))]

    # all deletions
    yield from (
        neighbor for neighbor in all_nbs_after_deletion
        if (neighbor is not None and check_size_and_depth(neighbor, max_size, max_depth) and last_node_check(neighbor))
    )





def generate_unique_neighbors(
    node: RichSketchNode,
    type: str,
    max_size=MAX_SIZE,
    max_depth=MAX_DEPTH,
    debug_flag = False
):
    nbs = []
    already_generated = set()
    all_nbs = list(generate_neighbors(node, type, max_size, max_depth, debug_flag=debug_flag))
    for neighbor in all_nbs:
        nb1 = remove_children_after_repeat_until_goal(neighbor)
        if nb1 not in already_generated and last_node_check(nb1):
            already_generated.add(neighbor)
            nbs.append(neighbor)


    for neighbor in generate_nbs_with_node_anywhere(node, type, max_size, max_depth):
        nb2 = remove_children_after_repeat_until_goal(neighbor)
        if nb2 not in already_generated and last_node_check(nb2):
            already_generated.add(neighbor)
            nbs.append(neighbor)

    return nbs

def generate_nbs_with_node_anywhere(
        sketch: RichSketchNode,
        type: str,
        max_size=MAX_SIZE,
        max_depth=MAX_DEPTH,
):

    og_size = get_size(sketch)
    new_nodes = []

    all_node_types = node_types_for_task(type)
    for ele in all_node_types:
        if ele == 'if_only' or ele == 'if_else' or ele == 'while':
            param = ['bool_cond']
        elif ele == 'repeat_until_goal':
            param = ['bool_cond']
        elif ele == 'repeat':
            param = ['X']
        else:
            param = []
        for p in param:
            new_nodes.append(create_empty_node(ele, p))

    all_nbs = []
    queue = collections.deque([sketch])
    while len(queue):
        for i in range(len(queue)):
            node = queue.popleft()
            for j in range(len(node._children)):
                for n in new_nodes:
                    nbs = node.with_inserted_node_anywhere(n)
                    if nbs is not None:
                        all_nbs = all_nbs + nbs

            for child in node._children:
                queue.append(child)

    all_neighbors = []
    for neighbor in all_nbs:
        nbs_size = get_size(neighbor)
        if neighbor is None:
            continue
        if not check_size_and_depth(neighbor, max_size, max_depth):
            continue
        if not last_node_check(neighbor):
            continue
        if not (nbs_size > og_size):
            continue
        new_nb = remove_children_after_repeat_until_goal(neighbor)
        all_neighbors.append(new_nb)

    return all_neighbors



def sketch_to_json(node: RichSketchNode):
    ''' Converts an RichSketchNode into a JSON dictionary '''


    if len(node.children()) == 0:
        if node._condition is not None:
            if node._type == 'do' or node._type == 'else':
                return {'type': node._type}
            else:
                return {
                    'type': node._type + '(' + node._condition + ')'
                }
        else:
            return {'type': node._type }

    if node._condition is not None:
        if node._type == 'do' or node._type == 'else':
            node_dict = {'type': node._type}
        else:
            node_dict = {'type': node._type + '(' + node._condition + ')'}
    else:
        node_dict = {'type': node._type }

    children = [sketch_to_json(child) for child in node.children()]

    if node._type == 'if_only':
        do_dict = {'type': 'do'}
        do_list = node.children()[0]
        do_dict['children'] = [sketch_to_json(child) for child in do_list.children()]
        #children.append(do_dict)
    elif node._type == 'if_else':
        do_dict = {'type': 'do'}
        do_list = node.children()[0]
        do_dict['children'] = [sketch_to_json(child) for child in do_list.children()]
        #children.append(do_dict)
        else_dict = {'type': 'else'}
        else_list = node.children()[1]
        else_dict['children'] = [sketch_to_json(child) for child in else_list.children()]
        #children.append(else_dict)
    elif node._type == 'S;S':
        s1_dict = {'type': 'S'}
        s1_list = node.children()[0]
        s1_dict['children'] = [sketch_to_json(child) for child in s1_list.children()]
        #children.append(s1_dict)
        s2_dict = {'type': 'S'}
        s2_list = node.children()[1]
        s2_dict['children'] = [sketch_to_json(child) for child in s2_list.children()]
        #children.append(s2_dict)



    if children:
        node_dict['children'] = children

    return node_dict


def json_to_sketch(root):
    ''' Converts a JSON dictionary to an RichSketchNode.'''

    def get_children(json_node):
        children = json_node.get('children', [])
        return children

    node_type = root['type']
    children = get_children(root)

    if node_type == 'run':
        return RichSketchNode('run', None, [json_to_sketch(child) for child in children])

    if '(' in node_type:
        node_type_and_cond = node_type.split('(')
        node_type_only = node_type_and_cond[0]
        cond = node_type_and_cond[1][:-1]

        if node_type_only == 'if_else':
            assert (len(children) == 2)  # Must have do, else nodes for children

            do_node = children[0]
            assert (do_node['type'] == 'do')
            else_node = children[1]
            assert (else_node['type'] == 'else')
            do_list = [json_to_sketch(child) for child in get_children(do_node)]
            else_list = [json_to_sketch(child) for child in get_children(else_node)]
            # node_type is 'maze_ifElse_isPathForward' or 'maze_ifElse_isPathLeft' or 'maze_ifElse_isPathRight'
            return RichSketchNode(
                'if_else', cond,
                [RichSketchNode('do', cond, do_list), RichSketchNode('else', cond, else_list)],
            )

        if node_type_only == 'S;S':
            assert (len(children) == 2)  # Must have do, else nodes for children

            s1_node = children[0]
            assert (s1_node['type'] == 'S')
            s2_node = children[1]
            assert (s2_node['type'] == 'S')
            s1_list = [json_to_sketch(child) for child in get_children(s1_node)]
            s2_list = [json_to_sketch(child) for child in get_children(s2_node)]
            # node_type is 'maze_ifElse_isPathForward' or 'maze_ifElse_isPathLeft' or 'maze_ifElse_isPathRight'
            return RichSketchNode(
                'S;S', None,
                [RichSketchNode('S', cond, s1_list), RichSketchNode('S', cond, s2_list)],
            )


        elif node_type_only == 'if_only':
            assert (len(children) == 1)  # Must have condition, do nodes for children

            do_node = children[0]
            assert (do_node['type'] == 'do')

            do_list = [json_to_sketch(child) for child in get_children(do_node)]

            return RichSketchNode(
                'if_only', cond,
                [RichSketchNode('do', cond, do_list)],
            )



        elif node_type_only == 'while':

            while_list =  [json_to_sketch(child) for child in children]
            return RichSketchNode(
                'while',
                 cond,
                 while_list,
            )

        elif node_type_only == 'repeat':
            repeat_list = [json_to_sketch(child) for child in children]
            return RichSketchNode(
                'repeat',
                cond,
                repeat_list,
            )

        elif node_type_only == 'repeat_until_goal':

            repeat_until_goal_list = [json_to_sketch(child) for child in children]
            return RichSketchNode(
                'repeat_until_goal',
                cond,
                repeat_until_goal_list
            )

        else:
            print('Unexpected node type, failing:', node_type_only)
            assert (False)


    if node_type == 'A':
        return RichSketchNode('A')

    if node_type == 'Y':
        return RichSketchNode('Y')

    if node_type == 'S':
        return RichSketchNode('S')

    print('Unexpected node type, failing:', node_type)
    assert (False)


    return None


def unroll_A_type_nodes(sketch: RichSketchNode):
    queue = collections.deque([sketch])
    while len(queue):
        for i in range(len(queue)):
            node = queue.popleft()
            # print("Current node:", node)
            # print("Current node's children:", node._children)
            new_nodes_to_be_added = []
            for j in range(len(node._children)):
                if node._children[j]._type == 'A':
                    if len(node._children[j]._node_val) > 1:
                        new_child_nodes = []
                        for k in range(len(node._children[j]._node_val)-1, 0,-1):
                            node_vals = [node._children[j]._node_val[k]]
                            new_node = RichSketchNode('A', node_val=node_vals)
                            new_child_nodes.append(new_node)
                        new_nodes_to_be_added.append([j, new_child_nodes])
                        # print("Generated the following new child nodes:", j, new_child_nodes)
                        old_child = [node._children[j]._node_val[0]]
                        node._children[j]._node_val = copy.deepcopy(old_child)

            # print("Elements to be added:", new_nodes_to_be_added)
            counter = 0 # counter that resets whenever we have a change in number of children due to insertions
            for ele in new_nodes_to_be_added:
                # ele: [index, list-of-new-nodes]
                index = ele[0] + counter
                for n in ele[1]:
                    node._children.insert(index+1, n)
                    counter += 1

            for child in node._children:
                queue.append(child)
            # print("Queue:", queue)

    # print("Sketch:", sketch)
    # sketch_json = sketch_to_json(sketch)
    # sketch = json_to_sketch(sketch_json)
    return sketch


def sketch_to_json_for_ast(node: RichSketchNode, type='hoc', id = '18'):
    ''' Converts an RichSketchNode into a JSON dictionary: works only for unrolled A sketches '''


    if len(node.children()) == 0:
        if node._condition is not None:
            if node._type == 'do' or node._type == 'else':
                return {'type':  sketchnode_to_astnode[node._type]}
            else:
                condition = node._condition_val
                if condition is None:
                    if node._type == 'repeat':
                        condition = '8'
                    elif node._type == 'while' or node._type == 'if_only' or node._type == 'if_else':
                        if type == 'hoc' and id == '16':
                            condition = 'bool_path_left'
                        elif type == 'hoc':
                            condition = 'bool_path_ahead'
                        else:
                            condition = 'bool_no_marker'
                    elif node._type == 'repeat_until_goal':
                        condition = 'bool_goal'
                return {
                    'type': sketchnode_to_astnode[node._type] + '(' + condition + ')'
                }
        else:
            if node._type == 'A':
                # print("Node type:", node._type)
                node_type = node._node_val[0]
                return {'type': sketchnode_to_astnode[node_type]}
            else:
                return {'type': sketchnode_to_astnode[node._type] }

    if node._condition is not None:
        if node._type == 'do' or node._type == 'else':
            node_dict = {'type': sketchnode_to_astnode[node._type]}
        else:
            condition = node._condition_val
            if condition is None:
                if node._type == 'repeat':
                    condition = '8'
                elif node._type == 'while' or node._type=='if_only' or node._type == 'if_else':
                    if type == 'hoc' and id == '16':
                        condition = 'bool_path_left'
                    elif type == 'hoc':
                        condition = 'bool_path_ahead'
                    else:
                        condition = 'bool_no_marker'
                elif node._type == 'repeat_until_goal':
                        condition = 'bool_goal'
            node_dict = {'type': sketchnode_to_astnode[node._type] + '(' + condition + ')'}
    else:
        if node._type == 'A':
            # print("Node type:", node._type)
            node_type = node._node_val[0]
            node_dict =  {'type': sketchnode_to_astnode[node_type]}
        else:
            node_dict =  {'type': sketchnode_to_astnode[node._type]}

    children = [sketch_to_json_for_ast(child, type=type, id=id) for child in node.children()]

    if node._type == 'if_only':
        do_dict = {'type': 'do'}
        do_list = node.children()[0]
        do_dict['children'] = [sketch_to_json_for_ast(child, type=type, id=id) for child in do_list.children()]
        #children.append(do_dict)
    elif node._type == 'if_else':
        do_dict = {'type': 'do'}
        do_list = node.children()[0]
        do_dict['children'] = [sketch_to_json_for_ast(child, type=type, id=id) for child in do_list.children()]
        #children.append(do_dict)
        else_dict = {'type': 'else'}
        else_list = node.children()[1]
        else_dict['children'] = [sketch_to_json_for_ast(child, type=type, id=id) for child in else_list.children()]
        #children.append(else_dict)
    elif node._type == 'S;S':
        s1_dict = {'type': 'S'}
        s1_list = node.children()[0]
        s1_dict['children'] = [sketch_to_json_for_ast(child, type=type, id=id) for child in s1_list.children()]
        #children.append(s1_dict)
        s2_dict = {'type': 'S'}
        s2_list = node.children()[1]
        s2_dict['children'] = [sketch_to_json_for_ast(child, type=type, id=id) for child in s2_list.children()]
        #children.append(s2_dict)



    if children:
        node_dict['children'] = children

    return node_dict



def remove_null_nodes(root:RichSketchNode):
    queue = collections.deque([root])
    while len(queue):
        for i in range(len(queue)):
            node = queue.popleft()

            node._children = list(filter((RichSketchNode('phi')).__ne__, node._children))

            for child in node._children:
             queue.append(child)


    return root



def tree_edit_distance(sketch_a: RichSketchNode, sketch_b: RichSketchNode):
    ''' Computes the ZSS tree edit distance between two trees (as RichSketchNodes). '''

    def update_cost(node_a, node_b):
        label_a = node_a.label()
        label_b = node_b.label()
        if label_a == label_b:
            val = 0
        else:
            val = 2
        return val

    def insert_cost(node):
        label = node.label()
        if len(node.children()) == 0 and label == 'do':
            return 0
        if len(node.children()) == 0 and label == 'else':
            return 0
        # return 0 if label == 'do' or label == 'else' else 1
        return 0 if label == 'do' else 1

    def remove_cost(node):
        label = node.label()
        if len(node.children()) == 0 and label == 'do':
            return 0
        if len(node.children()) == 0 and label == 'else':
            return 0
        # return 0 if label == 'do' or label == 'else' else 1
        return 0 if label == 'do' else 1


    return zss.distance(
        sketch_a,
        sketch_b,
        RichSketchNode.children,
        lambda node : insert_cost(node),
        lambda node: remove_cost(node),
        lambda node_a, node_b:  update_cost(node_a, node_b),
    )


def tree_edit_distance_modified(sketch_a: RichSketchNode, sketch_b: RichSketchNode):
    ''' Computes the ZSS tree edit distance between two trees (as RichSketchNodes). '''

    def update_cost(node_a, node_b):
        label_a = node_a.label()
        label_b = node_b.label()
        if label_a == label_b:
            val = 0
        else:
            val = 2
        return val

    def insert_cost(node):
        label = node.label()
        if len(node.children()) == 0 and label == 'do':
            return 0
        if len(node.children()) == 0 and label == 'else':
            return 0
        if label == 'A':
            return 0
        # return 0 if label == 'do' or label == 'else' else 1
        return 1

    def remove_cost(node):
        label = node.label()
        if len(node.children()) == 0 and label == 'do':
            return 0
        if len(node.children()) == 0 and label == 'else':
            return 0
        if label == 'A':
            return 0
        # return 0 if label == 'do' or label == 'else' else 1
        return 1


    return zss.distance(
        sketch_a,
        sketch_b,
        RichSketchNode.children,
        lambda node : insert_cost(node),
        lambda node: remove_cost(node),
        lambda node_a, node_b:  update_cost(node_a, node_b),
    )


def get_size(node:RichSketchNode):
    ## this routine returns the depth and size of the tree
    if node._type is not None:
        size = 1

    for i, child in enumerate(node.children()):
        if child._type != 'phi':
            size = size + get_size(child)


    return size


def add_missing_do_else_nodes(root:RichSketchNode):
    queue = collections.deque([root])
    while len(queue):
        for i in range(len(queue)):
            node = queue.popleft()

            if node._type == 'if_else':
                if len(node._children) != 2:
                    do_child = RichSketchNode('do', node_type_condition='bool_cond', children = [])
                    else_child = RichSketchNode('else', node_type_condition='bool_cond', children = [])
                    node._children = [do_child, else_child]
            elif node._type == 'if_only':
                if len(node._children) != 1:
                    old_children = copy.deepcopy(node._children)
                    do_child = RichSketchNode('do', node_type_condition='bool_cond', children=old_children)
                    node._children = [do_child]
            else:
                pass
                ##TODO: Can add a check for codes that have elements after repeat_until_goal

            for child in node._children:
                queue.append(child)

    return root


def get_astnode_from_sketch(node:RichSketchNode, type='hoc', id='18'):
    # add additional missing do/else nodes
    root = add_missing_do_else_nodes(node)
    # unroll the A's
    unrolled_sketch = unroll_A_type_nodes(root)
    # print("Unrolled sketch:", unrolled_sketch)
    # get the json
    json_sketch = sketch_to_json_for_ast(unrolled_sketch, type=type, id=id)
    # print("JSON Sketch:", json_sketch)
    # get the astnode from the json
    astnode = json_to_ast(json_sketch)

    return astnode



def tree_equality(root_1:RichSketchNode, root_2:RichSketchNode):

    if root_1 is None and root_2 is not None:
        return False
    if root_2 is None and root_1 is not None:
        return False
    if root_1._type != root_2._type:
        return False

    if root_1._children is not None and root_2._children is not None:
        if len(root_1._children) != len(root_2._children):
            return False
        for i in range(len(root_1._children)):
            flag =  tree_equality(root_1._children[i], root_2._children[i])
            if not flag:
                return False

    elif root_1._children is not None and root_2._children is None:
        if len(root_1._children) == 0:
            return False
    elif root_2._children is not None and root_1._children is None:
        if len(root_2._children) == 0:
            return False

    return True


def get_hash_code_of_sketch(root:ASTNode):
    hash = int(root._type_enum)

    if root._children == [] or root._children is None:
        return hash

    for i, child in enumerate(root._children):
        if child._type != 'phi':
            hash = join_ints(get_hash_code_of_sketch(child) * (i + 1), hash, max_pow=MAX_POW)

    return hash
