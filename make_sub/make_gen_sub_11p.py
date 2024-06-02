'''
make submission files for submission file generator for simulations
command: python make_gen_sub.py
--json_file=../latin_design/matterLatin_11p_90x3.json --box=100 --npart=75
--nproc=16 --cores=32 --mpi_ranks=8 --threads=16
--py_script=make_sim_sub.py --gadget_dir=~/bigdata/MP-Gadget3/
--cluster_class=clusters.BIOClass
--outdir_base=/rhome/yyang440/bigdata/tentative_sim_suite/cosmo_11p

python make_gen_sub.py
--json_file=../latin_design/matterLatin_11p_90x3.json --box=100 --npart=75
--nproc=16 --cores=32 --mpi_ranks=8 --threads=16
--py_script=make_sim_sub.py --gadget_dir=~/bigdata/MP-Gadget3/
--cluster_class=clusters.BIOClass
--outdir_base=/rhome/yyang440/bigdata/tentative_sim_suite/cosmo_11p

python make_gen_sub.py --json_file=../latin_design/matterLatin_11p_90x3.json --points="99, 100, 101, 186, 187, 188, 222, 223, 224, 156, 157, 158, 87, 88, 89, 144, 145, 146" --box=100 --npart=300 --nproc=224 --cores=56 --mpi_ranks=8 --threads=28 --py_script=make_sim_sub.py --gadget_dir=/work2/01317/yyang440/frontera/MP-Gadget/ --cluster_class=clusters.FronteraClass --outdir_base=/work2/01317/yyang440/frontera/tentative_sims/cosmo_11p --submit_base=new_HF

python make_gen_sub.py --json_file=../latin_design/matterLatin_11p_2x5.json  --box=100 --npart=300 --nproc=168 --cores=56 --mpi_ranks=12 --threads=14 --py_script=make_sim_sub.py --gadget_dir=/work2/01317/yyang440/frontera/MP-Gadget/ --cluster_class=clusters.FronteraClass --outdir_base=/work2/01317/yyang440/frontera/tentative_sims/test_11p --submit_base=test
'''
import argparse
import json
# from SimulationRunner import simulationics, clusters


def take_params_dict(Latin_dict: dict):
    '''
    take the next param dict with a single
    sample for each param
    '''
    parameter_names = Latin_dict['parameter_names']
    length          = len(Latin_dict[parameter_names[0]])
    
    assert length == len(Latin_dict[parameter_names[-1]])

    param_dicts = []
    for i in range(length):
        param_dict = {}

        for key in parameter_names:
            if key == 'MWDM_inverse':
                param_dict['MWDM'] = 1.0 / Latin_dict[key][i]
            else:
                param_dict[key] = Latin_dict[key][i]
        param_dicts.append(param_dict)
        
    return param_dicts

def write_directives(f, cluster_class, outdir: str = None, ntasks: int = 56, gen_index: int = 0):
    if cluster_class == "hpcc":
        f.write("#SBATCH --partition=epyc\n")    
        f.write("#SBATCH --job-name={}\n".format(outdir[-8:]))   
        f.write("#SBATCH --time=48:0:00\n") 
        f.write("#SBATCH --nodes=1\n")
        f.write("#SBATCH --ntasks-per-node=1\n")
        f.write("#SBATCH --cpus-per-task=1\n")
        f.write("#SBATCH --mem=10G\n")
        f.write("# SBATCH --mail-type=end\n")
        f.write("# SBATCH --mail-user=yyang440@ucr.edu\n")
        f.write("# SBATCH --exclude=c01,c02,c03,c04,c05,c06,c07,c08,c09,c10,c11,c12,c13,c14,c15,c16,c17,c18,c19,c20,c21,c23,c24,c25,c26,c27,c28,c29,c30,c31,c32,c33,c34,c35,c36,c37,c38,c39,c40,c41,c42,c43,c44,c45,c46,c47\n\n")
    elif cluster_class == "frontera":
        f.write("#SBATCH --partition=small\n")    
        f.write(f"#SBATCH --job-name=gen_{gen_index}\n")   
        f.write("#SBATCH --time=5:00:00\n") 
        f.write("#SBATCH --nodes=1\n")
        f.write(f"#SBATCH --ntasks-per-node={ntasks}\n")
        f.write("# SBATCH --mail-type=end\n")
        f.write("# SBATCH --mail-user=yyang440@ucr.edu\n\n")
    else:
        print("Invalid cluster class name.\n")

