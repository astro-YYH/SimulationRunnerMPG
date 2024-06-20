from matter_power_design import MatterDesign

# set the bounds for uniform priors
matter = MatterDesign(
    omegab_bounds=(0.04, 0.055), 
    omega0_bounds=(0.22, 0.40), 
    hubble_bounds=(0.60, 0.76), 
    scalar_amp_bounds=(1.*1e-9, 3.*1e-9), 
    ns_bounds=(0.8, 1.1),
    w0_bounds=(-1.3, .25),
    # wa_bounds=(-0.7, 0.5),
    wa_bounds=(-3, 0.5),
    mnu_bounds=(0.0, 0.6),
    Neff_bounds=(2.2, 4.5),
    alphas_bounds=(-.05, .05),
    # MWDM_inverse_bounds=(0, 1)
)

# number of samples
# point_count = 50
# matter.save_slhd_json(filename="SLHD_t120_m3_k11.csv", out_filename="matterLatin_11p_120x3.json")
matter.save_slhd_json(filename="SLHD_t99_m3_k10.csv", out_filename="matterLatin_10p_99x3.json") # test set
# matter.save_slhd_json(filename="SLHD_t280_m4_k11.csv", out_filename="matterLatin_11p_280x4.json")  # test
