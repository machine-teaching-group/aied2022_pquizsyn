#!/bin/bash

# Runs the demos and synethics script executions for the repository in one command
# Needs pdflatex (TeX Live) and convert (ImageMagick) to run in its entirety
# Also uses Python >=3.7.3 for execution

echo 'Running Demos...'

python -m code.demo.run_fig1 --latex_images_flag 1
python -m code.demo.run_fig5 --latex_images_flag 1

echo 'Running Synthetics...'

python -m code.step0_inputdata.wrapper_gen-all_input_data
python -m code.step1_hintpolicy.wrapper_gen_all_hintpolicies_struct
python -m code.step4_intervention.wrapper_gen_substructures
python -m code.step4_intervention.wrapper_gen_intervention

echo 'Finished! All outputs are in the \'.\/data\' folder'
