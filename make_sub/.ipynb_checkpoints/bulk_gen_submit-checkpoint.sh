#!/bin/bash

# Find all submit files in the current directory
submit_base="gen_Box25_Part75"
# submit_base="gen_Box100_Part75"
# submit_base="test_Box100_Part300" # "cosmo_Box1000_Part3000" 

# Submit each submit file using sbatch
for submit_file in ${submit_base}*submit; do
    sbatch $submit_file
done
