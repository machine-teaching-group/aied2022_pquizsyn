## Generating all Reference Tasks, Solution Codes and Student Attempts

This repository contains code for the algorithm PQuizSyn, introduced in the paper ["Adaptive Scaffolding in Block-Based Programming
via Synthesizing New Tasks as Pop Quizzes"](https://machineteaching.mpi-sws.org/files/papers/aied2022_pquizsyn_preprint.pdf).

### Overview
This step generates input data for all the tasks.
To generate input data, run the following command from the parent folder (aied2022_pquizsyn_code):

```python -m code.step0_inputdata.wrapper_gen-all_input_data```

The execution takes upto a minute and generates all the data in the folder: ```data/input/```. The script generates data for 7 tasks. The details of the tasks are listed below (also see Fig. 4 in the paper).

|Task |Source |Number of student attempts |
|:-----|:------:|:------------------------:|
|task-0 |HOC: Maze08 |4|
|task-1 |HOC: Maze16 |4|
|task-2 |HOC: Maze18 |4|
|task-3 |HOC: Maze20 |4|
|task-4 |Karel: Opposite |4|
|task-5 |Karel: Stairway |4|
|task-6 |Karel: Diagonal |N/A| 

Each task contains the reference task grid, the solution code, and 4 simulated student attempts used for the expert study. 

NOTE: As we did not conduct the expert study with task-6, we did not design any simulated students attempts for it.
