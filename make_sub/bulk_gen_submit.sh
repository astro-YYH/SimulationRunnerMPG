#!/bin/bash

# Find all submit files in the current directory
# submit_base="cosmo_Box1000_Part750"
submit_base="cosmo_Box250_Part750" # "cosmo_Box1000_Part3000" 

# Submit each submit file using sbatch
for submit_file in ${submit_base}*submit; do
    sbatch $submit_file
done
