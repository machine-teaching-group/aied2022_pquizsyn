import json
import os
import enum
import copy
import collections
from code.step2_struct2code.sym_ast import AST, get_consecutive_action_nodes
from code.step2_struct2code.sym_vocab import SymVocab
from code.utils.ast import ASTNode


ast_node_to_sym_node = {
    'run': 'run',
    'repeat': 'repeat',
    'while': 'while',
    'repeat_until_goal': 'repeatuntil',
    # 'if_only': 'conditional',
    # 'if_else': 'conditional',
    'do': 'conditional',
    'else': 'else',
    'move': 'action',
    'turn_left': 'action',
    'turn_right': 'action',
    'pick_marker': 'action',
    'put_marker': 'action'
}

val_constraints_hoc = {
    'bool_path_ahead': ['bool_path_ahead'],
    'bool_path_left': ['bool_path_left', 'bool_path_right'],
    'bool_path_right': ['bool_path_left', 'bool_path_right'],
}


val_constraints_karel = {
    'bool_path_ahead': ['bool_path_ahead', 'bool_no_path_ahead'],
    'bool_path_left': ['bool_path_left', 'bool_path_right', 'bool_no_path_left', 'bool_no_path_right'],
    'bool_path_right': ['bool_path_left', 'bool_path_right', 'bool_no_path_left', 'bool_no_path_right'],
    'bool_no_path_ahead':  ['bool_path_ahead', 'bool_no_path_ahead'],
    'bool_no_path_left': ['bool_path_left', 'bool_path_right', 'bool_no_path_left', 'bool_no_path_right'],
    'bool_no_path_right': ['bool_path_left', 'bool_path_right', 'bool_no_path_left', 'bool_no_path_right'],
    'bool_marker': ['bool_marker', 'bool_no_marker'],
    'bool_no_marker': ['bool_marker', 'bool_no_marker']

}

basic_action_blocks_hoc = {
    'move': ['move'],
    'turn_left': ['turn_left', 'turn_right'],
    'turn_right': ['turn_left', 'turn_right'],
}

basic_action_blocks_karel = {
    'move': ['move'],
    'turn_left': ['turn_left', 'turn_right'],
    'turn_right': ['turn_left', 'turn_right'],
    'put_marker': ['put_marker', 'pick_marker'],
    'pick_marker': ['put_marker', 'pick_marker']
}


