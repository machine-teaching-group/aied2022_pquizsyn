from z3 import z3
import sys
import collections
import json

from code.step2_struct2code.smt_constraints_task5.utils_smt import VariableType, ConditionalType, str_to_type, type_to_str,  gen_model, gen_all
from code.step2_struct2code.smt_constraints_task5.utils_block_smt import SMT_Block, single_block_change
from code.step2_struct2code.smt_constraints_task5.utils_ast_smt import ASTNode, remove_null_nodes, json_to_ast


def generate_assignments(thresh= 2, id='karel'):

    solver = z3.Solver()
    # declare the SMT variables for the specific code
    values = []
    c1 = z3.Int('c1')  # bool_no_path_ahead (while)
    values.append(z3.Or(c1 == 7, c1 == 12))  # bool_path_ahead, bool_no_path_ahead

    c2 = z3.Int('c2')  # bool_marker (if_only)
    values.append(z3.Or(c2 == 10, c2 == 11)) # bool_marker, bool_no_marker



    # Block 1
    block_1 = {'b1_1': 'pick_marker'}
    block_1_obj = SMT_Block(block_1, thresh, id=id)
    values.extend(block_1_obj.block_values)
    block_1_vars = [ele.var for ele in block_1_obj.block_z3_vars]  # for the conditional constraints

    block_2 = {'b2_1': 'turn_left', 'b2_2': 'move', 'b2_3': 'turn_right', 'b2_4': 'move'}
    block_2_obj = SMT_Block(block_2, thresh, id=id)
    values.extend(block_2_obj.block_values)
    block_2_vars = [ele.var for ele in block_2_obj.block_z3_vars]  # for the conditional constraints

    block_3 = {'b3_1': 'pick_marker'}
    block_3_obj = SMT_Block(block_3, thresh, id=id)
    values.extend(block_3_obj.block_values)
    block_3_vars = [ele.var for ele in block_3_obj.block_z3_vars]  # for the conditional constraints

    block_4 = {'b4_1': 'phi'}
    block_4_obj = SMT_Block(block_4, thresh, id=id)
    values.extend(block_4_obj.block_values)
    block_4_vars = [ele.var for ele in block_4_obj.block_z3_vars]  # for the conditional constraints



    # all block objects
    block_objs = [block_1_obj, block_2_obj, block_3_obj, block_4_obj]



    X = [c1, c2]
    X.extend([ele.var for ele in block_1_obj.block_z3_vars])  # added the variables for block 1
    X.extend([ele.var for ele in block_2_obj.block_z3_vars])  # added the variables for block 2
    X.extend([ele.var for ele in block_3_obj.block_z3_vars])  # added the variables for block 3
    X.extend([ele.var for ele in block_4_obj.block_z3_vars])  # added the variables for block 4


    constraints = block_1_obj.block_append_constraints + block_1_obj.flip_turns_constraints + block_1_obj.flip_marker_constraints + \
                  block_1_obj.block_elimination_constraints + \
                  block_2_obj.block_append_constraints + block_2_obj.flip_turns_constraints + \
                  block_2_obj.flip_marker_constraints + block_2_obj.block_elimination_constraints + \
                  block_3_obj.block_append_constraints + block_3_obj.flip_turns_constraints + \
                  block_3_obj.flip_marker_constraints + block_3_obj.block_elimination_constraints + \
                  block_4_obj.block_append_constraints + block_4_obj.flip_turns_constraints + \
                  block_4_obj.flip_marker_constraints + block_4_obj.block_elimination_constraints



    single_block_change_cons = single_block_change(block_objs)

    constraints.extend(single_block_change_cons)

    constraints.extend([

        # conditional constraints: while(bool_path_ahead)---while block constraints
        ######## DO NOT REQUIRE ONE OF THE VARS OF BLOCK NESTED IN BOOL_MARKER / BOOL_NO_MARKER TO BE MOVE
        # z3.Implies(c1 == 7,
        #            z3.Or(block_1_vars[0] == 1, block_1_vars[1] == 1,
        #                  block_1_vars[2] == 1,
        #
        #                  block_1_vars[3] == 1,
        #                  block_1_vars[4] == 1,
        #
        #                  )),
        z3.Implies(z3.And(c1 == 7, block_1_vars[1] == 1, block_1_vars[0] != 1), z3.And(block_1_vars[0] != 2, block_1_vars[0] != 3)),
        z3.Implies(z3.And(c1 == 7, block_1_vars[2] == 1,
                          block_1_vars[0] != 1, block_1_vars[1] != 1), z3.And(block_1_vars[0] != 2, block_1_vars[0] != 3,
                                                                 block_1_vars[1] != 2, block_1_vars[1] != 3)),


        ############ THRESH = 2
        z3.Implies(z3.And(c1 == 7, block_1_vars[3] == 1,
                          block_1_vars[0] != 1, block_1_vars[1] != 1,
                          block_1_vars[2] != 1), z3.And(block_1_vars[0] != 2, block_1_vars[0] != 3,
                                                                 block_1_vars[1] != 2, block_1_vars[1] != 3,
                                                                 block_1_vars[2] != 2, block_1_vars[2] != 3)),
        z3.Implies(z3.And(c1 == 7, block_1_vars[4] == 1,
                          block_1_vars[0] != 1, block_1_vars[1] != 1,
                          block_1_vars[2] != 1, block_1_vars[3] != 1
                          ), z3.And(block_1_vars[0] != 2, block_1_vars[0] != 3,
                                                                 block_1_vars[1] != 2, block_1_vars[1] != 3,
                                                                 block_1_vars[2] != 2, block_1_vars[2] != 3,
                                                                 block_1_vars[3] != 2, block_1_vars[3] != 3)),




##################################
        z3.Implies(c1 == 7,
                   z3.Or(block_2_vars[0] == 1, block_2_vars[1] == 1,
                         block_2_vars[2] == 1, block_2_vars[3] == 1,
                         block_2_vars[4] == 1, block_2_vars[5] == 1,
                         block_2_vars[6] == 1, block_2_vars[7] == 1,
                         block_2_vars[8] == 1,

                         block_2_vars[9] == 1,
                         block_2_vars[10] == 1,


                         )),
        z3.Implies(z3.And(c1 == 7, block_2_vars[1] == 1, block_2_vars[0] != 1), z3.And(block_2_vars[0] != 2, block_2_vars[0] != 3)),
        z3.Implies(z3.And(c1 == 7, block_2_vars[2] == 1,
                          block_2_vars[0] != 1, block_2_vars[1] != 1), z3.And(block_2_vars[0] != 2, block_2_vars[0] != 3,
                                                                 block_2_vars[1] != 2, block_2_vars[1] != 3)),
        z3.Implies(z3.And(c1 == 7, block_2_vars[3] == 1,
                          block_2_vars[0] != 1, block_2_vars[1] != 1,
                          block_2_vars[2] != 1), z3.And(block_2_vars[0] != 2, block_2_vars[0] != 3,
                                                                 block_2_vars[1] != 2, block_2_vars[1] != 3,
                                                                 block_2_vars[2] != 2, block_2_vars[2] != 3)),
        z3.Implies(z3.And(c1 == 7, block_2_vars[4] == 1,
                          block_2_vars[0] != 1, block_2_vars[1] != 1,
                          block_2_vars[2] != 1, block_2_vars[3] != 1
                          ), z3.And(block_2_vars[0] != 2, block_2_vars[0] != 3,
                                                                 block_2_vars[1] != 2, block_2_vars[1] != 3,
                                                                 block_2_vars[2] != 2, block_2_vars[2] != 3,
                                                                 block_2_vars[3] != 2, block_2_vars[3] != 3)),
        z3.Implies(z3.And(c1 == 7, block_2_vars[5] == 1,
                          block_2_vars[0] != 1, block_2_vars[1] != 1,
                          block_2_vars[2] != 1, block_2_vars[3] != 1,
                          block_2_vars[4] != 1
                          ), z3.And(block_2_vars[0] != 2, block_2_vars[0] != 3,
                                                                 block_2_vars[1] != 2, block_2_vars[1] != 3,
                                                                 block_2_vars[2] != 2, block_2_vars[2] != 3,
                                                                 block_2_vars[3] != 2, block_2_vars[3] != 3,
                                                                 block_2_vars[4] != 2, block_2_vars[4] != 3)),
        z3.Implies(z3.And(c1 == 7, block_2_vars[6] == 1,
                          block_2_vars[0] != 1, block_2_vars[1] != 1,
                          block_2_vars[2] != 1, block_2_vars[3] != 1,
                          block_2_vars[4] != 1, block_2_vars[5] != 1
                          ), z3.And(block_2_vars[0] != 2, block_2_vars[0] != 3,
                                                                 block_2_vars[1] != 2, block_2_vars[1] != 3,
                                                                 block_2_vars[2] != 2, block_2_vars[2] != 3,
                                                                 block_2_vars[3] != 2, block_2_vars[3] != 3,
                                                                 block_2_vars[4] != 2, block_2_vars[4] != 3,
                                                                 block_2_vars[4] != 2, block_2_vars[4] != 3,
                                                                 block_2_vars[5] != 2, block_2_vars[5] != 3)),
        z3.Implies(z3.And(c1 == 7, block_2_vars[7] == 1,
                          block_2_vars[0] != 1, block_2_vars[1] != 1,
                          block_2_vars[2] != 1, block_2_vars[3] != 1,
                          block_2_vars[4] != 1, block_2_vars[5] != 1,
                          block_2_vars[6] != 1
                          ), z3.And(block_2_vars[0] != 2, block_2_vars[0] != 3,
                                                                 block_2_vars[1] != 2, block_2_vars[1] != 3,
                                                                 block_2_vars[2] != 2, block_2_vars[2] != 3,
                                                                 block_2_vars[3] != 2, block_2_vars[3] != 3,
                                                                 block_2_vars[4] != 2, block_2_vars[4] != 3,
                                                                 block_2_vars[4] != 2, block_2_vars[4] != 3,
                                                                 block_2_vars[5] != 2, block_2_vars[5] != 3,
                                                                 block_2_vars[6] != 2, block_2_vars[6] != 3,)),
        z3.Implies(z3.And(c1 == 7, block_2_vars[8] == 1,
                          block_2_vars[0] != 1, block_2_vars[1] != 1,
                          block_2_vars[2] != 1, block_2_vars[3] != 1,
                          block_2_vars[4] != 1, block_2_vars[5] != 1,
                          block_2_vars[6] != 1, block_2_vars[7] != 1
                          ), z3.And(block_2_vars[0] != 2, block_2_vars[0] != 3,
                                                                 block_2_vars[1] != 2, block_2_vars[1] != 3,
                                                                 block_2_vars[2] != 2, block_2_vars[2] != 3,
                                                                 block_2_vars[3] != 2, block_2_vars[3] != 3,
                                                                 block_2_vars[4] != 2, block_2_vars[4] != 3,
                                                                 block_2_vars[4] != 2, block_2_vars[4] != 3,
                                                                 block_2_vars[5] != 2, block_2_vars[5] != 3,
                                                                 block_2_vars[6] != 2, block_2_vars[6] != 3,
                                                                 block_2_vars[7] != 2, block_2_vars[7] != 3)),

        ############ THRESH = 2

        z3.Implies(z3.And(c1 == 7, block_2_vars[9] == 1,
                          block_2_vars[0] != 1, block_2_vars[1] != 1,
                          block_2_vars[2] != 1, block_2_vars[3] != 1,
                          block_2_vars[4] != 1, block_2_vars[5] != 1,
                          block_2_vars[6] != 1, block_2_vars[7] != 1,
                          block_2_vars[8] != 1
                          ), z3.And(block_2_vars[0] != 2, block_2_vars[0] != 3,
                                                                 block_2_vars[1] != 2, block_2_vars[1] != 3,
                                                                 block_2_vars[2] != 2, block_2_vars[2] != 3,
                                                                 block_2_vars[3] != 2, block_2_vars[3] != 3,
                                                                 block_2_vars[4] != 2, block_2_vars[4] != 3,
                                                                 block_2_vars[4] != 2, block_2_vars[4] != 3,
                                                                 block_2_vars[5] != 2, block_2_vars[5] != 3,
                                                                 block_2_vars[6] != 2, block_2_vars[6] != 3,
                                                                 block_2_vars[7] != 2, block_2_vars[7] != 3,
                                                                 block_2_vars[8] != 2, block_2_vars[8] != 3)),




        z3.Implies(z3.And(c1 == 7, block_2_vars[10] == 1,
                          block_2_vars[0] != 1, block_2_vars[1] != 1,
                          block_2_vars[2] != 1, block_2_vars[3] != 1,
                          block_2_vars[4] != 1, block_2_vars[5] != 1,
                          block_2_vars[6] != 1, block_2_vars[7] != 1,
                          block_2_vars[8] != 1, block_2_vars[9] != 1
                          ), z3.And(block_2_vars[0] != 2, block_2_vars[0] != 3,
                                    block_2_vars[1] != 2, block_2_vars[1] != 3,
                                    block_2_vars[2] != 2, block_2_vars[2] != 3,
                                    block_2_vars[3] != 2, block_2_vars[3] != 3,
                                    block_2_vars[4] != 2, block_2_vars[4] != 3,
                                    block_2_vars[4] != 2, block_2_vars[4] != 3,
                                    block_2_vars[5] != 2, block_2_vars[5] != 3,
                                    block_2_vars[6] != 2, block_2_vars[6] != 3,
                                    block_2_vars[7] != 2, block_2_vars[7] != 3,
                                    block_2_vars[8] != 2, block_2_vars[8] != 3,
                                    block_2_vars[9] != 2, block_2_vars[9] != 3,
                                    )),



#############################

        # # conditional constraints: while(bool_no_path_ahead)---while block constraints
        z3.Implies(c1 == 12, block_1_vars[0] != 1),
        z3.Implies(z3.And(c1 == 12, block_1_vars[1] == 1, block_1_vars[0] != 1), z3.Or(block_1_vars[0] == 2, block_1_vars[0] == 3)),
        z3.Implies(z3.And(c1 == 12, block_1_vars[2] == 1,
                          block_1_vars[0] != 1, block_1_vars[1] != 1), z3.Or(block_1_vars[0] == 2, block_1_vars[0] == 3,
                                                                 block_1_vars[1] == 2, block_1_vars[1] == 3)),
        ######### THRESH = 2

        z3.Implies(z3.And(c1 == 12, block_1_vars[3] == 1,
                          block_1_vars[0] != 1, block_1_vars[1] != 1,
                          block_1_vars[2] != 1),
                   z3.Or(block_1_vars[0] == 2, block_1_vars[0] == 3,
                         block_1_vars[1] == 2, block_1_vars[1] == 3,
                         block_1_vars[2] == 2, block_1_vars[2] == 3)),
        z3.Implies(z3.And(c1 == 12, block_1_vars[4] == 1,
                          block_1_vars[0] != 1, block_1_vars[1] != 1,
                          block_1_vars[2] != 1, block_1_vars[3] != 1
                          ),
                   z3.Or(block_1_vars[0] == 2, block_1_vars[0] == 3,
                         block_1_vars[1] == 2, block_1_vars[1] == 3,
                         block_1_vars[2] == 2, block_1_vars[2] == 3,
                         block_1_vars[3] == 2, block_1_vars[3] == 3)),




################################
        z3.Implies(c1 == 12, block_2_vars[0] != 1),
        z3.Implies(z3.And(c1 == 12, block_2_vars[1] == 1, block_2_vars[0] != 1), z3.Or(block_2_vars[0] == 2, block_2_vars[0] == 3)),
        z3.Implies(z3.And(c1 == 12, block_2_vars[2] == 1,
                          block_2_vars[0] != 1, block_2_vars[1] != 1), z3.Or(block_2_vars[0] == 2, block_2_vars[0] == 3,
                                                                 block_2_vars[1] == 2, block_2_vars[1] == 3)),
        z3.Implies(z3.And(c1 == 12, block_2_vars[3] == 1,
                          block_2_vars[0] != 1, block_2_vars[1] != 1,
                          block_2_vars[2] != 1),
                   z3.Or(block_2_vars[0] == 2, block_2_vars[0] == 3,
                         block_2_vars[1] == 2, block_2_vars[1] == 3,
                         block_2_vars[2] == 2, block_2_vars[2] == 3)),
        z3.Implies(z3.And(c1 == 12, block_2_vars[4] == 1,
                          block_2_vars[0] != 1, block_2_vars[1] != 1,
                          block_2_vars[2] != 1, block_2_vars[3] != 1
                          ),
                   z3.Or(block_2_vars[0] == 2, block_2_vars[0] == 3,
                         block_2_vars[1] == 2, block_2_vars[1] == 3,
                         block_2_vars[2] == 2, block_2_vars[2] == 3,
                         block_2_vars[3] == 2, block_2_vars[3] == 3)),
        z3.Implies(z3.And(c1 == 12, block_2_vars[5] == 1,
                          block_2_vars[0] != 1, block_2_vars[1] != 1,
                          block_2_vars[2] != 1, block_2_vars[3] != 1,
                          block_2_vars[4] != 1
                          ),
                   z3.Or(block_2_vars[0] == 2, block_2_vars[0] == 3,
                         block_2_vars[1] == 2, block_2_vars[1] == 3,
                         block_2_vars[2] == 2, block_2_vars[2] == 3,
                         block_2_vars[3] == 2, block_2_vars[3] == 3,
                         block_2_vars[4] == 2, block_2_vars[4] == 3)),
        z3.Implies(z3.And(c1 == 12, block_2_vars[6] == 1,
                          block_2_vars[0] != 1, block_2_vars[1] != 1,
                          block_2_vars[2] != 1, block_2_vars[3] != 1,
                          block_2_vars[4] != 1, block_2_vars[5] != 1
                          ),
                   z3.Or(block_2_vars[0] == 2, block_2_vars[0] == 3,
                         block_2_vars[1] == 2, block_2_vars[1] == 3,
                         block_2_vars[2] == 2, block_2_vars[2] == 3,
                         block_2_vars[3] == 2, block_2_vars[3] == 3,
                         block_2_vars[4] == 2, block_2_vars[4] == 3,
                         block_2_vars[5] == 2, block_2_vars[5] == 3)),

        z3.Implies(z3.And(c1 == 12, block_2_vars[7] == 1,
                          block_2_vars[0] != 1, block_2_vars[1] != 1,
                          block_2_vars[2] != 1, block_2_vars[3] != 1,
                          block_2_vars[4] != 1, block_2_vars[5] != 1,
                          block_2_vars[6] != 1
                          ),
                   z3.Or(block_2_vars[0] == 2, block_2_vars[0] == 3,
                         block_2_vars[1] == 2, block_2_vars[1] == 3,
                         block_2_vars[2] == 2, block_2_vars[2] == 3,
                         block_2_vars[3] == 2, block_2_vars[3] == 3,
                         block_2_vars[4] == 2, block_2_vars[4] == 3,
                         block_2_vars[5] == 2, block_2_vars[5] == 3,
                         block_2_vars[6] == 2, block_2_vars[6] == 3)),
        z3.Implies(z3.And(c1 == 12, block_2_vars[8] == 1,
                          block_2_vars[0] != 1, block_2_vars[1] != 1,
                          block_2_vars[2] != 1, block_2_vars[3] != 1,
                          block_2_vars[4] != 1, block_2_vars[5] != 1,
                          block_2_vars[6] != 1, block_2_vars[7] != 1
                          ),
                   z3.Or(block_2_vars[0] == 2, block_2_vars[0] == 3,
                         block_2_vars[1] == 2, block_2_vars[1] == 3,
                         block_2_vars[2] == 2, block_2_vars[2] == 3,
                         block_2_vars[3] == 2, block_2_vars[3] == 3,
                         block_2_vars[4] == 2, block_2_vars[4] == 3,
                         block_2_vars[5] == 2, block_2_vars[5] == 3,
                         block_2_vars[6] == 2, block_2_vars[6] == 3,
                         block_2_vars[7] == 2, block_2_vars[7] == 3)),


        ################ THRESH = 2
        z3.Implies(z3.And(c1 == 12, block_2_vars[9] == 1,
                          block_2_vars[0] != 1, block_2_vars[1] != 1,
                          block_2_vars[2] != 1, block_2_vars[3] != 1,
                          block_2_vars[4] != 1, block_2_vars[5] != 1,
                          block_2_vars[6] != 1, block_2_vars[7] != 1,
                          block_2_vars[8] != 1
                          ),
                   z3.Or(block_2_vars[0] == 2, block_2_vars[0] == 3,
                         block_2_vars[1] == 2, block_2_vars[1] == 3,
                         block_2_vars[2] == 2, block_2_vars[2] == 3,
                         block_2_vars[3] == 2, block_2_vars[3] == 3,
                         block_2_vars[4] == 2, block_2_vars[4] == 3,
                         block_2_vars[5] == 2, block_2_vars[5] == 3,
                         block_2_vars[6] == 2, block_2_vars[6] == 3,
                         block_2_vars[7] == 2, block_2_vars[7] == 3,
                         block_2_vars[8] == 2, block_2_vars[8] == 3)),



        z3.Implies(z3.And(c1 == 12, block_2_vars[10] == 1,
                          block_2_vars[0] != 1, block_2_vars[1] != 1,
                          block_2_vars[2] != 1, block_2_vars[3] != 1,
                          block_2_vars[4] != 1, block_2_vars[5] != 1,
                          block_2_vars[6] != 1, block_2_vars[7] != 1,
                          block_2_vars[8] != 1, block_2_vars[9] != 1
                          ),
                   z3.Or(block_2_vars[0] == 2, block_2_vars[0] == 3,
                         block_2_vars[1] == 2, block_2_vars[1] == 3,
                         block_2_vars[2] == 2, block_2_vars[2] == 3,
                         block_2_vars[3] == 2, block_2_vars[3] == 3,
                         block_2_vars[4] == 2, block_2_vars[4] == 3,
                         block_2_vars[5] == 2, block_2_vars[5] == 3,
                         block_2_vars[6] == 2, block_2_vars[6] == 3,
                         block_2_vars[7] == 2, block_2_vars[7] == 3,
                         block_2_vars[8] == 2, block_2_vars[8] == 3,
                         block_2_vars[9] == 2, block_2_vars[9] == 3,
                         )),




##################################

        # conditional constraints: if(bool_no_marker)---if block constraints
        z3.Implies(c2 == 11, block_1_vars[0] != 4),
        z3.Implies(z3.And(c2 == 11, block_1_vars[1] == 4, block_1_vars[0] != 4), z3.Or(block_1_vars[0] == 1, block_1_vars[0] == 5)),
        z3.Implies(z3.And(c2 == 11, block_1_vars[2] == 4,
                          block_1_vars[0] != 4, block_1_vars[1] != 4), z3.Or(block_1_vars[0] == 1, block_1_vars[0] == 5,
                                                                 block_1_vars[1] == 1, block_1_vars[1] == 5)),

        ############# THRESH = 2
        z3.Implies(z3.And(c2 == 11, block_1_vars[3] == 4,
                          block_1_vars[0] != 4, block_1_vars[1] != 4,
                          block_1_vars[2] != 4),
                   z3.Or(block_1_vars[0] == 1, block_1_vars[0] == 5,
                         block_1_vars[1] == 1, block_1_vars[1] == 5,
                         block_1_vars[2] == 1, block_1_vars[2] == 5)),
        z3.Implies(z3.And(c1 == 11, block_1_vars[4] == 4,
                          block_1_vars[0] != 4, block_1_vars[1] != 4,
                          block_1_vars[2] != 4, block_1_vars[3] != 4
                          ),
                   z3.Or(block_1_vars[0] == 1, block_1_vars[0] == 5,
                          block_1_vars[1] == 1, block_1_vars[1] == 5,
                          block_1_vars[2] == 1, block_1_vars[2] == 5,
                          block_1_vars[3] == 1, block_1_vars[3] == 5)),



########################
        # conditional constraints: if(bool_marker)---if block constraints
        z3.Implies(c2 == 10, block_1_vars[0] != 5),
        z3.Implies(z3.And(c2 == 10, block_1_vars[1] == 5, block_1_vars[0] != 5), z3.Or(block_1_vars[0] == 1, block_1_vars[0] == 4)),
        z3.Implies(z3.And(c2 == 10, block_1_vars[2] == 5,
                          block_1_vars[0] != 5, block_1_vars[1] != 5), z3.Or(block_1_vars[0] == 1, block_1_vars[0] == 4,
                                                                 block_1_vars[1] == 1, block_1_vars[1] == 4)),

        ############ THRESH = 2
        z3.Implies(z3.And(c2 == 10, block_1_vars[3] == 5,
                          block_1_vars[0] != 5, block_1_vars[1] != 5,
                          block_1_vars[2] != 5),
                   z3.Or(block_1_vars[0] == 1, block_1_vars[0] == 4,
                         block_1_vars[1] == 1, block_1_vars[1] == 4,
                         block_1_vars[2] == 1, block_1_vars[2] == 4)),
        z3.Implies(z3.And(c2 == 10, block_1_vars[4] == 5,
                          block_1_vars[0] != 5, block_1_vars[1] != 5,
                          block_1_vars[2] != 5, block_1_vars[3] != 5
                          ),
                   z3.Or(block_1_vars[0] == 1, block_1_vars[0] == 4,
                          block_1_vars[1] == 1, block_1_vars[1] == 4,
                          block_1_vars[2] == 1, block_1_vars[2] == 4,
                          block_1_vars[3] == 1, block_1_vars[3] == 4))



    ])

    # add the values and the constraints
    solver.add(values + constraints)

    # generate all the assignments
    models = gen_all(solver, X)

    assignments = []
    for model in models:
        a = [type_to_str[ConditionalType(model[c1].as_long())], type_to_str[ConditionalType(model[c2].as_long())]]
        a.extend([type_to_str[VariableType(model[ele].as_long())]
                  for ele in block_1_vars

                  ])
        a.extend([type_to_str[VariableType(model[ele].as_long())]
                  for ele in block_2_vars

                  ])

        a.extend([type_to_str[VariableType(model[ele].as_long())]
                  for ele in block_3_vars

                  ])
        a.extend([type_to_str[VariableType(model[ele].as_long())]
                  for ele in block_4_vars

                  ])

        assignments.append(a)
        # print(a)

    print('Found #{} SAT values'.format(len(models)))
    return assignments


