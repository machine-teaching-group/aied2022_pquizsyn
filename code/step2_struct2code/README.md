## Stage 2(i): Synthesizing Cquiz from Squiz
This repository contains code for the algorithm PQuizSyn, introduced in the paper ["Adaptive Scaffolding in Block-Based Programming
via Synthesizing New Tasks as Pop Quizzes"](https://machineteaching.mpi-sws.org/files/papers/aied2022_pquizsyn_preprint.pdf).

### Overview
In this step, we generate the codes from the sketch and also have a wrapper to generate the task-code pair. We first generate all possible code candidates for a sketch from the reduced/minimal code corresponding to the sketch. We set the threshold of additional blocks added in the code to 2.
We use the z3-solver to generate code candidates for task synthesis in the next step. This folder also contains the delta-debugging routine used to filter low quality (task-code) pairs.

* ```sym_ast```: this is an ast object on which constraints are applied to generate concrete code candidates.
* ```sym_vocab```: this contains the list of tokens used in the sym_ast object.
* ```sketch_to_symcode```: generates the sym_ast object from a sketch which is converted later into concrete code.
* ```minimal_code_to_symcode```: converts the reduced code into a object of the sym_ast class.
* ```z3_constraints_for_minimal_code```: generates all the z3 constraints applied to an object of sym_ast class, for sketches of depth <= 3.
* ```z3_solver```: contains the z3 smt solver to generate all possible values for a sym_ast object.
* ```get_concrete_code_for_minimal_code```: generates the concrete code candidates from a sym_ast object.
* ```delta_debugging```: routine to carry out delta-debugging procedure to filter out low quality task,code pairs. Our delta-debugging threshold is set to 1.
* ```get_task_code_pair```: generates the final set of (task,code) pairs for a sym_ast object.
* ```smt_constraints_task3```: contains the routines to generate codes for sketches of depth > 3 for task-3.
* ```smt_constraints_task5```: contains the routines to generate codes for sketches of depth > 3 for task-5.