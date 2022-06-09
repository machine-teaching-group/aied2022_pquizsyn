import zss
from itertools import groupby
from code.step2_struct2code.sym_vocab import SymVocab, get_vocabT, get_attr
import collections
import enum
import json
import copy


class SymNodeType(enum.IntEnum):

    MOVE_FORWARD = 1
    TURN_LEFT = 2
    TURN_RIGHT = 3
    PICK_MARKER = 4
    PUT_MARKER = 5


    IF_PATH_AHEAD = 6
    IF_NO_PATH_AHEAD = 7

    IF_PATH_LEFT = 8
    IF_NO_PATH_LEFT = 9

    IF_PATH_RIGHT = 10
    IF_NO_PATH_RIGHT = 11

    IF_MARKER = 12
    IF_NO_MARKER = 13

    ELSE = 14


    WHILE_PATH_AHEAD = 15
    WHILE_NO_PATH_AHEAD = 16

    WHILE_PATH_LEFT = 17
    WHILE_NO_PATH_LEFT = 18

    WHILE_PATH_RIGHT = 19
    WHILE_NO_PATH_RIGHT = 20

    WHILE_MARKER = 21
    WHILE_NO_MARKER = 22



    REPEAT_2 = 23
    REPEAT_3 = 24
    REPEAT_4 = 25
    REPEAT_5 = 26
    REPEAT_6 = 27
    REPEAT_7 = 28
    REPEAT_8 = 29
    REPEAT_9 = 30

    REPEAT_UNTIL_GOAL = 31


    PHI = 32
    RUN = 33

    OTHER = 34

    IFELSE_PATH_AHEAD = 35
    IFELSE_NO_PATH_AHEAD = 36

    IFELSE_PATH_LEFT = 37
    IFELSE_NO_PATH_LEFT = 38

    IFELSE_PATH_RIGHT = 39
    IFELSE_NO_PATH_RIGHT = 40

    IFELSE_MARKER = 41
    IFELSE_NO_MARKER = 42

    DO = 43



node_str_to_symtype = {

    'run': SymNodeType.RUN,

    'while(bool_goal)': SymNodeType.REPEAT_UNTIL_GOAL,
    'repeat_until_goal(bool_goal)': SymNodeType.REPEAT_UNTIL_GOAL,
    'while(bool_path_ahead)': SymNodeType.WHILE_PATH_AHEAD,
    'while(bool_no_path_ahead)': SymNodeType.WHILE_NO_PATH_AHEAD,
    'while(bool_path_left)': SymNodeType.WHILE_PATH_LEFT,
    'while(bool_no_path_left)': SymNodeType.WHILE_NO_PATH_LEFT,
    'while(bool_path_right)': SymNodeType.WHILE_PATH_RIGHT,
    'while(bool_no_path_right)': SymNodeType.WHILE_NO_PATH_RIGHT,
    'while(bool_marker)': SymNodeType.WHILE_MARKER,
    'while(bool_no_marker)': SymNodeType.WHILE_NO_MARKER,

    'repeat(2)': SymNodeType.REPEAT_2,
    'repeat(3)': SymNodeType.REPEAT_3,
    'repeat(4)': SymNodeType.REPEAT_4,
    'repeat(5)': SymNodeType.REPEAT_5,
    'repeat(6)': SymNodeType.REPEAT_6,
    'repeat(7)': SymNodeType.REPEAT_7,
    'repeat(8)': SymNodeType.REPEAT_8,
    'repeat(9)': SymNodeType.REPEAT_9,

    'if(bool_path_ahead)': SymNodeType.IF_PATH_AHEAD,
    'if(bool_path_left)': SymNodeType.IF_PATH_LEFT,
    'if(bool_path_right)': SymNodeType.IF_PATH_RIGHT,
    'if(bool_marker)': SymNodeType.IF_MARKER,
    'if(bool_no_marker)': SymNodeType.IF_NO_MARKER,
    'if(bool_no_path_ahead)': SymNodeType.IF_NO_PATH_AHEAD,
    'if(bool_no_path_left)': SymNodeType.IF_NO_PATH_LEFT,
    'if(bool_no_path_right)': SymNodeType.IF_NO_PATH_RIGHT,


    'else': SymNodeType.ELSE,


    'move': SymNodeType.MOVE_FORWARD,
    'turn_left': SymNodeType.TURN_LEFT,
    'turn_right': SymNodeType.TURN_RIGHT,
    'pick_marker': SymNodeType.PICK_MARKER,
    'put_marker': SymNodeType.PUT_MARKER,
    'phi': SymNodeType.PHI,

    'hocaction': SymNodeType.OTHER,
    'karelaction': SymNodeType.OTHER,
    'hocconditional': SymNodeType.OTHER,
    'karelconditional': SymNodeType.OTHER,
    'hocrepeat': SymNodeType.OTHER,
    'karelrepeat': SymNodeType.OTHER,
    'hocrepeatuntil': SymNodeType.OTHER,
    'karelwhile': SymNodeType.OTHER,

    'ifelse(bool_path_ahead)': SymNodeType.IFELSE_PATH_AHEAD,
    'ifelse(bool_path_left)': SymNodeType.IFELSE_PATH_LEFT,
    'ifelse(bool_path_right)': SymNodeType.IFELSE_PATH_RIGHT,
    'ifelse(bool_marker)': SymNodeType.IFELSE_MARKER,
    'ifelse(bool_no_marker)': SymNodeType.IFELSE_NO_MARKER,
    'ifelse(bool_no_path_ahead)': SymNodeType.IFELSE_NO_PATH_AHEAD,
    'ifelse(bool_no_path_left)': SymNodeType.IFELSE_NO_PATH_LEFT,
    'ifelse(bool_no_path_right)': SymNodeType.IFELSE_NO_PATH_RIGHT,

    'do': SymNodeType.DO



}



