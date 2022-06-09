from z3 import *
import itertools
from code.step2_struct2code.sym_ast import AST, get_consecutive_action_nodes
from code.step2_struct2code.sym_vocab import Var, get_vocabT


def get_vars(variables):
    # Create Z3 vars
    X = [Var(n[0], fixed_vals=n[1]) # Pass name, and its vocab-type
        for n in variables if '-' in n[0]]
    vars_map = {x.name:x for x in X}
    return X, vars_map

def get_valuesC(X):
    '''Add Range of values as constraints (ORed)'''
    values_c = []
    for x in X:
        if len(x.fixed_vals) != 0:
            constraint = [x.var == val for val in x.fixed_vals]
        else:
            constraint = [x.var == val for val in x.range]
        values_c.append(constraint)
    # remove the empty lists
    filtered_val_c = []
    for ele in values_c:
        if len(ele) != 0:
            filtered_val_c.append(ele)
    all_values = [z3.Or(e) for e in filtered_val_c]
    return all_values


def get_fwdC(ast, vars_map):
    '''Search for repeat/while blocks. If exist, atleast one action should be moveForward'''
    fwds_c = []
    if ast.check_loop():  # If current block is loop
        names_a = [name for name in ast.get_names() if get_vocabT(name) in ['hocaction', 'karelaction']]  # Fetch all actions
        vars_a = [vars_map[name] for name in vars_map if name in names_a]  # Map to actual vars
        constraint = z3.Or([x.var == 1 for x in vars_a])
        fwds_c.append(constraint)  # Add constraints

    for child in ast.children:  # Else, search in children
        fwds_c.extend(get_fwdC(child, vars_map))

    return fwds_c

def get_condC_ajs(ai, ai_val, ajs):
    '''ai does the Action related to xc, provided previous ajs don't counter it before'''
    #### if ai_val in [5, 6, 7, 8], the base cases change as these conditions are negative (no_path/no_marker)
    if ai_val == 6: # no_path_ahead
        baseC = ai.var != 1
    elif ai_val == 7: # no_path_left
        baseC = ai.var != 2
    elif ai_val == 8: # no_path_right
        baseC = ai.var != 3
    elif ai_val == 5: # no_marker
        baseC = ai.var != 4
    else:
        baseC = ai.var == ai_val # for all positive conditionals [1,2,3,4] --> heavily dependent on SYM_VOCAB

    negC = None
    if ai_val == 1:  # fwd => no left/right
        negC = z3.And([z3.And([aj.var != 2, aj.var != 3]) for aj in ajs])
    elif ai_val == 2:  # left => no fwd/right
        negC = z3.And([z3.And([aj.var != 1, aj.var != 3]) for aj in ajs])
    elif ai_val == 3:  # right => no fwd/left
        negC = z3.And([z3.And([aj.var != 1, aj.var != 2]) for aj in ajs])
    elif ai_val == 4:  # isMarker => no fwd/put-marker
        negC = z3.And([z3.And([aj.var != 1, aj.var != 5]) for aj in ajs])
    elif ai_val == 5:  # noMarker => no fwd/pick-marker
        negC = z3.And([z3.Or([aj.var != 1, aj.var != 4]) for aj in ajs])
    ##TODO: Double Check constraints for conditions no-fwd, no-left, no-right -- it is working, but might want to verify the corner cases
    elif ai_val == 6: # no-fwd => left/right
        negC = z3.Or([z3.Or([aj.var == 2, aj.var == 3]) for aj in ajs])
    elif ai_val == 7: # no-left => move/right
        negC = z3.Or([z3.Or([aj.var == 1, aj.var == 3]) for aj in ajs])
    elif ai_val == 8: # no-right => move/left
        negC = z3.Or([z3.Or([aj.var == 1, aj.var == 3]) for aj in ajs])

    if len(ajs) == 0 or negC is None:
        return baseC
    return z3.And(baseC, negC)



def get_condC_ajs_alt(xc, ai, ai_val, ajs, vars_a):
    '''ai does the Action related to xc, provided previous ajs don't counter it before'''
    #### if ai_val in [5, 6, 7, 8], the base cases change as these conditions are negative (no_path/no_marker)
    if ai_val == 6: # no_path_ahead
        baseC = z3.Implies(xc.var == 6, ai.var != 1)
    elif ai_val == 7: # no_path_left
        baseC = z3.Implies(xc.var == 7, ai.var != 2)
    elif ai_val == 8: # no_path_right
        baseC = z3.Implies(xc.var == 8, ai.var != 3)
    else:
        baseC = z3.Implies(xc.var == ai_val, z3.Or([ele.var == ai_val for ele in vars_a])) # for all positive conditionals [1,2,3,4] --> heavily dependent on SYM_VOCAB

    negC = None
    if ai_val == 1:  # fwd => no left/right
        negC_1 = z3.And([xc.var == 1, ai.var == 1])
        negC_1 = z3.And(negC_1, z3.And([aj.var != 1 for aj in ajs]))
        negC_2 = z3.And([z3.And([aj.var !=2, aj.var != 3]) for aj in ajs])
        negC = z3.Implies(negC_1, negC_2)
    elif ai_val == 2:  # left => no fwd/right
        negC_1 = z3.And([xc.var == 2, ai.var == 2])
        negC_1 = z3.And(negC_1, z3.And([aj.var != 2 for aj in ajs]))
        if len(ajs) > 0:
            negC_2 = z3.And([z3.And([aj.var !=1, aj.var != 3]) for aj in ajs])
        else:
            negC_2 = True

        negC = z3.Implies(negC_1, negC_2)
    elif ai_val == 3:  # right => no fwd/left
        negC_1 = z3.And([xc.var == 3, ai.var == 3])
        negC_1 = z3.And(negC_1, z3.And([aj.var != 3 for aj in ajs]))
        if len(ajs) >0:
            negC_2 = z3.And([z3.And([aj.var !=1, aj.var != 2]) for aj in ajs])
        else:
            negC_2 = True
        negC = z3.Implies(negC_1, negC_2)
    ##TODO: Double Check constraints for conditions no-fwd, no-left, no-right -- it is working, but might want to verify the corner cases
    elif ai_val == 6: # no-fwd => left/right
        negC_1 = z3.And([xc.var == 6, ai.var == 1])
        negC_1 = z3.And(negC_1, z3.And([aj.var != 1 for aj in ajs]))
        if len(ajs) > 0:
            negC_2 = z3.Or([z3.Or([aj.var == 2, aj.var == 3]) for aj in ajs])
        else:
            negC_2 = True
        negC = z3.Implies(negC_1, negC_2)
    elif ai_val == 7: # no-left => move/right
        negC_1 = z3.And([xc.var == 7, ai.var == 2])
        negC_1 = z3.And(negC_1, z3.And([aj.var != 2 for aj in ajs]))
        if len(ajs) > 0:
            negC_2 = z3.Or([z3.Or([aj.var == 1, aj.var == 3]) for aj in ajs])
        else:
            negC_2 = True
        negC = z3.Implies(negC_1, negC_2)
    elif ai_val == 8: # no-right => move/left
        negC_1 = z3.And([xc.var == 8, ai.var == 3])
        negC_1 = z3.And(negC_1, z3.And([aj.var != 3 for aj in ajs]))
        if len(ajs) > 0:
            negC_2 = z3.Or([z3.Or([aj.var == 1, aj.var == 2]) for aj in ajs])
        else:
            negC_2 = True
        negC = z3.Implies(negC_1, negC_2)


    if len(ajs) == 0 or negC is None:
        return baseC

    # return z3.And(baseC, negC)
    return negC




