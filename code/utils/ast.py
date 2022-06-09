import enum
import json
import zss
import copy
import collections
import re
from code.utils.definitions import NodeType as NodeType
from code.utils.definitions import node_str_to_type as node_str_to_type


MAX_SIZE = 30
MAX_DEPTH = 10

### Util function just to preprocess HOC-Dataset
node_type_parameters = {
    'maze_turn': [ 'turnLeft', 'turnRight' ],
    'maze_ifElse': [ 'isPathForward', 'isPathLeft', 'isPathRight' ],
}

### Util function for other ASTs
all_node_type_parameters = {
    'turn_left': ['turn_left', 'turn_right'],
    'turn_right': ['turn_left', 'turn_right' ],
    'pick_marker': ['pick_marker', 'put_marker'],
    'put_marker': [ 'pick_marker', 'put_marker'],
    'bool_hoc': [ 'bool_path_left', 'bool_path_right', 'bool_path_ahead' ],
    'bool_karel': [ 'bool_path_left', 'bool_path_right', 'bool_path_ahead',
                    'bool_no_path_ahead', 'bool_no_path_left', 'bool_no_path_right',
                    'bool_marker', 'bool_no_marker'
                    ],
    'bool_goal': ['bool_goal'],
    'X': ['2','3','4','5','6','7','8','9']
}

#### all node-types for insertion
hoc_types = ['turn_left', 'turn_right', 'move', 'repeat', 'repeat_until_goal', 'if', 'ifelse']
karel_types = ['turn_left', 'turn_right', 'move', 'pick_marker', 'put_marker', 'repeat', 'while', 'if', 'ifelse']

#### basic-action node-types for insertion
hoc_types_basic_action = ['turn_left', 'turn_right', 'move']
karel_types_basic_action = ['turn_left', 'turn_right', 'move', 'pick_marker', 'put_marker']



def split_list(data, n):
    from itertools import combinations, chain
    for splits in combinations(range(1, len(data)), n-1):
        result = []
        prev = None
        for split in chain(splits, [None]):
            result.append(data[prev:split])
            prev = split
        yield result

### Util function just to preprocess HOC-Dataset
def merge_node_type_parameter(node_type: str, parameter):
    ''' Merges node type and its parameter into a single label.
        E.g.: (maze_turn, turnLeft) -> turn_left '''

    if parameter is None:
        return node_type
    assert(parameter in node_type_parameters.get(node_type, []))
    return parameter




P = 10000000007
M = 10 ** 40

MAX_POW = 40


