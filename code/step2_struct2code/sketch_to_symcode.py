import json
import os
import enum
import copy
import collections
from step2_struct2code.sym_ast import AST, remove_null_nodes, valid_prog, add_if_else_node, convert_to_json
from utils.sketch import sketch_to_json, SketchNode


sketch_node_to_sym_node = {
    'run': 'run',
    'repeat': 'repeat',
    'while': 'while',
    'repeat_until_goal': 'repeatuntil',
    # 'if_only': 'conditional',
    # 'if_else': 'conditional',
    'do': 'conditional',
    'else': 'else'
}


class GenerateSymCode:
    def __init__(self, sketch:SketchNode, max_blk_size:int, type='hoc'):
        self._sketch = sketch
        self._type = type
        self._max_block_size = max_blk_size
        self.action_counter = 1
        self.if_conditional_counter = 1
        self.repeat_counter = 1
        self.repeat_until_counter = 1
        if self._type != 'hoc':
            self.while_conditional_counter = 1

        self._symcode = self.get_sym_code_from_sketch(self._sketch, self._max_block_size, self._type)

    def create_sym_node(self, name, children=None):
        if children is None:
            children = []
        symnode = AST(name, children, type=self._type)
        return symnode


    def get_sym_code_from_sketch(self, sketch:SketchNode, max_block_size:int, type:str):

        sym_node = AST('phi', type=self._type)
        do_flag = False
        if sketch.conditional() is not None:
            if sketch.conditional() == 'X': # repeat
                name = self._type + sketch_node_to_sym_node[sketch._type] + '-' + str(self.repeat_counter)
                self.repeat_counter += 1
                children_repeat = []
                name_act = self._type + 'action-'
                for i in range(self._max_block_size):
                    n = name_act + str(self.action_counter)
                    children_repeat.append(self.create_sym_node(n))
                    self.action_counter += 1
                sym_node = self.create_sym_node(name, children=children_repeat)
            else: # if, if_else, while, repeat_until
                do_flag = False
                if sketch._type == 'if_only' or sketch._type == 'if_else': # if, if_else
                    do_flag = True
                    sym_node = self.create_sym_node('phi', children=[])
                    sym_node.children.extend([self.get_sym_code_from_sketch(c, self._max_block_size, self._type) for c in
                                         sketch.children()])

                    return sym_node

                elif sketch._type == 'else': # else
                    name = 'else'
                elif sketch._type == 'repeat_until_goal': # while(bool_goal)
                    name = self._type + sketch_node_to_sym_node[sketch._type] + '-' + str(self.repeat_until_counter)
                    self.repeat_until_counter += 1
                elif sketch._type == 'do': # do nothing if 'do' node encountered
                    name = self._type + sketch_node_to_sym_node[sketch._type] + '-' + str(self.if_conditional_counter)
                    self.if_conditional_counter += 1
                else: # while, repeat_until_goal
                    name = self._type + sketch_node_to_sym_node[sketch._type] + '-' + str(self.while_conditional_counter)
                    self.while_conditional_counter += 1

                if not do_flag:
                    children_conditional = []
                    name_act = self._type + 'action-'
                    for i in range(self._max_block_size):
                        n = name_act + str(self.action_counter)
                        children_conditional.append(AST(n, type=self._type))
                        self.action_counter += 1
                    sym_node = self.create_sym_node(name, children=[])
                    sym_node.children.extend(children_conditional)



        else:
            sym_node = self.create_sym_node(sketch_node_to_sym_node[sketch._type], children=[])


        if len(sketch.children()) == 0:
            return sym_node

        else:
            if not do_flag:
                sym_node.children.extend([self.get_sym_code_from_sketch(c, self._max_block_size, self._type) for c in sketch.children()])


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


            # for child in node._children:
            #     if child._type == 'phi':
            #         node._children.remove(child)

            for child in node.children:
                queue.append(child)

    return root





def add_additional_actions(root:AST, init_count:int, max_blk_size:int, type='hoc'):
    # name_act = type + 'action_' + str(init_count)
    # if max_blk_size < 3:
    blk_size = 2 # fixed set of actions added before and after a block
    # else:
    #     blk_size = 1 # for actions in the beginning and the end
    cur_count = init_count
    common_name = type + 'action'
    if_name = type + 'conditional'
    queue = collections.deque([root])
    while len(queue):
        for i in range(len(queue)):
            add_count = 0
            node = queue.popleft()
            children = node.children
            children_copy = copy.deepcopy(node.children)
            # node.children = list(filter((AST('phi', [])).__ne__, node.children))
            children_names = [c.name.split('-')[0] for c in node.children]
            if all(x == common_name for x in children_names) and len(children) != 0:
                continue
            else:
                for i in range(len(children)-1):
                    if children_names[i] == common_name and children_names[i+1] == common_name:
                        continue
                    elif children_names[i] == common_name and children_names[i+1] != common_name:
                        continue
                    elif children_names[i] != common_name and children_names[i+1] == common_name:
                        continue
                    elif children_names[i] == if_name and children_names[i+1] == 'else':
                        continue
                    else:
                        for k in range(max_blk_size):
                            cur_count += 1
                            cname = common_name + '-' + str(cur_count)
                            children_copy.insert(i+1+max_blk_size*add_count, AST(cname, type=type))
                        add_count += 1
                        # all action children added

                node.children = children_copy

            ## adds actions in the beginning, end
            if node.name == 'run':
                if len(node.children) == 0: # no nodes in the sketch
                    for k in range(blk_size):
                        cname = common_name + '-' + str(cur_count)
                        node.children.append(AST(cname, type=type))
                        cur_count += 1
                    break

                else:
                    if node.children[0].name.split('-')[0] != common_name:
                        for k in range(blk_size):
                            cur_count += 1
                            cname = common_name + '-' + str(cur_count)
                            node.children.insert(k, AST(cname, type=type))

                    if node.children[-1].name.split('(')[0] != common_name:
                        if node.children[-1].name.split('-')[0] != 'hocrepeatuntil':
                            for k in range(blk_size):
                                cur_count += 1
                                cname = common_name + '-' + str(cur_count)
                                node.children.append(AST(cname, type=type))


            for child in node.children:
                queue.append(child)

    return root


