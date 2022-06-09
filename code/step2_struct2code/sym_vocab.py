from z3 import *

class SymVocab:
    # HoC
    hocrepeat = {1: 'repeat(2)', 2: 'repeat(3)', 3: 'repeat(4)', 4: 'repeat(5)',
                 5: 'repeat(6)',
                 6: 'repeat(7)',
                 7: 'repeat(8)', 8: 'repeat(9)'}
    hocrepeatuntil = {1: 'while(bool_goal)'}
    hocconditional = {1: 'if(bool_path_ahead)', 2: 'if(bool_path_left)', 3: 'if(bool_path_right)'}  # 4:isMarker
    hocaction = {1: 'move', 2: 'turn_left', 3: 'turn_right', 4:'phi'}

    # Karel
    karelrepeat = {1: 'repeat(2)', 2: 'repeat(3)', 3: 'repeat(4)', 4: 'repeat(5)',
                   5: 'repeat(6)',
                   6: 'repeat(7)',
                   7: 'repeat(8)', 8: 'repeat(9)'}
    karelwhile = {1: 'while(bool_path_ahead)', 2: 'while(bool_path_left)',
          3: 'while(bool_path_right)', 4: 'while(bool_marker)', 5: 'while(bool_no_marker)', 6:'while(bool_no_path_ahead)', 7:'while(bool_no_path_left)', 8:'while(bool_no_path_right)'}
    karelconditional = {1: 'if(bool_path_ahead)', 2: 'if(bool_path_left)',
          3: 'if(bool_path_right)', 4: 'if(bool_marker)', 5: 'if(bool_no_marker)', 6: 'if(bool_no_path_ahead)', 7:'if(bool_no_path_left)', 8:'if(bool_no_path_right)'}
    karelaction = {1: 'move', 2: 'turn_left', 3: 'turn_right', 4: 'pick_marker', 5: 'put_marker', 6:'phi'}


def get_vocabT(name):
    return name.split('-')[0]


def get_attr():
    return {x: getattr(SymVocab, x) for x in dir(SymVocab) if not x.startswith("__")}





# Define variables
class Var:
    def __init__(self, name, fixed_vals=None):
        self.name = name
        self.vocabT = self.name.split('-')[0]
        self.vocabs = get_attr()
        self.decoder = self.vocabs[self.vocabT]  # Value to program
        self.range = list(self.decoder.keys())
        self.var = z3.Int(self.name)
        if fixed_vals is None:
            fixed_vals = []
        self.fixed_vals = fixed_vals

    def decode(self, model):
        try:
            val = model[self.var].as_long()
        except:
            print(model)
            exit(0)
        return self.decoder[val]

    def __str__(self):
        return self.name