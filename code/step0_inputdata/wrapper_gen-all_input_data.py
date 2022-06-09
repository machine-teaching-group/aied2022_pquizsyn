from code.step0_inputdata.gen_input_task0 import get_all_data_for_task as get_all_data_for_task0
from code.step0_inputdata.gen_input_task1 import get_all_data_for_task as get_all_data_for_task1
from code.step0_inputdata.gen_input_task2 import get_all_data_for_task as get_all_data_for_task2
from code.step0_inputdata.gen_input_task3 import get_all_data_for_task as get_all_data_for_task3
from code.step0_inputdata.gen_input_task4 import get_all_data_for_task as get_all_data_for_task4
from code.step0_inputdata.gen_input_task5 import get_all_data_for_task as get_all_data_for_task5
from code.step0_inputdata.gen_input_task6 import get_all_data_for_task as get_all_data_for_task6


task_func_dict = {
    '0': 'get_all_data_for_task0',
    '1': 'get_all_data_for_task1',
    '2': 'get_all_data_for_task2',
    '3': 'get_all_data_for_task3',
    '4': 'get_all_data_for_task4',
    '5': 'get_all_data_for_task5',
    '6': 'get_all_data_for_task6'
}

if __name__ == "__main__":
    inputfolder = "data/input/"
    task_ids = ['0', '1', '2', '3', '4', '5', '6']
    for tid in task_ids:
        taskfolder = 'task-'+ str(tid) +'/'
        foldername = inputfolder + taskfolder
        eval(task_func_dict[tid])(foldername)