class GenerateSymASTfromCode:
    def __init__(self, minimal_code:ASTNode, max_additional_blocks:int, type='hoc'):
        self._minimal_code = minimal_code
        self._max_blk_size = max_additional_blocks
        self._type = type
        # counters are added for variable naming in the symbolic codes
        self.action_counter = 1
        self.if_conditional_counter = 1
        self.repeat_counter = 1
        self.repeat_until_counter = 1
        if self._type != 'hoc':
            self.while_conditional_counter = 1

        self.sym_code = self.get_sym_code_from_minimal_code(self._minimal_code, self._max_blk_size, self._type)
        # remove the empty 'phi' nodes
        self.sym_code = remove_null_nodes_for_symnode(self.sym_code)
        # add action nodes in between: This order is important for action sequencing --> first add actions in between and then to the end, and start
        self.sym_code, self.action_counter, self.between_names, self.before_after_block_nodes = insert_action_nodes_between(self.sym_code, self.action_counter, self._max_blk_size, type=self._type)
        # add action nodes in the beginning and the end
        self.sym_code, self.action_counter, self.prefix_suffix_names = insert_action_nodes_beginning_end(self.sym_code, self.action_counter, self._max_blk_size, self._type)
        # add the prefix, between, and suffix actions in one dictionary
        self.additional_actions = {'prefix': self.prefix_suffix_names['prefix'],
                                   'between': self.between_names['between'],
                                   'suffix': self.prefix_suffix_names['suffix'],
                                   'before_block': self.before_after_block_nodes['before'],
                                   'after_block': self.before_after_block_nodes['after']
                                   }


    def create_sym_node(self, name, children=None, val_constraints =None):
        if children is None:
            children = []
        if val_constraints is None:
            val_constraints = []

        symnode = AST(name, children, val_constraints, type=self._type)
        return symnode


    def get_sym_code_from_minimal_code(self, root:ASTNode, max_block_size:int, type:str):

        sym_node = AST('phi', type=self._type)
        do_flag = False
        if root.conditional() is not None:
            if type == 'hoc':
                conditional_dict = val_constraints_hoc
            else: # type is karel
                conditional_dict = val_constraints_karel
            if root.conditional() in ['2', '3', '4', '5', '6', '7', '8' ,'9']: # repeat
                name = self._type + ast_node_to_sym_node[root._type] + '-' + str(self.repeat_counter)
                self.repeat_counter += 1
                constraints_repeat = [int(root.conditional())-1, int(root.conditional()), int(root.conditional())+1]
                values_repeat = [ele-1 for ele in constraints_repeat]
                sym_node = self.create_sym_node(name, val_constraints=values_repeat)
            else: # if, if_else, while, repeat_until
                norm_boolean_constraints = []
                do_flag = False
                if root._type == 'if' or root._type == 'ifelse': # if, if_else
                    do_flag = True
                    sym_node = self.create_sym_node('phi', children=[], val_constraints=[])
                    sym_node.children.extend([self.get_sym_code_from_minimal_code(c, max_block_size, self._type) for c in
                                         root.children()])

                    return sym_node

                elif root._type == 'else': # else
                    name = 'else'
                elif root._type == 'repeat_until_goal': # while(bool_goal)
                    name = self._type + ast_node_to_sym_node[root._type] + '-' + str(self.repeat_until_counter)
                    self.repeat_until_counter += 1
                elif root._type == 'do': # do nothing if 'do' node encountered
                    if self._type == 'hoc':
                        bool_dict = SymVocab.hocconditional
                    else: # type is karel
                        bool_dict = SymVocab.karelconditional
                    rev_bool_dict = {value : key for (key, value) in bool_dict.items()}
                    boolean_constraints = conditional_dict[root._condition]
                    norm_boolean_constraints = []
                    for b in boolean_constraints:
                        key = 'if(' + b + ')'
                        v = rev_bool_dict[key]
                        norm_boolean_constraints.append(v)
                    name = self._type + ast_node_to_sym_node[root._type] + '-' + str(self.if_conditional_counter)
                    self.if_conditional_counter += 1
                else: # while, repeat_until_goal
                    if root._type == 'while':
                        if self._type == 'hoc':
                            assert "No WHILE Construct in HOC tasks!"
                            exit(0)
                        else:  # type is karel
                            bool_dict = SymVocab.karelwhile
                        rev_bool_dict = {value: key for (key, value) in bool_dict.items()}
                        boolean_constraints = conditional_dict[root._condition]
                        norm_boolean_constraints = []
                        for b in boolean_constraints:
                            key = 'while(' + b + ')'
                            v = rev_bool_dict[key]
                            norm_boolean_constraints.append(v)
                    name = self._type + ast_node_to_sym_node[root._type] + '-' + str(self.while_conditional_counter)
                    self.while_conditional_counter += 1

                if not do_flag: # for nodes not if, ifelse
                    sym_node = self.create_sym_node(name, val_constraints=norm_boolean_constraints)




        else: # run node, action nodes
            if type == "hoc":
                action_dict = basic_action_blocks_hoc
            else: #type is 'karel'
                action_dict = basic_action_blocks_karel
            if root._type == "run":
                sym_node = self.create_sym_node(ast_node_to_sym_node[root._type], children=[])
            elif root._type == "move" or root._type == "turn_left" or root._type == "turn_right" or \
                    root._type == "pick_marker" or root._type == "put_marker":
                if self._type == 'hoc':
                    act_dict = SymVocab.hocaction
                else:  # type is karel
                    act_dict = SymVocab.karelaction
                rev_act_dict = {value: key for (key, value) in act_dict.items()}
                act_constraints = action_dict[root._type]
                norm_act_constraints = []
                for b in act_constraints:
                    key = b
                    v = rev_act_dict[key]
                    norm_act_constraints.append(v)

                n = self._type+ast_node_to_sym_node[root._type]+"-"+str(self.action_counter)
                sym_node = self.create_sym_node(n, val_constraints=norm_act_constraints)
                self.action_counter += 1
            else:
                assert "Unknown node encountered!"



        if len(root.children()) == 0:
            return sym_node

        else:
            if not do_flag:
                sym_node.children.extend([self.get_sym_code_from_minimal_code(c, max_block_size, type) for c in root.children()])


        return sym_node




