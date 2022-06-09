## Stage 2(ii): Synthesizing Tquiz from Cquiz
This repository contains code for the algorithm PQuizSyn, introduced in the paper ["Adaptive Scaffolding in Block-Based Programming
via Synthesizing New Tasks as Pop Quizzes"](https://machineteaching.mpi-sws.org/files/papers/aied2022_pquizsyn_preprint.pdf).

### Overview
In this step, we generate tasks from codes using symbolic execution, based on the methodology introduced in the paper [Synthesizing Tasks for Block-based Programming](https://proceedings.neurips.cc/paper/2020/file/fd9dd764a6f1d73f4340d570804eacc4-Supplemental.pdf). This folder has the following files:
* sym_code: SymCode class to run symbolic execution during task synthesis.
* sym_ascii: Class to display symbolic code and task during synthesis.
* sym_world: SymWorld class to carry out symbolic execution and generate the visual task grids.
* symbolic_execution: the routine to carry out symbolic execution on an object of SymWorld and SymCode.
* run_random: carries out N rollouts to obtain different tasks for a code and picks the best one based on a scoring function defined in ```utils/```. 

### Acknowledgement
We acknowledge using the repository of standfordkarel ([https://github.com/TylerYep/stanfordkarel](https://github.com/TylerYep/stanfordkarel)) for executing Karel tasks.
We cloned the repository in ```github_standfordkarel/``` and changed it for our task synthesis methodology.