def dsamepow10(num, max_pow=MAX_POW): # returns the max pow of 40 in num
    r = 1
    while num >= max_pow:
        num = int(num // max_pow)
        r *= max_pow
    return r


def join_ints(a, b, max_pow=MAX_POW):
    return a * dsamepow10(b) * max_pow + b



class ASTNode:
    ''' A custom AST class to represent raw prgrams '''

    # @staticmethod
    def from_json(json_dict):
        return json_to_ast(json_dict)

    def to_int(self):
        return self._hash

    def to_json(self):
        return ast_to_json(self)

    def __init__(self, node_type_str, node_type_condition=None, children=[], node_type_enum=None):

        self._type_enum = node_type_enum or node_str_to_type[node_type_str]
        self._type = node_type_str
        self._condition = node_type_condition
        self._children = children
        self._size = 0
        self._depth = 0
        self._hash = int(self._type_enum)
        if self._condition is not None:
            cond_enum = node_str_to_type[self._condition]
            self._hash = join_ints(cond_enum, self._hash, max_pow=MAX_POW)

        # counts of the constructs
        self._n_if_only = 0
        self._n_while = 0
        self._n_repeat = 0
        self._n_if_else = 0
        self._n_repeat_until = 0


        for child in children:
            if child._type != 'phi':
                self._size += child._size
            self._depth = max(self._depth, child._depth)
            if child._type != 'phi':
                self._hash = join_ints(child._hash, self._hash, max_pow=MAX_POW)
            self._n_if_else += child._n_if_else
            self._n_while += child._n_while
            self._n_if_only += child._n_if_only
            self._n_repeat_until += child._n_repeat_until

        if self._type_enum == NodeType.MOVE_FORWARD:
            self._size += 1
        elif self._type_enum == NodeType.TURN_LEFT:
            self._size += 1
        elif self._type_enum == NodeType.TURN_RIGHT:
            self._size += 1
        elif self._type_enum == NodeType.PICK_MARKER:
            self._size += 1
        elif self._type_enum == NodeType.PUT_MARKER:
            self._size += 1
        elif self._type_enum == NodeType.WHILE:
            self._size += 1
            self._depth += 1
            self._n_while += 1
        elif self._type_enum == NodeType.REPEAT:
            self._size += 1
            self._depth += 1
            self._n_repeat += 1
        elif self._type_enum == NodeType.IF_ELSE:
            self._size += 1
            self._depth += 1
            self._n_if_else += 1
        elif self._type_enum == NodeType.IF_ONLY:
            self._size += 1
            self._depth += 1
            self._n_if_only += 1
        elif self._type_enum == NodeType.REPEAT_UNTIL_GOAL:
            self._size += 1
            self._depth += 1
            self._n_repeat_until += 1
        elif self._type_enum == NodeType.RUN:
            self._size += 1
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
        if self._condition is not None:
            label = self._type + ' ' + self._condition
        else:
            label = self._type
        return label

    def label(self):
        return self._type


    def label_enum(self):
        return self._type_enum

    def with_label(self, label, cond):
        if self._type == 'if':
            return ASTNode(label, cond, [ASTNode('do', cond, self.children()[0].children())])
        elif self._type == 'ifelse':
            return ASTNode(label, cond, [ASTNode('do', cond, self.children()[0].children()),
                                         ASTNode('else', cond, self.children()[1].children())
                                         ])
        else:
            return ASTNode(label, cond, self.children())

    def with_ith_child(self, i, child):
        # changing this condition temporarily. might bring it back later
        # if must_be_last_node(child) and i + 1 != len(self._children) and i != -1:
        #     return None
        new_children = self._children[:i] + [child]
        if i != -1:
            new_children += self._children[i + 1:]
        return ASTNode(self._type, self._condition, new_children, self._type_enum)

    def with_inserted_child(self, i, child):
        if i > 0 and must_be_last_node(self.children()[i - 1]):
            return None
        if must_be_last_node(child) and i != len(self._children):
            return None
        if self._type == 'if' and i == 0:
            return None
        if self._type == 'ifelse' and (i == 0 or i == 1):
            return None
        new_children = self.children().copy()
        new_children.insert(i, child)
        return ASTNode(self._type, self._condition, new_children, self._type_enum)

    def with_inserted_child_basic_action(self, i, child):
        # if i > 0 and must_be_last_node(self.children()[i - 1]):
        #     return None
        # if must_be_last_node(child) and i != len(self._children):
        #     return None
        if self._type == 'if' and i == 0:
            return None
        if self._type == 'ifelse' and (i == 0 or i == 1):
            return None
        new_children = self.children().copy()
        if self._type == 'else' and self.children is None:
            new_children = []
        elif self._type == 'do' and self.children is None:
            new_children = []
        elif self._type == 'while' and self.children is None:
            new_children = []
        elif self._type == 'repeat' and self.children is None:
            new_children = []
        elif self._type == 'repeat_until_goal' and self.children is None:
            new_children = []
        elif self._type == 'run' and self.children is None:
            new_children = []
        else:
            pass
        new_children.insert(i, child)
        return ASTNode(self._type, self._condition, new_children, self._type_enum)

    def with_removed_child(self, i):
        if self.children()[i]._type == 'repeat' or self.children()[i]._type == 'repeat_until_goal' or \
                self.children()[i]._type == 'while' or self.children()[i]._type == 'if' or self.children()[i]._type == 'ifelse':

            if self.children()[i]._type == 'repeat' and len(self.children()[i].children()) == 0:
                old_children = self.children()
                new_children = old_children[:i] + old_children[i + 1:]
                return ASTNode(self._type, self._condition, new_children, self._type_enum)

            elif self.children()[i]._type == 'repeat_until_goal' and len(self.children()[i].children()) == 0:
                old_children = self.children()
                new_children = old_children[:i] + old_children[i + 1:]
                return ASTNode(self._type, self._condition, new_children, self._type_enum)

            elif self.children()[i]._type == 'while' and len(self.children()[i].children()) == 0:
                old_children = self.children()
                new_children = old_children[:i] + old_children[i + 1:]
                return ASTNode(self._type, self._condition, new_children, self._type_enum)

            elif self.children()[i]._type == 'ifelse' and len(self.children()[i].children()[0].children()) == 0 and \
                    len(self.children()[i].children()[1].children()) == 0:
                old_children = self.children()
                new_children = old_children[:i] + old_children[i + 1:]
                return ASTNode(self._type, self._condition, new_children, self._type_enum)

            elif self.children()[i]._type == 'if' and len(self.children()[i].children()[0].children()) == 0:
                old_children = self.children()
                new_children = old_children[:i] + old_children[i + 1:]
                return ASTNode(self._type, self._condition, new_children, self._type_enum)

            else:
                return None


        old_children = self.children()
        new_children = old_children[:i] + old_children[i + 1:]
        return ASTNode(self._type, self._condition, new_children, self._type_enum)


    def with_removed_child_basic_action(self, i):
        # print("Operating on node:", self, i)
        if self.children()[i]._type == 'repeat' or self.children()[i]._type == 'repeat_until_goal' or \
                self.children()[i]._type == 'while' or self.children()[i]._type == 'if' or self.children()[i]._type == 'ifelse' or\
            self.children()[i]._type == 'do' or self.children()[i]._type == 'else':
            # print("Not returning....")
            return

        else:
            pass
            # print("Node:",self.children()[i]._type)

        # will only remove the basic actions
        old_children = self.children()
        new_children = old_children[:i] + old_children[i + 1:]

        # print("Returning:", ASTNode(self._type, self._condition, new_children, self._type_enum))

        return ASTNode(self._type, self._condition, new_children, self._type_enum)



    def __repr__(self, offset=''):
        cs = offset + self.label_print() + '\n'
        for child in self.children():
            cs += offset + child.__repr__(offset + '   ')
        return cs

    def __eq__(self, other):
        hash_self = get_hash_code_of_ast(self)
        hash_other = get_hash_code_of_ast(other)
        if hash_self == hash_other:
            # check using tree traversal also because linearization does not work for corner cases
            return tree_equality(self, other)
        return hash_self == hash_other


    def __hash__(self):
        return self._hash

def must_be_last_node(node: ASTNode):
    return node.label() == 'repeat_until_goal'


def tree_equality(root_1:ASTNode, root_2:ASTNode):

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








def node_types_for_task(type: str):
    ''' Generates all available AST node types for a dataset. '''
    if type == 'hoc':
        return hoc_types
    elif type == 'karel':
        return karel_types
    else:
        return hoc_types


def node_types_for_basic_action(type: str):
    ''' Generates all available AST node types for a dataset. '''
    if type == 'hoc':
        return hoc_types_basic_action
    elif type == 'karel':
        return karel_types_basic_action
    else:
        return hoc_types_basic_action



def parameters_for_node_type(node_type: str):
    ''' Returns all possible parameters for a node type. '''

    return all_node_type_parameters.get(node_type, [])

def create_empty_node(node_type: str, parameter=None):
    ''' A shorthand to create a single AST node of a given type. '''

    children = []
    if node_type == 'if':
        children.append(ASTNode('do', parameter, []))
    if node_type == 'ifelse':
        children.append(ASTNode('do', parameter, []))
        children.append(ASTNode('else', parameter, []))
    return ASTNode(node_type, parameter, children)


#### recursive functions to add/delete nodes to AST
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

@generate_recursively
def with_changed_parameter(node: ASTNode, type='hoc'):
    ''' Generates all possible ASTs obtainable by changing parameter (if any) of
        any node in the tree. '''
    if node.label() == 'do' or node.label() == 'else' or node.label() == 'repeat_until_goal':
        return
    node_type, node_parameter = node.label(), node.conditional()
    if node_type == 'if' or node_type == 'ifelse' or node_type == 'while':
        new_labels = (
            new_parameter
            for new_parameter in parameters_for_node_type('bool_'+type)
            if new_parameter != node_parameter
        )
        yield from (node.with_label(node_type, label) for label in new_labels)

    elif node_type == 'repeat':
        new_labels = (
            new_parameter
            for new_parameter in parameters_for_node_type('X')
            if new_parameter != node_parameter
        )
        yield from (node.with_label(node_type, label) for label in new_labels)
    else:
        new_labels = (
            new_parameter
            for new_parameter in parameters_for_node_type(node_type)
            if new_parameter != node_type
        )
        yield from (node.with_label(label, node_parameter) for label in new_labels)


@generate_recursively
def with_inserted_node(node: ASTNode, type: str):
    ''' Generates all possible ASTs obtainable by inserting a new single node
        as a child anywhere in the tree. '''
    if node.label() == 'move' or node.label() == 'turn_left' or \
            node.label() == 'turn_right' or node.label() == 'pick_marker' \
            or node.label() == 'put_marker' or node.label() == 'if' or node.label() == 'ifelse':
        return
    new_nodes = []
    all_node_types = node_types_for_task(type)
    for ele in all_node_types:
        if ele == 'if' or ele == 'ifelse' or ele == 'while':
            param = all_node_type_parameters.get('bool_'+str(type), [None])
        elif ele == 'repeat_until_goal':
            param = ['bool_goal']
        elif ele == 'repeat':
            param = all_node_type_parameters.get('X', [None])
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



@generate_recursively
def with_inserted_node_basic_action_only(node: ASTNode, type: str):
    ''' Generates all possible ASTs obtainable by inserting a new single node
        as a child anywhere in the tree. '''
    if node.label() == 'move' or node.label() == 'turn_left' or \
            node.label() == 'turn_right' or node.label() == 'pick_marker' \
            or node.label() == 'put_marker' or node.label() == 'if' or node.label() == 'ifelse':
        return
    new_nodes = []
    all_node_types = node_types_for_basic_action(type)
    for ele in all_node_types:
        new_nodes.append(create_empty_node(ele))

    yield from (
        node.with_inserted_child_basic_action(i, new_node)
        for new_node in new_nodes
        for i in range(0, node.n_children() + 1)
    )



@generate_recursively
def with_deleted_node(node: ASTNode):
    # print("Node:", node)
    # if node.label() == 'if' or node.label() == 'ifelse' or node.label() == 'do' or node.label() == 'else':
    #     return

    yield from (
        node.with_removed_child(i)
        for i in range(0, node.n_children())
    )



@generate_recursively
def with_deleted_node_basic_action_only(node: ASTNode):
    # print("Node:", node)
    # if node.label() == 'if' or node.label() == 'ifelse' or node.label() == 'do' or node.label() == 'else':
    #     return

    # print("Deleting for node:", node)
    # print("Neighbors:", list(node.with_removed_child(i) for i in range(0, node.n_children())))
    yield from (
        node.with_removed_child_basic_action(i)
        for i in range(0, node.n_children())
    )





def check_size_and_depth(
    node: ASTNode,
    max_size=MAX_SIZE,
    max_depth=MAX_DEPTH,
):
    return node.size() <= max_size and node.depth() <= max_depth


def generate_neighbors(
    node: ASTNode,
    type: str,
    max_size=MAX_SIZE,
    max_depth=MAX_DEPTH,
):
    if not check_size_and_depth(node, max_size, max_depth):
        return

    yield from with_changed_parameter(node, type)

    yield from (
        neighbor for neighbor in with_inserted_node(node, type)
        if check_size_and_depth(neighbor, max_size, max_depth)
    )

    # print("Deleted nodes:", list(with_deleted_node(node)))
    yield from with_deleted_node(node)



def generate_neighbors_with_basic_action_only(
    node: ASTNode,
    type: str,
    max_size=MAX_SIZE,
    max_depth=MAX_DEPTH,
):
    if not check_size_and_depth(node, max_size, max_depth):
        return

    yield from with_changed_parameter(node, type)

    inserted_neighbors = list(with_inserted_node_basic_action_only(node, type))
    inserted_neighbors = list(filter(None.__ne__, inserted_neighbors))


    yield from (
        neighbor for neighbor in inserted_neighbors
        if check_size_and_depth(neighbor, max_size, max_depth)
    )


    deleted_neighbors = list(with_deleted_node_basic_action_only(node))
    deleted_neighbors = list(filter(None.__ne__, deleted_neighbors))


    yield from (deleted_neighbors)



def generate_unique_neighbors(
    node: ASTNode,
    type: str,
    max_size=MAX_SIZE,
    max_depth=MAX_DEPTH,
):
    nbs = []
    already_generated = set()

    for neighbor in generate_neighbors(node, type, max_size, max_depth):
        if neighbor not in already_generated:
            already_generated.add(neighbor)
            nbs.append(neighbor)




    return nbs


def generate_unique_neighbors_with_basic_action_only(
    node: ASTNode,
    type: str,
    max_size=MAX_SIZE,
    max_depth=MAX_DEPTH,
):
    nbs = []
    already_generated = set()

    all_nbs = list(generate_neighbors_with_basic_action_only(node, type, max_size, max_depth))
    for neighbor in all_nbs:
        if neighbor not in already_generated:
            already_generated.add(neighbor)
            nbs.append(neighbor)


    return nbs



def tree_edit_distance(ast_a: ASTNode, ast_b: ASTNode):
    ''' Computes the ZSS tree edit distance between two trees (as ASTNodes). '''

    def update_cost(node_a, node_b):
        label_a = node_a.label_print()
        label_b = node_b.label_print()
        labela = node_a.label()
        labelb = node_b.label()
        if label_a == label_b:
            return 0
        else:
            if labela in ['turn_left', 'turn_right'] and \
                    labelb in ['turn_left', 'turn_right']:
                return 1
            elif labela in ['put_marker', 'pick_marker'] and \
                    labelb in ['put_marker', 'pick_marker']:
                return 1

            elif labela == 'ifelse' and labelb == 'ifelse':
                return 1

            elif labela == 'if' and labelb == 'if':
                return 1

            elif labela == 'while' and labelb == 'while':
                return 1

            elif labela == 'repeat' and labelb == 'repeat':
                return 1
            elif labela == 'do' and labelb == 'do':
                return 0
            elif labela == 'else' and labelb == 'else':
                return 0
            else:
                return 2


    def insert_cost(node):
        label = node.label()
        return 1
        # return 0 if label == 'do' or label == 'else' else 1

    def remove_cost(node):
        label = node.label()
        if node.label() == 'repeat' or node.label() == 'while' or node.label() == 'repeat_until_goal':
            if len(node.children()) == 0:
                return 1
            else:
                return len(node.children())

        return 1
        # return 0 if label == 'do'or label == 'else' else 1

    return zss.distance(
        ast_a,
        ast_b,
        ASTNode.children,
        insert_cost=insert_cost,
        remove_cost=remove_cost,
        update_cost=update_cost,
    )



def ast_to_json(node: ASTNode):
    ''' Converts an ASTNode into a JSON dictionary.'''

    if len(node.children()) == 0:
        if node._condition is not None:
            if node._type == 'do' or node._type == 'else':
                node_dict = {'type': node._type}
            else:
                node_dict = {'type': node._type + '(' + node._condition + ')'}
        else:
            node_dict = {'type': node._type}
        return node_dict


    if node._condition is not None:
        if node._type == 'do' or node._type == 'else':
            node_dict = {'type': node._type}
        else:
            node_dict = {'type': node._type + '(' + node._condition + ')'}
    else:
        node_dict = {'type': node._type }

    children = [ast_to_json(child) for child in node.children()]

    # if node._type == 'if':
    #     do_dict = {'type': 'do'}
    #     do_list = node.children()[0]
    #     do_dict['children'] = [ast_to_json(child) for child in do_list.children()]
    #     children.append(do_dict)
    # elif node._type == 'ifelse':
    #     do_dict = {'type': 'do'}
    #     do_list = node.children()[0]
    #     do_dict['children'] = [ast_to_json(child) for child in do_list.children()]
    #     children.append(do_dict)
    #     else_dict = {'type': 'else'}
    #     else_list = node.children()[1]
    #     else_dict['children'] = [ast_to_json(child) for child in else_list.children()]
    #     children.append(else_dict)


    if children:
        node_dict['children'] = children

    return node_dict

def remove_null_nodes(root:ASTNode):
    queue = collections.deque([root])
    while len(queue):
        for i in range(len(queue)):
            node = queue.popleft()

            node._children = list(filter((ASTNode('phi')).__ne__, node._children))

            # for child in node._children:
            #     if child._type == 'phi':
            #         node._children.remove(child)


            for child in node._children:
                 queue.append(child)


    return root


def json_to_ast(root):
    ''' Converts a JSON dictionary to an ASTNode.'''

    def get_children(json_node):
        children = json_node.get('children', [])
        return children

    node_type = root['type']
    children = get_children(root)

    if node_type == 'run':
        return ASTNode('run', None, [json_to_ast(child) for child in children])

    if '(' in node_type:
        node_type_and_cond = node_type.split('(')
        node_type_only = node_type_and_cond[0]
        cond = node_type_and_cond[1][:-1]

        if node_type_only == 'ifelse':
            assert (len(children) == 2)  # Must have do, else nodes for children

            do_node = children[0]
            assert (do_node['type'] == 'do')
            else_node = children[1]
            assert (else_node['type'] == 'else')
            do_list = [json_to_ast(child) for child in get_children(do_node)]
            else_list = [json_to_ast(child) for child in get_children(else_node)]
            # node_type is 'maze_ifElse_isPathForward' or 'maze_ifElse_isPathLeft' or 'maze_ifElse_isPathRight'
            return ASTNode(
                'ifelse', cond,
                [ASTNode('do', cond, do_list), ASTNode('else', cond, else_list)],
            )

        elif node_type_only == 'if':
            assert (len(children) == 1)  # Must have condition, do nodes for children

            do_node = children[0]
            assert (do_node['type'] == 'do')

            do_list = [json_to_ast(child) for child in get_children(do_node)]

            return ASTNode(
                'if', cond,
                [ASTNode('do', cond, do_list)],
            )



        elif node_type_only == 'while':

            while_list =  [json_to_ast(child) for child in children]
            return ASTNode(
                'while',
                 cond,
                 while_list,
            )

        elif node_type_only == 'repeat':
            repeat_list = [json_to_ast(child) for child in children]
            return ASTNode(
                'repeat',
                cond,
                repeat_list,
            )

        elif node_type_only == 'repeat_until_goal':

            repeat_until_goal_list = [json_to_ast(child) for child in children]
            return ASTNode(
                'repeat_until_goal',
                cond,
                repeat_until_goal_list
            )

        else:
            print('Unexpected node type, failing:', node_type_only)
            assert (False)


    if node_type == 'move':
        return ASTNode('move')

    if node_type == 'turn_left':
        return ASTNode('turn_left')

    if node_type == 'turn_right':
        return ASTNode('turn_right')

    if node_type == 'pick_marker':
        return ASTNode('pick_marker')

    if node_type == 'put_marker':
        return ASTNode('put_marker')


    print('Unexpected node type, failing:', node_type)
    assert (False)


    return None


### Routine used to parse the HOC4/18 datasets
def json_to_ast_for_hoc_dataset(root) -> ASTNode:
    ''' Converts a JSON dictionary to an ASTNode.
        Works for both HOC4 and HOC18 datasets. '''

    def get_children(json_node):
        children = json_node.get('children', [])
        # Avoid inconsistencies with missing statementList
        if len(children) == 1 and children[0]['type'] == 'statementList':
            return get_children(children[0])
        return children

    node_type = root['type']
    children = get_children(root)

    if node_type == 'program':
        return ASTNode('run', None, [ json_to_ast_for_hoc_dataset(child) for child in children ])

    if node_type == 'statementList':
        return ASTNode('run', None, [ json_to_ast_for_hoc_dataset(child) for child in children ])

    if node_type == 'maze_forever':
        do = children[0]
        if do['type'] == 'DO':
            children = get_children(do)
        # else: # This AST is missing 'DO' node for some reason
        return ASTNode('repeat_until_goal', 'bool_goal', [json_to_ast_for_hoc_dataset(child) for child in children])

    if node_type == 'maze_ifElse':
        assert(len(children) == 3) # Must have condition, do, else nodes for children
        condition = children[0]
        assert(condition['type'] in node_type_parameters[node_type])
        if condition['type'] == 'isPathForward':
            cond = 'bool_path_ahead' # for simplifying notation
        elif condition['type'] == 'isPathLeft':
            cond = 'bool_path_left'
        elif condition['type'] == 'isPathRight':
            cond = 'bool_path_right'
        else:
            print('Unexpected node type, failing:', node_type, condition)
            return None
        do_node = children[1]
        assert(do_node['type'] == 'DO')
        else_node = children[2]
        assert(else_node['type'] == 'ELSE')
        do_list = [ json_to_ast_for_hoc_dataset(child) for child in get_children(do_node) ]
        else_list = [ json_to_ast_for_hoc_dataset(child) for child in get_children(else_node) ]
        # node_type is 'maze_ifElse_bool_path_ahead' or 'maze_ifElse_bool_path_left' or 'maze_ifElse_bool_path_right'
        return ASTNode(
            'ifelse',
            cond,
            [ ASTNode('do', cond, do_list), ASTNode('else', cond, else_list) ],
        )

    if node_type == 'maze_moveForward':
        return ASTNode('move')

    if node_type == 'maze_turn':
        direction = children[0]
        if direction['type'] == 'turnLeft':
            dir = 'turn_left' # for simplicity of notation
        elif direction['type'] == 'turnRight':
            dir = 'turn_right'
        else:
            print('Unexpected node type, failing:', node_type, direction)
            return None
        assert(direction['type'] in node_type_parameters[node_type])
        # node_type is 'maze_turn_turnLeft' or 'maze_turn_turnRight'
        return ASTNode(dir)
    # The following have to be 'turnLeft'/'turnRight' in correct ASTs:
    if node_type == 'maze_turnLeft':
        return ASTNode('turn_left')
    if node_type == 'maze_turnRight':
        return ASTNode('turn_right')

    print('Unexpected node type, failing:', node_type)
    assert(False)
    return None



def is_last_child_turn(root:ASTNode):

    children = root.children()
    if children[-1]._type == "turn_left" or children[-1]._type == "turn_right":
        return True
    else:
        return False


def get_size(root:ASTNode):
    size = 0
    for i, child in enumerate(root._children):
        if child._type != 'phi':
            size += get_size(child)

    if root._type != 'phi' and root._type != 'else' and root._type != 'do':
        size += 1

    return size


def last_node_check(sketch: ASTNode):
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


def get_max_block_size(root:ASTNode):

    max_blk_size = 0
    node_without_children = ['move', 'turn_right', 'turn_left', 'pick_marker', 'put_marker']
    queue = collections.deque([root])
    while len(queue):
        for i in range(len(queue)):
            node = queue.popleft()
            node_types = [node._type for node in node._children]
            labled_nodes = ''
            for n in node_types:
                if n in node_without_children:
                    labled_nodes += 'A'
                else:

                    labled_nodes += 'O'
            # get the longest subsequence
            max_len = len(max(re.compile("(A+)*").findall(labled_nodes)))
            if max_blk_size < max_len:
                max_blk_size = max_len


            for child in node._children:
                queue.append(child)

    return max_blk_size

def extract_conditionals_from_code(root:ASTNode):

    conditional_list = []
    conditional_node_types = ['if', 'ifelse', 'while', 'repeat_until_goal']
    queue = collections.deque([root])
    while len(queue):
        for i in range(len(queue)):
            node = queue.popleft()
            node_types = [[node._type, node._condition] for node in node._children]
            for n in node_types:
                if n[0] in conditional_node_types:
                    conditional_list.append(n)


            for child in node._children:
                queue.append(child)



    return conditional_list



def valid_ASTNode(root:ASTNode, type='karel'):
    node_with_children = ['while', 'repeat', 'if',
                          'do', 'else', 'ifelse']
    node_repeats = ['while', 'repeat']

    only_repeats = ['repeat']

    queue = collections.deque([root])
    while len(queue):
        for i in range(len(queue)):
            node = queue.popleft()
            if node._type == "run" and type == "hoc":
                if len(node._children) != 0:
                    last_child = node._children[-1].name
                    if last_child in ["turn_left", "turn_right"]:
                        return False

            node_children = [n._type for n in node._children]
            if node._type in node_with_children:
                if len(node._children) == 0:
                    return False

            # to avoid cases with repeat(X1){a}; repeat(X1){a}/ while(b){c}; while(b){c}
            for i in range(len(node_children)):
                if node_children[i] in node_repeats:
                    if i + 1 < len(node_children):

                        if node_children[i + 1] == node_children[i]:
                            if (node._children[i + 1]._hash == node._children[i]._hash):
                                return False

                    if i - 1 >= 0:
                        # if node_children[i - 1] == node_children[i]:
                        #     return False
                        if node_children[i - 1] == node_children[i]:
                            if (node._children[i - 1]._hash == node._children[i]._hash):
                                return False

                # to avoid cases with repeat(X1){a}; repeat(X2){a}
                if node_children[i] in only_repeats:
                    if i + 1 < len(node_children):
                        if node_children[i + 1] in only_repeats:
                            child_1 = node._children[i]._children
                            child_2 = node._children[i + 1]._children
                            if len(child_1) == len(child_2):
                                flag = False
                                for j in range(len(child_1)):
                                    if (child_1[j]._hash != child_2[j]._hash):
                                        flag = True
                                        break
                                return flag

                    if i - 1 >= 0:
                        if node_children[i - 1] in only_repeats:
                            child_1 = node._children[i]._children
                            child_2 = node._children[i - 1]._children
                            if len(child_1) == len(child_2):
                                flag = False
                                for j in range(len(child_1)):
                                    if (child_1[j]._hash != child_2[j]._hash):
                                        flag = True
                                        break
                                return flag

            for child in node._children:
                queue.append(child)

    return True




def get_hash_code_of_ast(root:ASTNode):
    hash = int(root._type_enum)

    if root._children == [] or root._children is None:
        return hash

    for i, child in enumerate(root._children):
        if child._type != 'phi':
            hash = join_ints(get_hash_code_of_ast(child) * (i + 1), hash, max_pow=MAX_POW)

    return hash



























