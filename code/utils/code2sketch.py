import enum
import json
import copy
import collections
from queue import Queue
from .ast import ASTNode as ASTNode
from .ast import json_to_ast as json_to_ast
from .definitions import SketchNodeType as SketchNodeType
from .definitions import node_str_to_sketch_type as node_str_to_sketch_type
from .sketch import SketchNode as SketchNode
from .definitions import node_type_to_sketch as node_type_to_sketch
from .sketch import sketch_to_json as sketch_to_json
from .sketch import json_to_sketch as json_to_sketch


MAX_POW = 17




P = 1000000007
M = 10 ** MAX_POW

def dsamepow10(num, max_pow=MAX_POW): # returns the max pow of 14 in num
    r = 1
    while num >= max_pow:
        num = int(num // max_pow)
        r *= max_pow
    return r


def join_ints(a, b, max_pow=MAX_POW):
    return a * dsamepow10(b) * max_pow + b


class GenerateSketch:

    def __init__(self, program:ASTNode, type='hoc'):
        self._program = program
        self._type = type
        self._raw_sketch = self.prune_raw_sketch(self.get_raw_sketch_from_program(program))
        self._sketch_without_A = self.remove_action_nodes(self.prune_raw_sketch(self.get_raw_sketch_from_program(program)))
        self._sketch = self.get_sketch_from_program(self._program)
        self._modified_sketch = self.get_modified_sketch(self._sketch)
        self._hash = get_hash_code_of_sketch(self._sketch_without_A) ## change the input to this function if the primary sketch of the class changes

    def create_sketch_node(self, node_type, conditional=None, children=[]):
        cfg_node = SketchNode(node_type, conditional, children)
        return cfg_node

    def get_raw_sketch_from_program(self, prog: ASTNode):

        if node_type_to_sketch[prog._type_enum] == 'A':
            if prog.conditional() is not None:
                if prog.conditional() in ['2', '3', '4', '5', '6', '7', '8', '9']:
                    cfg = self.create_sketch_node(node_type_to_sketch[prog._type_enum], 'X',  children=[])
                else:
                    cfg = self.create_sketch_node(node_type_to_sketch[prog._type_enum], 'bool_cond', children=[])
            else:
                cfg = self.create_sketch_node(node_type_to_sketch[prog._type_enum], None,  children=[])
        else:
            if prog.conditional() is not None:
                if prog.conditional() in ['2', '3', '4', '5', '6', '7', '8', '9']:
                    cfg = self.create_sketch_node(node_type_to_sketch[prog._type_enum], 'X', children=[])
                else:
                    cfg = self.create_sketch_node(node_type_to_sketch[prog._type_enum], 'bool_cond', children=[])
            else:
                cfg = self.create_sketch_node(node_type_to_sketch[prog._type_enum], None, children=[])
        if not prog.children():
            return cfg
        # elif prog._type_enum == NodeType.IF_ONLY:
        #     cfg._children = [get_cfg_from_program(c) for c in prog.children()[0].children()]
        #
        # elif prog._type_enum == NodeType.IF_ELSE:
        #     cfg._children = [get_cfg_from_program(c) for i in range(len(prog.children())) for c in prog.children()[i].children()]

        else:
            cfg._children = [self.get_raw_sketch_from_program(c) for c in prog.children()]

        return cfg

    def prune_raw_sketch(self, sketch: SketchNode):

        # merge A_BLOCK nodes
        queue = collections.deque([sketch])
        while len(queue):
            for i in range(len(queue)):
                node = queue.popleft()
                delete_indices = []
                for j in range(len(node._children) - 1):
                    if node._children[j]._type == 'A' \
                            and node._children[j + 1]._type == 'A':
                        delete_indices.append(j + 1)
                        # node._children[delete_indices[0] - 1]._alphabet['block'].append(
                        #     node._children[j +1]._alphabet['block'][0])

                if len(delete_indices) != 0:
                    for k in sorted(delete_indices, reverse=True):
                        #node = node.with_removed_child(i)
                        node._children.pop(k)

                for child in node._children:
                    queue.append(child)

        sketch._hash = get_hash_code_of_sketch(sketch)
        return sketch


    def remove_action_nodes(self, sketch: SketchNode):
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
                        #node = node.with_removed_child(k)
                        node._children.pop(k)
                        #print("Node", node)

                for child in node._children:
                    queue.append(child)
                #print("Queue:", queue)

        #print("Sketch:", sketch)
        sketch._hash = get_hash_code_of_sketch(sketch)
        sketch_json = sketch_to_json(sketch)
        sketch = json_to_sketch(sketch_json)
        return sketch


    def get_sketch_from_program(self, prog: ASTNode):

        cfg = self.get_raw_sketch_from_program(prog)
        pruned_cfg = self.prune_raw_sketch(cfg)


        return pruned_cfg

    ## adds node/prod-rule Y to the raw sketch
    def modify_sketch_tree_level_1(self, sketch: SketchNode):

        if sketch._type == 'run': ## add the sketch node Y as child of 'run'
            cfg = self.create_sketch_node('Y', None, children=[]) ## Create the empty sketch Y node
            cfg._children = sketch._children
            sketch._children = [cfg]
            # print(sketch)

        return sketch


    ## adds node/prod-rule S to the sketch tree
    def modify_sketch_tree_level_2(self, sketch: SketchNode):

        if sketch._type == 'if_else' or sketch._type == 'if_only'\
            or sketch._type == 'while' or sketch._type == 'repeat'\
                or sketch._type == 'A':
            cfg = self.create_sketch_node('S', None, children=[])
            cfg._children = [copy.deepcopy(sketch)]
            sketch = cfg
            sketch._parent = cfg

            if sketch.children()[0].children() == []:
                return sketch
            else:
                sketch._children[0]._children = [self.modify_sketch_tree_level_2(c) for c in
                                                 sketch.children()[0].children()]


        elif sketch.children() == []:
            return sketch

        else:
            sketch._children = [self.modify_sketch_tree_level_2(c) for c in sketch.children()]

        return sketch

    def contains(self, subseq, inseq):
        return any(inseq[pos:pos + len(subseq)] == subseq for pos in range(0, len(inseq) - len(subseq) + 1))

    ### combines the [S,S]/ [S;S, S] nodes to get the parent node S;S
    def modify_sketch_tree_level_3(self, sketch: SketchNode):


        # get the children of the node
        children = [c for c in sketch.children()]
        children_types = [c._type for c in children]

        while self.contains(['S', 'S'], children_types) and sketch._type!= 'if_else' and sketch._type != 'S;S'\
                and sketch._type != 'S;G':
            for i in range(len(children)-1):
                if children_types[i] == 'S' and children_types[i + 1] == 'S':
                    k1 = i
                    k2 = i+1
                    break
            cfg = self.create_sketch_node('S;S', None, [])
            cfg._children = [children[k1], children[k2]]
            children[k1]._parent = cfg
            children[k2]._parent = cfg
            children[k1] = cfg
            children_types[k1] = cfg._type
            del children_types[k2]
            del children[k2]
            sketch._children[k1] = cfg
            del sketch._children[k2]



        while self.contains(['S;S', 'S'], children_types) and sketch._type!= 'if_else' and sketch._type != 'S;S'\
                and sketch._type != 'S;G':
            for i in range(len(children)-1):
                if children_types[i] == 'S;S' and children_types[i + 1] == 'S':
                    k1 = i
                    k2 = i+1
                    break
            cfg = self.create_sketch_node('S;S', None, [])
            cfg._children = [children[k1], children[k2]]
            children[k1]._parent = cfg
            children[k2]._parent = cfg
            children[k1] = cfg
            children_types[k1] = cfg._type
            del children_types[k2]
            del children[k2]
            sketch._children[k1] = cfg
            del sketch._children[k2]


        while self.contains(['S', 'S;S'], children_types) and sketch._type!= 'if_else' and sketch._type != 'S;S' \
                and sketch._type != 'S;G':
            for i in range(len(children)-1):
                if children_types[i] == 'S' and children_types[i + 1] == 'S;S':
                    k1 = i
                    k2 = i + 1
                    break
            cfg = self.create_sketch_node('S;S', None, [])
            cfg._children = [children[k1], children[k2]]
            children[k1]._parent = cfg
            children[k2]._parent = cfg
            children[k1] = cfg
            children_types[k1] = cfg._type
            del children_types[k2]
            del children[k2]
            sketch._children[k1] = cfg
            del sketch._children[k2]

        while self.contains(['S;S', 'S;S'], children_types) and sketch._type!= 'if_else' and sketch._type != 'S;S' \
                and sketch._type != 'S;G':
            for i in range(len(children)-1):
                if children_types[i] == 'S;S' and children_types[i + 1] == 'S;S':
                    k1 = i
                    k2 = i + 1
                    break
            cfg = self.create_sketch_node('S;S', None, [])
            cfg._children = [children[k1], children[k2]]
            children[k1]._parent = cfg
            children[k2]._parent = cfg
            children[k1] = cfg
            children_types[k1] = cfg._type
            del children_types[k2]
            del children[k2]
            sketch._children[k1] = cfg
            del sketch._children[k2]



        if sketch.children() == []:
            return sketch

        else:
            sketch._children = [self.modify_sketch_tree_level_3(c) for c in sketch.children()]


        return sketch

    ### add parent node S for nodes S;S
    def modify_sketch_tree_level_4(self, sketch:SketchNode):
        if sketch._type == 'S;S':
            cfg = self.create_sketch_node('S', None, children=[])
            cfg._children = [copy.deepcopy(sketch)]
            sketch = cfg
            sketch._parent = cfg

            if sketch.children()[0].children() == []:
                return sketch
            else:
                sketch._children[0]._children = [self.modify_sketch_tree_level_4(c) for c in
                                                 sketch.children()[0].children()]


        elif sketch.children() == []:
            return sketch

        else:
            sketch._children = [self.modify_sketch_tree_level_4(c) for c in sketch.children()]

        return sketch


    ## combine nodes [S,G] with a common parent node S;G
    def modify_sketch_tree_level_5(self, sketch: SketchNode):

        # get the children of the node
        children = [c for c in sketch.children()]
        children_types = [c._type for c in children]

        while self.contains(['S', 'repeat_until_goal'], children_types) and sketch._type != 'if_else' and sketch._type != 'S;S'  \
                and sketch._type != 'S;G':
            for i in range(len(children) - 1):
                if children_types[i] == 'S' and children_types[i + 1] == 'repeat_until_goal':
                    k1 = i
                    k2 = i + 1
                    break
            cfg = self.create_sketch_node('S;G', None, [])
            cfg._children = [children[k1], children[k2]]
            children[k1]._parent = cfg
            children[k2]._parent = cfg
            children[k1] = cfg
            children_types[k1] = cfg._type
            del children_types[k2]
            del children[k2]
            sketch._children[k1] = cfg
            del sketch._children[k2]


        if sketch.children() == []:
            return sketch

        else:
            sketch._children = [self.modify_sketch_tree_level_5(c) for c in sketch.children()]


        return sketch





    def get_modified_sketch(self, sketch: SketchNode):
        modified_sketch_l1 = self.modify_sketch_tree_level_1(sketch)
        #print("After step 1:", modified_sketch_l1)
        modified_sketch_l2 = self.modify_sketch_tree_level_2(modified_sketch_l1)
        #print("After step 2:", modified_sketch_l2)
        modified_sketch_l3 = self.modify_sketch_tree_level_3(modified_sketch_l2)
        #print("After step 3:", modified_sketch_l3)
        modified_sketch_l4 = self.modify_sketch_tree_level_4(modified_sketch_l3)
        # print("After step 4:", modified_sketch_l4)
        modified_sketch_l5 = self.modify_sketch_tree_level_5(modified_sketch_l4)
        # print("After step 5:", modified_sketch_l5)
        return sketch



    def __repr__(self, offset=''):
        cs = offset + self._modified_sketch.label_print() + '\n'
        for child in self._modified_sketch.children():
            cs += offset + child.__repr__(offset + '   ')
        return cs


    def __hash__(self):
        return self._hash


    def __eq__(self, other):
      return self._hash == other._hash


## this routine computes the hash of a given sketch
def get_hash_code_of_sketch(sketch: SketchNode):
    hash = int(sketch._type_enum)
    if sketch._condition is not None:
        cond_enum = node_str_to_sketch_type[sketch._condition]
        hash = join_ints(cond_enum, hash, max_pow=MAX_POW)

    if sketch.children() == []:
        return hash

    for i,child in enumerate(sketch.children()):
        if child._type != 'phi':
            hash = join_ints(get_hash_code_of_sketch(child)*(i+1), hash, max_pow=MAX_POW)

    return hash

