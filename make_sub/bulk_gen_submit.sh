#!/bin/bash

# Find all submit files in the current directory
submit_files=$(find . -name "gen_Box25*.submit")

# Submit each submit file using sbatch
for submit_file in $submit_files; do
    sbatch $submit_file
done
