from matter_power_design import MatterDesign

# set the bounds for uniform priors
matter = MatterDesign(
    omegab_bounds=(0.04, 0.05), 
    omega0_bounds=(0.26, 0.33), 
    hubble_bounds=(0.64, 0.76), 
    scalar_amp_bounds=(1.5*1e-9, 2.7*1e-9), 
    ns_bounds=(0.88, 1.0),
    w0_bounds=(-1.3, -0.7),
    wa_bounds=(-0.7, 0.5),
    mnu_bounds=(0.0, 0.45),
    Neff_bounds=(2.2, 3.6),
    alphas_bounds=(-.025, .016),
    MWDM_inverse_bounds=(0, 1)
)

# number of samples
# point_count = 50
# matter.save_slhd_json(filename="SLHD_t90_m3_k11.csv", out_filename="matterLatin_11p_90x3.json")
matter.save_slhd_json(filename="SLHD_t280_m4_k11.csv", out_filename="matterLatin_11p_280x4.json")  # test
