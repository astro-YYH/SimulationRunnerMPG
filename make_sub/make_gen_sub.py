'''
make submission files for submission file generator for simulations
command: python make_gen_sub.py --json_file=../latin_design/matterLatin_11p_90x3.json --box=100 --npart=75 --nproc=256 --cores=32 --py_script=make_sim_sub.py --gadget_dir=~/bigdata/codes/MP-Gadget3/ --cluster_class=clusters.BIOClass --outdir_base=/rhome/yyang440/bigdata/tentative_sim_suite/L1/cosmo_11p
'''
from typing import Generator
import argparse
import json
# from SimulationRunner import simulationics, clusters


def take_params_dict(Latin_dict: dict) -> Generator:
    '''
    take the next param dict with a single
    sample for each param
    '''
    parameter_names = Latin_dict['parameter_names']
    length          = len(Latin_dict[parameter_names[0]])
    
    assert length == len(Latin_dict[parameter_names[-1]])

    for i in range(length):
        param_dict = {}

        for key in parameter_names:
            param_dict[key] = Latin_dict[key][i]
        
        yield param_dict

def write_gen_submit(index: int, box: int,   npart: int,
        hubble:     float, omega0: float, omegab: float,
        scalar_amp: float, ns:     float, w0:     float,
        wa:         float, mnu:    float, Neff:   float,
        alphas:     float, MWDM:   float,
        nproc :     int,   cores: int,
        outdir:     str = "data",
        gadget_dir: str = "~/bigdata/MP-Gadget3/",
        python:     str = "python", # it's annoying
        py_script:  str = "make_sim_sub.py",
        cluster_class: str = "clusters.BIOClass"):
    with open("gen_Box{}_Part{}_{}.submit".format(box, npart, str(index).zfill(4)), "w") as f:
        f.write("#!/bin/bash\n")
        f.write("#SBATCH --partition=short\n")    
        f.write("#SBATCH --job-name={}\n".format(outdir[-6:]))   
        f.write("#SBATCH --time=2:0:00\n") 
        f.write("#SBATCH --nodes=1\n")
        f.write("#SBATCH --ntasks-per-node=1\n")
        f.write("#SBATCH --cpus-per-task=1\n")
        f.write("#SBATCH --mem=6G\n")
        f.write("# SBATCH --mail-type=end\n")
        f.write("# SBATCH --mail-user=yyang440@ucr.edu\n")
        f.write("#SBATCH --exclude=c01,c02,c03,c04,c05,c06,c07,c08,c09,c10,c11,c12,c13,c14,c15,c16,c17,c18,c19,c20,c21,c22,c23,c24,c25,c26,c27,c28,c29,c30,c31,c32,c33,c34,c35,c36,c37,c38,c39,c40,c41,c42,c43,c44,c45,c46,c47,c48\n\n")
        f.write("which python\n")
        f.write("current_datetime=$(date \"+%Y-%m-%d %H:%M:%S\")\n")
        f.write("echo \"Current date and time: $current_datetime\"\n")
        f.write("python {} --box={} --npart={} --hubble={} --omega0={} --omegab={} --scalar_amp={} --ns={} --w0={} --wa={} --mnu={} --Neff={} --alphas={} --MWDM={} --nproc={} --cores={} --outdir={} --gadget_dir={} --python={} --cluster_class={}\n".format(py_script, str(box), str(npart), str(hubble), str(omega0), str(omegab),str(scalar_amp),str(ns), str(w0), str(wa), str(mnu), str(Neff), str(alphas), str(MWDM), str(nproc),str(cores), outdir, gadget_dir, python, cluster_class))
        f.write("current_datetime=$(date \"+%Y-%m-%d %H:%M:%S\")\n")
        f.write("echo \"Current date and time: $current_datetime\"\n")           

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    # load the json file with the cosmological parameters in this format
    # { 'hubble' : [0.5, 0.6, 0.7], 'omega0' : [0.2, 0.15, 0.17], ... }
    # should write another function to generate samples
    parser.add_argument("--json_file", type=str, default="matterLatin_high.json")
    
    parser.add_argument("--gadget_dir", type=str,
        default="~/bigdata/MP-Gadget3/")
    parser.add_argument("--cluster_class", type=str,
        default="clusters.BIOClass")
    parser.add_argument("--outdir_base", type=str, default="~/bigdata/test_sims/cosmo_11p")

    # keep a separated flags for boxsize and resolution
    parser.add_argument("--box", type=int, default=256)
    parser.add_argument("--npart", type=int, default=128)

    # mpi settings
    parser.add_argument("--nproc", type=int, default=256)
    parser.add_argument("--cores", type=int, default=32)
    parser.add_argument("--py_script", type=str, default="make_sim_sub.py")
    parser.add_argument("--submit_base", type=str, default="gen")

    args = parser.parse_args()

    # make the cluster class to be a str so can put in argparser
    # cc = eval(args.cluster_class)
    cc = args.cluster_class  # in this script, it is just a string

    with open(args.json_file, 'r') as f:
        Latin_dict = json.load(f)

    # handle the param file generation one-by-one
    for i, param_dict in enumerate(take_params_dict(Latin_dict)):
        # outdir auto generated, since we will have many folders
        outdir = "{}_Part{}_Box{}_{}".format(args.outdir_base, args.npart, args.box, str(i).zfill(4))

        write_gen_submit(index=i,py_script=args.py_script, npart=args.npart, box=args.box, nproc=args.nproc, cores=args.cores,
            outdir=outdir, gadget_dir=args.gadget_dir,
            cluster_class=cc,
            **param_dict)


