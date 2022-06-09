from code.step1_hintpolicy.wrapper_hintpolicies import get_sketch_hint as get_sketch_hint





if __name__ == "__main__":
    inputfolder = "../../data/input/"
    outputfolder = "../../data/output/expert-survey-input-data/"

    task_ids = ['0', '3', '4', '5']
    student_ids = ['0', '1', '2', '3']
    alg_ids = ['reduced-code', 'same-0', 'same-2', 'hop-0', 'hop-2', 'ours-0', 'ours-2']

    for tid in task_ids:
        for sid in student_ids:
            for aid in alg_ids:
                 hint = get_sketch_hint(tid, sid, aid, inputfolder, outputfolder, save_image=True)