def write_gen_submit(index: int, box: int,   npart: int,
        hubble:     float, omega0: float, omegab: float,
        scalar_amp: float, ns:     float, w0:     float,
        wa:         float, mnu:    float, Neff:   float,
        alphas:     float, MWDM:   float,
        nproc :     int,   cores: int, mpi_ranks: int, threads: int,
        outdir:     str = "data",
        gadget_dir: str = "~/bigdata/MP-Gadget/",
        python:     str = "python", 
        py_script:  str = "make_sim_sub.py",
        cluster_class: str = "clusters.BIOClass", submit_base: str = "gen", sub_cluster: str = "hpcc"):
    with open("{}_Box{}_Part{}_{}.submit".format(submit_base, box, npart, str(index).zfill(4)), "w") as f:
        f.write("#!/bin/bash\n")
        write_directives(f, sub_cluster, outdir)
        f.write("hostname\n")
        f.write("which python\n")
        f.write("date\n")
        f.write("python -u {} --box={} --npart={} --hubble={} --omega0={} --omegab={} --scalar_amp={} --ns={} --w0={} --wa={} --mnu={} --Neff={} --alphas={} --MWDM={} --nproc={} --cores={} --mpi_ranks={} --threads={} --outdir={} --gadget_dir={} --python={} --cluster_class={}\n".format(py_script, str(box), str(npart), str(hubble), str(omega0), str(omegab),str(scalar_amp),str(ns), str(w0), str(wa), str(mnu), str(Neff), str(alphas), str(MWDM), str(nproc),str(cores), str(mpi_ranks), str(threads), outdir, gadget_dir, python, cluster_class))
        f.write("date\n")           

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    # load the json file with the cosmological parameters in this format
    # { 'hubble' : [0.5, 0.6, 0.7], 'omega0' : [0.2, 0.15, 0.17], ... }
    # should write another function to generate samples
    parser.add_argument("--json_file", type=str, default="matterLatin_high.json")
    parser.add_argument("--points", type=str, default=None)
    
    parser.add_argument("--gadget_dir", type=str,
        default="~/bigdata/MP-Gadget/")
    parser.add_argument("--cluster_class", type=str,
        default="clusters.BIOClass")
    parser.add_argument("--outdir_base", type=str, default="~/bigdata/test_sims/cosmo_11p")

    # keep a separated flags for boxsize and resolution
    parser.add_argument("--box", type=int, default=256)
    parser.add_argument("--npart", type=int, default=128)

    # mpi settings
    parser.add_argument("--nproc", type=int, default=256)
    parser.add_argument("--cores", type=int, default=32)
    parser.add_argument("--mpi_ranks", type=int, default=8)
    parser.add_argument("--threads", type=int, default=16)
    
    parser.add_argument("--py_script", type=str, default="make_sim_sub.py")
    parser.add_argument("--submit_base", type=str, default="gen")
    # parser.add_argument("--single_submit", type=int, default=0)
    parser.add_argument("--sub_cluster", type=str, default="hpcc")  # cluster on which the submission files are generated

    args = parser.parse_args()

    # make the cluster class to be a str so can put in argparser
    # cc = eval(args.cluster_class)
    cc = args.cluster_class  # in this script, it is just a string

    

    with open(args.json_file, 'r') as f:
        Latin_dict = json.load(f)

    param_dicts = take_params_dict(Latin_dict)

    if args.points != None:
        points = [int(num) for num in args.points.split(',')]
    else:
        points = None

    # handle the param file generation one-by-one
    if args.sub_cluster == "frontera":
        if points == None:
            points = list(range(len(param_dicts)))
        gen_i_max = len(points) // 56 + 1
        for gen_i in range(gen_i_max):
            with open(f"{args.submit_base}_{gen_i}.submit", "w") as f:
                f.write("#!/bin/bash\n")
                write_directives(f, args.sub_cluster)
                f.write("hostname\n")
                f.write("which python\n")
                f.write("date\n")
                for i in points[gen_i*56:(gen_i+1)*56]:
                    if i >= len(param_dicts):
                        break
                    param_dict = param_dicts[i]
        # outdir auto generated, since we will have many folders
                    outdir = "{}_Box{}_Part{}_{}".format(args.outdir_base, args.box, args.npart, str(i).zfill(4))
                    f.write("python -u {} --box={} --npart={} --hubble={} --omega0={} --omegab={} --scalar_amp={} --ns={} --w0={} --wa={} --mnu={} --Neff={} --alphas={} --MWDM={} --nproc={} --cores={} --mpi_ranks={} --threads={} --outdir={} --gadget_dir={} --python={} --cluster_class={} &\n".format(args.py_script, str(args.box), str(args.npart), param_dict["hubble"], param_dict["omega0"], param_dict["omegab"],param_dict["scalar_amp"],param_dict["ns"], param_dict["w0"], param_dict["wa"], param_dict["mnu"], param_dict["Neff"], param_dict["alphas"], param_dict["MWDM"], str(args.nproc),str(args.cores), str(args.mpi_ranks), str(args.threads), outdir, args.gadget_dir, "python", cc))
                f.write("wait\n")
                f.write("date\n")
            f.close()
    else:  # hpcc
        for i, param_dict in enumerate(param_dicts):
            if points != None and i not in points:
                continue
        # outdir auto generated, since we will have many folders
            outdir = "{}_Box{}_Part{}_{}".format(args.outdir_base, args.box, args.npart, str(i).zfill(4))

            write_gen_submit(index=i,py_script=args.py_script, npart=args.npart, box=args.box, nproc=args.nproc, cores=args.cores, mpi_ranks=args.mpi_ranks, threads=args.threads,
            outdir=outdir, gadget_dir=args.gadget_dir,
            cluster_class=cc, submit_base=args.submit_base,
            **param_dict)


