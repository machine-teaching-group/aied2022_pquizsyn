import enum
from z3 import z3


class VariableType(enum.IntEnum):
    MOVE_FORWARD = 1
    TURN_LEFT = 2
    TURN_RIGHT = 3
    PICK_MARKER = 4
    PUT_MARKER = 5
    PHI = 6
    BOOL_PATH_AHEAD = 7,
    BOOL_PATH_RIGHT = 8,
    BOOL_PATH_LEFT = 9,
    BOOL_MARKER = 10,
    BOOL_NO_MARKER = 11,
    BOOL_NO_PATH_AHEAD = 12,
    BOOL_NO_PATH_LEFT = 13,
    BOOL_NO_PATH_RIGHT = 14,
    IF_ELSE = 15,
    IF_ONLY = 16,
    IF = 17,
    ELSE = 18,
    REPEAT = 19,
    WHILE = 20,
    REPEAT_UNTIL_GOAL = 21
    BOOL_GOAL = 22

class ConditionalType(enum.IntEnum):
    BOOL_PATH_AHEAD = 7,
    BOOL_PATH_RIGHT = 9,
    BOOL_PATH_LEFT = 8,
    BOOL_MARKER = 10,
    BOOL_NO_MARKER = 11,
    BOOL_NO_PATH_AHEAD = 12,
    BOOL_NO_PATH_LEFT = 13,
    BOOL_NO_PATH_RIGHT = 14,




str_to_type = {
    'move': VariableType.MOVE_FORWARD,
    'turn_left': VariableType.TURN_LEFT,
    'turn_right': VariableType.TURN_RIGHT,
    'pick_marker': VariableType.PICK_MARKER,
    'put_marker': VariableType.PUT_MARKER,
    'phi': VariableType.PHI,
    'bool_path_left': ConditionalType.BOOL_PATH_LEFT,
    'bool_path_right': ConditionalType.BOOL_PATH_RIGHT,
    'bool_path_ahead': ConditionalType.BOOL_PATH_AHEAD,
    'bool_goal': VariableType.BOOL_GOAL,
    'bool_no_path_ahead': ConditionalType.BOOL_NO_PATH_AHEAD,
    'bool_no_path_left': ConditionalType.BOOL_NO_PATH_LEFT,
    'bool_no_path_right': ConditionalType.BOOL_NO_PATH_RIGHT,
    'bool_marker': ConditionalType.BOOL_MARKER,
    'bool_no_marker': ConditionalType.BOOL_NO_MARKER,
    'while': VariableType.WHILE,
    'repeat_until_goal': VariableType.REPEAT_UNTIL_GOAL,
    'repeat': VariableType.REPEAT,
    'do': VariableType.IF,
    'else': VariableType.ELSE,
    'if_else': VariableType.IF_ELSE,
    'if_only': VariableType.IF_ONLY


}

type_to_str = {v: k for k, v in str_to_type.items()}



# region: Invoke Z3 solver
def gen_model(solver, X):
    '''Given a Z3 solver instance and set of variables X, return single set of value assignments if SAT.'''
    if solver.check() == z3.sat:  # Satisfiable
        model = solver.model()  # Gen model
        if len(model) == 0:
            print('SAT, but no values returned. Typically occurs when 0 constraints are passed to Z3.')
            return None

        counter_c = z3.Or([x != model[x] for x in X])  # Add counter constraint
        solver.add(counter_c)

        return model

    return None


def gen_all(solver, X):
    '''Given a Z3 solver and the set of free variables X, return all satisfying assignments'''
    values = []

    while True:
        assign = gen_model(solver, X)
        if assign:
            values.append(assign)
        else:
            break

    return values