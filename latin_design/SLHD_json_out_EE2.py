from matter_power_design import MatterDesign

# set the bounds for uniform priors
# matter = MatterDesign(
#     omegab_bounds=(0.04, 0.055), 
#     omega0_bounds=(0.24, 0.40), 
#     hubble_bounds=(0.61, 0.73), 
#     scalar_amp_bounds=(1.7*1e-9, 2.5*1e-9), 
#     ns_bounds=(0.92, 1.),
#     w0_bounds=(-1.3, -.7),
#     # wa_bounds=(-0.7, 0.5),
#     wa_bounds=(-.7, 0.5),
#     mnu_bounds=(0.0, 0.15),
#     Neff_bounds=(3.046,3.046),
#     alphas_bounds=(-.0, .0),
#     # MWDM_inverse_bounds=(0, 1)
# )

# narrow
matter = MatterDesign(
    omegab_bounds=(0.045, 0.051), 
    omega0_bounds=(0.26, 0.35), 
    hubble_bounds=(0.64, 0.73), 
    scalar_amp_bounds=(1.7*1e-9, 2.5*1e-9), 
    ns_bounds=(0.95, 1.),
    w0_bounds=(-1.3, -.7),
    # wa_bounds=(-0.7, 0.5),
    wa_bounds=(-.7, 0.5),
    mnu_bounds=(0.06, 0.15),
    Neff_bounds=(3.046,3.046),
    alphas_bounds=(-.0, .0),
    # MWDM_inverse_bounds=(0, 1)
)

# # omega0 omegab hubble scalar_amp ns w0 wa mnu Neff alphas
# cosmo_lower = np.array([0.24, 0.04, 0.61, 1.7e-9, 0.92, -1.3, -0.7, 0.0, 3.046, 0.])
# cosmo_upper = np.array([0.40, 0.055, 0.73, 2.5e-9, 1., -.7, 0.5, 0.15, 3.046, 0.])
# number of samples
# point_count = 50
# matter.save_slhd_json(filename="SLHD_t120_m3_k11.csv", out_filename="matterLatin_11p_120x3.json")
matter.save_slhd_json(filename="SLHD_narrow_t10_m5_k10.csv", out_filename="matterLatin_EE2_narrow_10x5.json") # test set
# matter.save_slhd_json(filename="SLHD_t280_m4_k11.csv", out_filename="matterLatin_11p_280x4.json")  # test