def remove_null_nodes_for_symnode(root: AST):
    queue = collections.deque([root])
    while len(queue):
        for i in range(len(queue)):
            node = queue.popleft()
            children = node.children
            #node.children = list(filter((AST('phi', [])).__ne__, node.children))
            children_names = [c.name for c in node.children]
            if 'phi' in children_names:
                index = children_names.index('phi')
                phi_children = children[index].children
                if phi_children:
                    for j in range(len(phi_children)):
                        children.insert(index+j+1, phi_children[j])
                children.pop(index)


            for child in node.children:
                queue.append(child)

    return root


def insert_action_nodes_between(root:AST, current_action_counter:int, max_blk_size:int, type='hoc'):
    between_action_nodes = {'between':[]}
    block_before_after_nodes = {'before':[], 'after':[]}
    action_counter = current_action_counter
    queue = collections.deque([root])
    while len(queue):
        for i in range(len(queue)):
            node = queue.popleft()
            children = node.children
            children_names = [c.name for c in node.children]
            children_types = [c.name_type for c in node.children]
            # print("Children Types:", children_types)
            new_children = copy.deepcopy(children)
            new_child_counter = 1
            new_middle_actions = 0
            flag_block = False
            append_counter = [] # collects the index of the first time an action node occurs in a block
            if len(children_types) == 1 and children_types[0] in ['hocaction', 'karelaction']:
                flag_block = True
                append_counter = [0]
            # add additional action nodes in between two action nodes
            for j in range(len(children_types)-1):
                if (children_types[j] in ['hocaction', 'karelaction']) and \
                    (children_types[j + 1] in ['hocaction', 'karelaction']):
                    flag_block = True
                    n = type + 'action-' + str(action_counter)
                    between_action_nodes['between'].append(n)
                    action_counter += 1
                    child_2 = AST(n, type=type)
                    new_children.insert(j+new_child_counter, child_2)
                    new_middle_actions += 1
                    new_child_counter += 1
                    append_counter.append(j) # collects the index of the first time an action node occurs in a block
                elif j>0 and (children_types[j-1] not in ['hocaction', 'karelaction']) and (children_types[j] in ['hocaction', 'karelaction']) and \
                    (children_types[j + 1] not in ['hocaction', 'karelaction']):
                    flag_block = False
                    before_actions = []
                    for b in range(max_blk_size):
                        n = type + 'action-' + str(action_counter)
                        before_actions.append(n)
                        action_counter += 1
                        child_n = AST(n, type=type)
                        new_children.insert(j, child_n)
                    block_before_after_nodes['before'].append(before_actions)
                    # actions added after a block
                    after_actions = []
                    for b in range(max_blk_size):
                        n = type + 'action-' + str(action_counter)
                        after_actions.append(n)
                        action_counter += 1
                        child_n = AST(n, type=type)
                        new_children.insert(j+1+max_blk_size, child_n)
                    block_before_after_nodes['after'].append(after_actions)
                elif j==0 and (children_types[j] in ['hocaction', 'karelaction']) and  (children_types[j + 1] not in ['hocaction', 'karelaction']):
                    flag_block = False
                    before_actions = []
                    for b in range(max_blk_size):
                        n = type + 'action-' + str(action_counter)
                        before_actions.append(n)
                        action_counter += 1
                        child_n = AST(n, type=type)
                        new_children.insert(j, child_n)
                    block_before_after_nodes['before'].append(before_actions)
                    # actions added after a block
                    after_actions = []
                    for b in range(max_blk_size):
                        n = type + 'action-' + str(action_counter)
                        after_actions.append(n)
                        action_counter += 1
                        child_n = AST(n, type=type)
                        new_children.insert(j + 1 + max_blk_size, child_n)
                    block_before_after_nodes['after'].append(after_actions)
                else:
                    continue

            # check if the last action in the children_types is a action-node
            if (len(children_types) > 1) and (children_types[-1] in ['hocaction', 'karelaction']) and \
                    (children_types[-2] not in ['hocaction', 'karelaction']):
                flag_block = False
                before_actions = []
                for b in range(max_blk_size):
                    n = type + 'action-' + str(action_counter)
                    before_actions.append(n)
                    action_counter += 1
                    child_n = AST(n, type=type)
                    new_children.insert(-1, child_n)
                block_before_after_nodes['before'].append(before_actions)
                # actions added after a block
                after_actions = []
                for b in range(max_blk_size):
                    n = type + 'action-' + str(action_counter)
                    after_actions.append(n)
                    action_counter += 1
                    child_n = AST(n, type=type)
                    new_children.insert(len(new_children) + 1, child_n)
                block_before_after_nodes['after'].append(after_actions)


            node.children = copy.deepcopy(new_children)
            # add additional actions before and after a block as well
            if flag_block == True:
                # actions added before a block
                before_actions = []
                for b in range(max_blk_size):
                    n = type + 'action-' + str(action_counter)
                    before_actions.append(n)
                    action_counter += 1
                    child_n = AST(n, type=type)
                    node.children.insert(append_counter[0], child_n)
                block_before_after_nodes['before'].append(before_actions)
                # actions added after a block
                after_actions = []
                for b in range(max_blk_size):
                    n = type + 'action-' + str(action_counter)
                    after_actions.append(n)
                    action_counter += 1
                    child_n = AST(n, type=type)
                    # node.children.insert(len(node.children)-b, child_n) # change the index of this to the last known action block index
                    node.children.insert(append_counter[-1]+new_middle_actions+max_blk_size+1+1, child_n)
                    # print([n.name_type for n in node.children])
                    # print(append_counter[-1]+new_middle_actions+max_blk_size+1+1)
                    # exit(0)
                    # node.children.insert(append_counter[-1]+new_middle_actions+1, child_n)
                block_before_after_nodes['after'].append(after_actions)



            for child in node.children:
                queue.append(child)


    return root, action_counter,  between_action_nodes, block_before_after_nodes


