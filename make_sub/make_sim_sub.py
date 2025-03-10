import sys
import os
# Add the parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import datetime
current_time = datetime.datetime.now()
from SimulationRunner import simulationics, clusters
import argparse



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    parser.add_argument("--gadget_dir", type=str,
        default="~/bigdata/MP-Gadget/")
    parser.add_argument("--cluster_class", type=str,
        default="clusters.BIOClass")
    parser.add_argument("--outdir", type=str, default="data")

    # keep a separated flags for boxsize and resolution
    parser.add_argument("--box", type=int, default=256)
    parser.add_argument("--npart", type=int, default=128)

    # mpi settings
    parser.add_argument("--nproc", type=int, default=256)
    parser.add_argument("--cores", type=int, default=32)
    parser.add_argument("--mpi_ranks", type=int, default=8)
    parser.add_argument("--threads", type=int, default=16)

    # comological params
    parser.add_argument("--omega0", type=float, default=.288)
    parser.add_argument("--omegab", type=float, default=.0472)
    parser.add_argument("--scalar_amp", type=float, default=2.427e-9)
    parser.add_argument("--ns", type=float, default=.97)
    parser.add_argument("--hubble", type=float, default=.7)
    # extensions
    parser.add_argument("--w0", type=float, default=-1.)
    parser.add_argument("--wa", type=float, default=0.)
    parser.add_argument("--mnu", type=float, default=0.)
    parser.add_argument("--Neff", type=float, default=3.046)
    parser.add_argument("--alphas", type=float, default=0.)
    parser.add_argument("--MWDM", type=float, default=0.)


    parser.add_argument("--python", type=str, default="python")

    args = parser.parse_args()

    # make the cluster class to be a str so can put in argparser
    # cc = eval(args.cluster_class)
    cc = args.cluster_class  # in this script, it is just a string


# set the desired input parameters for your simulation
box = args.box   # Mpc/h
npart = args.npart # 128^3

hubble = args.hubble # Hubble parameter, h, which is H0 / (100 km/s/Mpc)
omega0 = args.omega0 # Total matter density at z=0 (includes massive neutrinos and baryons)
omegab = args.omegab # baryon density.
scalar_amp = args.scalar_amp # A_s at k = 0.05, comparable to the Planck value.
ns = args.ns # Scalar spectral index

nproc = args.nproc # Total number of processors
cores = args.cores # Number of cores per node
mpi_ranks = args.mpi_ranks
threads = args.threads

m_nu = args.mnu # total neutrino mass
w0_fld = args.w0
wa_fld = args.wa
alpha_s = args.alphas # Running of the spectral index
N_ur = args.Neff
MWDM_therm = args.MWDM

# set the paths
outdir = args.outdir # Output folder name
gadget_dir = args.gadget_dir # Your path to MP-Gadget folder
python = args.python # Your path to python binary

# here you run on UCR biocluster
# if you don't want to send emails to my email address, change the email in
# BIOClass class :)
print("Creating cluster_calss...", current_time)
cluster_class = eval(args.cluster_class)
print("Done.", current_time,"\n")

print("Output directory: ", outdir,"\n")

Sim = simulationics.SimulationICs(
    redshift = 99, redend = 0,
    box    = box, npart = npart,
    hubble = hubble, omega0 = omega0,
    omegab = omegab, scalar_amp = scalar_amp, ns = ns,
    w0_fld=w0_fld, wa_fld=wa_fld, m_nu=m_nu, N_ur=N_ur, alpha_s=alpha_s, MWDM_therm=MWDM_therm,
    nproc  = nproc, cores=cores, mpi_ranks=mpi_ranks, threads=threads,
    outdir = outdir,
    gadget_dir = gadget_dir,
    python = python,
    cluster_class = cluster_class)

Sim.make_simulation(pkaccuracy=0.07)
outdir = os.path.expanduser(outdir)
assert os.path.exists(outdir)