def get_markerCondc(xc, ai, ai_val, ajs):
    '''Only for marker conditionals: bool_no_marker, bool_marker'''
    if ai_val == 4: # bool_marker
        baseC = z3.Implies(xc.var == 4, ai.var != 5)
    elif ai_val == 5: # bool_no_marker
        baseC = z3.Implies(xc.var == 5, ai.var != 4)
    else:
        print("Incorrect value encountered in marker conditionals")
        exit(0)

    negC = None
    if ai_val == 4: # bool_marker
        if len(ajs) >0:
            neg1 = z3.And([aj.var != 5 for aj in ajs])
            neg1 = z3.And(xc.var == 4, ai.var == 5, neg1)
            neg2 = z3.Or([z3.Or([aj.var ==1, aj.var ==4]) for aj in ajs])
            negC = z3.Implies(neg1, neg2)
        else:
            negC = True
    elif ai_val == 5: # bool_no_marker
        if len(ajs) >0:
            neg1 = z3.And([aj.var != 4 for aj in ajs])
            neg1 = z3.And(xc.var == 5, ai.var == 4, neg1)
            neg2 = z3.Or([z3.Or([aj.var == 1, aj.var == 5]) for aj in ajs])
            negC = z3.Implies(neg1, neg2)
        else:
            negC = True

    if len(ajs) == 0 or negC is None:
        return baseC

    return negC


def get_markerCondc_else(xc, ai, ai_val, ajs):
    '''Only for marker conditionals: bool_no_marker, bool_marker'''
    if ai_val == 4: # bool_marker
        baseC = z3.Implies(xc.var == 4, ai.var != 4)
    elif ai_val == 5: # bool_no_marker
        baseC = z3.Implies(xc.var == 5, ai.var != 5)
    else:
        print("Incorrect value encountered in marker conditionals")
        exit(0)

    negC = None
    if ai_val == 4: # bool_marker
        if len(ajs) >0:
            neg1 = z3.And([aj.var != 4 for aj in ajs])
            neg1 = z3.And(xc.var == 4, ai.var == 4, neg1)
            neg2 = z3.Or([z3.Or([aj.var ==1, aj.var ==5]) for aj in ajs])
            negC = z3.Implies(neg1, neg2)
        else:
            negC = True
    elif ai_val == 5: # bool_no_marker
        if len(ajs) > 0:
            neg1 = z3.And([aj.var != 5 for aj in ajs])
            neg1 = z3.And(xc.var == 5, ai.var == 5, neg1)
            neg2 = z3.Or([z3.Or([aj.var == 1, aj.var == 4]) for aj in ajs])
            negC = z3.Implies(neg1, neg2)
        else:
            negC = True

    if len(ajs) == 0 or negC is None:
        return baseC

    return negC



def get_condC_action(xc, ai, ajs, vars_a, fixed_vals):
    if len(fixed_vals) == 0:
        cond_vals = [1,2,3,4,5,6,7,8]
    else:
        cond_vals = fixed_vals

    vals_without_markers = cond_vals
    if 4 in cond_vals:
        vals_without_markers.remove(4)
    if 5 in cond_vals:
        vals_without_markers.remove(5)

    constraints =  z3.And([
        z3.Implies(xc.var == val, get_condC_ajs_alt(xc, ai, val, ajs, vars_a))
        for val in vals_without_markers])

    marker_4_cond = True
    if 4 in cond_vals:
        marker_4_cond = get_markerCondc(xc, ai, 4, ajs)

    marker_5_cond = True
    if 5 in cond_vals:
        marker_5_cond = get_markerCondc(xc, ai, 5, ajs)

    constraints_m = z3.And(marker_4_cond, marker_5_cond)
    # print("Constraints M:", marker_4_cond)

    # return constraints_m
    return z3.And([constraints, constraints_m])
    # return constraints


def get_condC_action_alt(xc, ai, ajs, vars_a, fixed_vals):
    if len(fixed_vals) == 0:
        cond_vals = [1,2,3,4,5,6,7,8]
    else:
        cond_vals = copy.deepcopy(fixed_vals)

    vals_without_markers = copy.deepcopy(cond_vals)
    # print(xc.var, vals_without_markers, [ele.var for ele in vars_a])
    if 4 in cond_vals:
        vals_without_markers.remove(4)
    if 5 in cond_vals:
        vals_without_markers.remove(5)

    if len(vals_without_markers) == 0:
        constraints = True
    else:
        constraints =  z3.And([
           get_condC_ajs_alt(xc, ai, val, ajs, vars_a)
            for val in vals_without_markers])

    marker_4_cond = True
    if 4 in cond_vals:
        marker_4_cond = get_markerCondc(xc, ai, 4, ajs)

    marker_5_cond = True
    if 5 in cond_vals:
        marker_5_cond = get_markerCondc(xc, ai, 5, ajs)

    constraints_m = z3.And(marker_4_cond, marker_5_cond)
    # print("Constraints M:", marker_4_cond)

    # return constraints_m
    return z3.And([constraints, constraints_m])
    # return constraints



def get_condC_block(vars_a, xc, fixed_vals):
    # ci->ai, such that 1<=j<i aj != negation(Action[ci])
    conds_c = []
    for i in range(len(vars_a)):
        ai = vars_a[i]
        ajs = vars_a[:i] # variables before ai
        fval = copy.deepcopy(fixed_vals)
        # print("From get_condC_block:", fval)
        implies_c = get_condC_action_alt(xc, ai, ajs, vars_a, fval)
        conds_c.append(implies_c)

    if len(conds_c) == 1:
        return conds_c[0]

    # return z3.Or(conds_c)
    return z3.And(conds_c) # works only for karel task E for now


