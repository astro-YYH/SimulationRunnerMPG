from matter_power_design import MatterDesign

# set the bounds for uniform priors
matter = MatterDesign(
    omegab_bounds=(0.045, 0.051), 
    omega0_bounds=(0.26, 0.35), 
    hubble_bounds=(0.64, 0.74), 
    scalar_amp_bounds=(1.7*1e-9, 2.5*1e-9), 
    ns_bounds=(0.95, 1.),
    w0_bounds=(-1.3, -.5),
    # wa_bounds=(-0.7, 0.5),
    wa_bounds=(-1., 0.5),
    mnu_bounds=(0.06, 0.15),
    Neff_bounds=(2.3, 3.7),
    alphas_bounds=(-.03, .03),
    # MWDM_inverse_bounds=(0, 1)
)

# number of samples
# point_count = 50
# matter.save_slhd_json(filename="SLHD_t120_m3_k11.csv", out_filename="matterLatin_11p_120x3.json")
matter.save_slhd_json(filename="SLHD_narrow_t4_m3_k10.csv", out_filename="matterLatin_narrow_10p_4x3.json") # test set
# matter.save_slhd_json(filename="SLHD_t280_m4_k11.csv", out_filename="matterLatin_11p_280x4.json")  # test