def generate_ast_nodes_from_assignments(assignments: list):
    all_ast_progs = []

    for a in assignments:
        # this template is specific to HOC_A's ASTNode structure
        ast = ASTNode('run', None, [


            ###### Thresh = 2
            ASTNode(a[23]), ASTNode(a[24]),
            ASTNode(a[25]),
            ASTNode(a[26]), ASTNode(a[27]),



               ASTNode('while', a[0], [
                   ASTNode('if', a[1], [
                       ASTNode('do', a[1], [
                           ###### Thresh = 1
                           ASTNode(a[2]), ASTNode(a[3]),
                           ASTNode(a[4]),

                           ####### Thresh = 2
                           ASTNode(a[5]), ASTNode(a[6]),

                       ])
                   ]),


                   ####### Thresh = 2
                   ASTNode(a[7]), ASTNode(a[8]),
                   ASTNode(a[9]),
                   ASTNode(a[10]),
                   ASTNode(a[11]),
                   ASTNode(a[12]),
                   ASTNode(a[13]),
                   ASTNode(a[14]),
                   ASTNode(a[15]),
                   ASTNode(a[16]), ASTNode(a[17]),


               ]),


            ### Thresh = 2
            ASTNode(a[18]), ASTNode(a[19]),
            ASTNode(a[20]),
            ASTNode(a[21]), ASTNode(a[22]),

        ])

        ast = remove_null_nodes(ast)
        if ast not in all_ast_progs:
            all_ast_progs.append(ast)



    return all_ast_progs


def get_p_star():

    Karel_H = ASTNode('run', None, [
        ASTNode('while', 'bool_no_path_ahead', [
            ASTNode('if', 'bool_marker', [
                ASTNode('do', 'bool_marker', [ASTNode('pick_marker')])
            ]),
            ASTNode('turn_left'), ASTNode('move'), ASTNode('turn_right'), ASTNode('move')
        ]),
        ASTNode('pick_marker')
    ])

    karel_h_json = Karel_H.to_json()
    print("Karel_H:", karel_h_json)

    return Karel_H