def get_condC(ast, vars_map):
    '''Search for if-cond (and Karel loop) blocks. If exist, match action to conditional'''
    conds_c = []
    if (ast.check_conditional() or ast.check_karelLoop()):  # If current block is conditional
        xc = vars_map[ast.name]
        fixed_vals = copy.deepcopy(xc.fixed_vals)
        names_a = ast.get_actionChildren()  # current block action
        vars_a = [vars_map[name] for name in names_a]  # Map to actual vars

        # For each action, add OR(c->a1, c->a2)
        # print("From get_condC routine:", fixed_vals)
        conds_c.append(get_condC_block(vars_a, xc, fixed_vals))  # Add constraints

    for child in ast.children:  # Else, search in children
        conds_c.extend(get_condC(child, vars_map))

    return conds_c


def get_elseC_ajs(ai, ai_val, ajs):
    '''If ai does the Action related to xc, ensure previous ajs counter it before'''
    baseC = ai.var != ai_val
    negC = None

    if ai_val == 1:  # fwd => left/right
        negC = z3.Or([z3.Or([aj.var == 2, aj.var == 3]) for aj in ajs])
    elif ai_val == 2:  # left => fwd/right
        negC = z3.Or([z3.Or([aj.var == 1, aj.var == 3]) for aj in ajs])
    elif ai_val == 3:  # right => fwd/left
        negC = z3.Or([z3.Or([aj.var == 1, aj.var == 2]) for aj in ajs])
    elif ai_val == 4:  # isMarker => fwd/put-marker
        negC = z3.Or([z3.Or([aj.var == 1, aj.var == 5]) for aj in ajs])
    elif ai_val == 5:  # noMarker => fwd/pick-marker
        negC = z3.Or([z3.Or([aj.var == 1, aj.var == 4]) for aj in ajs])
    ##TODO: Double Check the constraints for conditions no-fwd, no-left, no-right -- it is working, but might want to verify for corner cases
    if ai_val == 6:  # no-fwd => no left/right
        negC = z3.Or([z3.Or([aj.var != 2, aj.var != 3]) for aj in ajs])
    if ai_val == 7:  # no-left => no move/right
        negC = z3.Or([z3.Or([aj.var != 1, aj.var != 3]) for aj in ajs])
    if ai_val == 8:  # no-right => no move/left
        negC = z3.Or([z3.Or([aj.var != 1, aj.var != 2]) for aj in ajs])


    if len(ajs) == 0 or negC is None:
        return baseC
    return z3.Or(baseC, negC)



def get_elseC_ajs_alt(xc, ai, ai_val, ajs, vars_a):
    '''If ai does the Action related to xc, ensure previous ajs counter it before'''
    if ai_val == 6:  # no_path_ahead
        baseC = z3.Implies(xc.var == ai_val, z3.Or([ele.var == 1 for ele in vars_a]))
    elif ai_val == 7:  # no_path_left
        baseC = z3.Implies(xc.var == ai_val, z3.Or([ele.var == 2 for ele in vars_a]))
    elif ai_val == 8:  # no_path_right
        baseC = z3.Implies(xc.var == ai_val, z3.Or([ele.var == 3 for ele in vars_a]))
    else: # path-ahead, path-left, path-right
        baseC = z3.Implies(xc.var == ai_val, ai.var != ai_val)  # for all positive conditionals [1,2,3,4] --> heavily dependent on SYM_VOCAB

    negC = None

    if ai_val == 1:  # fwd => left/right
        negC_1 = z3.And(xc.var == ai_val, ai.var == 1)
        negC_1 = z3.And(negC_1, z3.And([aj.var != 1 for aj in ajs]))
        if len(ajs) > 0:
            negC_2 = z3.Or([z3.Or([aj.var == 2, aj.var == 3]) for aj in ajs])
        else:
            negC_2 = True
        negC = z3.Implies(negC_1, negC_2)
    elif ai_val == 2:  # left => fwd/right
        negC_1 = z3.And(xc.var == ai_val, ai.var == 2)
        negC_1 = z3.And(negC_1, z3.And([aj.var != 2 for aj in ajs]))
        if len(ajs) > 0:
            negC_2 = z3.Or([z3.Or([aj.var == 1, aj.var == 3]) for aj in ajs])
        else:
            negC_2 = True
        negC = z3.Implies(negC_1, negC_2)
    elif ai_val == 3:  # right => fwd/left
        negC_1 = z3.And(xc.var == ai_val, ai.var == 3)
        negC_1 = z3.And(negC_1, z3.And([aj.var != 3 for aj in ajs]))
        if len(ajs) > 0:
            negC_2 = z3.Or([z3.Or([aj.var == 2, aj.var == 1]) for aj in ajs])
        else:
            negC_2 = True
        negC = z3.Implies(negC_1, negC_2)

    ##TODO: Double Check the constraints for conditions no-fwd, no-left, no-right -- it is working, but might want to verify for corner cases
    elif ai_val == 6:  # no-fwd => no left/right
        negC_1 = z3.And([xc.var == 6, ai.var == 1])
        negC_1 = z3.And(negC_1, z3.And([aj.var != 1 for aj in ajs]))
        negC_2 = z3.And([z3.And([aj.var != 2, aj.var != 3]) for aj in ajs])
        negC = z3.Implies(negC_1, negC_2)
    elif ai_val == 7:  # no-left => no move/right
        negC_1 = z3.And([xc.var == 7, ai.var == 2])
        negC_1 = z3.And(negC_1, z3.And([aj.var != 2 for aj in ajs]))
        negC_2 = z3.And([z3.And([aj.var != 1, aj.var != 3]) for aj in ajs])
        negC = z3.Implies(negC_1, negC_2)
    elif ai_val == 8:  # no-right => no move/left
        negC_1 = z3.And([xc.var == 8, ai.var == 3])
        negC_1 = z3.And(negC_1, z3.And([aj.var != 3 for aj in ajs]))
        negC_2 = z3.And([z3.And([aj.var != 1, aj.var != 2]) for aj in ajs])
        negC = z3.Implies(negC_1, negC_2)


    if len(ajs) == 0 or negC is None:
        return baseC

    return negC


def get_elseC_action(xc, ai, ajs):
    return z3.And([
        z3.Implies(xc.var == val, get_elseC_ajs(ai, val, ajs))
        for val in range(1, 6)])