MAX_POW = 44

def dsamepow10(num, max_pow=MAX_POW): # returns the max pow of max_pow in num
    r = 1
    while num >= max_pow:
        num = int(num // max_pow)
        r *= max_pow
    return r


def join_ints(a, b, max_pow=MAX_POW):
    return a * dsamepow10(b) * max_pow + b


class AST:

    def __init__(self, name, children=None, val_constraints=None, type='hoc'):

        if children is None:
            children = []
        if val_constraints is None:
            val_constraints = []

        self.type = type
        self.name = name
        self.name_type = self.name.split('-')[0]
        self.children = children
        self.val_constraints = val_constraints


        self._type_enum = node_str_to_symtype[self.name_type]
        self._hash = int(self._type_enum)
        self._size = 0
        self._depth = 0

        # counts of the constructs
        self._n_if = 0
        self._n_while = 0
        self._n_repeat = 0
        self._n_else = 0
        self._n_repeat_until_goal = 0

        for i, child in enumerate(children):
            if child.name != 'phi':
                self._size += child._size
            self._depth = max(self._depth, child._depth)
            if child.name != 'phi':
                self._hash = join_ints(child._hash * (i + 1), self._hash, max_pow=MAX_POW)

            self._n_if += child._n_if
            self._n_while += child._n_while
            self._n_else += child._n_else
            self._n_repeat += child._n_repeat
            self._n_repeat_until_goal += child._n_repeat_until_goal
            child._parent = self

        if self._type_enum != SymNodeType.PHI and self._type_enum != SymNodeType.ELSE and self._type_enum != SymNodeType.DO:
            self._size += 1
        if self._type_enum != SymNodeType.MOVE_FORWARD or self._type_enum != SymNodeType.TURN_RIGHT or\
            self._type_enum != SymNodeType.TURN_LEFT or self._type_enum != SymNodeType.PUT_MARKER or\
            self._type_enum != SymNodeType.PICK_MARKER:
            self._depth += 1

        if self._type_enum == SymNodeType.WHILE_NO_MARKER or self._type_enum == SymNodeType.WHILE_MARKER or\
                self._type_enum == SymNodeType.WHILE_PATH_AHEAD or self._type_enum == SymNodeType.WHILE_NO_PATH_AHEAD or\
                self._type_enum == SymNodeType.WHILE_PATH_LEFT or self._type_enum == SymNodeType.WHILE_NO_PATH_LEFT or\
                self._type_enum == SymNodeType.WHILE_PATH_RIGHT or self._type_enum == SymNodeType.WHILE_NO_PATH_RIGHT:
             self._n_while += 1
        elif self._type_enum == SymNodeType.REPEAT_2 or self._type_enum == SymNodeType.REPEAT_3 or self._type_enum == SymNodeType.REPEAT_4 or \
             self._type_enum == SymNodeType.REPEAT_5 or self._type_enum == SymNodeType.REPEAT_6 or self._type_enum == SymNodeType.REPEAT_7 or\
             self._type_enum == SymNodeType.REPEAT_8 or self._type_enum == SymNodeType.REPEAT_9:
             self._n_repeat += 1
        elif self._type_enum == SymNodeType.IF_PATH_AHEAD or self._type_enum == SymNodeType.IF_NO_PATH_AHEAD or \
             self._type_enum == SymNodeType.IF_PATH_LEFT or self._type_enum == SymNodeType.IF_NO_PATH_LEFT or \
             self._type_enum == SymNodeType.IF_PATH_RIGHT or self._type_enum == SymNodeType.IF_NO_PATH_RIGHT or \
             self._type_enum == SymNodeType.IF_MARKER or self._type_enum == SymNodeType.IF_NO_MARKER:
             self._n_if += 1
        elif self._type_enum == SymNodeType.ELSE:
             self._n_else += 1
        elif self._type_enum == SymNodeType.REPEAT_UNTIL_GOAL:
             self._n_repeat_until_goal += 1
        else:
            pass

    def to_int(self):
        return self._hash

    def to_json(self):
        return convert_to_json(self, type=self.type)

    def size(self):
        return self._size

    def children(self):
        return self.children

    def __str__(self):
        return self.to_str()

    def __eq__(self, other):
        # return self._hash == other._hash
        self_json = json.dumps(self.to_json())
        other_json = json.dumps(other.to_json())
        return self_json == other_json

    def __hash__(self):
        return self._hash


    def to_str(self, indent=0):
        '''Given a prog, print it with indents'''
        constraints_string = ','
        if len(self.val_constraints) != 0:
            constraints_string = str(self.val_constraints)


        stri = '  ' * indent + self.name + ' '+ constraints_string +'\n'
        for child in self.children:
            stri += child.to_str(indent + 1)

        return stri

    def get_names(self):
        '''Given a prog, extract the vars'''
        li = []
        if '-' in self.name:
            li.append(self.name)

        for child in self.children:
            li.extend(child.get_names())
        return li

    def get_names_with_fixed_vals(self):
        '''Given a prog, extract the vars with their fixed constraints'''
        li = []
        if '-' in self.name:
            t_var = [self.name, self.val_constraints]
            li.append(t_var)
        for child in self.children:
            li.extend(child.get_names_with_fixed_vals())
        return li

    def get_actionChildren(self):
        '''Get all children which are action'''
        return [child.name
                for child in self.children
                if get_vocabT(child.name) in ['hocaction', 'karelaction']]


    def get_if_conditionals(self):
        '''Get all conditional variables'''
        li = []
        if get_vocabT(self.name) in ['hocconditional', 'karelconditional']:
            li.append(self.name)

        for child in self.children:
            li.extend(child.get_if_conditionals())
        return li

    def get_while_conditionals(self):
        '''Get all conditional variables'''
        li = []
        if get_vocabT(self.name) in ['karelwhile']:
            li.append(self.name)

        for child in self.children:
            li.extend(child.get_while_conditionals())
        return li

    def get_repeat_vars(self):
        '''Get all the repeat variables'''
        li = []
        if get_vocabT(self.name) in ['hocrepeat', 'karelrepeat']:
            li.append(self.name)
        for child in self.children:
            li.extend(child.get_repeat_vars())
        return li



    def check_conditional(self):
        return get_vocabT(self.name) in ['hocconditional', 'karelconditional']

    def check_loop(self):
        return get_vocabT(self.name) in ['hocrepeatuntil', 'karelwhile']

    def check_karelLoop(self):
        return get_vocabT(self.name) in ['karelwhile']

    def check_repeat(self):
        return get_vocabT(self.name) in ['hocrepeat', 'karelrepeat']

    def check_repeatuntil(self):
        return get_vocabT(self.name) in ['hocrepeatuntil']




def remove_null_nodes(root:AST):
    queue = collections.deque([root])
    while len(queue):
        for i in range(len(queue)):
            node = queue.popleft()
            node.children = list(filter((AST('phi', [])).__ne__, node.children))

            # for child in node._children:
            #     if child._type == 'phi':
            #         node._children.remove(child)


            for child in node.children:
                 queue.append(child)


    return root

def valid_prog(root:AST, type='karel'):
    node_with_children = ['while(bool_path_ahead)', 'while(bool_no_path_ahead)', 'while(bool_path_left)', 'while(bool_no_path_left)', 'while(bool_path_right)',
                          'while(bool_no_path_right)', 'while(bool_marker)', 'while(bool_no_marker)', 'repeat(2)', 'repeat(3)', 'repeat(4)', 'repeat(5)',
                          'repeat(6)', 'repeat(7)', 'repeat(8)', 'repeat(9)', 'if(bool_path_ahead)', 'if(bool_path_left)', 'if(bool_path_right)',
                          'if(bool_marker)', 'if(bool_no_marker)', 'if(bool_no_path_ahead)', 'if(bool_no_path_left)', 'if(bool_no_path_right)', 'else']
    node_repeats = ['while(bool_path_ahead)', 'while(bool_no_path_ahead)', 'while(bool_path_left)', 'while(bool_no_path_left)', 'while(bool_path_right)',
                          'while(bool_no_path_right)', 'while(bool_marker)', 'while(bool_no_marker)', 'repeat(2)', 'repeat(3)', 'repeat(4)', 'repeat(5)',
                          'repeat(6)', 'repeat(7)', 'repeat(8)', 'repeat(9)']

    only_repeats = ['repeat(2)', 'repeat(3)', 'repeat(4)', 'repeat(5)', 'repeat(6)', 'repeat(7)', 'repeat(8)', 'repeat(9)']


    queue = collections.deque([root])
    while len(queue):
        for i in range(len(queue)):
            node = queue.popleft()
            if node.name == "run" and type == "hoc":
                if len(node.children) != 0:
                    last_child = node.children[-1].name
                    if last_child in ["turn_left", "turn_right"]:
                        return False


            node_children = [n.name for n in node.children]
            if node.name in node_with_children:
                if len(node.children) == 0:
                    return False

            # to avoid cases with repeat(X1){a}; repeat(X1){a}/ while(b){c}; while(b){c}
            for i in range(len(node_children)):
                if node_children[i] in node_repeats:
                    if i+1 < len(node_children):
                        # if node_children[i+1] == node_children[i]:
                        #     return False
                        if node_children[i+1] == node_children[i]:
                            if (node.children[i+1]._hash == node.children[i]._hash):
                                return False

                    if i-1 >= 0:
                        # if node_children[i - 1] == node_children[i]:
                        #     return False
                        if node_children[i - 1] == node_children[i]:
                            if (node.children[i-1]._hash == node.children[i]._hash):
                                return False


                # to avoid cases with repeat(X1){a}; repeat(X2){a}
                if node_children[i] in only_repeats:
                    if i + 1 < len(node_children):
                        if node_children[i+1] in only_repeats:
                            child_1 = node.children[i].children
                            child_2 = node.children[i+1].children
                            if len(child_1) == len(child_2):
                                flag = False
                                for j in range(len(child_1)):
                                    if (child_1[j]._hash != child_2[j]._hash):
                                        flag = True
                                        break
                                return flag

                    if i - 1 >= 0:
                        if node_children[i-1] in only_repeats:
                            child_1 = node.children[i].children
                            child_2 = node.children[i-1].children
                            if len(child_1) == len(child_2):
                                flag = False
                                for j in range(len(child_1)):
                                    if (child_1[j]._hash != child_2[j]._hash):
                                        flag = True
                                        break
                                return flag





            for child in node.children:
                queue.append(child)

    return True




def add_if_else_node(root:AST):

    queue = collections.deque([root])
    while len(queue):
        for i in range(len(queue)):
            node = queue.popleft()
            children = node.children
            children_names = [c.name for c in children]
            children_names_clean = [c.split('(')[0] for c in children_names]
            # print(children_names)
            if 'if' in children_names_clean and 'ifelse' not in node.name:
                indices = [i for i, s in enumerate(children_names) if 'if' in s]
                cond = children_names[indices[0]].split('(')
                if cond[0] != 'ifelse':
                    bool_cond = cond[-1].split(')')[0]
                    if indices[0]+1 < len(children_names):
                        if children_names[indices[0] + 1] == 'else':
                            new_node = AST('ifelse'+'('+bool_cond+')')
                            children[indices[0]].name = 'do'
                            new_node.children = [children[indices[0]], children[indices[0]+1]]
                            node.children.pop(indices[0]+1)
                            node.children.pop(indices[0])
                            node.children.insert(indices[0], new_node)
                            # print(node)
                        else:# only if-node present
                            for i in indices:
                                if children[i].children[0].name != 'do':
                                    new_node = AST('do')
                                    new_node.children = copy.deepcopy(node.children[i].children)
                                    node.children[i].children = [new_node]


                    else: # only if-node present
                        for i in indices:
                            if children[i].children[0].name != 'do':
                                new_node = AST('do')
                                new_node.children = copy.deepcopy(node.children[i].children)
                                node.children[i].children = [new_node]


            for child in node.children:
                    queue.append(child)

    return root


def convert_to_json(node: AST, type:str):
    ''' Converts an SymAST into a JSON dictionary.'''

    if len(node.children) == 0:
        return {
            'type': node.name,
            # 'children': [],
        }
    node_dict = None
    if node.name != 'do' and node.name != 'else':
        if type!= 'karel':
            if node.name.split('(')[0] == 'while':
                node_dict = {'type': 'repeat_until_goal(bool_goal)'}
                children = [convert_to_json(child, type) for child in node.children]
            else:
                node_dict = {'type': node.name}
                children = [convert_to_json(child, type) for child in node.children]
        else:
            node_dict = {'type': node.name}
            children = [convert_to_json(child, type) for child in node.children]

        if node.name.split('(')[0] == 'if':
            do_dict = {'type': 'do'}
            do_list = node.children[0]
            do_dict['children'] = [convert_to_json(child, type) for child in do_list.children]
            children.append(do_dict)

        elif node.name.split('(')[0] == 'ifelse':
            do_dict = {'type': 'do'}
            do_list = node.children[0]
            do_dict['children'] = [convert_to_json(child, type) for child in do_list.children]
            children.append(do_dict)
            else_dict = {'type': 'else'}
            else_list = node.children[1]
            else_dict['children'] = [convert_to_json(child, type) for child in else_list.children]
            children.append(else_dict)

        children = list(filter(None.__ne__, children))
        if children:
            node_dict['children'] = children

    return node_dict


def get_ast_size(ast:AST):
    size = 0
    for i, child in enumerate(ast.children):
        if child.name != 'phi':
            size += get_ast_size(child)
    if ast.name != 'phi':
        size += 1

    return size


def get_consecutive_action_nodes(root:AST):
    consecutive_actions = []
    queue = collections.deque([root])
    while len(queue):
        for i in range(len(queue)):
            node = queue.popleft()
            children = node.children
            # get the names of the children
            children_names = [c.name for c in children]
            children_types = [c.name.split('-')[0] for c in children]

            # group the above list with common elements
            grouped_list =  [list(y) for x, y in groupby(children_types)]

            index_tuples = []
            # get the indices of consecutive action nodes
            counter = 0
            for ele in grouped_list:
                if ele[0] in ['hocaction', 'karelaction']:
                    index_tuples.append((counter, counter + len(ele) - 1))
                counter += len(ele)
            # get the action names
            for ele in index_tuples:
                action_nodes = []
                id_list = list(range(ele[0], ele[1] + 1))
                for i in id_list:
                    action_nodes.append(children_names[i])

                consecutive_actions.append(action_nodes)

            for child in node.children:
                    queue.append(child)


    return consecutive_actions











def tree_edit_distance_symast(ast_a: AST, ast_b: AST):
    ''' Computes the ZSS tree edit distance between two trees (as ASTNodes). '''

    def update_cost(node_a, node_b):
        label_a = node_a.name
        label_a_split = label_a.split('(')[0]
        label_b = node_b.name
        label_b_split = label_b.split('(')[0]

        if label_a == label_b:
            return 0
        else:
            if label_a in ['turn_left', 'turn_right'] and \
                    label_b in ['turn_left', 'turn_right']:
                return 1
            elif label_a in ['put_marker', 'pick_marker'] and \
                    label_b in ['put_marker', 'pick_marker']:
                return 1

            elif label_a_split == 'ifelse' and label_b_split == 'ifelse':
                return 1

            elif label_a_split == 'if' and label_b_split == 'if':
                return 1

            elif label_a_split == 'while' and label_b_split == 'while':
                return 1

            elif label_a_split == 'repeat' and label_b_split == 'repeat':
                return 1
            elif label_a == 'do' and label_b == 'do':
                return 1
            elif label_a == 'else' and label_b == 'else':
                return 1
            else:
                return 2


    def insert_cost(node):
        label = node.name
        return 0 if label == 'do' or label == 'else' else 1

    def remove_cost(node):
        label = node.name
        label_split = label.split('(')[0]
        if label_split == 'repeat' or label_split == 'while' or label_split == 'repeat_until_goal':
            if len(node.children) == 0:
                return 1
            else:
                return len(node.children)

        return 0 if label == 'do'or label == 'else' else 1

    return zss.distance(
        ast_a,
        ast_b,
        AST.children,
        insert_cost=insert_cost,
        remove_cost=remove_cost,
        update_cost=update_cost,
    )


## this routine computes the hash of a given SYMAST
def get_hash_code_of_symast(root: AST):
    hash = int(root._type_enum)

    if root.children == []:
        return hash

    for i,child in enumerate(root.children):
        if child.name != 'phi':
            hash = join_ints(get_hash_code_of_symast(child)*(i+1), hash, max_pow=MAX_POW)

    return hash

## this routine computes the size of a given SYMAST
def get_size_of_symast(root: AST):
    size = 0
    for i, child in enumerate(root.children):
        if child.name != 'phi':
            size += get_size_of_symast(child)

    if root.name != 'phi' and root.name != 'else' and root.name != 'do':
        size += 1


    return size


def get_action_type(name:str):
    if name in ['move', 'turn_left', 'turn_right', 'pick_marker', 'put_marker']:
        return 'action'
    else:
        return 'not_action'


# this routine is added to cater to codes where actions occuring before or after a repeat loop, should be removed if same as
# actions nested in repeat
# call this routine on codes with repeat construct AFTER phi nodes have been removed
def filter_codes_with_repeat_nodes(root:AST):

    repeat_valid = True
    for index in range(len(root.children)):
        childrepeat = root.children[index]
        if 'repeat(' in childrepeat.name:  # repeat_node found at index
            # get the siblings of repeat which are action nodes
            siblings = []
            siblings_before = []
            if index - 1 >= 0:
                for i in range(0, index):
                    siblings_before.append(root.children[i])
            if index + 1 < len(root.children):
                for i in range(index + 1, len(root.children)):
                    siblings.append(root.children[i])

            sibling_names = [s.name for s in siblings]
            sibling_name_types = [get_action_type(s) for s in sibling_names]
            sibling_names_before = [s.name for s in siblings_before]
            sibling_name_types_before = [get_action_type(s) for s in sibling_names_before]
            # scan this list to get the first set of action nodes
            indices = []
            # first occurrence of action node
            if len(sibling_name_types) != 0:
                if sibling_name_types[0] in ['action']:
                    indices.append(0)
                    for j in range(1, len(sibling_name_types)):
                        if sibling_name_types[j] in ['action']:
                            indices.append(j)
                        else:
                            break
            vars_1 = [sibling_names[i] for i in indices] # all action nodes before repeat

            # get the occurrence of action nodes before repeat
            indices_before = []
            if len(sibling_name_types_before) != 0:
                if sibling_name_types_before[-1] in ['action']:
                    indices_before.append(len(sibling_name_types_before) - 1)
                    for j in range(len(sibling_name_types_before) - 2, -1, -1):
                        if sibling_name_types_before[j] in ['action']:
                            indices_before.append(j)
                        else:
                            break
            indices_before = reversed(indices_before)
            vars_3 = [sibling_names_before[i] for i in indices_before] # all action nodes after repeat



            # check if all children of repeat are only action nodes
            children_repeat = [n.name for n in childrepeat.children]
            children_repeat_types = [get_action_type(n) for n in children_repeat]
            flag = True
            for c in children_repeat_types:
                if c in ['action']:
                    continue
                else:
                    flag = False
                    return True
            # all children of repeat are action nodes
            vars_2 = []
            if flag:
                vars_2 = [n for n in children_repeat]
                # additionally do not allow all elements nested inside repeat to be 'move', if action nodes are more than 1
                if len(vars_2)>1 and all(ele == "move" for ele in vars_2):
                    return False

            # print(vars_1, vars_2, vars_3)

            if len(vars_1) == 0 and len(vars_3) == 0:
                return True

            if len(vars_2) <= len(vars_1):
                pre_vars_1 = vars_1[:len(vars_2)]
                if pre_vars_1 == vars_2:
                    return False

            if len(vars_2) <= len(vars_3):
                suff_vars_3 = vars_3[-len(vars_2):]
                if suff_vars_3 == vars_2:
                    return False



    for child in root.children:  # Else, search in children
        if len(child.children) != 0:
            filter_codes_with_repeat_nodes(child)

    return repeat_valid
