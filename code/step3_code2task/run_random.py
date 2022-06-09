from __future__ import absolute_import
import time
import os
import argparse
from tqdm import tqdm
from code.step3_code2task.github_stanfordkarel.stanfordkarel.karel_world import Direction as Direction
from code.step3_code2task.symbolic_execution import run_symbolic_execution
from code.step3_code2task.sym_ascii import AsciiSymWorld, display_current_sym_world
from code.step3_code2task.utils.scoring import qual_score, cut_score, dissimilarity_score, coverage_score
from code.step3_code2task.utils.parser import get_dict_from_task, convert_json_to_python
from code.step3_code2task.utils.run_testcases import solves_karel_task




def run_random(type:str, iters:int, code_file:str, jsoncodefile:str, task_dims:dict, outputfolder:str, outputfilename:str, prob_front=0.5, prob_left=0.5, prob_right=0.5, prob_beepers=0.5, init_config_flag=False, init_config_file=''):
    all_runs = []
    start = time.time()
    scores = {}
    for i in tqdm(range(iters)):
        sym_run = run_symbolic_execution(code_file, jsoncodefile, task_dims, prob_front, prob_left, prob_right, prob_beepers, init_config_flag=init_config_flag, init_config_file=init_config_file)
        if sym_run is not None:
            all_runs.append(sym_run)
            start_karel_world = sym_run[0].karel.create_karel_world()
            end_karel_world = sym_run[0].karel.create_karel_world(post_world_flag=True)
            start_karel_world.walls = end_karel_world.walls
            scores[sym_run[0]] = ((0.5 * qual_score(sym_run[0].karel)
                          + 0.5 * dissimilarity_score(sym_run[0].karel.ref_task,sym_run[0].karel, type)
                           ))*coverage_score(sym_run[0])

    # res = list(filter(None, all_runs))
    end = time.time()
    print("\nSymbolic execution Processing time:", end-start)
    # score the trajectories that did not crash
    start = time.time()
    # print(len(res))
    # for ele in res:
    #     start_karel_world = ele[0].karel.create_karel_world()
    #     end_karel_world = ele[0].karel.create_karel_world(post_world_flag=True)
    #     start_karel_world.walls = end_karel_world.walls
    #     scores.append((0.5*qual_score(ele[0].karel) + 0.5*dissimilarity_score(ele[0].karel.ref_task, ele[0].karel))*cut_score(start_karel_world, end_karel_world, ele[0].num_code_blocks))

    # Return the task with no short-cut sequence of actions
    if len(all_runs) == 0:
        print("No valid tasks created.")
        return None, None, None, 0
    sorted_tasks = dict(sorted(scores.items(), key=lambda item: item[1], reverse=True))
    output_task = None
    start_karel_world = None
    end_karel_world = None
    max_score = 0
    short_cut = 0
    print("Checking the cut score of the valid tasks generated...")
    for key, val in tqdm(sorted_tasks.items()):
        start_karel_world = key.karel.create_karel_world()
        end_karel_world = key.karel.create_karel_world(post_world_flag=True)
        start_karel_world.walls = end_karel_world.walls
        short_cut = cut_score(key.karel, start_karel_world, end_karel_world, key.num_code_blocks, key.basic_action_flag, type=type)
        if short_cut == 1:
            output_task = key
            #print("Sym path:", key.karel.karel_seq)
            print("Karel's initial location:", start_karel_world.karel_start_location, start_karel_world.karel_start_direction)
            print("Karel's final location:", end_karel_world.karel_start_location, end_karel_world.karel_start_direction)
            max_score = val
            break

    end= time.time()
    print("Scoring time:", end-start)
    if short_cut == 0:
        print("No valid tasks created.")
        return None, None, None, 0

    if output_task is not None:
        output_task.karel.save_task_grid_to_file(start_karel_world, end_karel_world, end_karel_world.karel_start_location,
                                                 end_karel_world.karel_start_direction, outputfolder, outputfilename)

    return output_task, start_karel_world, end_karel_world, max_score


