"""
conftest.py needed for pytest to detect files.
This also contains helper methods for running tests or autograders.
"""
import os
import argparse
from code.step3_code2task.github_stanfordkarel.stanfordkarel.karel_application import StudentCode
from code.step3_code2task.github_stanfordkarel.stanfordkarel.karel_program import KarelProgram
from code.step3_code2task.github_stanfordkarel.stanfordkarel.karel_world import KarelWorld
from code.step3_code2task.utils.parser import convert_json_to_python, convert_task_to_world,  convert_world_to_grid
import signal
from contextlib import contextmanager

class TimeoutException(Exception): pass

@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)




def solves_karel_task(code_file:str, starting_task_file:str, final_task_file:str, type='hoc')->bool:

    # get the python module name from the python code file
    module_name = os.path.basename(code_file)
    if module_name.endswith(".py"):
        module_name = os.path.splitext(module_name)[0]
    karel = KarelProgram(starting_task_file, type)
    # print(karel)
    test_code = StudentCode(code_file)
    test_code.inject_namespace(karel)

    # run the test code on the starting Karel World
    try:
        with time_limit(100): # time-limit set for codes that might run in an infinite loop
            _ = test_code.mod.main()
    except:
        return False

    try:
        assert karel.compare_with(
        KarelProgram(final_task_file, type)
    ), "Resulting world did not match expected result."

    except:
        return False

    return karel.compare_with(
        KarelProgram(final_task_file, type)
    )







def execute_karel_code(code_file: str, task_file:str, testcase_num:int, type:str, outputid:str, outputfolder:str, temp_outputfolder:str) -> bool:

    # taskfilename = task_file.split('/')
    # taskfilename = taskfilename[-1].split('.')[0]

    module_name = os.path.basename(code_file)
    if module_name.endswith(".py"):
        module_name = os.path.splitext(module_name)[0]
    karel = KarelProgram(task_file, type)
    start_karel_world = KarelWorld(task_file)
    student_code = StudentCode(code_file)
    student_code.inject_namespace(karel)
    try:
        with time_limit(100):
            _ = student_code.mod.main()  # type: ignore
    except:
        f = open(os.path.join(temp_outputfolder,  outputid + "_output_cur_" + str(testcase_num)+ ".w"), "w")
        f.write("Karel Crashed!")
        f.close()
        fp = open(os.path.join(outputfolder,  outputid + "_output_cur_" + str(testcase_num)+ ".txt"), "w")
        fp.write("Karel Crashed!")
        fp.close()
        return False

    # save the world file
    karel.world.save_to_file(os.path.join(temp_outputfolder,  outputid + "_output_cur_" + str(testcase_num)+ ".w"))
    # save the student output
    karel.world.karel_start_location = (karel.avenue, karel.street)
    karel.world.karel_start_direction = karel.direction
    convert_world_to_grid(start_karel_world, karel.world, outputid+"_output_cur_"+str(testcase_num), type, outputfolder)

    end_world = task_file[:-6]
    try:
        assert karel.compare_with(
        KarelProgram(end_world+"_post.w", type)
    ), "Resulting world did not match expected result."

    except:
        print("Failed on testcase:", task_file)
        return False

    return karel.compare_with(
        KarelProgram(end_world+"_post.w", type)
    )


# def create_solution_worlds() -> None:
#     for problem_name in PROBLEMS:
#         karel = KarelProgram(problem_name)
#         student_code = StudentCode(problem_name)
#         student_code.inject_namespace(karel)
#         student_code.mod.main()  # type: ignore
#         karel.world.save_to_file(os.path.join("full_code/code/worlds", problem_name + "_end.w"))


class Testcases:

    def __init__(self, type:str, codefile:str, testtasks: list, outputid:str, outputfolder:str, temp_outputfolder:str):
        self.type = type
        self.outputid = outputid
        self.outputfolder = outputfolder
        self.temp_outputfolder = temp_outputfolder
        self.student_code_file = codefile
        self.testcases = testtasks # list of tuples with input world files and their output world files

    def run_testcases(self):
        i = 0
        testcase_flags = []
        testcases_all = []
        for ele in self.testcases:
            i += 1
            task_name = ele[0].split('/')
            task_name = task_name[-1]
            task_name = task_name.split('.')
            task_name = task_name[0]
            flag = execute_karel_code(self.student_code_file, ele[0], i, self.type, self.outputid, self.outputfolder, self.temp_outputfolder)
            if flag == False:
                testcase_flags.append((False, task_name))
                testcases_all.append(False)
            else:
                testcase_flags.append((True, task_name))
                testcases_all.append(True)

        if all(testcases_all):
            print("Passed all testcases!")
        else:
            print("Some testcases failed. Check the status file.")

        return testcase_flags


def main():

    arg_parser = argparse.ArgumentParser()
    # arg_parser.add_argument('--input_task_start', type=str, required=True,
    #                         help='input task file start')
    # arg_parser.add_argument('--input_task_end', type=str, required=True, help='input task file end')
    arg_parser.add_argument('--type', type=str, required=True,
                            help='Type of task: hoc/karel')
    arg_parser.add_argument('--input_code_file', type=str, required=True,
                            help='filename of python code')
    arg_parser.add_argument('--input_tasks', action='store', dest='tasklist',
                        type=str, nargs='*', required = True,
                        help="Examples: -input_tasks task1 task2 task3")
    arg_parser.add_argument('--output_id', type=str, default='output_id', help='Output ID of generated tasks.')
    arg_parser.add_argument('--output_folder', type=str, default='', help='Output Folder of generated tasks.')



    args = arg_parser.parse_args()
    directory = args.output_folder + 'output/'
    if not os.path.exists(directory):
        os.makedirs(directory)
    temp_dir = args.output_folder + 'output/temp/'
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    _ = convert_json_to_python(args.input_code_file, temp_dir, args.output_id)
    # codefile = args.input_code_file.split('/')
    # codefile = codefile[-1].split('.')[0]
    python_codefile = temp_dir +args.output_id + '_input.py'
    test_tasks = args.tasklist


    ## create the world files for each of the input tasks
    test_worlds = []
    for i in range(len(test_tasks)):
        test_tuple = convert_task_to_world(test_tasks[i], temp_dir)
        test_worlds.append(test_tuple)

    ## run testcases
    testcases_obj = Testcases(args.type, python_codefile,
                              test_worlds, args.output_id, directory, temp_dir)
    testcase_flag = testcases_obj.run_testcases()
    count_succ = 0
    count_fail = 0
    for i in testcase_flag:
        if i[0] == True:
            count_succ += 1
        else:
            count_fail += 1

    # save the list in a status file
    f = open(directory+ args.output_id + "_output_status.txt", 'w')
    f.write("Total Testcases:\t" + str(len(test_tasks)) + "\n")
    f.write("Passed:\t" + str(count_succ)+ "\n")
    f.write("Failed:\t" + str(count_fail)+ "\n")
    f.write("-----------------------------------\n")
    f.write("Testcase-ID\tStatus\n")
    for i in testcase_flag:
        f.write(i[1] + "\t")
        if i[0] == True:
            f.write("Passed\n")
        else:
            f.write("Failed\n")


    # print(testcase_flag)
    f.close()
    return testcase_flag



if __name__ == "__main__":
    main()

