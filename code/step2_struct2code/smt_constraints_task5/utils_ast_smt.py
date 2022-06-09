import enum
import json
import collections

class NodeType(enum.IntEnum):
    MOVE_FORWARD = 1
    TURN_LEFT = 2
    TURN_RIGHT = 3
    PICK_MARKER = 4
    PUT_MARKER = 5

    IF_ONLY = 6
    END_IF_ONLY = 7
    IF_ELSE = 8
    IF = 9
    ELSE = 10
    END_IF_IF_ELSE = 11
    END_ELSE_IF_ELSE = 12

    WHILE = 13
    END_WHILE = 14
    REPEAT = 15
    REPEAT_UNTIL_GOAL = 21
    END_REPEAT = 16

    BLOCK = 17
    BLOCK_IF = 18
    BLOCK_ELSE = 19

    RUN = 20
    PHI = 21

    TWO = 22
    THREE = 23
    FOUR = 24
    FIVE = 25
    SIX = 26
    SEVEN = 27
    EIGHT = 28
    NINE = 29
    TEN = 30

    BOOL_PATH_AHEAD = 31
    BOOL_NO_PATH_AHEAD = 32
    BOOL_PATH_LEFT = 33
    BOOL_NO_PATH_LEFT = 34
    BOOL_PATH_RIGHT = 35
    BOOL_NO_PATH_RIGHT = 36
    BOOL_MARKER = 37
    BOOL_NO_MARKER = 38
    BOOL_GOAL = 39


node_str_to_type = {

    'run': NodeType.RUN,
    'repeat_until_goal': NodeType.REPEAT_UNTIL_GOAL,
    'while': NodeType.WHILE,
    'repeat': NodeType.REPEAT,
    'if': NodeType.IF_ONLY,
    'ifelse': NodeType.IF_ELSE,
    'do': NodeType.IF,
    'else': NodeType.ELSE,
    'move': NodeType.MOVE_FORWARD,
    'turn_left': NodeType.TURN_LEFT,
    'turn_right': NodeType.TURN_RIGHT,
    'pick_marker': NodeType.PICK_MARKER,
    'put_marker': NodeType.PUT_MARKER,
    'phi': NodeType.PHI,

    '2': NodeType.TWO,
    '3': NodeType.THREE,
    '4': NodeType.FOUR,
    '5': NodeType.FIVE,
    '6': NodeType.SIX,
    '7': NodeType.SEVEN,
    '8': NodeType.EIGHT,
    '9': NodeType.NINE,
    '10': NodeType.TEN,
    'bool_path_ahead': NodeType.BOOL_PATH_AHEAD,
    'bool_no_path_ahead': NodeType.BOOL_NO_PATH_AHEAD,
    'bool_path_left': NodeType.BOOL_PATH_LEFT,
    'bool_no_path_left': NodeType.BOOL_NO_PATH_LEFT,
    'bool_path_right': NodeType.BOOL_PATH_RIGHT,
    'bool_no_path_right': NodeType.BOOL_NO_PATH_RIGHT,
    'bool_marker': NodeType.BOOL_MARKER,
    'bool_no_marker': NodeType.BOOL_NO_MARKER,
    'bool_goal': NodeType.BOOL_GOAL


}




P = 10000000007
M = 10 ** 40





def dsamepow10(num, max_pow=40): # returns the max pow of 14 in num
    r = 1
    while num >= max_pow:
        num = int(num // max_pow)
        r *= max_pow
    return r


def join_ints(a, b, max_pow=40):
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
            self._hash = join_ints(cond_enum, self._hash, max_pow=40)

        # counts of the constructs
        self._n_if_only = 0
        self._n_while = 0
        self._n_repeat = 0
        self._n_if_else = 0


        for child in children:
            if child._type != 'phi':
                self._size += child._size
            self._depth = max(self._depth, child._depth)
            if child._type != 'phi':
                self._hash = join_ints(child._hash, self._hash, max_pow=39)
            self._n_if_else += child._n_if_else
            self._n_while += child._n_while
            self._n_if_only += child._n_if_only

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

    def label(self):
        if self._condition is not None:
            label = self._type + ' ' + self._condition
        else:
            label = self._type
        return label

    def label_enum(self):
        return self._type_enum

    def with_label(self, label):
        return ASTNode(label, self.children())

    def with_children(self, children):
        return ASTNode(self._type, self._condition, children, self._type_enum)


    def __repr__(self, offset=''):
        cs = offset + self.label() + '\n'
        for child in self.children():
            cs += offset + child.__repr__(offset + '   ')
        return cs

    def __eq__(self, other):
        return self._hash == other._hash

    def __hash__(self):
        return self._hash


def ast_to_json(node: ASTNode):
    ''' Converts an ASTNode into a JSON dictionary.
        Works for both HOC4 and HOC18 datasets. '''

    if len(node.children()) == 0:
        return {
            'type': node._type,
            #'children': [],
        }


    if node._condition is not None:
        if node._type == 'do' or node._type == 'else':
            node_dict = {'type': node._type}
        else:
            node_dict = {'type': node._type + '(' + node._condition + ')'}
    else:
        node_dict = {'type': node._type }

    children = [ast_to_json(child) for child in node.children()]

    if node._type == 'if_only':
        do_dict = {'type': 'do'}
        do_list = node.children()[0]
        do_dict['children'] = [ast_to_json(child) for child in do_list.children()]
        children.append(do_dict)
    elif node._type == 'if_else':
        do_dict = {'type': 'do'}
        do_list = node.children()[0]
        do_dict['children'] = [ast_to_json(child) for child in do_list.children()]
        children.append(do_dict)
        else_dict = {'type': 'else'}
        else_list = node.children()[1]
        else_dict['children'] = [ast_to_json(child) for child in else_list.children()]
        children.append(else_dict)


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


def is_last_child_turn(root:ASTNode):

    children = root.children()
    if children[-1]._type == "turn_left" or children[-1]._type == "turn_right":
        return True
    else:
        return False