def get_elseC_action_alt(xc, ai, ajs, vars_a):

        cond_vals = [1, 2, 3, 4, 5, 6, 7, 8]
        vals_without_markers = copy.deepcopy(cond_vals)

        if 4 in cond_vals:
            vals_without_markers.remove(4)
        if 5 in cond_vals:
            vals_without_markers.remove(5)

        constraints = z3.And([
            get_elseC_ajs_alt(xc, ai, val, ajs, vars_a)
            for val in vals_without_markers])

        marker_4_cond = True
        if 4 in cond_vals:
            marker_4_cond = get_markerCondc_else(xc, ai, 4, ajs)

        marker_5_cond = True
        if 5 in cond_vals:
            marker_5_cond = get_markerCondc_else(xc, ai, 5, ajs)

        constraints_m = z3.And(marker_4_cond, marker_5_cond)
        # print("Constraints M:", marker_4_cond)

        # return constraints_m
        return z3.And([constraints, constraints_m])
        # return constraints


def get_elseC_block(vars_a, xc):
    # ci doesn't imply ai. If it does imply, ensure 1<=j<i aj = negation(Action[ci])
    conds_c = []
    for i in range(len(vars_a)):
        ai = vars_a[i]
        ajs = vars_a[:i]
        implies_c = get_elseC_action(xc, ai, ajs)
        conds_c.append(implies_c)

    if len(conds_c) == 1:
        return conds_c[0]

    return z3.And(conds_c)

def get_elseC_block_alt(vars_a, xc):
    # ci doesn't imply ai. If it does imply, ensure 1<=j<i aj = negation(Action[ci])
    conds_c = []
    for i in range(len(vars_a)):
        ai = vars_a[i]
        ajs = vars_a[:i]
        implies_c = get_elseC_action_alt(xc, ai, ajs, vars_a)
        conds_c.append(implies_c)

    if len(conds_c) == 1:
        return conds_c[0]

    return z3.And(conds_c)


def get_elseC(ast, vars_map):
    '''Search for else block. If exist, ensure negation of if(C) actions occur.'''
    else_c = []
    for index in range(len(ast.children)):
        childIf = ast.children[index]

        if childIf.check_conditional():  # If(C) found
            ##TODO: Double Check this part for contraints where actions in if-block do not match that of else -- it is working, but might want to verify with corner cases
            names_if = childIf.get_actionChildren() # if block actions
            vars_if = [vars_map[name] for name in names_if]  # Map to actual vars

            if index + 1 < len(ast.children):  # and sibling exists
                childElse = ast.children[index + 1]

                if childElse.name == 'else':  # and sibling is an else block
                    xc = vars_map[childIf.name]  # Extract original condition
                    names_a = childElse.get_actionChildren()  # and else block actions
                    vars_a = [vars_map[name] for name in names_a]  # Map to actual vars

                    else_c.append(get_elseC_block(vars_a, xc))  # Add the constraint
                    ##TODO: Double Check this part for contraints where actions in if-block do not match that of else -- it is working, but might want to verify with corner cases
                    if len(vars_if) != len(vars_a):
                        continue
                    else: # same number of action children under if and else
                        s = len(vars_if)
                        and_c = [z3.Not(vars_if[i] == vars_a[i]) for i in range(s)]
                        or_c = [z3.Or(and_c)]
                        else_c.extend(or_c)


        else_c.extend(get_elseC(childIf, vars_map))

    return else_c


def get_elseC_alt(ast, vars_map):
    '''Search for else block. If exist, ensure negation of if(C) actions occur.'''
    else_c = []
    for index in range(len(ast.children)):
        childIf = ast.children[index]

        if childIf.check_conditional():  # If(C) found
            ##TODO: Double Check this part for contraints where actions in if-block do not match that of else -- it is working, but might want to verify with corner cases
            names_if = childIf.get_actionChildren() # if block actions
            vars_if = [vars_map[name] for name in names_if]  # Map to actual vars

            if index + 1 < len(ast.children):  # and sibling exists
                childElse = ast.children[index + 1]

                if childElse.name == 'else':  # and sibling is an else block
                    xc = vars_map[childIf.name]  # Extract original condition
                    names_a = childElse.get_actionChildren()  # and else block actions
                    vars_a = [vars_map[name] for name in names_a]  # Map to actual vars

                    else_c.append(get_elseC_block_alt(vars_a, xc))  # Add the constraint
                    ##TODO: Double Check this part for contraints where actions in if-block do not match that of else -- it is working, but might want to verify with corner cases
                    if len(vars_if) != len(vars_a):
                        continue

                    else: # same number of action children under if and else
                        s = len(vars_if)
                        and_c = [z3.Not(vars_if[i] == vars_a[i]) for i in range(s)]
                        or_c = [z3.Or(and_c)]
                        else_c.extend(or_c)


        else_c.extend(get_elseC_alt(childIf, vars_map))

    return else_c



## TODO: Get the actions nested in repeat, and check that same sequence does not occur just outside repeat
def get_repeatC(ast, vars_map):

    repeat_action_const = []
    for index in range(len(ast.children)):
        childrepeat = ast.children[index]
        if childrepeat.check_repeat(): # repeat_node found at index
            # get the siblings of repeat which are action nodes
            siblings = []
            siblings_before = []
            if index-1 >= 0:
                for i in range(0,index):
                    siblings_before.append(ast.children[i])
            if index + 1< len(ast.children):
                for i in range(index+1, len(ast.children)):
                    siblings.append(ast.children[i])

            sibling_names = [s.name for s in siblings]
            sibling_name_types = [s.name_type for s in siblings]
            sibling_names_before = [s.name for s in siblings_before]
            sibling_name_types_before = [s.name_type for s in siblings_before]
            # scan this list to get the first set of action nodes
            indices = []
            # first occurrence of action node
            if len(sibling_name_types) != 0:
                if sibling_name_types[0] in ['hocaction', 'karelaction']:
                    indices.append(0)
                    for j in range(1, len(sibling_name_types)):
                        if sibling_name_types[j] in ['hocaction', 'karelaction']:
                            indices.append(j)
                        else:
                            break
            vars_1 = [sibling_names[i] for i in indices]

            # get the occurrence of action nodes before repeat
            indices_before = []
            if len(sibling_name_types_before) != 0:
                if sibling_name_types_before[-1] in ['hocaction', 'karelaction']:
                    indices_before.append(len(sibling_name_types_before)-1)
                    for j in range(len(sibling_name_types_before)-2, -1, -1):
                        if sibling_name_types_before[j] in ['hocaction', 'karelaction']:
                            indices_before.append(j)
                        else:
                            break
            vars_3 = [sibling_names_before[i] for i in indices_before]

            # check if all children of repeat are only action nodes
            children_repeat = [n.name for n in childrepeat.children]
            children_repeat_types = [n.name_type for n in childrepeat.children]
            flag = True
            for c in children_repeat_types:
                if c in ['hocaction', 'karelaction']:
                    continue
                else:
                    flag = False
                    break
            # all children of repeat are action nodes
            vars_2 = []
            if flag:
                vars_2 = [n for n in children_repeat]

            if len(vars_1) == 0 and len(vars_3) == 0:
                repeat_action_const.extend([])

            # generate the constraints: actions before repeat
            if (len(vars_1) == len(vars_2)) and (len(vars_1)>0) and (len(vars_2)>0):
                and_c = [z3.Not(vars_map[vars_1[i]].var == vars_map[vars_2[i]].var) for i in range(len(vars_1))]
                constr = [z3.Or(and_c)]
                repeat_action_const.extend(constr)
            # generate the constraints: actions after repeat
            if len(vars_3) == len(vars_2) and (len(vars_3)>0) and (len(vars_2)>0):
                and_c = [z3.Not(vars_map[vars_3[i]].var == vars_map[vars_2[i]].var) for i in range(len(vars_3))]
                constr = [z3.Or(and_c)]
                repeat_action_const.extend(constr)


    for child in ast.children:  # Else, search in children
        if len(child.children) != 0:
            repeat_action_const.extend(get_repeatC(child, vars_map))


    return repeat_action_const




