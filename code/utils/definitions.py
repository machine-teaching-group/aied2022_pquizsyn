import enum


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

class SketchNodeType(enum.IntEnum):
    RUN = 1
    Y = 2
    S = 3
    G = 4
    A = 5
    S_S = 6
    S_G = 7

    IF_ONLY = 8
    IF_ELSE = 9
    REPEAT = 10
    WHILE = 11

    IF = 12
    ELSE = 13

    BOOL_COND = 14
    REPEAT_PARAM = 15

    PHI = 16


node_str_to_sketch_type = {

    'run': SketchNodeType.RUN,
    'Y': SketchNodeType.Y,
    'S': SketchNodeType.S,
    'A': SketchNodeType.A,
    'S;S': SketchNodeType.S_S,
    'S;G': SketchNodeType.S_G,
    'repeat_until_goal': SketchNodeType.G,
    'while': SketchNodeType.WHILE,
    'repeat': SketchNodeType.REPEAT,
    'if_only': SketchNodeType.IF_ONLY,
    'if_else': SketchNodeType.IF_ELSE,
    'do': SketchNodeType.IF,
    'else': SketchNodeType.ELSE,
    'bool_cond': SketchNodeType.BOOL_COND,
    'X': SketchNodeType.REPEAT_PARAM,
    'phi': SketchNodeType.PHI
}


node_type_to_sketch = {

    NodeType.RUN: 'run',
    NodeType.WHILE:'while',
    NodeType.REPEAT: 'repeat',
    NodeType.REPEAT_UNTIL_GOAL: 'repeat_until_goal',
    NodeType.IF_ELSE: 'if_else',
    NodeType.IF_ONLY: 'if_only',
    NodeType.IF: 'do',
    NodeType.ELSE: 'else',
    NodeType.MOVE_FORWARD: 'A',
    NodeType.TURN_LEFT: 'A',
    NodeType.TURN_RIGHT: 'A',
    NodeType.PICK_MARKER: 'A',
    NodeType.PUT_MARKER: 'A'

}

sketchnode_to_astnode = {

    'run': 'run',

    'if_else': 'ifelse',
    'if_only': 'if',
    'do': 'do',
    'else': 'else',
    'while': 'while',
    'repeat_until_goal': 'repeat_until_goal',
    'repeat': 'repeat',

    'move': 'move',
    'turn_left': 'turn_left',
    'turn_right': 'turn_right',
    'pick_marker': 'pick_marker',
    'put_marker': 'put_marker',

    # these are kept for completeness: ideally should not encounter these
    'S;S': 'S;S',
    'S': 'S'
}