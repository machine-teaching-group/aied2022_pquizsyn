import json
import os
import sys
import collections
sys.path.append("..")
from code.utils.ast import ASTNode as ASTNode
from code.utils.sketch import SketchNode as SketchNode
from code.utils.sketch import json_to_sketch as json_to_sketch
from code.utils.sketch import sketch_to_json as sketch_to_json
from code.utils.sketch import generate_neighbors as generate_neighbors
from code.utils.sketch import generate_unique_neighbors as generate_unique_neighbors
from code.utils.sketch import tree_edit_distance as tree_edit_distance
from code.utils.sketch import with_deleted_node as with_deleted_node
from code.utils.code2sketch import GenerateSketch as GenerateSketch


def get_sketch_same(stu_sketch: SketchNode, solu_sketch: SketchNode, type='karel'):

    return solu_sketch