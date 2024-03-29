#!/bin/bash

# submit basename
submit_base="cosmo_Box250_Part750"

# Loop over all directories starting with "cosmo_"
echo "Submission files generated or not?"
count_yes=0
count_tot=0

for dir in /rhome/yyang440/bigdata/cosmo_11p_sims/cosmo_11p_Box250_Part750_*; do
    # Check if "output" directory exists under the current directory
    ((count_tot++))
    if [[ -f "$dir/mpi_submit_one" ]]; then
        echo "$dir Yes"
        ((count_yes++))
    else
        echo "$dir No"
        echo submitting $submit_base\_${dir: -4}.submit
        # pwd
        sbatch ./$submit_base\_${dir: -4}.submit
    fi
done
echo "Completed $count_yes/$count_tot"