def insert_action_nodes_beginning_end(root:AST, current_action_counter:int, max_blk_size:int, type='hoc'):
    prefix_suffix_action_nodes = {'prefix': [], 'suffix':[]}
    action_counter = current_action_counter
    if root.name == "run":
        # action_nodes = []
        # adds action nodes in the beginning if there aren't action nodes already
        if root.children[0].name_type not in ['hocaction', 'karelaction']:
            for i in range(max_blk_size):
                n = type + "action-" + str(action_counter+i)
                node = AST(n, type=type)
                root.children.insert(i, node)
                prefix_suffix_action_nodes['prefix'].append(n)
            action_counter += max_blk_size

        # add nodes in the end
        if "repeatuntil" in root.children[-1].name: # do not append actions if repeat_until_goal is the last node
            return root, action_counter, prefix_suffix_action_nodes
        # add nodes in the end if there already isn't an action node there
        if root.children[-1].name_type not in ['hocaction', 'karelaction']:
            for i in range(max_blk_size):
                n = type + "action-" + str(action_counter+i)
                node = AST(n, type=type)
                root.children.append(node)
                prefix_suffix_action_nodes['suffix'].append(n)
            action_counter += max_blk_size
    else:
        return root, action_counter, prefix_suffix_action_nodes

    return root, action_counter, prefix_suffix_action_nodes

