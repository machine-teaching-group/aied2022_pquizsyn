import json
import os
from code.utils.gen_task_image import gen_task_script





def gen_output_images(task_id, student_id, alg_id, outputfolder, inputfolder = '../../data/temp/'):


    output_path = outputfolder + 'task-' + task_id + '/student-' + student_id + '/alg-' + alg_id + '/'
    taskfile = output_path + 'task.txt'
    task_script = gen_task_script(taskfile)
    with open(inputfolder + 'task.tex', 'w') as fp:
        fp.write("%s" % task_script)

    # generate the image file
    input_path = inputfolder + 'task.tex'
    os.system("pdflatex -interaction=nonstopmode -output-directory ../../data/temp %s" % (input_path))
    output_path = output_path + 'task.jpg'
    os.system("convert -density 1200 -quality 100 ../../data/temp/task.pdf %s" % output_path)

    print("Generated task image")
    return 0



