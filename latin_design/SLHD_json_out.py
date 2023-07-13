from matter_power_design import MatterDesign

# set the bounds for uniform priors
matter = MatterDesign(
    omegab_bounds=(0.04, 0.06), 
    omega0_bounds=(0.24, 0.40), 
    hubble_bounds=(0.63, 0.76), 
    scalar_amp_bounds=(1.7*1e-9, 2.5*1e-9), 
    ns_bounds=(0.92, 1.0),
    w0_bounds=(-1.3, -0.7),
    wa_bounds=(-0.7, 0.7),
    mnu_bounds=(0., 0.3),
    Neff_bounds=(3.046, 4.5),
    alphas_bounds=(-.03, .03),
    MWDM_bounds=(2, 40)
)

# number of samples
# point_count = 50
matter.save_slhd_json(filename="SLHD_t90_m3_k11.csv", out_filename="matterLatin_11p_90x3.json")