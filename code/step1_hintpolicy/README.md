## Stage 1: Generating the Pop Quiz Sketch Squiz

This repository contains code for the algorithm PQuizSyn, introduced in the paper ["Adaptive Scaffolding in Block-Based Programming
via Synthesizing New Tasks as Pop Quizzes"](https://machineteaching.mpi-sws.org/files/papers/aied2022_pquizsyn_preprint.pdf).

### Overview
This is the first stage in our algorithm, PQuizSyn, to generate the sketch hint Squiz. Squiz is generated from the solution code and the student attempt for a task.
We present scripts to generate different types of hints for a given student code.
* ```hintpolicy_code```: generates the next-step hint with basic action nodes (move, turn_left, turn_right, pick_marker, put_marker) only.
* ```hintpolicy_struct_onehop_with_action```: generates the next-step hint prioritizing code constructs (such as IfElse, Repeat, etc.) over basic actions.
* ```hintpolicy_struct_hop```: generates the next-step hint in the sketch space, within the immediate neighbohood of the student sketch.
* ```hintpolicy_struct_same```: generates the hint in the sketch space, and returns the sketch of the solution code of the task.
* ```hintpolicy_struct_multihop```: generates the hint in the sketch space for PQuizSyn.
