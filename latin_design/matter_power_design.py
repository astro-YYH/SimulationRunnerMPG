'''
Generate cosmological samples from ParameterSpace using emukit

:class: MatterDesign
'''
from typing import Tuple, Optional
import json
import numpy as np
from emukit.core import ContinuousParameter, ParameterSpace
from latin_design import LatinDesign

class MatterDesign(LatinDesign):
    '''
    Initial design for matter power spec interpolator, using Latin HyperCube.

    MP-Gadget Params:
    ----
    omegab     : baryon density. Note that if we do not have gas particles,
        still set omegab, but set separate_gas = False
    omega0     : Total matter density at z=0 (includes massive neutrinos and 
        baryons)
    hubble     : Hubble parameter, h, which is H0 / (100 km/s/Mpc)
    scalar_amp : A_s at k = 0.05, comparable to the Planck value.
    ns         : Scalar spectral index

    Methods:
    ----
    :method get_samples(point_count): get samples from ParameterSpace
    :method save_json(point_count): dump samples to a json file
    '''
    def __init__(self, omegab_bounds: Tuple, omega0_bounds: Tuple, 
            hubble_bounds: Tuple, scalar_amp_bounds: Tuple, 
            ns_bounds: Tuple, w0_bounds: Tuple, wa_bounds: Tuple, mnu_bounds: Tuple, Neff_bounds: Tuple, alphas_bounds: Tuple, MWDM_bounds: Tuple) -> None:
        # initialise Parameter instances
        omega0     = ContinuousParameter('omega0',     *omega0_bounds)
        omegab     = ContinuousParameter('omegab',     *omegab_bounds)
        hubble     = ContinuousParameter('hubble',     *hubble_bounds)
        scalar_amp = ContinuousParameter('scalar_amp', *scalar_amp_bounds)
        ns         = ContinuousParameter('ns',         *ns_bounds)
        w0         = ContinuousParameter('w0',         *w0_bounds)
        wa         = ContinuousParameter('wa',         *wa_bounds)
        mnu        = ContinuousParameter('mnu',        *mnu_bounds)
        Neff       = ContinuousParameter('Neff',       *Neff_bounds)
        alphas     = ContinuousParameter('alphas',     *alphas_bounds)
        MWDM       = ContinuousParameter('MWDM',       *MWDM_bounds)

        parameter_space = ParameterSpace([
            omega0, omegab, hubble, scalar_amp, ns, w0, wa, mnu, Neff, alphas, MWDM])

        super(MatterDesign, self).__init__(parameter_space)

    def save_json(self, point_count: int, 
            out_filename: str = "matter_power.json") -> None:
        '''
        Save Latin HyperCube of Cosmological ParameterSpace into a json file.
        '''
        dict_latin = {}

        # get a list of param names and then init the dict to save
        param_names = self.parameter_space.parameter_names

        samples = self.get_samples(point_count)

        for i,name in enumerate(param_names):
            # the samples are in order
            dict_latin[name] = samples[:, i].tolist()

        # saving some hyper-parameters
        dict_latin['bounds']          = self.parameter_space.get_bounds()
        dict_latin['parameter_names'] = param_names

        with open(out_filename, 'w') as f:
            json.dump(dict_latin, f, indent=2)

    def save_slhd_json(self,filename: str = "SLHD_t20_m3_k5_seed0.csv", slice: Optional[int] = None, 
            out_filename: str = "matter_power.json") -> None:
        '''
        Save Latin HyperCube of Cosmological ParameterSpace into a json file.
        '''
        dict_latin = {}

        # get a list of param names and then init the dict to save
        param_names = self.parameter_space.parameter_names

        samples = self.get_slhd_samples(filename=filename, slice=slice)

        for i,name in enumerate(param_names):
            # the samples are in order
            dict_latin[name] = samples[:, i].tolist()

        # saving some hyper-parameters
        dict_latin['bounds']          = self.parameter_space.get_bounds()
        dict_latin['parameter_names'] = param_names

        with open(out_filename, 'w') as f:
            json.dump(dict_latin, f, indent=2)
            # f.close()

class MatterDesignShrink(MatterDesign):
    '''
    Initial design for matter power spec interpolator, using Latin HyperCube.
    We still want a 5D json file, so fixed the Omegab and ns on the mean of priors.

    MP-Gadget Params:
    ----
    omega0     : Total matter density at z=0 (includes massive neutrinos and 
        baryons)
    hubble     : Hubble parameter, h, which is H0 / (100 km/s/Mpc)
    scalar_amp : A_s at k = 0.05, comparable to the Planck value.

    Methods:
    ----
    :method get_samples(point_count): get samples from ParameterSpace
    :method save_json(point_count): dump samples to a json file
    '''
    def __init__(self, omega0_bounds: Tuple, 
            hubble_bounds: Tuple, scalar_amp_bounds: Tuple,
            fixed_omegab: float, fixed_ns: float) -> None:
        # initialise Parameter instances
        omega0     = ContinuousParameter('omega0',     *omega0_bounds)
        hubble     = ContinuousParameter('hubble',     *hubble_bounds)
        scalar_amp = ContinuousParameter('scalar_amp', *scalar_amp_bounds)

        self.omegab = fixed_omegab
        self.ns     = fixed_ns

        parameter_space = ParameterSpace([
            omega0, hubble, scalar_amp])

        super(MatterDesign, self).__init__(parameter_space)

    def save_json(self, point_count: int, 
            out_filename: str = "matter_power.json") -> None:
        '''
        Save Latin HyperCube of Cosmological ParameterSpace into a json file.
        '''
        dict_latin = {}

        # get a list of param names and then init the dict to save
        param_names = self.parameter_space.parameter_names

        samples = self.get_samples(point_count)

        for i,name in enumerate(param_names):
            # the samples are in order
            dict_latin[name] = samples[:, i].tolist()

        # fixed values
        dict_latin['omegab'] = [self.omegab for i in range(point_count)]
        dict_latin['ns']     = [self.ns for i in range(point_count)]

        # saving some hyper-parameters
        dict_latin['bounds']          = self.parameter_space.get_bounds()
        dict_latin['parameter_names'] = list(param_names) + ['omegab', 'ns']

        with open(out_filename, 'w') as f:
            json.dump(dict_latin, f, indent=2)
