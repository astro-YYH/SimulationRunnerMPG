"""Class to generate simulation ICS, separated out for clarity."""
from __future__ import print_function
from typing import Tuple, List, Type, Any
import os.path
import math
import subprocess
import json
import shutil
#To do crazy munging of types for the storage format
import importlib
import numpy as np
import configobj
import classylss
import classylss.binding as CLASS
from . import utils
from . import clusters
from . import cambpower
import datetime

# DM-only
class SimulationICs(object):
    """
    Class for creating the initial conditions for a simulation.
    There are a few things this class needs to do:

    - Generate CAMB input files
    - Generate MP-GenIC input files (to use CAMB output)
    - Run CAMB and MP-GenIC to generate ICs

    The class will store the parameters of the simulation.

    We also save a copy of the input and enough information to reproduce the
    results exactly in SimulationICs.json.

    Many things are left hard-coded.

    We assume flatness.

    Init parameters:
    ----
    outdir     - Directory in which to save ICs
    box        - Box size in comoving Mpc/h
    npart      - Cube root of number of particles
    redshift   - redshift at which to generate ICs
    omegab     - baryon density. Note that if we do not have gas particles,
        still set omegab, but set separate_gas = False
    omega0     - Total matter density at z=0 (includes massive neutrinos and 
        baryons)
    hubble     - Hubble parameter, h, which is H0 / (100 km/s/Mpc)
    scalar_amp - A_s at k = 0.05, comparable to the Planck value.
    ns         - Scalar spectral index
    m_nu       - neutrino mass
    unitary    - if true, do not scatter modes, but use a unitary gaussian
        amplitude.

    Remove:
    ----
    separate_gas - if true the ICs will contain baryonic particles;
        If false, just DM.
    """
    def __init__(self, *,
            outdir: str, box: int,  npart: int,
            seed :         int   = 9281110,      redshift: float = 99,
            redend:        float = 0,            omega0:   float = 0.288, 
            omegab:        float = 0.0472,       hubble:   float = 0.7,
            scalar_amp:    float = 2.427e-9,     ns:       float = 0.97,
            rscatter:      bool  = False,        m_nu:     float = 0,
            nu_hierarchy:  str   = 'normal', uvb:      str   = "pu",
            nu_acc:        float = 1e-5,         unitary:  bool  = True,
            w0_fld:        float = -1.,           wa_fld:   float = 0., N_ur: float = 3.044, alpha_s: float = 0, MWDM_therm: float = 0,      
            cluster_class: Type[clusters.StampedeClass] = clusters.StampedeClass, 
            gadget_dir:    str = "~/codes/MP-Gadget/",
            python:        str = "python",
            nproc:         int = 256,            cores:    int   = 32, mpi_ranks: int = 8, threads: int = 16) -> None:
        #Check that input is reasonable and set parameters
        #In Mpc/h
        print("__init__: initializing parameters...", datetime.datetime.now())
        assert box  < 20000
        self.box      = box

        #Cube root
        assert npart > 1 and npart < 16000
        self.npart    = int(npart)

        #Physically reasonable
        assert omega0 <= 1 and omega0 > 0
        self.omega0   = omega0

        assert omegab > 0 and omegab < 1
        self.omegab   = omegab

        assert redshift > 1 and redshift < 1100
        self.redshift = redshift

        assert redend >= 0 and redend < 1100
        self.redend = redend

        assert hubble < 1 and hubble > 0
        self.hubble = hubble

        assert scalar_amp < 1e-7 and scalar_amp > 0
        self.scalar_amp = scalar_amp

        assert ns > 0 and ns < 2
        self.ns      = ns
        self.unitary = unitary

        # assert w0_fld < 0
        self.w0_fld = w0_fld

        # assert wa_fld < 1 and wa_fld > -1
        self.wa_fld = wa_fld

        assert N_ur >= 0
        self.N_ur = N_ur

        assert alpha_s < 1 and alpha_s > -1
        self.alpha_s = alpha_s

        T_CMB = 2.7255  # default cmb temperature
        omegag = 4.480075654158969e-07 * T_CMB**4 / self.hubble**2
        self.omegag = omegag
        self.omega_ur = omegag * 0.22710731766023898 * (self.N_ur - 1.013198221453432*3)  # MP-Gadget
        # assert self.omega_ur >= 0

        assert MWDM_therm >= 0
        self.MWDM_therm = MWDM_therm

        
        #Neutrino accuracy for CLASS
        self.nu_acc  = nu_acc

        #UVB? Only matters if gas
        self.uvb = uvb
        assert self.uvb == "hm" or self.uvb == "fg" or self.uvb == "sh" or self.uvb == "pu"

        self.rscatter = rscatter

        outdir = os.path.realpath(os.path.expanduser(outdir))

        #Make the output directory: will fail if parent does not exist
        if not os.path.exists(outdir):
            os.mkdir(outdir)
        else:
            if os.listdir(outdir) != []:
                print("Warning: ", outdir, " is non-empty")

        #Structure seed.
        self.seed = seed

        #Baryons?
        self.separate_gas = False # separate_gas

        #If neutrinos are combined into the DM,
        #we want to use a different CAMB transfer when checking output power.
        self.separate_nu  = False
        self.m_nu         = m_nu
        self.nu_hierarchy = nu_hierarchy

        self.outdir = outdir
        self._set_default_paths(gadget_dir)

        # initialize the cluster object: to store the submit info for specific
        # cluster in used
        self._cluster = cluster_class(
            gadget = self.gadgetexe, param      = self.gadgetparam, 
            genic  = self.genicexe,  genicparam = self.genicout, 
            nproc  = nproc,          cores      = cores,
            gadget_dir = gadget_dir, mpi_ranks = mpi_ranks, threads = threads)                     # add nproc and cores
                                                         # make them optional
        assert self._cluster.gadget_dir == os.path.expanduser(gadget_dir)

        #For repeatability, we store git hashes of Gadget, GenIC, CAMB and ourselves
        #at time of running.
        self.simulation_git = utils.get_git_hash(os.path.dirname(__file__))

        # sometime the path to python is slightly different, especially you have
        # multiple pythons and multiple virtual env
        self.python = python
        print("__init__: done.", datetime.datetime.now(),"\n")

    def __repr__(self) -> str:
        print_string  = "MP-Gadget path: {}\n\n".format(self.gadget_dir)

        # Hyperparameter for simulations 
        print_string += "HyperParameters: \n"
        print_string += "----\n"
        print_string += "box {} Mpc/h; npart {}; redshift {}-{}\n".format(
            self.box, self.npart, self.redshift, self.redend)
        print_string += "\n"

        # Cosmology parameters
        print_string += "Cosmology: \n"
        print_string += """----
Omega0 = {}; OmegaB   = {}; H    = {}; scalar amp = {};
n_s    = {}; rscatter = {}; m_nu = {}; nu_hierarchy = {}; w0 = {}; wa = {};
        \n""".format(
            self.omega0, self.omegab, self.hubble, self.scalar_amp,
            self.ns, self.rscatter, self.m_nu, self.nu_hierarchy, self.w0_fld, self.wa_fld)

        print_string += "Cluster: *{}*\n".format(self._cluster.cluster_name)
        print_string += "----\n"
        print_string += self.cluster.__repr__() + "\n"

        #Generate an mpi_submit for genic
        zstr = self._camb_zstr(self.redshift)
        check_ics = "{} cambpower.py {} --czstr {} --mnu {}".format(
            self.python, self.genicout, zstr, str(self.m_nu))

        # In case a sample submission script will be useful:
        print_string += "Example Submission Script:\n"
        print_string += "----\n"
        print_string += self._cluster.generate_mpi_submit_genic(self.outdir,
            extracommand=check_ics, return_str=True)
        print_string += "\n"
        print_string += self._cluster.generate_mpi_submit(self.outdir,
            return_str=True)

        return print_string
    
    @property
    def json(self) -> dict:
        """
        these are the variables will be saved into json
        """
        return self.__dict__

    @property
    def cluster(self) -> clusters.ClusterClass:
        return self._cluster

    def _set_default_paths(self, gadget_dir) -> None:
        """Default paths and parameter names. 
        This is part of the __init__ construction"""
        #Default parameter file names
        self.gadgetparam = "mpgadget.param"
        self.genicout    = "_genic_params.ini"

        #Executable names
        self.gadgetexe = "MP-Gadget"
        self.genicexe  = "MP-GenIC"

        defaultpath = os.path.dirname(__file__)

        #Default GenIC paths
        self.genicdefault = os.path.join(defaultpath, "mpgenic.ini")
        self.gadgetconfig = "Options.mk"

        # this is absolute path so make sure binary is there
        self.gadget_dir   = os.path.expanduser(gadget_dir)

    def cambfile(self) -> str:
        """
        Generate the IC power spectrum using classylss.
        
        Basically is using pre_params feed into class and compute the powerspec
        files based on the range of redshift and redend. All files are stored in
        the directory camb_out.

        Return:
        ----
        camb_output (str) : power specs directory. default: "camb_linear/"
        """
        #Load high precision defaults
        print("cambfile: loading defaults...", datetime.datetime.now())
        pre_params = {
            'tol_background_integration': 1e-9, 'tol_perturb_integration' : 1.e-7,
            'tol_thermo_integration':1.e-5, 'k_per_decade_for_pk': 50,'k_bao_width': 8,
            'k_per_decade_for_bao':  200, 'neglect_CMB_sources_below_visibility' : 1.e-30,
            'transfer_neglect_late_source': 3000., 'l_max_g' : 50,
            'l_max_ur':150, 'extra metric transfer functions': 'y'}

        #Set the neutrino density and subtract it from omega0
        omeganu = self.m_nu/93.14/self.hubble**2
        omcdm   = (self.omega0 - self.omegab) - omeganu
        gparams = {'h': self.hubble, 'Omega_cdm': omcdm,'Omega_b': self.omegab,
            'Omega_k': 0, 'n_s': self.ns, 'A_s': self.scalar_amp, 'alpha_s': self.alpha_s}

        #Lambda is computed self-consistently
        if self.w0_fld != -1.0 or self.wa_fld != 0.:
            gparams['Omega_Lambda'] = 0
            gparams['w0_fld'] = self.w0_fld 
            gparams['wa_fld'] = self.wa_fld
            if (gparams['w0_fld'] + gparams['wa_fld'] + 1) * (1 + gparams['w0_fld']) > 0: # if not phantom-crossing
                gparams['use_ppf'] = 'no'
        else:
            gparams['Omega_fld'] = 0

        numass = get_neutrino_masses(self.m_nu, self.nu_hierarchy)

        #Set up massive neutrinos
        if self.m_nu > 0:
            print("cambfile: setting up massive neutrinos...")
            # gparams['m_ncdm'] = '%.8f,%.8f,%.8f' % (numass[2], numass[1], numass[0])
            # gparams['N_ncdm'] = 3

            m_ncdm = ''
            N_ncdm = 0
            for i, numa in enumerate(numass):
                if numa == 0:
                    continue
                if N_ncdm == 0:
                    m_ncdm += '%.8f' % numa
                else:
                    m_ncdm += ',%.8f' % numa 
                N_ncdm += 1           
            gparams['m_ncdm'] = m_ncdm
            gparams['N_ncdm'] = N_ncdm
            
            # gparams['N_ur'] = 0.00641
            # gparams['N_ur'] = self.N_ur - 3
            gparams['N_ur'] = self.N_ur - gparams['N_ncdm'] * 1.013198221453432 # for N_ncdm = 3, N_ur = N_ur^desired - 3.0395946643602962
            #Neutrino accuracy: Default pk_ref.pre has tol_ncdm_* = 1e-10,
            #which takes 45 minutes (!) on my laptop.
            #tol_ncdm_* = 1e-8 takes 20 minutes and is machine-accurate.
            #Default parameters are fast but off by 2%.
            #I chose 1e-5, which takes 6 minutes and is accurate to 1e-5
            gparams['tol_ncdm_newtonian'] = min(self.nu_acc,1e-5)
            gparams['tol_ncdm_synchronous'] = self.nu_acc
            gparams['tol_ncdm_bg'] = 1e-10
            gparams['l_max_ncdm'] = 50
            #This disables the fluid approximations, which make P_nu not match 
            # camb on small scales.
            #We need accurate P_nu to initialise our neutrino code.
            gparams['ncdm_fluid_approximation'] = 3 # 3: disable approximation; # enum ncdmfa_method {ncdmfa_mb,ncdmfa_hu,ncdmfa_CLASS,ncdmfa_none};
            #Does nothing unless ncdm_fluid_approximation = 2
            #Spend less time on neutrino power for smaller neutrino mass
            gparams['ncdm_fluid_trigger_tau_over_tau_k'] = 30000.* (self.m_nu / 0.4)
        else:
            # gparams['N_ur'] = 3.046
            gparams['N_ur'] = self.N_ur # for mnu = 0, N_ur cannot be set to 0 in CLASS

        #Initial cosmology
        pre_params.update(gparams)

        maxk        = 2 * math.pi / self.box * self.npart * 8
        powerparams = {'output': 'dTk vTk mPk', 'P_k_max_h/Mpc' : maxk, 
            "z_max_pk" : self.redshift + 1}
        pre_params.update(powerparams)

        #At which redshifts should we produce CAMB output: we want the start and
        # end redshifts of the simulation, but we also want some other values
        # for checking purposes
        camb_zz = np.concatenate(
            [ [self.redshift,], 
             1 / self.generate_times() - 1,
              [self.redend,] ] )

        cambpars  = os.path.join(self.outdir, "_class_params.ini")
        classconf = configobj.ConfigObj()
        classconf.filename = cambpars
        classconf.update(pre_params)
        classconf['z_pk'] = camb_zz
        classconf.write()

        # feed in the parameters and generate the powerspec object
        print("cambfile: generating the powerspec object...")
        engine  = CLASS.ClassEngine(pre_params)
        powspec = CLASS.Spectra(engine) # powerspec is an object

        # bg = CLASS.Background(engine)
        # pre_params['Omega_fld'] = 1 - self.omega0 + bg.Omega0_lambda  # so that Omega0_lambda == 0 (forced)

        # engine  = CLASS.ClassEngine(pre_params)
        # powspec = CLASS.Spectra(engine) # powerspec is an object


        #Save directory
        camb_output = "camb_linear/" # actually class now
        camb_outdir = os.path.join(self.outdir, camb_output)
        try:
            os.mkdir(camb_outdir)
        except FileExistsError:
            pass

        #Save directory
        #Get and save the transfer functions
        print("cambfile: getting and saving the transfer functions...")
        for zz in camb_zz:
            trans = powspec.get_transfer(z=zz)

            #fp-roundoff
            trans['k'][-1] *= 0.9999
            transferfile = os.path.join(
                camb_outdir, "ics_transfer_" + self._camb_zstr(zz) + ".dat")
            save_transfer(trans, transferfile)

            pk_lin = powspec.get_pklin(k=trans['k'], z=zz)
            pkfile = os.path.join(
                camb_outdir, "ics_matterpow_" + self._camb_zstr(zz) + ".dat")

            np.savetxt(pkfile, np.vstack([trans['k'], pk_lin]).T)
        print("cambfile: done.", datetime.datetime.now(),"\n")
        return camb_output

    def _camb_zstr(self, zz : float) -> str:
        """Get the formatted redshift for CAMB output files."""
        if zz > 10:
            zstr = str(int(zz))
        else:
            zstr = '%.1g' % zz
        return zstr

    def genicfile(self, camb_output : str) -> Tuple[str, Any]:
        """
        Generate the GenIC parameter file
        
        Parameters:
        ----
        camb_output (str) : power specs directory. default: "camb_linear/"

        Returns:
        ----
        os.path.join(genicout, genicfile) (str) : path to genic file
        config.filename (str):  genicout filename
        """
        config = configobj.ConfigObj(self.genicdefault)
        
        config.filename   = os.path.join(self.outdir, self.genicout)
        config['BoxSize'] = self.box * 1000

        genicout = "ICS"

        try:
            os.mkdir(os.path.join(self.outdir, genicout))
        except FileExistsError:
            pass

        config['OutputDir'] = genicout

        #Is this enough information, or should I add a short hash?
        genicfile = str(self.box) + "_" + str(self.npart) + "_" + str(self.redshift)

        config['FileBase'] = genicfile
        config['Ngrid']    = self.npart
        config['NgridNu']  = 0
        #config['MaxMemSizePerNode'] = 0.8
        config['ProduceGas'] = 0 # int(self.separate_gas)

        #Suppress Gaussian mode scattering
        config['UnitaryAmplitude'] = int(self.unitary)

        #The 2LPT correction is computed for one fluid. It is not clear
        #what to do with a second particle species, so turn it off.
        #Even for CDM alone there are corrections from radiation:
        #order: Omega_r / omega_m ~ 3 z/100 and it is likely
        #that the baryon 2LPT term is dominated by the CDM potential
        #(YAH, private communication)

        #Total matter density, not CDM matter density.
        config['Omega0']      = self.omega0
        
        config['OmegaBaryon'] = self.omegab
        config['HubbleParam'] = self.hubble
        config['Redshift']    = self.redshift

        # MP-Gadget dark energy models
        if self.w0_fld != -1.0 or self.wa_fld != 0.:
            config['OmegaLambda'] = 0  # set to 0 since Omega_fld is enabled
            config["Omega_fld"]   = 1 - self.omega0 - self.omegag - self.omega_ur
            config["w0_fld"]      = self.w0_fld
            config["wa_fld"]      = self.wa_fld
        else:
            config['OmegaLambda'] = 1 - self.omega0 - self.omegag - self.omega_ur
            config["Omega_fld"]   = 0

        config["CLASS_Radiation"]      = 1 # CLASS convention Omega_tot = Omega_m + Omega_g + Omega_Lambda + Omega_fld + Omega_ur + Omega_K = 1 

        config["MWDM_therm"]  = self.MWDM_therm

        config["Omega_ur"]    = self.omega_ur
        
        zstr = self._camb_zstr(self.redshift)
        config['FileWithInputSpectrum']    = camb_output + "ics_matterpow_"+ zstr + ".dat"
        config['FileWithTransferFunction'] = camb_output + "ics_transfer_" + zstr + ".dat"

        numass = get_neutrino_masses(self.m_nu, self.nu_hierarchy)
        config['MNue'] = numass[2]
        config['MNum'] = numass[1]
        config['MNut'] = numass[0]
        assert config['WhichSpectrum'] == '2'  # we use class to generate the spectrum (A_s and n_s are used by class, so they are not included in gadget ic paramfile)
        assert config['RadiationOn'] == '1'
        assert config['DifferentTransferFunctions'] == '1'
        assert config['InputPowerRedshift'] == '-1'
        config['Seed'] = self.seed

        config = self._genicfile_child_options(config)
        config.update(self._cluster.cluster_runtime())
        config.write()

        return (os.path.join(genicout, genicfile), config.filename)

    def _alter_power(self, camb_output: str) -> None:
        """
        Function to hook if you want to change the CAMB output power spectrum.
        Should save the new power spectrum to camb_output + _matterpow_str(redshift).dat
        
        Parameters:
        ----
        camb_output (str) : power specs directory. default: "camb_linear/"

        Return:
        ----
        (None)
        """
        zstr      = self._camb_zstr(self.redshift)
        camb_file = os.path.join(camb_output, "ics_matterpow_" + zstr + ".dat")
        os.stat(camb_file)
        return

    def _genicfile_child_options(self,
            config : configobj.ConfigObj) -> configobj.ConfigObj:
        """Set extra parameters in child classes"""
        return config

    def txt_description(self) -> None:
        """
        Generate a text file describing the parameters of the code that generated
        this simulation, for reproducibility.
        """
        #But ditch the output of make
        self.make_output = ""
        self._really_arrays: List[str]= []
        self._really_types: List[str] = []
        cc = self._cluster
        self._cluster = 0   # this line causes mypy incompatible problem, but
                            # currently I ingore it due to do not want to make
                            # too many modifications to previous code

        for nn, val in self.__dict__.items():
            #Convert arrays to lists
            if isinstance(val, np.ndarray):
                self.__dict__[nn] = val.tolist()
                self._really_arrays.append(nn)
            #Convert types to string tuples
            if isinstance(val, type):
                self.__dict__[nn] = (val.__module__, val.__name__)
                self._really_types.append(nn)
        with open(os.path.join(self.outdir, "SimulationICs.json"), 'w') as jsout:
            json.dump(self.__dict__,jsout)

        #Turn the changed types back.
        self._fromarray()
        self._cluster = cc

    def _fromarray(self) -> None:
        """Convert the data stored as lists back to what it was."""
        for arr in self._really_arrays:
            self.__dict__[arr] = np.array(self.__dict__[arr])
        self._really_arrays = []
        for arr in self._really_types:
            #Some crazy nonsense to convert the module, name
            #string tuple we stored back into a python type.
            mod = importlib.import_module(self.__dict__[arr][0])
            self.__dict__[arr] = getattr(mod, self.__dict__[arr][1])
        self._really_types = []

    def load_txt_description(self) -> None:
        """
        Load the text file describing the parameters of the code that generated
        a simulation.
        """
        cc = self._cluster
        with open(os.path.join(self.outdir, "SimulationICs.json"), 'r') as jsin:
            self.__dict__ = json.load(jsin)
        self._fromarray()
        self._cluster = cc

    def gadget3config(self, prefix: str = "OPT += -D") -> str:
        """
        Generate a config Options file for Yu Feng's MP-Gadget.
        This code is configured via runtime options.
        
        Parameters:
        ----
        prefix (str) : default "OPT += -D"

        Returns:
        ----
        g_config_filename (str) : path to self.gadgetconfig
        """
        g_config_filename = os.path.join(self.outdir, self.gadgetconfig)

        with open(g_config_filename,'w') as config:
            config.write("MPICC = mpicc\nMPICXX = mpic++\n")
            optimize = self._cluster.cluster_optimize()
            config.write("OPTIMIZE = "+optimize+"\n")
            config.write(str(
                "GSL_INCL = $(shell gsl-config --cflags)\n"
                "GSL_LIBS = $(shell gsl-config --libs)\n"))
            self._cluster.cluster_config_options(config, prefix)
            # self._gadget3_child_options(config, prefix)

        return g_config_filename

    # unknown function here
    # def _gadget3_child_options(self, _, __) ->:
    #     """Gadget-3 compilation options for Config.sh which should be written by
    #     the child class. This is MP-Gadget, so it is likely there are none."""
    #     return

    def gadget3params(self, genicfileout: str) -> None:
        """MP-Gadget parameter file. This *is* a configobj.
        Note MP-Gadget supports default arguments, so no need for a defaults file.

        Arguments:
        ----
            genicfileout (str) - where the ICs are saved
        """
        config   = configobj.ConfigObj()
        filename = os.path.join(self.outdir, self.gadgetparam)
        
        config.filename = filename
        
        config['InitCondFile'] = genicfileout
        config['OutputDir']    = "output"

        try:
            os.mkdir(os.path.join(self.outdir, "output"))
        except FileExistsError:
            pass

        config['TimeLimitCPU'] = int(60 * 60 * self._cluster.timelimit - 300)
        config['TimeMax']      = 1. / (1 + self.redend)
        config['Omega0']       = self.omega0
        
        # dark energy models
        if self.w0_fld != -1.0 or self.wa_fld != 0.:
            config['OmegaLambda']  = 0
            config['Omega_fld'] = 1 - self.omega0 - self.omegag - self.omega_ur
            config["w0_fld"]      = self.w0_fld
            config["wa_fld"]      = self.wa_fld
        else:
            config['OmegaLambda']  = 1 - self.omega0 - self.omegag - self.omega_ur # LambdaCDM

        config["Omega_ur"]    = self.omega_ur

        #OmegaBaryon should be zero for gadget if we don't have gas particles
        config['OmegaBaryon'] = self.omegab * False # self.separate_gas; 
                                                    # always False for dm-only
        config['HubbleParam'] = self.hubble
        config['RadiationOn'] = 1
        config['HydroOn']     = 1

        #Neutrinos
        if self.m_nu > 0:
            config['MassiveNuLinRespOn'] = 1
        else:
            config['MassiveNuLinRespOn'] = 0

        numass = get_neutrino_masses(self.m_nu, self.nu_hierarchy)
        config['MNue'] = numass[2]
        config['MNum'] = numass[1]
        config['MNut'] = numass[0]

        #FOF
        config['SnapshotWithFOF']      = 1
        config['FOFHaloLinkingLength'] = 0.2
        config['OutputList']           =  ','.join(
            [str(t) for t in self.generate_times()])

        #These are only used for gas, but must be set anyway
        config['MinGasTemp'] = 100

        #In equilibrium with the CMB at early times.
        config['InitGasTemp'] = 2.7*(1+self.redshift)
        config['DensityIndependentSphOn'] = 1
        config['PartAllocFactor'] = 2
        config['WindOn'] = 0
        config['WindModel'] = 'nowind'
        config['BlackHoleOn'] = 0
        config['OutputPotential'] = 0
        config['MetalReturnOn'] = 0   # unknown parameter for some version of MP-Gadget3

        # Removed due to no need for baryon
        # if self.separate_gas:
        #     config['CoolingOn'] = 1
        #     config['TreeCoolFile'] = "TREECOOL"
        #     #Copy a TREECOOL file into the right place.
        #     self._copy_uvb()
        #     config = self._sfr_params(config)
        #     config = self._feedback_params(config)
        # else:
        config['CoolingOn'] = 0
        config['StarformationOn'] = 0

        if self.cluster.cluster_name == "FronteraClass":
            config['MaxMemSizePerNode'] = 0.8

        #Add other config parameters
        config = self._other_params(config)
        config.update(self._cluster.cluster_runtime())
        config.write()

        return

    # def _sfr_params(self, config):
    #     """Config parameters for the default Springel & Hernquist star formation model"""
    #     config['StarformationOn'] = 1
    #     config['StarformationCriterion'] = 'density'
    #     return config

    # def _feedback_params(self, config):
    #     """Config parameters for the feedback models"""
    #     return config

    def _other_params(self, config: configobj.ConfigObj) -> configobj.ConfigObj:
        """Function to override to set other config parameters"""
        return config

    def generate_times(self) -> np.ndarray:
        """List of output times for a simulation. Can be overridden."""
        astart = 1. / (1 + self.redshift)
        aend   = 1. / (1 + self.redend  )

        times = np.array([0.02, 0.1, 0.2, 0.25, 0.3333, 0.5, 0.66667, 0.83333])

        ii = np.where((times > astart) * (times < aend))
        assert np.size(times[ii]) > 0

        return times[ii]

    def do_gadget_build(self, gadget_config: str) -> None:
        """Make a gadget build and check it succeeded."""
        conffile = os.path.join(self.gadget_dir, self.gadgetconfig)
        if os.path.islink(conffile):
            os.remove(conffile)
        if os.path.exists(conffile):
            os.rename(conffile, conffile+".backup")
        os.symlink(gadget_config, conffile)
        #Build gadget
        gadget_binary = os.path.join(os.path.join(self.gadget_dir, "gadget"), self.gadgetexe)
        try:
            g_mtime = os.stat(gadget_binary).st_mtime
        except FileNotFoundError:
            g_mtime = -1
        self.gadget_git = utils.get_git_hash(gadget_binary)
        try:
            self.make_output = subprocess.check_output(
                ["make", "-j"], cwd=self.gadget_dir, universal_newlines=True,
                stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError as e:
            print(e.output)
            raise

        #Check that the last-changed time of the binary has actually changed..
        assert g_mtime != os.stat(gadget_binary).st_mtime
        shutil.copy(gadget_binary, os.path.join(os.path.dirname(gadget_config),self.gadgetexe))

    def generate_mpi_submit(self, genicout: str, return_str: bool = False) -> str:
        """Generate a sample mpi_submit file.
        The prefix argument is a string at the start of each line.
        It separates queueing system directives from normal comments"""
        # self._cluster.generate_mpi_submit(self.outdir)
        

        #Generate an mpi_submit for genic
        zstr = self._camb_zstr(self.redshift)
        check_ics = "{} cambpower.py {} --czstr {} --mnu {}".format(
            self.python, genicout, zstr, str(self.m_nu))

        self._cluster.generate_mpi_submit_one(self.outdir, extracommand=check_ics)
        # if return_str:
            # return self._cluster.generate_mpi_submit_genic(
                # self.outdir, extracommand=check_ics)

        # self._cluster.generate_mpi_submit_genic(
            # self.outdir, extracommand=check_ics)            

        #Copy the power spectrum routine
        shutil.copy(os.path.join(os.path.dirname(__file__), "cambpower.py"),
            os.path.join(self.outdir, "cambpower.py"))

    def make_simulation(self, pkaccuracy: float = 0.05,
            do_build: bool = False) -> str:
        """Wrapper function to make the simulation ICs."""
        #First generate the input files for CAMB
        print("Making simulation submission files,", datetime.datetime.now())
        print("Make simulation: generating the input file for CAMB...")
        camb_output = self.cambfile()

        #Then run CAMB
        print("Make simulation: running CAMB...")
        self.camb_git = classylss.__version__

        #Change the power spectrum file on disc if we want to do that
        print("Make simulation: changing the power spectrum file on disc...")
        self._alter_power(os.path.join(self.outdir,camb_output))

        #Now generate the GenIC parameters
        print("Make simulation: generating the GenIC parameters...")
        (genic_output, genic_param) = self.genicfile(camb_output)

        #Save a json of ourselves.
        # self.json to get the json dict variable
        self.txt_description()

        #Check that the ICs have the right power spectrum
        #Generate Gadget makefile
        print("Make simulation: generating Gadget makefile...")
        gadget_config = self.gadget3config()

        #Symlink the new gadget config to the source directory
        #Generate Gadget parameter file
        print("Make simulation: generating Gadget parameter file...")
        self.gadget3params(genic_output)

        #Generate mpi_submit file
        print("Make simulation: generate mpi_submit file...")
        self.generate_mpi_submit(genic_output)
        

        #Run MP-GenIC
        #Compile from source; usually not need
        if do_build:
            subprocess.check_call(
                [os.path.join(os.path.join(self.gadget_dir, "genic"),
                                           self.genicexe), 
                              genic_param],
                cwd=self.outdir)

            zstr = self._camb_zstr(self.redshift)
            cambpower.check_ic_power_spectra(genic_output, camb_zstr=zstr,
                m_nu=self.m_nu, outdir=self.outdir, accuracy=pkaccuracy)

            self.do_gadget_build(gadget_config)
        print("Make simulation: done.", datetime.datetime.now(),"\n")
        return gadget_config
        

def save_transfer(transfer: np.ndarray, transferfile: str) -> None:
    """
    Save a transfer function. Note we save the CLASS FORMATTED transfer functions.
    The transfer functions differ from CAMB by:
        T_CAMB(k) = -T_CLASS(k)/k^2
    """
    header="""Transfer functions T_i(k) for adiabatic (AD) mode (normalized to initial curvature=1)
d_i   stands for (delta rho_i/rho_i)(k,z) with above normalization
d_tot stands for (delta rho_tot/rho_tot)(k,z) with rho_Lambda NOT included in rho_tot
(note that this differs from the transfer function output from CAMB/CMBFAST, which gives the same
 quantities divided by -k^2 with k in Mpc^-1; use format=camb to match CAMB)
t_i   stands for theta_i(k,z) with above normalization
t_tot stands for (sum_i [rho_i+p_i] theta_i)/(sum_i [rho_i+p_i]))(k,z)
%s""" % " ".join(f"{index}. {item} " for index, item in enumerate(transfer.dtype.names, start=1))
    #This format matches the default output by CLASS command line.
    np.savetxt(transferfile, transfer, header=header)

def get_neutrino_masses(total_mass: float, hierarchy: str) -> np.ndarray:
    """Get the three neutrino masses, including the mass splittings.
        Hierarchy is 'inverted' (two heavy), 'normal' (two light) or degenerate."""
    #Neutrino mass splittings
    nu_M21 = 7.53e-5 #Particle data group 2016: +- 0.18e-5 eV2
    nu_M32n = 2.44e-3 #Particle data group: +- 0.06e-3 eV2
    nu_M32i = 2.51e-3 #Particle data group: +- 0.06e-3 eV2

    if hierarchy == 'normal':
        nu_M32 = nu_M32n
        #If the total mass is below that allowed by the hierarchy,
        #assign one active neutrino.
        # if total_mass < np.sqrt(nu_M32n) + np.sqrt(nu_M21):
        if total_mass < .06:
            return np.array([total_mass, 0, 0])
    elif hierarchy == 'inverted':
        nu_M32 = -nu_M32i
        if total_mass < 2*np.sqrt(nu_M32i) - np.sqrt(nu_M21):
            return np.array([total_mass/2., total_mass/2., 0])
    #Hierarchy == 0 is 3 degenerate neutrinos
    else:
        return np.ones(3)*total_mass/3.

    #DD is the summed masses of the two closest neutrinos
    DD1 = 4 * total_mass/3. - 2/3.*np.sqrt(total_mass**2 + 3*nu_M32 + 1.5*nu_M21)
    #Last term was neglected initially. This should be very well converged.
    DD = 4 * total_mass/3. - 2/3.*np.sqrt(total_mass**2 + 3*nu_M32 + 1.5*nu_M21+0.75*nu_M21**2/DD1**2)
    nu_masses = np.array([ total_mass - DD, 0.5*(DD + nu_M21/DD), 0.5*(DD - nu_M21/DD)])
    assert np.isfinite(DD)
    assert np.abs(DD1/DD -1) < 2e-2
    assert np.all(nu_masses >= 0)
    return nu_masses
