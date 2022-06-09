import z3
import enum
import sys
import copy
import itertools

from code.step2_struct2code.smt_constraints_task5.utils_smt import VariableType, str_to_type, type_to_str,  gen_model, gen_all
from code.step2_struct2code.smt_constraints_task5.utils_ast_smt import ASTNode, remove_null_nodes


class Var:
    def __init__(self, name):
        self.name = name
        self.var = z3.Int(self.name)

class SMT_Block:
    def __init__(self, curr_block_dict: dict, thresh: int, id = 'hoc'):
        self.id = id
        self.curr_block = curr_block_dict # {'b1_1': 'move', 'b1_2': 'turn_left', ...}
        self.len_block = len(curr_block_dict)
        self.thresh = thresh # number of lines appended before/after the block
        self.block_z3_vars, self.block_prefix_z3_vars, \
        self.block_suffix_z3_vars, self.block_mid_z3_vars = self.append_additional_block_variables(self.curr_block)
        self.size = len(self.block_z3_vars)
        # values-constraints
        self.block_values, self.flip_turns_constraints, self.flip_marker_constraints = \
            self.get_block_values(self.block_z3_vars, self.curr_block, id = self.id)
        # append-constraints
        self.block_append_constraints = self.append_block_constraints(self.block_prefix_z3_vars, self.block_suffix_z3_vars, \
                                                                      self.block_mid_z3_vars,id = self.id)
        # elimination-constraints
        self.block_elimination_constraints = self.eliminate_seq_constraints(self.block_z3_vars, id = self.id)



    def append_additional_block_variables(self, block:dict):
        block_vars = {} # new block variables
        var_name = list(self.curr_block.keys())[0]
        all_var_names = list(self.curr_block.keys())

        # break the string at '_' :
        var_all = var_name.split('_')[0]
        var_prefix = var_all + "_a"
        var_suffix = var_all + "_p"
        var_mid = var_all + "_b"

        # adding all the block variables
        var_names = [var_prefix+str(i) for i in range(self.thresh)]
        prefix_z3_vars = [Var(ele) for ele in var_names]
        var_names_suffix = [var_suffix+str(i) for i in range(self.thresh)]
        suffix_z3_vars = [Var(ele) for ele in var_names_suffix]

        # added to add vars in between a block
        if len(all_var_names) >1:
            var_names_mid = [var_mid+str(i) for i in range(len(all_var_names)-1)]
            mid_z3_vars = [Var(ele) for ele in var_names_mid]
            j = 0
            for i in range(len(mid_z3_vars)):
                all_var_names.insert(j+i+1, var_names_mid[i])
                j = j+1
        else:
            mid_z3_vars = []

        #mid_z3_vars = []

        # this seq is important for future reference of variables. DO NOT CHANGE.
        var_names.extend(all_var_names)
        var_names.extend(var_names_suffix)


        all_z3_vars = [Var(ele) for ele in var_names]

        return all_z3_vars, prefix_z3_vars, suffix_z3_vars, mid_z3_vars


    def get_block_values(self, block_vars:dict, block:dict, id = 'hoc'):
        # get the values for the blocks
        values = []
        turn_vars = {}
        marker_vars = {}

        for ele in block_vars:
            key_val = ele.name
            # check the value in the block dict
            val = block.get(key_val, None)
            if val is None:
                if id == 'hoc':
                    values.append(z3.Or(ele.var == 1, ele.var == 2, ele.var == 3, ele.var == 6))
                else:
                    values.append(
                        z3.Or(ele.var == 1, ele.var == 2, ele.var == 3, ele.var == 4, ele.var == 5, ele.var == 6))
            elif val == 'phi':
                values.append(ele.var == 6)
            elif val == 'move':
                values.append(ele.var == 1)
            elif val == 'turn_left' or val == 'turn_right':
                values.append(z3.Or(ele.var ==2, ele.var == 3))
                if val == 'turn_left':
                    turn_vars[ele] = 2
                else:
                    turn_vars[ele] = 3
            elif val == 'pick_marker' or val == 'put_marker':
                values.append(z3.Or(ele.var == 4, ele.var == 5))
                if val == 'put_marker':
                    marker_vars[ele] = 5
                else:
                    marker_vars[ele] = 4


        turn_vars_keys = list(turn_vars.keys())
        turn_vars_og = list(turn_vars.values())

        turn_vars_flip = []
        if len(turn_vars) != 0:
            for ele in turn_vars_og:
                if ele == 2:
                    turn_vars_flip.append(3)
                elif ele == 3:
                    turn_vars_flip.append(2)

            flip_turns_constraints = [z3.And([
                turn_vars_keys[i].var == 2                  # all left
            for i in range(len(turn_vars))] ) ]

            flip_turns_constraints.extend([z3.And([
                turn_vars_keys[i].var == 3                  # all right
            for i in range(len(turn_vars))] )])

            flip_turns_constraints.extend([z3.And([
                turn_vars_keys[i].var == turn_vars_og[i]     # original values
                for i in range(len(turn_vars))])])

            flip_turns_constraints.extend([z3.And([
                turn_vars_keys[i].var == turn_vars_flip[i]  # flipped values
                for i in range(len(turn_vars))])])


            flip_turns_all_cons = [z3.Or([ele for ele in flip_turns_constraints])]

        else:
            flip_turns_all_cons = []


        if id == 'karel':
            marker_vars_keys = list(marker_vars.keys())
            marker_vars_og = list(marker_vars.values())

            marker_vars_flip = []
            if len(marker_vars_keys) != 0:
                for ele in marker_vars_og:
                    if ele == 4:
                        marker_vars_flip.append(5)
                    elif ele == 5:
                        marker_vars_flip.append(4)

                flip_marker_constraints = [z3.And([
                    marker_vars_keys[i].var == 4              # all pick_marker
                    for i in range(len(marker_vars))])]

                flip_marker_constraints.extend([z3.And([
                    marker_vars_keys[i].var == 5              # all put marker
                    for i in range(len(marker_vars))])])

                flip_marker_constraints.extend([z3.And([
                    marker_vars_keys[i].var == marker_vars_og[i]  # original values
                    for i in range(len(marker_vars))])])

                flip_marker_constraints.extend([z3.And([
                    marker_vars_keys[i].var == marker_vars_flip[i]  # flipped values
                    for i in range(len(marker_vars))])])

                flip_marker_all_cons = [z3.Or([ele for ele in flip_marker_constraints])]
            else:
                flip_marker_all_cons = []


        else:
            flip_marker_all_cons = None

        return values, flip_turns_all_cons, flip_marker_all_cons

    # this is the routine that needs to be altered in case further actions need to be appended
    def get_all_vals(self, vals:list):

         all_vals = [p for p in itertools.product(vals, repeat = self.thresh)]
         return all_vals



    def append_block_constraints(self, prefix_vars:list, suffix_vars:list, mid_vars:list,id = 'hoc'):

        constraints = []
        # values pairs allowed: if thresh == 3, for other thresholds this needs to be changed
        if id == 'hoc':
            action_ids = self.get_all_vals(vals = [1,2,3,6])
        else:
            action_ids = self.get_all_vals(vals=[1, 2, 3, 4, 5, 6])


        prefix_constraints = [z3.Or([z3.And([prefix_vars[i].var == ele[i] for i in range(self.thresh)]) for ele in action_ids])]
        suffix_constraints = [z3.Or([z3.And([suffix_vars[i].var == ele[i] for i in range(self.thresh)]) for ele in action_ids])]


        # ensure that the actions are appended either only before or only after
        # not_equal constraints
        prefix_cons = [[prefix_vars[i].var != 6 for i in range(self.thresh)
                        #if i !=j
                        ]
                       for j in range(self.thresh)]
        for j in range(self.thresh):
            prefix_cons[j].append(prefix_vars[j].var != 6)

        suffix_cons = [[suffix_vars[i].var != 6 for i in range(self.thresh)
                        #if i != j
                        ] for j in range(self.thresh)]
        for j in range(self.thresh):
            suffix_cons[j].append(suffix_vars[j].var != 6)

        mid_cons = [[mid_vars[i].var != 6 for i in range(len(mid_vars))
                        # if i != j
                        ] for j in range(len(mid_vars))]
        for j in range(len(mid_vars)):
            mid_cons[j].append(mid_vars[j].var != 6)

        suff_mid = mid_vars + suffix_vars
        pre_mid = mid_vars + prefix_vars
        pre_suff = prefix_vars + suffix_vars

        append_constraints_prefix = [z3.Implies(
                                    z3.Or(ele),
                                    z3.And([suff_mid[k].var == 6 for k in range(len(suff_mid))])
                                        )
                              for ele in prefix_cons ]

        append_constraints_suffix = [z3.Implies(
                                    z3.Or(ele),
                                    z3.And([pre_mid[k].var == 6 for k in range(len(pre_mid))])
                                        )
                              for ele in suffix_cons ]

        append_constraints_mid = [z3.Implies(
            z3.Or(ele),
            z3.And([pre_suff[k].var == 6 for k in range(len(pre_suff))])
        )
            for ele in mid_cons]

        # add the constraint that only one element of the mid-vars can be changed at a time
        mid_indices = []
        for i in range(len(mid_vars)):
            ind = [i]
            rem = []
            for j in range(len(mid_vars)):
                if j != i:
                    rem.append(j)
            ind.append(rem)
            mid_indices.append(ind)

        append_single_mid_cons = []
        for i in range(len(mid_indices)):
            id_1 = mid_indices[i][0]
            other_ids = mid_indices[i][1]
            append_single_mid_cons.append(z3.Implies(mid_vars[id_1].var != 6, z3.And([mid_vars[j].var == 6 for j in other_ids])))


        constraints.extend(prefix_constraints)
        constraints.extend(suffix_constraints)

        constraints.extend(append_constraints_prefix)
        constraints.extend(append_constraints_suffix)
        constraints.extend(append_constraints_mid)
        constraints.extend(append_single_mid_cons)


        return constraints

    def eliminate_seq_constraints(self, block_vars: list, id = 'hoc'):

        left_right_constraints = [z3.Not(z3.And([block_vars[i].var == 2, block_vars[i+1].var == 3 ])) for i in range(len(block_vars)-1)]
        right_left_constraints = [z3.Not(z3.And([block_vars[i].var == 3, block_vars[i+1].var == 2 ])) for i in range(len(block_vars)-1)]

        all_left_constraints = [z3.Not(z3.And([block_vars[i].var == 2, block_vars[i+1].var == 2, block_vars[i+2].var ==2 ]))
                                       for i in range(len(block_vars)-2)]
                                # turn_left, turn_left, turn_left
        all_right_constraints = [z3.Not(z3.And([block_vars[i].var == 3, block_vars[i+1].var == 3, block_vars[i+2].var == 3 ]))
                                       for i in range(len(block_vars)-2)]
                                # turn_right, turn_right, turn_right

        left_phi_right_constraints = [z3.Not(z3.And([block_vars[i].var == 2, block_vars[i+1].var == 6, block_vars[i+2].var ==3 ]))
                                       for i in range(len(block_vars)-2)]
                                # turn_left, phi, turn_right
        right_phi_left_constraints = [z3.Not(z3.And([block_vars[i].var == 3, block_vars[i+1].var == 6, block_vars[i+2].var == 2 ]))
                                       for i in range(len(block_vars)-2)]
                                # turn_right, phi, turn_left

        left_phi_phi_right_constraints = [
            z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 6, block_vars[i + 2].var == 6,block_vars[i + 3].var == 3]))
            for i in range(len(block_vars) - 3)]
        # turn_left, phi, phi, turn_right
        right_phi_phi_left_constraints = [
            z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 6, block_vars[i + 2].var == 6, block_vars[i + 3].var == 2]))
            for i in range(len(block_vars) - 3)]
        # turn_right, phi, phi, turn_left


        left_phi_left_left_constraints = [z3.Not(z3.And([block_vars[i].var == 2, block_vars[i+1].var == 6,
                                                     block_vars[i+2].var == 2, block_vars[i+3].var == 2 ]))
                                       for i in range(len(block_vars)-3)]

        left_phi_phi_left_left_constraints = [z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 6,
                                                         block_vars[i + 2].var == 6, block_vars[i + 3].var == 2, block_vars[i + 4].var == 2]))
                                          for i in range(len(block_vars) - 4)]


        left_left_phi_left_constraints = [z3.Not(z3.And([block_vars[i].var == 2, block_vars[i+1].var == 2,
                                                     block_vars[i+2].var == 6, block_vars[i+3].var == 2 ]))
                                       for i in range(len(block_vars)-3)]

        left_left_phi_phi_left_constraints = [z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 2,
                                                         block_vars[i + 2].var == 6, block_vars[i + 3].var == 6, block_vars[i + 4].var == 2]))
                                          for i in range(len(block_vars) - 4)]

        left_phi_left_phi_left_constraints = [z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 6,
                                                             block_vars[i + 2].var == 2, block_vars[i + 3].var == 6,
                                                             block_vars[i + 4].var == 2]))
                                              for i in range(len(block_vars) - 4)]



        right_phi_right_right_constraints = [z3.Not(z3.And([block_vars[i].var == 3, block_vars[i+1].var == 6,
                                                     block_vars[i+2].var == 3, block_vars[i+3].var == 3 ]))
                                       for i in range(len(block_vars)-3)]

        right_phi_phi_right_right_constraints = [z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 6,
                                                            block_vars[i + 2].var == 6, block_vars[i + 3].var == 3, block_vars[i + 4].var == 3]))
                                             for i in range(len(block_vars) - 4)]

        right_phi_right_phi_right_constraints = [z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 6,
                                                                block_vars[i + 2].var == 3, block_vars[i + 3].var == 6,
                                                                block_vars[i + 4].var == 3]))
                                                 for i in range(len(block_vars) - 4)]



        right_right_phi_right_constraints = [z3.Not(z3.And([block_vars[i].var == 3, block_vars[i+1].var == 3,
                                                     block_vars[i+2].var == 6, block_vars[i+3].var == 3 ]))
                                       for i in range(len(block_vars)-3)]

        right_right_phi_phi_right_constraints = [z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 3,
                                                            block_vars[i + 2].var == 6, block_vars[i + 3].var == 6, block_vars[i + 4].var == 3]))
                                             for i in range(len(block_vars) - 4)]



        # if the id == karel, add additional seq to eliminate
        if id == 'karel':
            pick_put_constraints =  [z3.Not(z3.And([block_vars[i].var == 4, block_vars[i+1].var == 5 ])) for i in range(len(block_vars)-1)]
            put_pick_constraints = [z3.Not(z3.And([block_vars[i].var == 5, block_vars[i+1].var == 4 ])) for i in range(len(block_vars)-1)]

            pick_pick = [z3.Not(z3.And([block_vars[i].var == 4, block_vars[i+1].var == 4 ])) for i in range(len(block_vars)-1)]
            put_put = [z3.Not(z3.And([block_vars[i].var == 5, block_vars[i+1].var == 5 ])) for i in range(len(block_vars)-1)]

            pick_phi_put = [z3.Not(z3.And([block_vars[i].var == 4, block_vars[i+1].var == 6, block_vars[i+2].var ==5 ]))
                                       for i in range(len(block_vars)-2)]
            put_phi_phi_pick = [z3.Not(z3.And([block_vars[i].var == 5, block_vars[i+1].var == 6,
                                               block_vars[i+2].var == 6,  block_vars[i+3].var == 4]))
                                       for i in range(len(block_vars)-3)]

            pick_phi_phi_put = [
                z3.Not(z3.And([block_vars[i].var == 4, block_vars[i + 1].var == 6, block_vars[i + 2].var == 6, block_vars[i + 3].var == 5]))
                for i in range(len(block_vars) - 3)]

            put_phi_pick = [
                z3.Not(z3.And([block_vars[i].var == 5, block_vars[i + 1].var == 6, block_vars[i + 2].var == 4]))
                for i in range(len(block_vars) - 2)]

            pick_phi_pick = [
                z3.Not(z3.And([block_vars[i].var == 4, block_vars[i + 1].var == 6, block_vars[i + 2].var == 4]))
                for i in range(len(block_vars) - 2)]

            pick_phi_phi_pick = [
                z3.Not(z3.And([block_vars[i].var == 4, block_vars[i + 1].var == 6, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 4]))
                for i in range(len(block_vars) - 3)]


            put_phi_put = [
                z3.Not(z3.And([block_vars[i].var == 5, block_vars[i + 1].var == 6, block_vars[i + 2].var == 5]))
                for i in range(len(block_vars) - 2)]

            put_phi_phi_put = [
                z3.Not(z3.And([block_vars[i].var == 5, block_vars[i + 1].var == 6, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 5]))
                for i in range(len(block_vars) - 3)]


            # additional constraints which are a combination of turn_left/turn_right and pick_marker/put_marker

            left_put_right = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 5, block_vars[i + 2].var == 3]))
                for i in range(len(block_vars) - 2)]
            left_phi_put_right = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 6, block_vars[i + 2].var == 5,
                               block_vars[i + 3].var == 3]))
                for i in range(len(block_vars) - 3)]

            left_phi_phi_put_right = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 6, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 5,
                               block_vars[i + 4].var == 3]))
                for i in range(len(block_vars) - 4)]


            left_put_phi_right = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 5, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 3]))
                for i in range(len(block_vars) - 3)]

            left_put_phi_phi_right = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 5, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 3]))
                for i in range(len(block_vars) - 4)]

            left_phi_put_phi_right = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 6, block_vars[i + 2].var == 5,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 3]))
                for i in range(len(block_vars) - 4)]

            left_phi_put_phi_phi_right = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 6, block_vars[i + 2].var == 5,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 6, block_vars[i + 5].var == 3]))
                for i in range(len(block_vars) - 5)
            ]

            left_phi_phi_put_phi_right = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 6, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 5,
                               block_vars[i + 4].var == 6, block_vars[i + 5].var == 3]))
                for i in range(len(block_vars) - 5)
            ]

            left_pick_right = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 4, block_vars[i + 2].var == 3]))
                for i in range(len(block_vars) - 2)]

            left_phi_pick_right = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 6, block_vars[i + 2].var == 4,
                               block_vars[i + 3].var == 3]))
                for i in range(len(block_vars) - 3)]

            left_phi_phi_pick_right = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 6,
                               block_vars[i + 2].var == 6, block_vars[i + 3].var == 4,
                               block_vars[i + 4].var == 3]))
                for i in range(len(block_vars) - 4)]


            left_pick_phi_right = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 4, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 3]))
                for i in range(len(block_vars) - 3)]

            left_pick_phi_phi_right = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 4,
                               block_vars[i + 2].var == 6, block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 3]))
                for i in range(len(block_vars) - 4)]

            left_phi_pick_phi_right = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 6,
                               block_vars[i + 2].var == 4, block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 3]))
                for i in range(len(block_vars) - 4)
            ]

            left_phi_phi_pick_phi_right = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 6,
                               block_vars[i + 2].var == 6, block_vars[i + 3].var == 4,
                               block_vars[i + 4].var == 6, block_vars[i + 5].var == 3]))
                for i in range(len(block_vars) - 5)
            ]

            left_phi_pick_phi_phi_right = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 6,
                               block_vars[i + 2].var == 4, block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 6, block_vars[i + 5].var == 3]))
                for i in range(len(block_vars) - 5)
            ]


            right_put_left = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 5, block_vars[i + 2].var == 2]))
                for i in range(len(block_vars) - 2)]

            right_phi_put_left = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 6, block_vars[i + 2].var == 5,
                               block_vars[i + 3].var == 2]))
                for i in range(len(block_vars) - 3)]

            right_phi_phi_put_left = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 6,
                               block_vars[i + 1].var == 6, block_vars[i + 3].var == 5,
                               block_vars[i + 4].var == 2]))
                for i in range(len(block_vars) - 4)]



            right_put_phi_left = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 5, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 2]))
                for i in range(len(block_vars) - 3)]

            right_put_phi_phi_left = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 5,
                               block_vars[i + 2].var == 6, block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 2]))
                for i in range(len(block_vars) - 4)]

            right_phi_put_phi_left = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 6,
                               block_vars[i + 2].var == 5, block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 2]))
                for i in range(len(block_vars) - 4)
            ]

            right_phi_phi_put_phi_left = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 6,
                               block_vars[i + 2].var == 6, block_vars[i + 3].var == 5,
                               block_vars[i + 4].var == 6, block_vars[i + 5].var == 2]))
                for i in range(len(block_vars) - 5)
            ]

            right_phi_put_phi_phi_left = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 6,
                               block_vars[i + 2].var == 5, block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 6, block_vars[i + 5].var == 2]))
                for i in range(len(block_vars) - 5)
            ]


            right_pick_left = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 4, block_vars[i + 2].var == 2]))
                for i in range(len(block_vars) - 2)]

            right_phi_pick_left = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 6, block_vars[i + 2].var == 4,
                               block_vars[i + 3].var == 2]))
                for i in range(len(block_vars) - 3)]

            right_phi_phi_pick_left = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 6, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 4,
                               block_vars[i + 4].var == 2]))
                for i in range(len(block_vars) - 4)]


            right_pick_phi_left = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 4, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 2]))
                for i in range(len(block_vars) - 3)]

            right_pick_phi_phi_left = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 4, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 2]))
                for i in range(len(block_vars) - 4)]

            right_phi_pick_phi_left = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 6, block_vars[i + 2].var == 4,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 2]))
                for i in range(len(block_vars) - 4)]

            right_phi_phi_pick_phi_left = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 6, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 4,
                               block_vars[i + 4].var == 6, block_vars[i + 5].var == 2]))
                for i in range(len(block_vars) - 5)]

            right_phi_pick_phi_phi_left = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 6, block_vars[i + 2].var == 4,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 6, block_vars[i + 5].var == 2]))
                for i in range(len(block_vars) - 5)]

            pick_left_put = [
                z3.Not(z3.And([block_vars[i].var == 4, block_vars[i + 1].var == 2, block_vars[i + 2].var == 5]))
                for i in range(len(block_vars) - 2)]


            pick_phi_left_put = [
                z3.Not(z3.And([block_vars[i].var == 4, block_vars[i + 1].var == 6, block_vars[i + 2].var == 2,
                               block_vars[i + 3].var == 5]))
                for i in range(len(block_vars) - 3)]

            pick_phi_phi_left_put = [
                z3.Not(z3.And([block_vars[i].var == 4, block_vars[i + 1].var == 6, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 2,
                               block_vars[i + 4].var == 5]))
                for i in range(len(block_vars) - 4)]



            pick_left_phi_put = [
                z3.Not(z3.And([block_vars[i].var == 4, block_vars[i + 1].var == 2, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 5]))
                for i in range(len(block_vars) - 3)]

            pick_left_phi_phi_put = [
                z3.Not(z3.And([block_vars[i].var == 4, block_vars[i + 1].var == 2, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 5]))
                for i in range(len(block_vars) - 4)]

            pick_phi_left_phi_put = [
                z3.Not(z3.And([block_vars[i].var == 4, block_vars[i + 1].var == 6, block_vars[i + 2].var == 2,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 5]))
                for i in range(len(block_vars) - 4)
            ]

            pick_phi_phi_left_phi_put = [
                z3.Not(z3.And([block_vars[i].var == 4, block_vars[i + 1].var == 6,
                               block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 2,
                               block_vars[i + 4].var == 6, block_vars[i + 5].var == 5]))
                for i in range(len(block_vars) - 5)
            ]

            pick_phi_left_phi_phi_put = [
                z3.Not(z3.And([block_vars[i].var == 4, block_vars[i + 1].var == 6,
                               block_vars[i + 2].var == 2,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 6, block_vars[i + 5].var == 5]))
                for i in range(len(block_vars) - 5)
            ]

            pick_right_put = [
                z3.Not(z3.And([block_vars[i].var == 4, block_vars[i + 1].var == 3, block_vars[i + 2].var == 5]))
                for i in range(len(block_vars) - 2)]

            pick_phi_right_put = [
                z3.Not(z3.And([block_vars[i].var == 4, block_vars[i + 1].var == 6, block_vars[i + 2].var == 3,
                               block_vars[i + 3].var == 5]))
                for i in range(len(block_vars) - 3)]

            pick_phi_phi_right_put = [
                z3.Not(z3.And([block_vars[i].var == 4, block_vars[i + 1].var == 6, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 3,
                               block_vars[i + 4].var == 5]))
                for i in range(len(block_vars) - 4)]

            pick_phi_right_phi_put = [
                z3.Not(z3.And([block_vars[i].var == 4, block_vars[i + 1].var == 6, block_vars[i + 2].var == 3,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 5]))
                for i in range(len(block_vars) - 4)
            ]

            pick_phi_phi_right_phi_put = [
                z3.Not(z3.And([block_vars[i].var == 4, block_vars[i + 1].var == 6, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 3,
                               block_vars[i + 4].var == 6, block_vars[i + 5].var == 5]))
                for i in range(len(block_vars) - 5)
            ]

            pick_phi_right_phi_phi_put = [
                z3.Not(z3.And([block_vars[i].var == 4, block_vars[i + 1].var == 6, block_vars[i + 2].var == 3,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 6, block_vars[i + 5].var == 5]))
                for i in range(len(block_vars) - 5)
            ]


            pick_right_phi_put = [
                z3.Not(z3.And([block_vars[i].var == 4, block_vars[i + 1].var == 3, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 5]))
                for i in range(len(block_vars) - 3)]

            pick_right_pi_phi_put = [
                z3.Not(z3.And([block_vars[i].var == 4, block_vars[i + 1].var == 3, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 5]))
                for i in range(len(block_vars) - 4)]

            put_right_pick = [
                z3.Not(z3.And([block_vars[i].var == 5, block_vars[i + 1].var == 3, block_vars[i + 2].var == 4]))
                for i in range(len(block_vars) - 2)]

            put_phi_right_pick = [
                z3.Not(z3.And([block_vars[i].var == 5, block_vars[i + 1].var == 6, block_vars[i + 2].var == 3,
                               block_vars[i + 3].var == 4]))
                for i in range(len(block_vars) - 3)]

            put_phi_phi_right_pick = [
                z3.Not(z3.And([block_vars[i].var == 5, block_vars[i + 1].var == 6, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 3,
                               block_vars[i + 4].var == 4]))
                for i in range(len(block_vars) - 4)]



            put_right_phi_pick = [
                z3.Not(z3.And([block_vars[i].var == 5, block_vars[i + 1].var == 3, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 4]))
                for i in range(len(block_vars) - 3)]

            put_right_phi_phi_pick = [
                z3.Not(z3.And([block_vars[i].var == 5, block_vars[i + 1].var == 3, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 4]))
                for i in range(len(block_vars) - 4)]

            put_phi_right_phi_pick = [
                z3.Not(z3.And([block_vars[i].var == 5, block_vars[i + 1].var == 6, block_vars[i + 2].var == 3,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 4]))
                for i in range(len(block_vars) - 4)]

            put_phi_phi_right_phi_pick = [
                z3.Not(z3.And([block_vars[i].var == 5, block_vars[i + 1].var == 6,
                               block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 3,
                               block_vars[i + 4].var == 6, block_vars[i + 5].var == 4]))
                for i in range(len(block_vars) - 5)
            ]

            put_phi_right_phi_phi_pick = [
                z3.Not(z3.And([block_vars[i].var == 5, block_vars[i + 1].var == 6,
                               block_vars[i + 2].var == 3,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 6, block_vars[i + 5].var == 4]))
                for i in range(len(block_vars) - 5)
            ]




            put_left_pick = [
                z3.Not(z3.And([block_vars[i].var == 4, block_vars[i + 1].var == 3, block_vars[i + 2].var == 5]))
                for i in range(len(block_vars) - 2)]

            put_phi_left_pick = [
                z3.Not(z3.And([block_vars[i].var == 5, block_vars[i + 1].var == 6, block_vars[i + 2].var == 2,
                               block_vars[i + 3].var == 4]))
                for i in range(len(block_vars) - 3)]

            put_phi_phi_left_pick = [
                z3.Not(z3.And([block_vars[i].var == 5, block_vars[i + 1].var == 6, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 2,
                               block_vars[i + 4].var == 4]))
                for i in range(len(block_vars) - 4)]

            put_left_phi_pick = [
                z3.Not(z3.And([block_vars[i].var == 5, block_vars[i + 1].var == 2, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 4]))
                for i in range(len(block_vars) - 3)]

            put_left_phi_phi_pick = [
                z3.Not(z3.And([block_vars[i].var == 5, block_vars[i + 1].var == 2, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 4]))
                for i in range(len(block_vars) - 4)]

            put_phi_left_phi_pick = [
                z3.Not(z3.And([block_vars[i].var == 5, block_vars[i + 1].var == 6, block_vars[i + 2].var == 2,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 4]))
                for i in range(len(block_vars) - 4)
            ]

            put_phi_phi_left_phi_pick = [
                z3.Not(z3.And([block_vars[i].var == 5, block_vars[i + 1].var == 6,
                               block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 2,
                               block_vars[i + 4].var == 6, block_vars[i + 5].var == 4]))
                for i in range(len(block_vars) - 5)
            ]

            put_phi_left_phi_phi_pick = [
                z3.Not(z3.And([block_vars[i].var == 5, block_vars[i + 1].var == 6,
                               block_vars[i + 2].var == 2,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 6, block_vars[i + 5].var == 4]))
                for i in range(len(block_vars) - 5)
            ]


            put_left_put = [
                z3.Not(z3.And([block_vars[i].var == 4, block_vars[i + 1].var == 2, block_vars[i + 2].var == 4]))
                for i in range(len(block_vars) - 2)]

            put_phi_left_put = [
                z3.Not(z3.And([block_vars[i].var == 5, block_vars[i + 1].var == 6, block_vars[i + 2].var == 2,
                               block_vars[i + 3].var == 5]))
                for i in range(len(block_vars) - 3)]

            put_phi_phi_left_put = [
                z3.Not(z3.And([block_vars[i].var == 5, block_vars[i + 1].var == 6, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 2,
                               block_vars[i + 4].var == 5]))
                for i in range(len(block_vars) - 4)]



            put_left_phi_put = [
                z3.Not(z3.And([block_vars[i].var == 5, block_vars[i + 1].var == 2, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 5]))
                for i in range(len(block_vars) - 3)]

            put_left_phi_phi_put = [
                z3.Not(z3.And([block_vars[i].var == 5, block_vars[i + 1].var == 2, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 5]))
                for i in range(len(block_vars) - 4)]
            put_phi_left_phi_put = [
                z3.Not(z3.And([block_vars[i].var == 5, block_vars[i + 1].var == 6, block_vars[i + 2].var == 2,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 5]))
                for i in range(len(block_vars) - 4)]

            put_phi_phi_left_phi_put = [
                z3.Not(z3.And([block_vars[i].var == 5, block_vars[i + 1].var == 6,
                               block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 2,
                               block_vars[i + 4].var == 6, block_vars[i + 4].var == 5]))
                for i in range(len(block_vars) - 5)
            ]

            put_phi_left_phi_phi_put = [
                z3.Not(z3.And([block_vars[i].var == 5, block_vars[i + 1].var == 6,
                               block_vars[i + 2].var == 2,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 6, block_vars[i + 4].var == 5]))
                for i in range(len(block_vars) - 5)
            ]


            put_right_put = [
                z3.Not(z3.And([block_vars[i].var == 4, block_vars[i + 1].var == 3, block_vars[i + 2].var == 4]))
                for i in range(len(block_vars) - 2)]

            put_phi_right_put = [
                z3.Not(z3.And([block_vars[i].var == 5, block_vars[i + 1].var == 6, block_vars[i + 2].var == 3,
                               block_vars[i + 3].var == 5]))
                for i in range(len(block_vars) - 3)]

            put_phi_phi_right_put = [
                z3.Not(z3.And([block_vars[i].var == 5, block_vars[i + 1].var == 6, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 3,
                               block_vars[i + 4].var == 5]))
                for i in range(len(block_vars) - 4)]


            put_right_phi_put = [
                z3.Not(z3.And([block_vars[i].var == 5, block_vars[i + 1].var == 3, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 5]))
                for i in range(len(block_vars) - 3)]

            put_right_phi_phi_put = [
                z3.Not(z3.And([block_vars[i].var == 5, block_vars[i + 1].var == 3, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 5]))
                for i in range(len(block_vars) - 4)]

            put_phi_right_phi_put = [
                z3.Not(z3.And([block_vars[i].var == 5, block_vars[i + 1].var == 6, block_vars[i + 2].var == 3,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 5]))
                for i in range(len(block_vars) - 4)

            ]

            put_phi_phi_right_phi_put = [
                z3.Not(z3.And([block_vars[i].var == 5, block_vars[i + 1].var == 6,
                               block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 3,
                               block_vars[i + 4].var == 6, block_vars[i + 5].var == 5]))
                for i in range(len(block_vars) - 5)
            ]

            put_phi_right_phi_phi_put = [
                z3.Not(z3.And([block_vars[i].var == 5, block_vars[i + 1].var == 6,
                               block_vars[i + 2].var == 3,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 6, block_vars[i + 5].var == 5]))
                for i in range(len(block_vars) - 5)
            ]


            pick_left_pick =  [
                z3.Not(z3.And([block_vars[i].var == 5, block_vars[i + 1].var == 2, block_vars[i + 2].var == 5]))
                for i in range(len(block_vars) - 2)]

            pick_phi_left_pick = [
                z3.Not(z3.And([block_vars[i].var == 4, block_vars[i + 1].var == 6, block_vars[i + 2].var == 2,
                               block_vars[i + 3].var == 4]))
                for i in range(len(block_vars) - 3)]

            pick_phi_phi_left_pick = [
                z3.Not(z3.And([block_vars[i].var == 4, block_vars[i + 1].var == 6, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 2,
                               block_vars[i + 4].var == 4]))
                for i in range(len(block_vars) - 4)]



            pick_left_phi_pick = [
                z3.Not(z3.And([block_vars[i].var == 4, block_vars[i + 1].var == 2, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 4]))
                for i in range(len(block_vars) - 3)]

            pick_left_phi_phi_pick = [
                z3.Not(z3.And([block_vars[i].var == 4, block_vars[i + 1].var == 2, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 4]))
                for i in range(len(block_vars) - 4)]

            pick_left_phi_phi_pick = [
                z3.Not(z3.And([block_vars[i].var == 4, block_vars[i + 1].var == 2, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 4]))
                for i in range(len(block_vars) - 4)]

            pick_right_pick = [
                z3.Not(z3.And([block_vars[i].var == 5, block_vars[i + 1].var == 3, block_vars[i + 2].var == 5]))
                for i in range(len(block_vars) - 2)]

            pick_phi_right_pick = [
                z3.Not(z3.And([block_vars[i].var == 4, block_vars[i + 1].var == 6, block_vars[i + 2].var == 3,
                               block_vars[i + 3].var == 4]))
                for i in range(len(block_vars) - 3)]

            pick_phi_phi_right_pick = [
                z3.Not(z3.And([block_vars[i].var == 4, block_vars[i + 1].var == 6, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 3,
                               block_vars[i + 4].var == 4]))
                for i in range(len(block_vars) - 4)]


            pick_right_phi_pick = [
                z3.Not(z3.And([block_vars[i].var == 4, block_vars[i + 1].var == 3, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 4]))
                for i in range(len(block_vars) - 3)]

            pick_right_phi_phi_pick = [
                z3.Not(z3.And([block_vars[i].var == 4, block_vars[i + 1].var == 3, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 4]))
                for i in range(len(block_vars) - 4)]

            pick_right_phi_phi_pick = [
                z3.Not(z3.And([block_vars[i].var == 4, block_vars[i + 1].var == 3, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 4]))
                for i in range(len(block_vars) - 4)]

            pick_phi_right_phi_pick  = [
                z3.Not(z3.And([block_vars[i].var == 4, block_vars[i + 1].var == 6, block_vars[i + 2].var == 3,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 4]))
                for i in range(len(block_vars) - 4)
            ]

            pick_phi_phi_right_phi_pick = [
                z3.Not(z3.And([block_vars[i].var == 4, block_vars[i + 1].var == 6,
                               block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 3,
                               block_vars[i + 4].var == 6, block_vars[i + 5].var == 4]))
                for i in range(len(block_vars) - 5)
            ]

            pick_phi_right_phi_phi_pick = [
                z3.Not(z3.And([block_vars[i].var == 4, block_vars[i + 1].var == 6,
                               block_vars[i + 2].var == 3,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 6, block_vars[i + 5].var == 4]))
                for i in range(len(block_vars) - 5)
            ]


            right_pick_right_right = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 4, block_vars[i + 2].var == 3,
                               block_vars[i + 3].var == 3]))
                for i in range(len(block_vars) - 3)]

            right_pick_phi_right_right = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 4, block_vars[i + 2].var == 6, block_vars[i + 3].var == 3,
                               block_vars[i + 4].var == 3]))
                for i in range(len(block_vars) - 4)]

            right_pick_right_phi_right = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 4, block_vars[i + 2].var == 3,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 3]))
                for i in range(len(block_vars) - 4)]

            right_phi_pick_right_right = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 6, block_vars[i + 2].var == 4,
                               block_vars[i + 3].var == 3,
                               block_vars[i + 4].var == 3]))
                for i in range(len(block_vars) - 4)
            ]


            right_phi_pick_right_phi_right = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 6, block_vars[i + 2].var == 4,
                               block_vars[i + 3].var == 3,
                               block_vars[i + 4].var == 6,  block_vars[i + 5].var == 3]))
                for i in range(len(block_vars) - 5)
            ]

            right_phi_pick_phi_right_right = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 6, block_vars[i + 2].var == 4,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 3, block_vars[i + 5].var == 3]))
                for i in range(len(block_vars) - 5)

            ]

            right_pick_phi_right_phi_right = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 4, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 3,
                               block_vars[i + 4].var == 6, block_vars[i + 5].var == 3]))
                for i in range(len(block_vars) - 5)
            ]

            right_put_right_right = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 5, block_vars[i + 2].var == 3,
                               block_vars[i + 3].var == 3]))
                for i in range(len(block_vars) - 3)]

            right_put_phi_right_right = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 5, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 3,
                               block_vars[i + 4].var == 3]))
                for i in range(len(block_vars) - 4)]

            right_put_right_phi_right = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 5, block_vars[i + 2].var == 3,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 3]))
                for i in range(len(block_vars) - 4)]

            right_phi_put_right_right = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 6, block_vars[i + 2].var == 5,
                               block_vars[i + 3].var == 3,
                               block_vars[i + 4].var == 3]))
                for i in range(len(block_vars) - 4)
            ]

            right_phi_put_right_phi_right = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 6, block_vars[i + 2].var == 5,
                               block_vars[i + 3].var == 3,
                               block_vars[i + 4].var == 6, block_vars[i + 5].var == 3]))
                for i in range(len(block_vars) - 5)
            ]

            right_phi_put_phi_right_right = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 6, block_vars[i + 2].var == 5,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 3, block_vars[i + 5].var == 3]))
                for i in range(len(block_vars) - 5)

            ]

            right_put_phi_right_phi_right = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 5, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 3,
                               block_vars[i + 4].var == 6, block_vars[i + 5].var == 3]))
                for i in range(len(block_vars) - 5)

            ]

            right_right_pick_right = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 3, block_vars[i + 2].var == 4,
                               block_vars[i + 3].var == 3]))
                for i in range(len(block_vars) - 3)]

            right_right_phi_pick_right = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 3, block_vars[i + 2].var == 6,block_vars[i + 3].var == 4,
                               block_vars[i + 4].var == 3]))
                for i in range(len(block_vars) - 4)]

            right_right_pick_phi_right = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 3, block_vars[i + 2].var == 4,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 3]))
                for i in range(len(block_vars) - 4)]

            right_phi_right_pick_right = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 6, block_vars[i + 2].var == 3,
                               block_vars[i + 3].var == 4,
                               block_vars[i + 4].var == 3]))
                for i in range(len(block_vars) - 4)
            ]



            right_phi_right_pick_phi_right = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 6, block_vars[i + 2].var == 3,
                               block_vars[i + 3].var == 4,
                               block_vars[i + 4].var == 6, block_vars[i + 5].var == 3]))
                for i in range(len(block_vars) - 5)
            ]

            right_phi_right_phi_pick_right = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 6, block_vars[i + 2].var == 3,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 4, block_vars[i + 5].var == 3]))
                for i in range(len(block_vars) - 5)

            ]

            right_right_phi_pick_phi_right = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 3, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 4,
                               block_vars[i + 4].var == 6, block_vars[i + 5].var == 3]))
                for i in range(len(block_vars) - 5)
            ]


            right_right_put_right = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 3, block_vars[i + 2].var == 5,
                               block_vars[i + 3].var == 3]))
                for i in range(len(block_vars) - 3)]

            right_right_phi_put_right = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 3, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 5,
                               block_vars[i + 4].var == 3]))
                for i in range(len(block_vars) - 4)]

            right_right_put_phi_right = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 3, block_vars[i + 2].var == 5,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 3]))
                for i in range(len(block_vars) - 4)]

            right_phi_right_put_right = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 6, block_vars[i + 2].var == 3,
                               block_vars[i + 3].var == 5,
                               block_vars[i + 4].var == 3]))
                for i in range(len(block_vars) - 4)
            ]


            right_phi_right_put_phi_right = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 6, block_vars[i + 2].var == 3,
                               block_vars[i + 3].var == 5,
                               block_vars[i + 4].var == 6, block_vars[i + 5].var == 3]))
                for i in range(len(block_vars) - 5)
            ]

            right_phi_right_phi_put_right = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 6, block_vars[i + 2].var == 3,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 5, block_vars[i + 5].var == 3]))
                for i in range(len(block_vars) - 5)

            ]

            right_right_phi_put_phi_right = [
                z3.Not(z3.And([block_vars[i].var == 3, block_vars[i + 1].var == 3, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 5,
                               block_vars[i + 4].var == 6, block_vars[i + 5].var == 3]))
                for i in range(len(block_vars) - 5)
            ]


            left_pick_left_left = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 4, block_vars[i + 2].var == 2,
                               block_vars[i + 3].var == 2]))
                for i in range(len(block_vars) - 3)]

            left_pick_phi_left_left = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 4, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 2,
                               block_vars[i + 4].var == 2]))
                for i in range(len(block_vars) - 4)]

            left_pick_left_phi_left = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 4, block_vars[i + 2].var == 2,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 2]))
                for i in range(len(block_vars) - 4)]


            left_phi_pick_left_left = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 6, block_vars[i + 2].var == 4,
                               block_vars[i + 3].var == 2,
                               block_vars[i + 4].var == 2]))
                for i in range(len(block_vars) - 4)
            ]



            left_phi_pick_phi_left_left = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 6, block_vars[i + 2].var == 4,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 2, block_vars[i + 5].var == 2]))
                for i in range(len(block_vars) - 5)
            ]

            left_pick_phi_left_phi_left = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 4, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 2,
                               block_vars[i + 4].var == 6, block_vars[i + 5].var == 2]))
                for i in range(len(block_vars) - 5)
            ]

            left_phi_pick_left_phi_left = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 6, block_vars[i + 2].var == 4,
                               block_vars[i + 3].var == 2,
                               block_vars[i + 4].var == 6, block_vars[i + 5].var == 2]))
                for i in range(len(block_vars) - 5)
            ]

            left_put_left_left = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 5, block_vars[i + 2].var == 2,
                               block_vars[i + 3].var == 2]))
                for i in range(len(block_vars) - 3)]

            left_put_phi_left_left = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 5, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 2,
                               block_vars[i + 4].var == 2]))
                for i in range(len(block_vars) - 4)]

            left_put_left_phi_left = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 5, block_vars[i + 2].var == 2,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 2]))
                for i in range(len(block_vars) - 4)]

            left_phi_put_left_left = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 6, block_vars[i + 2].var == 5,
                               block_vars[i + 3].var == 2,
                               block_vars[i + 4].var == 2]))
                for i in range(len(block_vars) - 4)
            ]


            left_phi_put_phi_left_left = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 6, block_vars[i + 2].var == 5,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 2, block_vars[i + 5].var == 2]))
                for i in range(len(block_vars) - 5)
            ]

            left_put_phi_left_phi_left = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 5, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 2,
                               block_vars[i + 4].var == 6, block_vars[i + 5].var == 2]))
                for i in range(len(block_vars) - 5)
            ]

            left_phi_put_left_phi_left = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 6, block_vars[i + 2].var == 5,
                               block_vars[i + 3].var == 2,
                               block_vars[i + 4].var == 6, block_vars[i + 5].var == 2]))
                for i in range(len(block_vars) - 5)
            ]


            left_left_put_left = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 2, block_vars[i + 2].var == 4,
                               block_vars[i + 3].var == 2]))
                for i in range(len(block_vars) - 3)]

            left_left_phi_put_left = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 2, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 5,
                               block_vars[i + 4].var == 2]))
                for i in range(len(block_vars) - 4)]

            left_left_put_phi_left = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 2, block_vars[i + 2].var == 5,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 2]))
                for i in range(len(block_vars) - 4)]

            left_phi_left_put_left = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 6, block_vars[i + 2].var == 2,
                               block_vars[i + 3].var == 5,
                               block_vars[i + 4].var == 2]))
                for i in range(len(block_vars) - 4)
            ]


            left_phi_left_phi_put_left = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 6, block_vars[i + 2].var == 2,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 5, block_vars[i + 4].var == 2]))
                for i in range(len(block_vars) - 5)
            ]

            left_phi_left_put_phi_left = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 6, block_vars[i + 2].var == 2,
                               block_vars[i + 3].var == 5,
                               block_vars[i + 4].var == 6, block_vars[i + 4].var == 2]))
                for i in range(len(block_vars) - 5)
            ]

            left_left_phi_put_phi_left = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 2, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 5,
                               block_vars[i + 4].var == 6, block_vars[i + 4].var == 2]))
                for i in range(len(block_vars) - 5)
            ]



            left_left_pick_left = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 2, block_vars[i + 2].var == 4,
                               block_vars[i + 3].var == 2]))
                for i in range(len(block_vars) - 3)]

            left_left_phi_pick_left = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 2, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 4,
                               block_vars[i + 4].var == 2]))
                for i in range(len(block_vars) - 4)]

            left_left_pick_phi_left = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 2, block_vars[i + 2].var == 4,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 2]))
                for i in range(len(block_vars) - 4)]

            left_phi_left_pick_left = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 6, block_vars[i + 2].var == 2,
                               block_vars[i + 3].var == 4,
                               block_vars[i + 4].var == 2]))
                for i in range(len(block_vars) - 4)
            ]


            left_phi_left_pick_phi_left = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 6, block_vars[i + 2].var == 2,
                               block_vars[i + 3].var == 4,
                               block_vars[i + 4].var == 6, block_vars[i + 5].var == 2]))
                for i in range(len(block_vars) - 5)
            ]

            left_left_phi_pick_phi_left = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 2, block_vars[i + 2].var == 6,
                               block_vars[i + 3].var == 4,
                               block_vars[i + 4].var == 6, block_vars[i + 5].var == 2]))
                for i in range(len(block_vars) - 5)
            ]

            left_phi_left_phi_pick_left = [
                z3.Not(z3.And([block_vars[i].var == 2, block_vars[i + 1].var == 6, block_vars[i + 2].var == 2,
                               block_vars[i + 3].var == 6,
                               block_vars[i + 4].var == 4, block_vars[i + 5].var == 2]))
                for i in range(len(block_vars) - 5)

            ]




            elimination_constraints = left_right_constraints + right_left_constraints + \
                                      all_left_constraints + all_right_constraints + \
                                      left_phi_right_constraints + right_phi_left_constraints + \
                                      left_phi_phi_right_constraints + right_phi_phi_left_constraints + \
                                      left_phi_left_left_constraints + left_left_phi_left_constraints + \
                                      left_phi_phi_left_left_constraints + left_left_phi_phi_left_constraints + \
                                      right_phi_right_right_constraints + right_right_phi_right_constraints + \
                                      right_phi_phi_right_right_constraints + right_right_phi_phi_right_constraints + \
                                      left_phi_left_phi_left_constraints + right_phi_right_phi_right_constraints +\
                                      pick_put_constraints +  put_pick_constraints + pick_pick + put_put + \
                                      pick_phi_put + put_phi_pick + pick_phi_pick + put_phi_put + \
                                      pick_phi_phi_pick + pick_phi_phi_put + put_phi_phi_pick + put_phi_phi_put +\
                                      left_left_pick_left + left_left_put_left + left_put_left_left + left_pick_left_left +\
                                      right_right_put_right + right_right_pick_right + right_put_right_right + right_pick_right_right + \
                                      pick_right_phi_pick + pick_phi_phi_right_pick + pick_phi_right_pick + pick_right_pick + pick_left_phi_pick + \
            pick_phi_phi_left_pick + pick_phi_left_pick+ pick_left_pick + put_right_phi_put + put_phi_phi_right_put +\
            put_phi_right_put + put_right_put +  put_left_phi_put + put_phi_phi_left_put + put_phi_left_put + put_left_put + put_left_phi_pick +\
            put_phi_phi_left_pick + put_phi_left_pick + put_left_pick + put_right_phi_pick + put_phi_phi_right_pick +\
            put_phi_right_pick + put_right_pick + pick_right_phi_put + pick_phi_phi_right_put + pick_phi_right_put +\
            pick_right_put + pick_left_phi_put +\
            pick_phi_phi_left_put + pick_phi_left_put + pick_left_put+\
            right_pick_phi_left + right_phi_phi_pick_left +right_phi_pick_left + right_pick_left + right_put_phi_left +\
            right_phi_phi_put_left + right_phi_put_left + right_put_left + left_pick_phi_right + left_phi_phi_pick_right +\
                                      left_phi_pick_right + left_pick_right + left_put_phi_right +\
            left_phi_phi_put_right + left_phi_put_right + left_put_right + left_left_pick_phi_left +\
            left_left_phi_pick_left + left_left_put_phi_left + left_left_phi_put_left + left_put_left_phi_left + left_put_phi_left_left + \
            left_pick_left_phi_left + left_pick_phi_left_left + right_right_put_phi_right + right_right_phi_put_right + right_right_pick_phi_right + \
            right_right_phi_pick_right + right_put_right_phi_right + right_put_phi_right_right + right_pick_right_phi_right + right_pick_phi_right_right + \
            pick_right_phi_phi_pick + pick_right_phi_phi_pick + pick_left_phi_phi_pick + put_right_phi_phi_put + put_left_phi_phi_put + \
            put_left_phi_phi_pick + put_right_phi_phi_pick + pick_right_pi_phi_put + pick_left_phi_phi_put + right_pick_phi_phi_left + \
            right_put_phi_phi_left + left_pick_phi_phi_right + left_put_phi_phi_right + \
            left_phi_put_phi_right + left_phi_pick_phi_right + right_phi_put_phi_left + right_phi_pick_phi_left + pick_phi_left_phi_put + \
            pick_phi_right_phi_put + put_phi_right_phi_pick + put_phi_left_phi_pick + put_phi_left_phi_put + put_phi_right_phi_put + \
            pick_left_phi_phi_pick + pick_right_phi_phi_pick + pick_phi_right_phi_pick + right_phi_pick_right_right + right_phi_pick_right_phi_right + \
            right_phi_pick_phi_right_right + right_pick_phi_right_phi_right + right_phi_put_right_right + right_phi_put_right_phi_right + \
            right_phi_put_phi_right_right + right_put_phi_right_phi_right + right_phi_right_pick_right + right_phi_right_pick_phi_right + \
            right_phi_right_phi_pick_right + right_right_phi_pick_phi_right + right_phi_right_put_right + right_phi_right_put_phi_right + \
            right_phi_right_phi_put_right + right_right_phi_put_phi_right + left_phi_pick_left_left + left_phi_pick_phi_left_left + \
            left_pick_phi_left_phi_left + left_phi_pick_left_phi_left + left_phi_put_left_left + left_phi_put_phi_left_left + left_put_phi_left_phi_left + \
            left_phi_put_left_phi_left + left_phi_left_put_left + left_phi_left_phi_put_left + left_phi_left_put_phi_left + left_left_phi_put_phi_left + \
            left_phi_left_pick_left + left_phi_left_pick_phi_left + left_left_phi_pick_phi_left + left_phi_left_phi_pick_left + \
                                      left_phi_put_phi_phi_right + left_phi_phi_put_phi_right + \
            left_phi_phi_pick_phi_right + left_phi_pick_phi_phi_right + right_phi_phi_put_phi_left + right_phi_put_phi_phi_left + right_phi_phi_pick_phi_left +\
            right_phi_pick_phi_phi_left + pick_phi_phi_left_phi_put + pick_phi_left_phi_phi_put + pick_phi_phi_right_phi_put + pick_phi_right_phi_phi_put + \
            put_phi_phi_right_phi_pick + put_phi_right_phi_phi_pick + put_phi_phi_left_phi_pick + put_phi_left_phi_phi_pick + put_phi_phi_left_phi_put + \
            put_phi_left_phi_phi_put + put_phi_phi_right_phi_put + put_phi_right_phi_phi_put + pick_left_phi_phi_pick + pick_right_phi_phi_pick + \
            pick_phi_phi_right_phi_pick + pick_phi_right_phi_phi_pick


            return elimination_constraints




        elimination_constraints = left_right_constraints + right_left_constraints + \
                                  all_left_constraints + all_right_constraints + \
                                  left_phi_right_constraints + right_phi_left_constraints+ \
                                  left_phi_phi_right_constraints + right_phi_phi_left_constraints + \
                                  left_phi_left_left_constraints + left_left_phi_left_constraints + \
                                  left_phi_phi_left_left_constraints + left_left_phi_phi_left_constraints + \
                                  right_phi_right_right_constraints + right_right_phi_right_constraints + \
                                  right_phi_phi_right_right_constraints + right_right_phi_phi_right_constraints + \
                                  left_phi_left_phi_left_constraints + right_phi_right_phi_right_constraints

        return elimination_constraints





