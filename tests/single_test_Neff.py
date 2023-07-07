import datetime

current_time = datetime.datetime.now()

print("Importing simulationics, clusters...", current_time)
from SimulationRunner import simulationics, clusters
print("Imported.", current_time, "\n")
import os

# set the desired input parameters for your simulation
box = 256   # Mpc/h
npart = 128 # 128^3
hubble = 0.7 # Hubble parameter, h, which is H0 / (100 km/s/Mpc)
omega0 = 0.288 # Total matter density at z=0 (includes massive neutrinos and baryons)
omegab = 0.0472 # baryon density.
scalar_amp = 2.427e-9 # A_s at k = 0.05, comparable to the Planck value.
ns = 0.97 # Scalar spectral index
nproc = 256 # Total number of processors
cores = 32 # Number of cores per node

m_nu = .1 # total neutrino mass
w0_fld = -1.1
wa_fld = .2
N_ur = 3.5

# set the paths
outdir = "/rhome/yyang440/bigdata/test_sims/test-128-256-Neff-0000" # Output folder name
gadget_dir = "~/bigdata/MP-Gadget3" # Your path to MP-Gadget folder
python = "python" # Your path to python binary

# here you run on UCR biocluster
# if you don't want to send emails to my email address, change the email in
# BIOClass class :)
print("Creating cluster_calss...", current_time)
cluster_class = clusters.BIOClass
print("Done.", current_time)

Sim = simulationics.SimulationICs(
    redshift = 99, redend = 0,
    box    = box, npart = npart,
    hubble = hubble, omega0 = omega0,
    omegab = omegab, scalar_amp = scalar_amp, ns = ns,
    w0_fld=w0_fld, wa_fld=wa_fld, m_nu=m_nu, N_ur=N_ur,
    nproc  = nproc, cores=cores,
    outdir = outdir,
    gadget_dir = gadget_dir,
    python = python,
    cluster_class = cluster_class)

Sim.make_simulation(pkaccuracy=0.07)
assert os.path.exists(outdir)