## TODO: Get the actions nested in repeat, and check that same sequence does not occur just outside repeat
def get_repeatuntilC(ast, vars_map):

    repeat_action_const = []
    for index in range(len(ast.children)):
        childrepeat = ast.children[index]
        if childrepeat.check_repeatuntil(): # repeat_node found at index
            # get the siblings of repeat which are action nodes
            siblings = []
            siblings_before = []
            if index-1 >= 0:
                for i in range(0,index):
                    siblings_before.append(ast.children[i])
            if index + 1< len(ast.children):
                for i in range(index+1, len(ast.children)):
                    siblings.append(ast.children[i])

            sibling_names = [s.name for s in siblings]
            sibling_name_types = [s.name_type for s in siblings]
            sibling_names_before = [s.name for s in siblings_before]
            sibling_name_types_before = [s.name_type for s in siblings_before]
            # scan this list to get the first set of action nodes
            indices = []
            # first occurrence of action node
            if len(sibling_name_types) != 0:
                if sibling_name_types[0] in ['hocaction', 'karelaction']:
                    indices.append(0)
                    for j in range(1, len(sibling_name_types)):
                        if sibling_name_types[j] in ['hocaction', 'karelaction']:
                            indices.append(j)
                        else:
                            break
            vars_1 = [sibling_names[i] for i in indices] # action nodes after repeat

            # get the occurrence of action nodes before repeat
            indices_before = []
            if len(sibling_name_types_before) != 0:
                if sibling_name_types_before[-1] in ['hocaction', 'karelaction']:
                    indices_before.append(len(sibling_name_types_before)-1)
                    for j in range(len(sibling_name_types_before)-2, -1, -1):
                        if sibling_name_types_before[j] in ['hocaction', 'karelaction']:
                            indices_before.append(j)
                        else:
                            break
            vars_3 = [sibling_names_before[i] for i in indices_before]

            # check if all children of repeat are only action nodes
            children_repeat = [n.name for n in childrepeat.children]
            children_repeat_types = [n.name_type for n in childrepeat.children]
            flag = True
            for c in children_repeat_types:
                if c in ['hocaction', 'karelaction']:
                    continue
                else:
                    flag = False
                    break
            # all children of repeat are action nodes
            vars_2 = []
            if flag:
                vars_2 = [n for n in children_repeat]

            if len(vars_1) == 0 and len(vars_3) == 0:
                repeat_action_const.extend([])

            # generate the constraints: actions before repeat
            if (len(vars_1) == len(vars_2)) and (len(vars_1)>0) and (len(vars_2)>0):
                and_c = [z3.Not(vars_map[vars_1[i]].var == vars_map[vars_2[i]].var) for i in range(len(vars_1))]
                constr = [z3.Or(and_c)]
                repeat_action_const.extend(constr)
            # generate the constraints: actions after repeat
            if len(vars_3) == len(vars_2) and (len(vars_3)>0) and (len(vars_2)>0):
                and_c = [z3.Not(vars_map[vars_3[i]].var == vars_map[vars_2[i]].var) for i in range(len(vars_3))]
                constr = [z3.Or(and_c)]
                repeat_action_const.extend(constr)




    for child in ast.children:  # Else, search in children
        if len(child.children) != 0:
            repeat_action_const.extend(get_repeatC(child, vars_map))


    return repeat_action_const





##TODO: Add function to check that if there are multiple conditionals in the AST, even the conditionals between while and if are not repeated
def get_conditional_seq(ast, vars_map):
    conditional_const_if = []
    conditional_const_while = []
    names_if = ast.get_if_conditionals()
    names_while = ast.get_while_conditionals()
    valid_if_c = []
    valid_while_c = []
    for ele in names_if:
        n = vars_map[ele]
        valid_if_c.append(n.var)
    for ele in names_while:
        n = vars_map[ele]
        valid_while_c.append(n.var)

    if len(valid_if_c) != 0 and len(valid_if_c) != 1:
        valid_if_pair = list(itertools.combinations(valid_if_c, 2))
        constr = [z3.And([ele[0] != ele[1]]) for ele in valid_if_pair]
        conditional_const_if.extend(constr)


    if len(valid_while_c) != 0 and len(valid_while_c) != 1:
        valid_while_pair = list(itertools.combinations(valid_while_c, 2))
        constr = [z3.And([ele[0] != ele[1]]) for ele in valid_while_pair]
        conditional_const_while.extend(constr)

    return conditional_const_if, conditional_const_while