def single_block_change(block_objs: list):

    single_block_change_constraints = []
    single_block_cons = []
    for ele in block_objs:
        prefix_suffix_mid_var = ele.block_prefix_z3_vars + ele.block_suffix_z3_vars + ele.block_mid_z3_vars
        single_block_cons.append([z3.Or([ele.var != 6 for ele in prefix_suffix_mid_var])])

    for i in range(len(single_block_cons)):
        # other block prefix/suffix vars
        prefix_suffix_mid_vars_other = []
        for j in range(len(block_objs)):
            if j == i:
                continue
            else:
                other_vars = block_objs[j].block_prefix_z3_vars + block_objs[j].block_suffix_z3_vars +  block_objs[j].block_mid_z3_vars
                prefix_suffix_mid_vars_other.extend(other_vars)

        And_cons = z3.And([ele.var == 6 for ele in prefix_suffix_mid_vars_other])

        single_block_change_constraints.extend([z3.Implies(single_block_cons[i][0],
                                                           And_cons)])

    return single_block_change_constraints

def block_unequal_constraint(block_obj_1, block_obj_2):

    if block_obj_1.size != block_obj_2.size:
        print("unequal block lengths")
        return []

    constraints = []

    and_cons = [z3.And([block_obj_1.block_z3_vars[i].var == block_obj_2.block_z3_vars[i].var for i in range(block_obj_1.size)])]

    not_cons = z3.Not(and_cons[0])

    constraints.extend([not_cons])

    return constraints










































