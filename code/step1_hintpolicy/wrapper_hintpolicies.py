import json
import os
from code.utils.gen_code_image import get_full_latex_script
from code.utils.sketch import json_to_sketch as json_to_sketch
from code.utils.sketch import sketch_to_json as sketch_to_json
from code.step1_hintpolicy.hintpolicy_struct_hop import get_sketch_one_hop as get_sketch_one_hop
from code.step1_hintpolicy.hintpolicy_struct_multihop import get_sketch_multihop_2 as get_sketch_multihop_2
from code.step1_hintpolicy.hintpolicy_struct_gcs import get_sketch_gcs as get_sketch_gcs
from code.step1_hintpolicy.hintpolicy_struct_same import get_sketch_same as get_sketch_same



alg_func_dict = {
    'same-0': 'get_sketch_same',
    'same-2': 'get_sketch_same',
    'hop-0': 'get_sketch_one_hop',
    'hop-2': 'get_sketch_one_hop',
    'ours-0': 'get_sketch_multihop_2',
    'ours-2': 'get_sketch_multihop_2',
    'reduced-code': 'get_sketch_multihop_2'
}

def gen_struct_images(structfile, outputfolder, inputfolder = '../../data/temp/'):

    struct_script = get_full_latex_script(structfile)
    with open(inputfolder + 'code_struct.tex', 'w') as fp:
        fp.write("%s" % struct_script)

    # generate the image file
    input_path = inputfolder + 'code_struct.tex'
    os.system("pdflatex -interaction=nonstopmode -output-directory ../../data/temp %s" % (input_path))
    output_path = outputfolder + 'code_struct.jpg'
    os.system("convert -density 600 -quality 100 ../../data/temp/code_struct.pdf %s" % output_path)

    print("Generated sketch hint image")
    return




def get_sketch_hint(task_id, student_id, alg_id, inputfolder, outputfolder, save_image = False):
    with open(inputfolder+'task-'+task_id+'/student-'+student_id+'_struct.json', 'r') as fp:
        stusketch_json = json.load(fp)
    stusketch = json_to_sketch(stusketch_json)
    with open(inputfolder+'task-'+task_id+'/code_struct.json', 'r') as fp:
        solsketch_json = json.load(fp)
    solsketch = json_to_sketch(solsketch_json)

    if task_id == '4' or task_id == '5':
        type = 'karel'
    else:
        type = 'hoc'

    outputpath = outputfolder + 'task-' + task_id + '/student-' + student_id + '/alg-' + alg_id + '/'
    sketch_hint = eval(alg_func_dict[alg_id])(stusketch, solsketch, type)
    sketch_hint_json = sketch_to_json(sketch_hint)

    with open(outputpath + 'code_struct.json', 'w', encoding='utf-8') as fp:
        json.dump(sketch_hint_json, fp, ensure_ascii=False, indent=4)
    print("Saved sketch-hint for task-" + task_id + " student-" + student_id + " alg-" + alg_id)
    #print(sketch_hint)
    if save_image:
        gen_struct_images(outputpath + 'code_struct.json', outputpath)



    return sketch_hint