def get_prefix_suffix_betweenC(ast, vars_map, additional_vars:dict, type='hoc'):

    if type == 'hoc':
        phi_val = 4
    else: # type is karel
        phi_val = 6

    prefix_names = additional_vars['prefix']
    prefix_vars = [vars_map[i] for i in prefix_names]
    suffix_names = additional_vars['suffix']
    suffix_vars = [vars_map[i] for i in suffix_names]
    between_names = additional_vars['between']
    between_vars = [vars_map[i] for i in between_names]

    # block level before/after variables
    before_names = []
    all_before_names = additional_vars['before_block']
    for ele in all_before_names:
        before_names.extend(ele)
    before_vars = [vars_map[i] for i in before_names]

    after_names = []
    all_after_names = additional_vars['after_block']
    for ele in all_after_names:
        after_names.extend(ele)
    after_vars = [vars_map[i] for i in after_names]


    all_cons = []
    # only 1 action node in between can be filled
    for ele in between_vars:
        other_between = copy.deepcopy(between_vars)
        for i in other_between:
            if i.name == ele.name:
                other_between.remove(i)
                break
        other_vars = prefix_vars + suffix_vars + other_between + before_vars + after_vars
        constraint = [z3.Implies(ele.var != phi_val, z3.And([j.var == phi_val for j in other_vars]))]
        all_cons.extend(constraint)

    # actions can be added only before/end: of RUN
    or_const_prefix = z3.Or([j.var != phi_val for j in prefix_vars])
    or_const_suff = z3.Or([j.var != phi_val for j in suffix_vars])
    suff_between = suffix_vars + between_vars + before_vars + after_vars
    prefix_between = prefix_vars + between_vars + before_vars + after_vars
    const_prefix = [z3.Implies(or_const_prefix, z3.And([j.var == phi_val for j in suff_between]))]
    const_suff = [z3.Implies(or_const_suff, z3.And([j.var == phi_val for j in prefix_between]))]
    all_cons.extend(const_prefix)
    all_cons.extend(const_suff)

    # actions can added only before and after a block
    # before
    for ele in all_before_names:
        b_vars = [vars_map[i] for i in ele]
        or_const_b = z3.Or([j.var != phi_val for j in b_vars])
        other_before = copy.deepcopy(before_names)
        for t in ele:
            other_before.remove(t)
        other_before_vars = [vars_map[i] for i in other_before]
        other_vars = prefix_vars + suffix_vars + between_vars + other_before_vars + after_vars
        const_b = [z3.Implies(or_const_b, z3.And([j.var == phi_val for j in other_vars]))]
        all_cons.extend(const_b)

    ### After
    for ele in all_after_names:
        b_vars = [vars_map[i] for i in ele]
        or_const_b = z3.Or([j.var != phi_val for j in b_vars])
        other_after = copy.deepcopy(after_names)
        for t in ele:
            other_after.remove(t)
        other_after_vars = [vars_map[i] for i in other_after]
        other_vars = prefix_vars + suffix_vars + between_vars + other_after_vars + before_vars
        const_b = [z3.Implies(or_const_b, z3.And([j.var == phi_val for j in other_vars]))]
        all_cons.extend(const_b)


    return all_cons