def run_random_with_quality_only(type:str, iters:int, code_file:str, jsoncodefile:str, task_dims:dict, prob_front=0.5, prob_left=0.5, prob_right=0.5, prob_beepers=0.5, init_config_flag=False, init_config_file='', quality_score_thresh=0.2, verbose=False):
    all_runs = []
    start = time.time()
    scores = {}
    # for i in tqdm(range(iters)):
    for i in range(iters):
        sym_run = run_symbolic_execution(code_file, jsoncodefile, task_dims, prob_front, prob_left, prob_right, prob_beepers, init_config_flag=init_config_flag, init_config_file=init_config_file)
        if sym_run is not None:
            all_runs.append(sym_run)
            start_karel_world = sym_run[0].karel.create_karel_world()
            end_karel_world = sym_run[0].karel.create_karel_world(post_world_flag=True)
            start_karel_world.walls = end_karel_world.walls
            scores[sym_run[0]] = (qual_score(sym_run[0].karel)
                           )*coverage_score(sym_run[0])

    # res = list(filter(None, all_runs))
    end = time.time()
    if verbose:
        print("\nSymbolic execution Processing time:", end-start)
    # score the trajectories that did not crash
    start = time.time()


    # Return the task with no short-cut sequence of actions
    if len(all_runs) == 0:
        # print("No valid tasks created from symbolic gen routine.")
        return None, None, None, 0
    sorted_tasks = dict(sorted(scores.items(), key=lambda item: item[1], reverse=True))
    output_task = None
    start_karel_world = None
    end_karel_world = None
    max_score = 0
    short_cut = 0
    if verbose:
        print("Checking the cut score of the valid tasks generated...")
    # for key, val in tqdm(sorted_tasks.items()):
    for key, val in sorted_tasks.items():
        start_karel_world = key.karel.create_karel_world()
        end_karel_world = key.karel.create_karel_world(post_world_flag=True)
        start_karel_world.walls = end_karel_world.walls
        if val > quality_score_thresh:
            # try:
            short_cut = cut_score(key.karel, start_karel_world, end_karel_world, key.num_code_blocks, key.basic_action_flag, type=type)
            # except:
            #     print(key.karel, start_karel_world.karel_start_location, start_karel_world.karel_start_direction, end_karel_world.karel_start_direction, end_karel_world.karel_start_location)
            #     exit(0)
        else:
            continue
        if short_cut == 1:
            output_task = key
            # print("Sym path:", key.karel.karel_seq)
            # print("Karel's initial location:", start_karel_world.karel_start_location, start_karel_world.karel_start_direction)
            # print("Karel's final location:", end_karel_world.karel_start_location, end_karel_world.karel_start_direction)
            # print("Final task:", key.karel)
            max_score = val
            break



    end= time.time()
    if verbose:
        print("Scoring time:", end-start)
    if short_cut == 0:
        # print("No valid tasks created due to shortcut score.", code_file)
        return None, None, None, 0

    # if output_task is not None:
    #     output_task.karel.save_task_grid_to_file(start_karel_world, end_karel_world, end_karel_world.karel_start_location,
    #                                              end_karel_world.karel_start_direction, outputfolder, outputfilename)

    if output_task.karel.type == 'hoc':
        output_task.karel.direction = Direction.UNK
        end_karel_world.karel_start_direction = Direction.UNK


    return output_task, start_karel_world, end_karel_world, max_score



