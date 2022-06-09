## Stage 3: Generating Multi-Choice Question from (Tquiz, Cquiz)
This repository contains code for the algorithm PQuizSyn, introduced in the paper ["Adaptive Scaffolding in Block-Based Programming
via Synthesizing New Tasks as Pop Quizzes"](https://machineteaching.mpi-sws.org/files/papers/aied2022_pquizsyn_preprint.pdf).

### Overview
In this stage, we generate all task-code pairs for the exhaustive list of subtstructures for the reference tasks.
We first run the script to generate all the substructures for the tasks, and their reduced codes. This is the starting point to generate the list of pop quizzes for each substructure.
Run the following command from the parent folder (aied2022_pquizsyn_code):

```python -m code.step4_intervention.wrapper_gen_substructures```

Next, we generate all the task-code pairs for each substructure of all 7 reference tasks, by running the following command from the parent folder (aied2022_pquizsyn_code):

```python -m code.step4_intervention.wrapper_gen_intervention```

NOTE: Running this routine is time-consuming and takes a few hours to complete execution. The output is generated in the task specific folders (for each of the 7 tasks) in: ```data/output/```. Except ```task-3/substructure-3``` and ```task-5/substructure-2```, all other task-code pairs are generated. These two substructures are treated separately, as the higher depth of their sketches requires a separate script to generate their z3 constraints.

### Generating task-code pairs for ```task-3/substructure-3```
Run the following command from the parent folder (aied2022_pquizsyn_code):

```python -m code.step2_struct2code.smt_constraints_task3.mutations```

This generates all the code mutations in the folder: ```data/output/task-3/substructure-3/all-mutations``` before running the task synthesis pipeline.
Next, run the following command from the parent folder (aied2022_pquizsyn_code):

```python -m code.step2_struct2code.smt_constraints_task3.run_full_pipeline```

This generates the set of all valid task-code pairs for the specific substructure.

### Generating task-code pairs for ```task-5/substructure-2```
Run the following command from the parent folder (aied2022_pquizsyn_code):

```python -m code.step2_struct2code.smt_constraints_task5.mutations```

This generates all the code mutations in the folder: ```data/output/task-5/substructure-2/all-mutations```.
Next, run the following command from the parent folder (aied2022_pquizsyn_code):

```python -m code.step2_struct2code.smt_constraints_task5.run_full_pipeline --bucket_id X``` 

where X is a value from the set { "9", "10_1", "10_2", "10_3", 11_1", "11_2", "11_3", "11_4", "11_5"}. Running it for all values in the set will give the final list of valid task-code pairs.

This generates the set of all valid task-code pairs for the specific substructure and specific bucket_id. 
We separate the execution of this stage into buckets as the total number of codes to process during task synthesis is very large.