## Check for elimination sequences
## TODO: Refector this code to look cleaner so that it is easier to add new elimination sequences
def get_elimination_seq(ast, vars_map):

    elimination_c = []

   # get all the action-node sequences
    all_action_nodes = get_consecutive_action_nodes(ast)


    vars_a = []
    type = all_action_nodes[0][0].split('-')[0]
    for ele in all_action_nodes:
        var_list = []
        for i in ele:
            if i in vars_map:
                var_list.append(vars_map[i])
        vars_a.append(var_list)


    for ele in vars_a:
        if len(ele) == 0 or len(ele) == 1:
            continue

        if len(ele) > 1:
            # left, right
            constraint = [z3.Not(z3.And([ele[i].var == 2, ele[i+1].var == 3])) for i in range(len(ele)-1)]
            elimination_c.extend(constraint)
            constraint = [z3.Not(z3.And([ele[i].var == 3, ele[i + 1].var == 2])) for i in range(len(ele) - 1)]
            elimination_c.extend(constraint)

            if type == 'karelaction':
                # pick_beeper, put_beeper
                constraint = [z3.Not(z3.And([ele[i].var == 4, ele[i + 1].var == 5])) for i in range(len(ele) - 1)]
                elimination_c.extend(constraint)
                constraint = [z3.Not(z3.And([ele[i].var == 5, ele[i + 1].var == 4])) for i in range(len(ele) - 1)]
                elimination_c.extend(constraint)
                # put_beeper, put_beeper
                constraint = [z3.Not(z3.And([ele[i].var == 4, ele[i + 1].var == 4])) for i in range(len(ele) - 1)]
                elimination_c.extend(constraint)
                # pick_beeper, pick_beeper
                constraint = [z3.Not(z3.And([ele[i].var == 5, ele[i + 1].var == 5])) for i in range(len(ele) - 1)]
                elimination_c.extend(constraint)



        if len(ele) > 2: # assumes max length of action block can be 3
            if type == 'hocaction':
                # left, phi, right
                constraint = [z3.Not(z3.And([ele[i].var == 2, ele[i + 1].var == 4, ele[i+2].var == 3])) for i in range(len(ele) - 2)]
                elimination_c.extend(constraint)
                constraint = [z3.Not(z3.And([ele[i].var == 3, ele[i + 1].var == 4, ele[i+2].var == 2])) for i in range(len(ele) - 2)]
                elimination_c.extend(constraint)
                # left, left, left
                constraint = [z3.Not(z3.And([ele[i].var == 2, ele[i + 1].var == 2, ele[i + 2].var == 2])) for i in
                              range(len(ele) - 2)]
                elimination_c.extend(constraint)
                # right, right, right
                constraint = [z3.Not(z3.And([ele[i].var == 3, ele[i + 1].var == 3, ele[i + 2].var == 3])) for i in
                              range(len(ele) - 2)]
                elimination_c.extend(constraint)
            else: #type = karelaction
               constraint = [z3.Not(z3.And([ele[i].var == 2, ele[i + 1].var == 6, ele[i + 2].var == 3])) for i in
                             range(len(ele) - 2)]
               elimination_c.extend(constraint)
               constraint = [z3.Not(z3.And([ele[i].var == 3, ele[i + 1].var == 6, ele[i + 2].var == 2])) for i in
                             range(len(ele) - 2)]
               elimination_c.extend(constraint)
               # left, left, left
               constraint = [z3.Not(z3.And([ele[i].var == 2, ele[i + 1].var == 2, ele[i + 2].var == 2])) for i in
                             range(len(ele) - 2)]
               elimination_c.extend(constraint)
               # right, right, right
               constraint = [z3.Not(z3.And([ele[i].var == 3, ele[i + 1].var == 3, ele[i + 2].var == 3])) for i in
                             range(len(ele) - 2)]
               elimination_c.extend(constraint)
                # pick, phi, put
               constraint = [z3.Not(z3.And([ele[i].var == 4, ele[i + 1].var == 6, ele[i + 2].var == 5])) for i in
                          range(len(ele) - 2)]
               elimination_c.extend(constraint)
               constraint = [z3.Not(z3.And([ele[i].var == 5, ele[i + 1].var == 6, ele[i + 2].var == 4])) for i in
                          range(len(ele) - 2)]
               elimination_c.extend(constraint)
                # pick, left, put
               constraint = [z3.Not(z3.And([ele[i].var == 4, ele[i + 1].var == 2, ele[i + 2].var == 5])) for i in
                             range(len(ele) - 2)]
               elimination_c.extend(constraint)
               constraint = [z3.Not(z3.And([ele[i].var == 5, ele[i + 1].var == 2, ele[i + 2].var == 4])) for i in
                             range(len(ele) - 2)]
               elimination_c.extend(constraint)
                # pick, right, put
               constraint = [z3.Not(z3.And([ele[i].var == 4, ele[i + 1].var == 3, ele[i + 2].var == 5])) for i in
                             range(len(ele) - 2)]
               elimination_c.extend(constraint)
               constraint = [z3.Not(z3.And([ele[i].var == 5, ele[i + 1].var == 3, ele[i + 2].var == 4])) for i in
                             range(len(ele) - 2)]
               elimination_c.extend(constraint)
                # left, pick, right
               constraint = [z3.Not(z3.And([ele[i].var == 3, ele[i + 1].var == 4, ele[i + 2].var == 2])) for i in
                             range(len(ele) - 2)]
               elimination_c.extend(constraint)
               constraint = [z3.Not(z3.And([ele[i].var == 2, ele[i + 1].var == 4, ele[i + 2].var == 3])) for i in
                             range(len(ele) - 2)]
               elimination_c.extend(constraint)
                # left, put, right
               constraint = [z3.Not(z3.And([ele[i].var == 3, ele[i + 1].var == 5, ele[i + 2].var == 2])) for i in
                             range(len(ele) - 2)]
               elimination_c.extend(constraint)
               constraint = [z3.Not(z3.And([ele[i].var == 2, ele[i + 1].var == 5, ele[i + 2].var == 3])) for i in
                             range(len(ele) - 2)]
               elimination_c.extend(constraint)
                # pick, phi, pick
               constraint = [z3.Not(z3.And([ele[i].var == 4, ele[i + 1].var == 6, ele[i + 2].var == 4])) for i in
                             range(len(ele) - 2)]
               elimination_c.extend(constraint)
               # put, phi, put
               constraint = [z3.Not(z3.And([ele[i].var == 5, ele[i + 1].var == 6, ele[i + 2].var == 5])) for i in
                             range(len(ele) - 2)]
               elimination_c.extend(constraint)
               # pick, right, pick
               constraint = [z3.Not(z3.And([ele[i].var == 4, ele[i + 1].var == 3, ele[i + 2].var == 4])) for i in
                             range(len(ele) - 2)]
               elimination_c.extend(constraint)
               # put, right, put
               constraint = [z3.Not(z3.And([ele[i].var == 5, ele[i + 1].var == 3, ele[i + 2].var == 5])) for i in
                             range(len(ele) - 2)]
               elimination_c.extend(constraint)
               # pick, left, pick
               constraint = [z3.Not(z3.And([ele[i].var == 4, ele[i + 1].var == 2, ele[i + 2].var == 4])) for i in
                             range(len(ele) - 2)]
               elimination_c.extend(constraint)
               # put, left, put
               constraint = [z3.Not(z3.And([ele[i].var == 5, ele[i + 1].var == 2, ele[i + 2].var == 5])) for i in
                             range(len(ele) - 2)]
               elimination_c.extend(constraint)


        if len(ele) > 3: # assumes max length of action block can be 4
            if type == 'hocaction':
                # left, phi, phi, right
                constraint = [z3.Not(z3.And([ele[i].var == 2, ele[i + 1].var == 4, ele[i+2].var == 4, ele[i+3].var == 3])) for i in range(len(ele) - 3)]
                elimination_c.extend(constraint)
                constraint = [
                    z3.Not(z3.And([ele[i].var == 3, ele[i + 1].var == 4, ele[i + 2].var == 4, ele[i + 3].var == 2])) for i
                    in range(len(ele) - 3)]
                elimination_c.extend(constraint)

                # left, left, phi, left
                constraint = [
                    z3.Not(z3.And([ele[i].var == 2, ele[i + 1].var == 2, ele[i + 2].var == 4, ele[i + 3].var == 2])) for i
                    in range(len(ele) - 3)]
                elimination_c.extend(constraint)
                # right, right, phi, right
                constraint = [
                    z3.Not(z3.And([ele[i].var == 3, ele[i + 1].var == 3, ele[i + 2].var == 4, ele[i + 3].var == 3])) for i
                    in range(len(ele) - 3)]
                elimination_c.extend(constraint)
                # left, phi, left, left
                constraint = [
                    z3.Not(z3.And([ele[i].var == 2, ele[i + 1].var == 4, ele[i + 2].var == 2, ele[i + 3].var == 2])) for i
                    in range(len(ele) - 3)]
                elimination_c.extend(constraint)
                # right, phi, right, right
                constraint = [
                    z3.Not(z3.And([ele[i].var == 3, ele[i + 1].var == 4, ele[i + 2].var == 3, ele[i + 3].var == 3])) for i
                    in range(len(ele) - 3)]
                elimination_c.extend(constraint)
            else: ###type:karelaction
                # left, phi, phi, right
                constraint = [
                    z3.Not(z3.And([ele[i].var == 2, ele[i + 1].var == 6, ele[i + 2].var == 6, ele[i + 3].var == 3])) for i
                    in range(len(ele) - 3)]
                elimination_c.extend(constraint)
                constraint = [
                    z3.Not(z3.And([ele[i].var == 3, ele[i + 1].var == 6, ele[i + 2].var == 6, ele[i + 3].var == 2])) for i
                    in range(len(ele) - 3)]
                elimination_c.extend(constraint)

                # left, left, phi, left
                constraint = [
                    z3.Not(z3.And([ele[i].var == 2, ele[i + 1].var == 2, ele[i + 2].var == 6, ele[i + 3].var == 2])) for i
                    in range(len(ele) - 3)]
                elimination_c.extend(constraint)
                # right, right, phi, right
                constraint = [
                    z3.Not(z3.And([ele[i].var == 3, ele[i + 1].var == 3, ele[i + 2].var == 6, ele[i + 3].var == 3])) for i
                    in range(len(ele) - 3)]
                elimination_c.extend(constraint)
                # left, phi, left, left
                constraint = [
                    z3.Not(z3.And([ele[i].var == 2, ele[i + 1].var == 6, ele[i + 2].var == 2, ele[i + 3].var == 2])) for i
                    in range(len(ele) - 3)]
                elimination_c.extend(constraint)
                # right, phi, right, right
                constraint = [
                    z3.Not(z3.And([ele[i].var == 3, ele[i + 1].var == 6, ele[i + 2].var == 3, ele[i + 3].var == 3])) for i
                    in range(len(ele) - 3)]
                elimination_c.extend(constraint)

                # add marker related constraints
                #put,left,phi,put
                constraint = [
                    z3.Not(z3.And([ele[i].var == 5, ele[i + 1].var == 2, ele[i + 2].var == 6, ele[i + 3].var == 5])) for i
                    in range(len(ele) - 3)]
                elimination_c.extend(constraint)
                constraint = [
                    z3.Not(z3.And([ele[i].var == 4, ele[i + 1].var == 2, ele[i + 2].var == 6, ele[i + 3].var == 4])) for i
                    in range(len(ele) - 3)]
                elimination_c.extend(constraint)
                # put, phi, left, put
                constraint = [
                    z3.Not(z3.And([ele[i].var == 5, ele[i + 1].var == 6, ele[i + 2].var == 2, ele[i + 3].var == 5])) for i
                    in range(len(ele) - 3)]
                elimination_c.extend(constraint)
                constraint = [
                    z3.Not(z3.And([ele[i].var == 4, ele[i + 1].var == 6, ele[i + 2].var == 2, ele[i + 3].var == 4])) for i
                    in range(len(ele) - 3)]
                elimination_c.extend(constraint)

                # put,right,phi,put
                constraint = [
                    z3.Not(z3.And([ele[i].var == 5, ele[i + 1].var == 3, ele[i + 2].var == 6, ele[i + 3].var == 5])) for i
                    in range(len(ele) - 3)]
                elimination_c.extend(constraint)
                constraint = [
                    z3.Not(z3.And([ele[i].var == 4, ele[i + 1].var == 3, ele[i + 2].var == 6, ele[i + 3].var == 4])) for i
                    in range(len(ele) - 3)]
                elimination_c.extend(constraint)
                # put, phi, right, put
                constraint = [
                    z3.Not(z3.And([ele[i].var == 5, ele[i + 1].var == 6, ele[i + 2].var == 3, ele[i + 3].var == 5])) for i
                    in range(len(ele) - 3)]
                elimination_c.extend(constraint)
                constraint = [
                    z3.Not(z3.And([ele[i].var == 4, ele[i + 1].var == 6, ele[i + 2].var == 3, ele[i + 3].var == 4])) for i
                    in range(len(ele) - 3)]
                elimination_c.extend(constraint)

                # put,left,phi,pick
                constraint = [
                    z3.Not(z3.And([ele[i].var == 5, ele[i + 1].var == 2, ele[i + 2].var == 6, ele[i + 3].var == 4])) for i
                    in range(len(ele) - 3)]
                elimination_c.extend(constraint)
                constraint = [
                    z3.Not(z3.And([ele[i].var == 4, ele[i + 1].var == 2, ele[i + 2].var == 6, ele[i + 3].var == 5])) for i
                    in range(len(ele) - 3)]
                elimination_c.extend(constraint)
                # put, phi, left, pick
                constraint = [
                    z3.Not(z3.And([ele[i].var == 5, ele[i + 1].var == 6, ele[i + 2].var == 2, ele[i + 3].var == 4])) for i
                    in range(len(ele) - 3)]
                elimination_c.extend(constraint)
                constraint = [
                    z3.Not(z3.And([ele[i].var == 4, ele[i + 1].var == 6, ele[i + 2].var == 2, ele[i + 3].var == 5])) for i
                    in range(len(ele) - 3)]
                elimination_c.extend(constraint)

                # put,right,phi,pick
                constraint = [
                    z3.Not(z3.And([ele[i].var == 5, ele[i + 1].var == 3, ele[i + 2].var == 6, ele[i + 3].var == 4])) for i
                    in range(len(ele) - 3)]
                elimination_c.extend(constraint)
                constraint = [
                    z3.Not(z3.And([ele[i].var == 4, ele[i + 1].var == 3, ele[i + 2].var == 6, ele[i + 3].var == 5])) for i
                    in range(len(ele) - 3)]
                elimination_c.extend(constraint)
                # put, phi, right, pick
                constraint = [
                    z3.Not(z3.And([ele[i].var == 5, ele[i + 1].var == 6, ele[i + 2].var == 3, ele[i + 3].var == 4])) for i
                    in range(len(ele) - 3)]
                elimination_c.extend(constraint)
                constraint = [
                    z3.Not(z3.And([ele[i].var == 4, ele[i + 1].var == 6, ele[i + 2].var == 3, ele[i + 3].var == 5])) for i
                    in range(len(ele) - 3)]
                elimination_c.extend(constraint)

                # left, phi, pick, right
                constraint = [
                    z3.Not(z3.And([ele[i].var == 2, ele[i + 1].var == 6, ele[i + 2].var == 4, ele[i + 3].var == 3])) for i
                    in range(len(ele) - 3)]
                elimination_c.extend(constraint)
                constraint = [
                    z3.Not(z3.And([ele[i].var == 3, ele[i + 1].var == 6, ele[i + 2].var == 4, ele[i + 3].var == 2])) for i
                    in range(len(ele) - 3)]
                elimination_c.extend(constraint)

                # left, phi, put, right
                constraint = [
                    z3.Not(z3.And([ele[i].var == 2, ele[i + 1].var == 6, ele[i + 2].var == 5, ele[i + 3].var == 3])) for i
                    in range(len(ele) - 3)]
                elimination_c.extend(constraint)
                constraint = [
                    z3.Not(z3.And([ele[i].var == 3, ele[i + 1].var == 6, ele[i + 2].var == 5, ele[i + 3].var == 2])) for i
                    in range(len(ele) - 3)]
                elimination_c.extend(constraint)

                # left, pick, phi, right
                constraint = [
                    z3.Not(z3.And([ele[i].var == 2, ele[i + 1].var == 4, ele[i + 2].var == 6, ele[i + 3].var == 3])) for i
                    in range(len(ele) - 3)]
                elimination_c.extend(constraint)
                constraint = [
                    z3.Not(z3.And([ele[i].var == 3, ele[i + 1].var == 4, ele[i + 2].var == 6, ele[i + 3].var == 2])) for i
                    in range(len(ele) - 3)]
                elimination_c.extend(constraint)

                # left, put, phi, right
                constraint = [
                    z3.Not(z3.And([ele[i].var == 2, ele[i + 1].var == 5, ele[i + 2].var == 6, ele[i + 3].var == 3])) for i
                    in range(len(ele) - 3)]
                elimination_c.extend(constraint)
                constraint = [
                    z3.Not(z3.And([ele[i].var == 3, ele[i + 1].var == 5, ele[i + 2].var == 6, ele[i + 3].var == 2])) for i
                    in range(len(ele) - 3)]
                elimination_c.extend(constraint)



    return elimination_c