def run_random_with_quality_only_no_shortcut(type:str, iters:int, code_file:str, jsoncodefile:str, task_dims:dict, prob_front=0.5, prob_left=0.5, prob_right=0.5, prob_beepers=0.5, init_config_flag=False, init_config_file='', quality_score_thresh=0, verbose=False):
    all_runs = []
    start = time.time()
    scores = {}
    for i in range(iters):
        sym_run = run_symbolic_execution(code_file, jsoncodefile, task_dims, prob_front, prob_left, prob_right, prob_beepers, init_config_flag=init_config_flag, init_config_file=init_config_file)
        if sym_run is not None:
            all_runs.append(sym_run)
            start_karel_world = sym_run[0].karel.create_karel_world()
            end_karel_world = sym_run[0].karel.create_karel_world(post_world_flag=True)
            start_karel_world.walls = end_karel_world.walls
            scores[sym_run[0]] = qual_score(sym_run[0].karel)

    end = time.time()
    if verbose:
        print("\nSymbolic execution Processing time:", end-start)

    # Return the task with no short-cut sequence of actions
    if len(all_runs) == 0:
        # print("No valid tasks created.")
        return None, None, None, 0
    sorted_tasks = dict(sorted(scores.items(), key=lambda item: item[1], reverse=True))
    output_task = None
    start_karel_world = None
    end_karel_world = None
    max_score = 0
    if verbose:
        print("Checking the cut score of the valid tasks generated...")
    # for key, val in tqdm(sorted_tasks.items()):
    for key, val in sorted_tasks.items():
        start_karel_world = key.karel.create_karel_world()
        end_karel_world = key.karel.create_karel_world(post_world_flag=True)
        start_karel_world.walls = end_karel_world.walls
        if val > quality_score_thresh:
            output_task = key
            max_score = val
            break
        else:
            continue

    if output_task.karel.type == 'hoc':
        output_task.karel.direction = Direction.UNK
        end_karel_world.karel_start_direction = Direction.UNK

    return output_task, start_karel_world, end_karel_world, max_score




def main():

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--ref_task', type=str, required=True,
                            help='Reference Task file')
    # arg_parser.add_argument('--input_code_file', type=str, required=True, help='filename of input code file')
    arg_parser.add_argument('--input_json_code_file', type=str, required=True,
                            help='filename of code in json format')
    arg_parser.add_argument('--output_id', type=str, required=True, help='The output id of generated task files.')
    arg_parser.add_argument('--output_folder', type=str, default='', help='The path to store the output tasks.')
    arg_parser.add_argument('--task_type', type=str, default='karel',
                            help='HOC/Karel Task specification')
    arg_parser.add_argument('--iterations', type=int, default=10000,
                            help='Number of random rollouts')

    args = arg_parser.parse_args()

    directory = args.output_folder + 'output/'
    if not os.path.exists(directory):
        os.makedirs(directory)
    temp_dir = args.output_folder + 'output/temp/'
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)


    reftaskfile = args.ref_task
    reftaskdict = get_dict_from_task(reftaskfile)

    jsoncodefile = args.input_json_code_file

    _ = convert_json_to_python(jsoncodefile, temp_dir, args.output_id)
    # codefile = jsoncodefile.split('/')
    # codefile = codefile[-1].split('.')[0]
    python_codefile = temp_dir+args.output_id+'_input.py'

    task_dims = {
        'type': args.task_type,
        'num_streets': 10,
        'num_avenues': 10,
        'random_init': True,
        'cond_flag': True,
        'init_loc_flag': True,
        'ref_task': reftaskdict,
        'ref_task_file': reftaskfile
    }

    output_task, karel_world_start, karel_world_end, score = run_random(args.task_type, args.iterations, python_codefile, jsoncodefile, task_dims, directory, args.output_id, prob_front=0.5, prob_right=0.5,
                                    prob_left=0.5, prob_beepers=0.5, init_config_flag=False, init_config_file='')
    if output_task is not None:
        print("Symbolic task:")
        display_current_sym_world(output_task.karel)
        print("Final task:\n", output_task.karel)
        # print("Concrete Seq:",output_task.karel.concrete_seq)
        # print(output_task.karel.conditionals_hit)
        # print(output_task.karel.karel_seq)
        # print(output_task.karel.karel_locations)
        print("Final score:", score)
        output_task.karel.save_current_sym_world_file(temp_dir, args.output_id+"_output")
        karel_world_start.save_to_file(temp_dir+ args.output_id+"_output_pre.w")
        karel_world_end.save_to_file(temp_dir+ args.output_id+ '_output_post.w')

        # print("Final seq:", output_task.karel.concrete_seq)
        # print("Reference task pregrid:", reftaskdict['pregrid'])
        # print("Postgrid:\n", reftaskdict['postgrid'])
