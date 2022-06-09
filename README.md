## Adaptive Scaffolding in Block-Based Programming via Synthesizing New Tasks as Pop Quizzes

This repository contains code for the algorithm PQuizSyn, introduced in the paper ["Adaptive Scaffolding in Block-Based Programming
via Synthesizing New Tasks as Pop Quizzes"](https://machineteaching.mpi-sws.org/files/papers/aied2022_pquizsyn_preprint.pdf).

### Overview
The repository is structured as follows:
* ```code/``` : This folder contains all the code files required for generating the reference tasks, codes, and pop-quizzes for a subset of block-based visual programming tasks taken from platforms such as 'Hour of Code' and 'codehs.com'.
* ```data/``` : This folder is where all the reference tasks, codes, and quizzes will be generated.

All code files require Python version >= 3.7.3 to run. Before running the scripts, please run ```pip install -r requirements.txt``` and satisfy all the libraries required for running the module.
Refer the individual READMEs available in each of the folders for further details.

Next, we present details to generate popquiz for the reference task, solution code and student in Fig. 1 and Fig. 5 of the paper run the demo scripts. 
Set the --latex_images_flag to 0, to generate only the text/json files of the reference task and the popquiz. To also generate the images of the files, set its value to 1. 
Each script takes a couple of minutes to run.

### Running demo to generate Fig. 1
Run the following command to generate Fig. 1 of the paper. The script generates popquiz for reference task Maze 20 from [Hour of Code: Maze Challenge](https://studio.code.org/hoc/20), and a specific student attempt. Note that, every run of this script will generate a different popquiz (Tquiz, Cquiz).
```python -m code.demo.run_fig1 --latex_images_flag 1```

The command generates data in the folder ```data/demo/fig1/```. The list of 13 files generated are: 
* Reference task: ```task_Tin.txt``` and ```task_Tin.pdf```
* Solution code: ```code_Cin_solution.json``` and ```code_Cin_solution.pdf```
* Student attempt: ```code_Cin_student.json``` and ```code_Cin_student.pdf```
* Popquiz task: ```task_Tquiz.txt``` and ```task_Tquiz.pdf```
* Popquiz solution code: ```code_Cquiz.json``` and ```code_Cquiz.pdf```
* Popquiz code with blank: ```code_Cquiz_with_blank.json``` and ```code_Cquiz_with_blank.pdf```
* Quiz options: ```quiz_options.pdf```

### Running demo to generate Fig. 5
Run the following command to generate Fig. 5 of the paper. The script generates popquiz for reference task Karel: Opposite from Intro to Programming with Karel by [codehs.com](https://codehs.com/), and a specific student attempt. Note that, every run of this script will generate a different popquiz (Tquiz, Cquiz).
```python -m code.demo.run_fig5 --latex_images_flag 1```

The command generates data in the folder ```data/demo/fig5/```. The list of 13 files generated are: 
* Reference task: ```task_Tin.txt``` and ```task_Tin.pdf```
* Solution code: ```code_Cin_solution.json``` and ```code_Cin_solution.pdf```
* Student Attempt: ```code_Cin_student.json``` and ```code_Cin_student.pdf```
* Popquiz task: ```task_Tquiz.txt``` and ```task_Tquiz.pdf```
* Popquiz solution code: ```code_Cquiz.json``` and ```code_Cquiz.pdf```
* Popquiz code with blank: ```code_Cquiz_with_blank.json``` and ```code_Cquiz_with_blank.pdf```
* Quiz options: ```quiz_options.pdf```

### Contact Details
For any questions or comments, contact [gahana@mpi-sws.org](mailto:gahana@mpi-sws.org).