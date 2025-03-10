"""
Specialised module to contain functions to specialise the simulation run to
different clusters
"""
from typing import List, Union, Any, TextIO
import os.path
import math
import numpy as np

class ClusterClass:
    """
    Generic class implementing some general defaults for cluster submissions.
    """
    def __init__(self, gadget: str = "MP-Gadget", genic: str = "MP-GenIC", 
            param: str = "mpgadget.param", 
            genicparam: str = "_genic_params.ini", 
            nproc: int = 256, cores: int = 16, mpi_ranks: int = 8, threads: int = 16,
            timelimit: Union[float, int] = 24, cluster_name: str = "Template", 
            gadget_dir: str = "~/bigdata/code/MP-Gadget/") -> None:
        """
        CPU parameters (walltime, number of cpus, etc):
        these are specified to a default here, but should be over-ridden in a
        machine-specific decorator."""
        self.nproc        = nproc
        self.cores        = cores
        self.mpi_ranks    = mpi_ranks
        self.threads      = threads
        self.email        = "yyang440@ucr.edu"
        self.timelimit    = timelimit  # in hours
        self.cluster_name = cluster_name

        self.gadget_dir   = os.path.expanduser(gadget_dir)

        #Maximum memory available for an MPI task
        self.memory      = 1800
        self.gadgetexe   = os.path.join( self.gadget_dir, 'gadget', gadget )
        self.gadgetparam = param
        self.genicexe    = os.path.join( self.gadget_dir, 'genic', genic   )
        self.genicparam  = genicparam


    def __repr__(self) -> str:
        '''
        print out the default setting
        '''
        print_string  = "N Processers: {}; N cores: {}; N nodes: {}; Email: {}\n".format(
            self.nproc, self.cores, self.nproc // self.cores, self.email)
        print_string += "Timelimit: {}\n".format(
            self.timestring(self.timelimit))

        return print_string

    def generate_mpi_submit(self, outdir: str, return_str: bool = False) -> Any:
        """
        Generate a sample mpi_submit file.
        The prefix argument is a string at the start of each line.
        It separates queueing system directives from normal comments
        
        Parameters:
        ----
        outdir (str)      : output directory
        return_str (bool) : do not write file but return a string of submission 
            file, I prefer to see the string before I write into file
        """
        name = os.path.basename(os.path.normpath(outdir))[-8:]

        if return_str:
            print_str  = "#!/bin/bash\n" 
            print_str += self._queue_directive(
                name, timelimit=self.timelimit, nproc=self.nproc, cores=self.cores)
            print_str += self._mpi_program(
                command="{} {}".format(self.gadgetexe, self.gadgetparam))
            return print_str

        with open(os.path.join(outdir, "mpi_submit"),'w') as mpis:
            mpis.write("#!/bin/bash\n")
            
            # #PBS -j eo
            # #PBS -m bae
            # #PBS -M {email}
            # #PBS -l walltime={timelimit}
            mpis.write(self._queue_directive(
                name, timelimit=self.timelimit, nproc=self.nproc, cores=self.cores))
            
            # mpirun -np {nproc} {command}
            mpis.write(self._mpi_program(command="{} {}".format(
                    self.gadgetexe, self.gadgetparam)))
        
        return

    def generate_mpi_submit_genic(
            self, outdir: str, extracommand: Union[str, Any] = None,
            return_str: bool = False) -> Any:
        """Generate a sample mpi_submit file for MP-GenIC.
        The prefix argument is a string at the start of each line.
        It separates queueing system directives from normal comments"""
        name: str = os.path.basename(os.path.normpath(outdir))

        if return_str:
            mpis  = "#!/bin/bash\n"
            mpis += self._queue_directive(name, timelimit=0.5, nproc=self.nproc)
            mpis += self._mpi_program(command=self.genicexe+" "+self.genicparam)

            if extracommand is not None:
                mpis += extracommand + "\n"

            return mpis

        with open(os.path.join(outdir, "mpi_submit_genic"),'w') as mpis:
            mpis.write("#!/bin/bash\n")
            mpis.write(self._queue_directive(name, timelimit=0.5, nproc=self.nproc))
            mpis.write(self._mpi_program(command=self.genicexe+" "+self.genicparam))
            if extracommand is not None:
                mpis.write(extracommand+"\n")

        return

    def generate_mpi_submit_one(
            self, outdir: str, extracommand: Union[str, Any] = None,
            return_str: bool = False) -> Any:
        """Generate a sample mpi_submit file for MP-GenIC.
        The prefix argument is a string at the start of each line.
        It separates queueing system directives from normal comments"""
        name: str = os.path.basename(os.path.normpath(outdir))[-8:]

        if return_str:
            mpis  = "#!/bin/bash\n"
            mpis += self._queue_directive(name, timelimit=self.timelimit, nproc=self.nproc)
            mpis += self._mpi_program(command=self.genicexe+" "+self.genicparam)

            if extracommand is not None:
                mpis += extracommand + "\n"

            return mpis

        with open(os.path.join(outdir, "mpi_submit_one"),'w') as mpis:
            mpis.write("#!/bin/bash\n")
            mpis.write(self._queue_directive(name, timelimit=self.timelimit, nproc=self.nproc, mpi_ranks=self.mpi_ranks))
            mpis.write("hostname\n")
            mpis.write("date\n")
            mpis.write(self._mpi_program(command=self.genicexe+" "+self.genicparam, threads=self.threads))
            # mpis.write(self._mpi_program(command="{} {}".format(
                  #  self.gadgetexe, self.gadgetparam)))
            mpis.write("mpirun {} {}\n".format(self.gadgetexe, self.gadgetparam))
            if extracommand is not None:
                mpis.write(extracommand+"\n")
            mpis.write("date\n")

        return

    def _mpi_program(self, command: str) -> str:
        """String for MPI program to execute"""
        qstring = "mpirun -np {} {}\n".format(str(self.nproc), command)
        return qstring

    def timestring(self, timelimit: Union[float, int]) -> str:
        """Convert a fractional timelimit into a string"""
        # timelimit in hour
        hr     = int(timelimit)
        minute = int((timelimit - hr)*60)
        assert 0 <= minute < 60
    
        timestring = "{}:{}:00".format(str(hr), str(minute))

        return timestring

    def _queue_directive(self, name: Union[str, TextIO],
            timelimit: Union[float, int], 
            nproc: int = 16, prefix: str = "#PBS") -> str:
        """Write the part of the mpi_submit file that directs the queueing 
        system. This is usually specific to a given cluster.
        The prefix argument is a string at the start of each line.
        It separates queueing system directives from normal comments"""
        _ = name
        _ = nproc
        
        qstring = prefix  + " -j eo\n"
        qstring += prefix + " -m bae\n"
        qstring += prefix + " -M {}\n".format(self.email)
        qstring += prefix + " -l walltime={}\n".format(self.timestring(timelimit))

        return qstring

    def cluster_runtime(self) -> dict:
        """Runtime options for cluster. Applied to both MP-GenIC and MP-Gadget."""
        return {}

    def cluster_config_options(self, config: str, prefix: str = "") -> None:
        """Config options that might be specific to a particular cluster"""
        _ = (config, prefix)
        #isend/irecv is quite slow on some clusters because of the extra memory 
        # allocations.
        #Maybe test this on your specific system and see if it helps.
        #config.write(prefix+"NO_ISEND_IRECV_IN_DOMAIN\n")
        #config.write(prefix+"NO_ISEND_IRECV_IN_PM\n")
        #config.write(prefix+"NOTYPEPREFIX_FFTW\n")

    def cluster_optimize(self) -> str:
        """Compiler optimisation options for a specific cluster.
        Only MP-Gadget pays attention to this."""
        return "-fopenmp -O3 -g -Wall -ffast-math -march=native"

class HipatiaClass(ClusterClass):
    """Subclassed for specific properties of the Hipatia cluster in Barcelona.
    __init__ and _queue_directive are changed."""
    def __init__(self, *args, cluster_name: str = "Hipatia", **kwargs) -> None:
        super().__init__(*args, cluster_name = cluster_name, **kwargs)
        self.memory = 2500

    def _queue_directive(self, name: Union[str, TextIO],
            timelimit: Union[float, int], nproc: int = 16,
            prefix: str = "#PBS") -> str:
        """Generate mpi_submit with coma specific parts"""
        qstring = super()._queue_directive(name=name, prefix=prefix, timelimit=timelimit)
        qstring += prefix+" -l nodes="+str(int(nproc/16))+":ppn=16\n"
        qstring += prefix+" -l mem="+str(int(self.memory*nproc/1000))+"g\n"
        #Pass environment to child processes
        qstring += prefix+" -V\n"
        return qstring

    def _mpi_program(self, command: str) -> str:
        """String for MPI program to execute. 
        Hipatia is weird because PBS_JOBID needs to be unset for the job to 
        launch."""
        #Change to current directory
        qstring = "cd $PBS_O_WORKDIR\n"
        #Don't ask me why this works, but it is necessary.
        qstring += "unset PBS_JOBID\n"
        qstring += "mpirun -np "+str(self.nproc)+" "+command+"\n"
        return qstring

class MARCCClass(ClusterClass):
    """Subclassed for the MARCC cluster at JHU.
    This has 24 cores per node, shared memory of 128GB pr node.
    Ask for complete nodes.
    Uses SLURM."""
    def __init__(self, *args, nproc: int = 48, timelimit: Union[float, int] = 8,
            cluster_name: str = "MARCC", **kwargs) -> None:
        #Complete nodes!
        assert nproc % 24 == 0
        super().__init__(*args, nproc = nproc, timelimit = timelimit,
            cluster_name = cluster_name, **kwargs)
        self.memory = 5000

    def _queue_directive(self, name: Union[str, TextIO], timelimit: Union[float, int], nproc: int = 48,
            prefix: str = "#SBATCH") -> str:
        """Generate mpi_submit with coma specific parts"""
        _ = timelimit
        qstring = prefix+" --partition=parallel\n"
        qstring += prefix+" --job-name="+name+"\n"
        qstring += prefix+" --time="+self.timestring(timelimit)+"\n"
        qstring += prefix+" --nodes="+str(int(nproc/24))+"\n"
        #Number of tasks (processes) per node
        qstring += prefix+" --ntasks-per-node=24\n"
        #Number of cpus (threads) per task (process)
        qstring += prefix+" --cpus-per-task=1\n"
        #Max 128 GB per node (24 cores)
        qstring += prefix+" --mem-per-cpu="+str(self.memory)+"\n"
        qstring += prefix+" --mail-type=end\n"
        qstring += prefix+" --mail-user="+self.email+"\n"
        return qstring

    def _mpi_program(self, command: str) -> str:
        """String for MPI program to execute.
        Note that this assumes you aren't using threads!"""
        #Change to current directory
        qstring = "export OMP_NUM_THREADS=1\n"
        #This is for threads
        #qstring += "export OMP_NUM_THREADS = $SLURM_CPUS_PER_TASK\n"
        #Adjust for thread/proc balance per socket.
        #qstring += "mpirun --map-by ppr:3:socket:PE=4 "+self.gadgetexe+" "+
        # self.gadgetparam+"\n"
        qstring += "mpirun --map-by core "+command+"\n"
        return qstring

    def cluster_optimize(self) -> str:
        """Compiler optimisation options for a specific cluster.
        Only MP-Gadget pays attention to this."""
        return "-fopenmp -O3 -g -Wall -march=native"

class BIOClass(ClusterClass):
    """Subclassed for the biocluster at UCR.
    This has 32 cores per node, shared memory of 256GB per node.
    Ask for complete nodes.
    Uses SLURM.
    
    Starting from new HPCC (since March 2022), we can use the threading to speed
    up the computation.
    """
    def __init__(self, *args, nproc: int = 8, timelimit: Union[float, int] = 2, 
            cluster_name: str = "BIOCluster", 
            cores: int = 2, mpi_ranks: int = 8, threads: int = 16, memory: int = 115, **kwargs) -> None:
        # nproc: int = 8 does not seem to work, it is still 256
        # (ClusterClass default)
        
        super().__init__(*args, nproc=nproc, timelimit=timelimit,
            cluster_name=cluster_name, cores=cores, mpi_ranks=mpi_ranks, threads=threads, **kwargs)
        self.mpi_ranks = mpi_ranks 

        if memory == 115:
            n_jobs = math.ceil(256/nproc)
            memory1 = int(1024 * .95 / n_jobs)
            memory = np.min([memory, memory1])  # such that more than 8 jobs could be run simultaneously
        self.memory : int = memory

    def _queue_directive(self, name: Union[str, TextIO],
            timelimit: Union[float, int], nproc: int = 8, cores: int = 32, mpi_ranks: int = 8,
            prefix: str = "#SBATCH") -> str:
        """Generate mpi_submit with coma specific parts"""
        _ = timelimit

        nodes = math.ceil(nproc/cores)
        # SBATCH descriptions
        qstring =  prefix + " --partition=short\n"
        qstring += prefix + " --job-name={}\n".format(name)
        qstring += prefix + " --time={}\n".format(self.timestring(timelimit))
        qstring += prefix + " --nodes={}\n".format(str(nodes))
        # print("nproc = {}".format(str(int(nproc))))
        # print("nodes = {}".format(str(int(nproc/cores))))

        #Number of tasks (processes) per node
        qstring += prefix + " --ntasks-per-node={}\n".format(str(int(mpi_ranks/nodes)))

        #Number of cpus (threads) per task (process)
        qstring += prefix + " --cpus-per-task={}\n".format(str(int(nproc/mpi_ranks)))

        # # exclusive, request a full node
        # qstring += prefix + " --exclusive\n"

        # mem instead of mem-per-task, since that does not work in new HPCC
        qstring += prefix + " --mem={}G\n".format(self.memory)
        # qstring += prefix + " --mail-type=end\n"
        # qstring += prefix + " --mail-user={}\n".format(self.email)

        prefix_comment = "# SBATCH"
        qstring += prefix_comment + " --mail-type=end\n"
        qstring += prefix_comment + " --mail-user={}\n\n".format(self.email)

        return qstring

    def _mpi_program(self, command: str, threads: int = 16,) -> str:
        """String for MPI program to execute."""
        #Change to current directory
        qstring = "export OMP_NUM_THREADS={}\n".format(str(int(threads)))

        qstring += self.slurm_modules()

        #This is for threads
        #qstring += "export OMP_NUM_THREADS = $SLURM_CPUS_PER_TASK\n"
        #Adjust for thread/proc balance per socket.
        #qstring += "mpirun --map-by ppr:3:socket:PE=4 "+self.gadgetexe+" "+
        # self.gadgetparam+"\n"
        qstring += "mpirun " + command + "\n"
        return qstring

    def slurm_modules(self) -> str:
        '''
        Generate a string to setup the modules I need to load on the BioCluster
        
        Example:
        ----
        module unload openmpi\n
        module load mpich\n
        '''
        # mstring  = "module unload openmpi\n"
        # mstring += "module load mpich\n"
        # mstring += "module list\n"

        mstring  = "module unload miniconda3/py39_4.12.0\n" 

        return mstring

    def cluster_runtime(self) -> dict:
        """Runtime options for cluster. Here memory."""
        # return {'MaxMemSizePerNode': 4 * 32 * 950}
        # return {'MaxMemSizePerNode': 24320} # usually works
        return {'MaxMemSizePerNode': self.memory * 978.2608} # make it to be 225000 for memory=230

    def cluster_optimize(self) -> str:
        """Compiler optimisation options for a specific cluster.
        Only MP-Gadget pays attention to this."""
        return "-fopenmp -O3 -g -Wall -ffast-math -march=corei7"

    def generate_spectra_submit(self, outdir: str) -> None:
        """Generate a sample spectra_submit file, which generates artificial 
        spectra. The prefix argument is a string at the start of each line.
        It separates queueing system directives from normal comments"""
        name = os.path.basename(os.path.normpath(outdir))[-8:]

        with open(os.path.join(outdir, "spectra_submit"),'w') as mpis:
            mpis.write("#!/bin/bash\n")
            mpis.write("#SBATCH --partition=short\n")
            mpis.write("#SBATCH --job-name={}\n".format(name))
            mpis.write("#SBATCH --time=1:55:00\n")
            mpis.write("#SBATCH --nodes=1\n")
            mpis.write("#SBATCH --ntasks-per-node=1\n")
            mpis.write("#SBATCH --cpus-per-task=32\n")
            mpis.write("#SBATCH --mem-per-cpu=4G\n")
            mpis.write("#SBATCH --mail-type=end\n")
            mpis.write("#SBATCH --mail-user={}\n".format(self.email))
            mpis.write("export OMP_NUM_THREADS=32\n")
            mpis.write("python flux_power.py {}\n".format(
                os.path.join(name, 'output') ))

class StampedeClass(ClusterClass):
    """Subclassed for Stampede2's Skylake nodes.
    This has 48 cores (96 threads) per node, each with two sockets, shared 
    memory of 192GB per node, 96 GB per socket.
    Charged in node-hours, uses SLURM and icc."""
    def __init__(self, *args, nproc: int = 2, timelimit: Union[float, int] = 3,
            cluster_name: str = "Stampede", **kwargs) -> None:
        super().__init__(*args, nproc=nproc,timelimit=timelimit,
            cluster_name=cluster_name, **kwargs)

    def _queue_directive(self, name: Union[str, TextIO],
            timelimit: Union[float, int], nproc: int = 2, cores: int = 1,
            prefix: str = "#SBATCH", ntasks: int = 4) -> str:
        """Generate mpi_submit with stampede specific parts"""
        _ = timelimit
        qstring = prefix+" --partition=skx-normal\n"
        qstring += prefix+" --job-name={}\n".format(name)
        qstring += prefix+" --time={}\n".format(self.timestring(timelimit))
        qstring += prefix+" --nodes=%d\n" % int(nproc/cores)

        #Number of tasks (processes) per node:
        #currently optimal is 2 processes per socket.
        qstring += prefix+" --ntasks-per-node=%d\n" % int(ntasks)
        qstring += prefix+" --mail-type=end\n"
        qstring += prefix+" --mail-user={}\n".format(self.email)
        qstring += prefix+"-A TG-ASTJOBID\n"

        return qstring

    def _mpi_program(self, command: str) -> str:
        """String for MPI program to execute."""
        #Should be 96/ntasks-per-node. This uses the hyperthreading,
        #which is perhaps an extra 10% performance.
        qstring  = "export OMP_NUM_THREADS=24\n"
        qstring += "ibrun {}\n".format(command)
        return qstring

    def generate_spectra_submit(self, outdir: str, threads: int = 48) -> None:
        """Generate a sample spectra_submit file, which generates artificial 
        spectra. The prefix argument is a string at the start of each line.
        It separates queueing system directives from normal comments"""
        name = os.path.basename(os.path.normpath(outdir))[-8:]

        with open(os.path.join(outdir, "spectra_submit"),'w') as mpis:
            mpis.write("#!/bin/bash\n")
            #Nodes!
            mpis.write(self._queue_directive(name, timelimit=1, nproc=1, cores=1, ntasks=1))
            mpis.write("export OMP_NUM_THREADS=%d\n" % threads)
            mpis.write(str("export PYTHONPATH=$HOME/.local/lib/python3.6/"
                    "site-packages/:$PYTHONPATH\n"))
            mpis.write("python3 flux_power.py output")

    def cluster_runtime(self) -> dict:
        """Runtime options for cluster."""
        #Trying to print a backtrace causes the job to hang on exit
        return {'ShowBacktrace': 0}

'''
class FronteraClass(StampedeClass):
    """Subclassed for Stampede2's Skylake nodes.
    This has 56 cores (56 threads) per node, each with two sockets, shared memory of 192GB per node, 96 GB per socket.
    Charged in node-hours, uses SLURM and icc. Hyperthreading is OFF"""
    def _mpi_program(self, command: str, threads: int = 28,) -> str:
        """String for MPI program to execute."""
        #Should be 96/ntasks-per-node. This uses the hyperthreading,
        #which is perhaps an extra 10% performance.
        qstring = "export OMP_NUM_THREADS={}\n".format(str(threads))
        qstring += "ibrun "+command+"\n"
        return qstring
    
        def _queue_directive(self, name: str, timelimit: Union[int, float], nproc: int = 224, cores: int = 56, prefix: str = "#SBATCH", ntasks: int = 4):
        """Generate mpi_submit with stampede specific parts"""
        _ = timelimit
        qstring = prefix+" --partition=normal\n"
        qstring += prefix+" --job-name="+name+"\n"
        qstring += prefix+" --time="+self.timestring(timelimit)+"\n"
        qstring += prefix+" --nodes=%d\n" % int(nproc/cores)
        #Number of tasks (processes) per node:
        #currently optimal is 2 processes per socket.
        qstring += prefix+" --ntasks-per-node=%d\n" % int(ntasks)
        qstring += prefix+" --mail-type=end\n"
        qstring += prefix+" --mail-user="+self.email+"\n"
        return qstring

    def generate_spectra_submit(self, outdir: str, threads: int = 56):
        """Generate a sample spectra_submit file, which generates artificial spectra.
        The prefix argument is a string at the start of each line.
        It separates queueing system directives from normal comments"""
        super().generate_spectra_submit(outdir, threads=threads)

    def cluster_optimize(self):
        """Compiler optimisation options for frontera.
        Only MP-Gadget pays attention to this. I don't trust the compiler,
        so these are not as aggressive as usual."""
        return "-fopenmp -O2 -g -Wall -xCORE-AVX2 -Zp16 -fp-model fast=1"
'''

class FronteraClass(ClusterClass):
    def __init__(self, *args, nproc: int = 8, timelimit: Union[float, int] = 24, 
            cluster_name: str = "FronteraClass", 
            cores: int = 2, mpi_ranks: int = 8, threads: int = 16, **kwargs) -> None:
        # nproc: int = 8 does not seem to work, it is still 256
        # (ClusterClass default)
        
        super().__init__(*args, nproc=nproc, timelimit=timelimit,
            cluster_name=cluster_name, cores=cores, mpi_ranks=mpi_ranks, threads=threads, **kwargs)
        self.mpi_ranks = mpi_ranks 

    def _queue_directive(self, name: Union[str, TextIO],
            timelimit: Union[float, int], nproc: int = 224, cores: int = 56, mpi_ranks: int = 14,
            prefix: str = "#SBATCH") -> str:
        """Generate mpi_submit with coma specific parts"""
        _ = timelimit

        nodes = math.ceil(nproc/cores)
        # SBATCH descriptions
        qstring =  prefix + " --partition=normal\n"
        qstring += prefix + " --job-name={}\n".format(name)
        qstring += prefix + " --time={}\n".format(self.timestring(timelimit))
        qstring += prefix + " --nodes={}\n".format(str(nodes))
        # print("nproc = {}".format(str(int(nproc))))
        # print("nodes = {}".format(str(int(nproc/cores))))

        #Total number of tasks (processes)
        qstring += prefix + " --ntasks-per-node={}\n".format(str(int(mpi_ranks/nodes)))

        # # exclusive, request a full node
        # qstring += prefix + " --exclusive\n"
        # qstring += prefix + " --mail-type=end\n"
        # qstring += prefix + " --mail-user={}\n".format(self.email)

        prefix_comment = "# SBATCH"
        qstring += prefix_comment + " --mail-type=end\n"
        qstring += prefix_comment + " --mail-user={}\n\n".format(self.email)

        return qstring

    
    def _mpi_program(self, command: str, threads: int = 28,) -> str:
        """String for MPI program to execute."""
        #Change to current directory
        qstring = "export OMP_NUM_THREADS={}\n".format(str(int(threads)))

        # qstring += self.slurm_modules()

        #This is for threads
        #qstring += "export OMP_NUM_THREADS = $SLURM_CPUS_PER_TASK\n"
        #Adjust for thread/proc balance per socket.
        #qstring += "mpirun --map-by ppr:3:socket:PE=4 "+self.gadgetexe+" "+
        # self.gadgetparam+"\n"
        qstring += "ibrun "+command+"\n"
        return qstring
    
    def slurm_modules(self) -> str:
        '''
        Generate a string to setup the modules I need to load on the BioCluster
        
        Example:
        ----
        module unload openmpi\n
        module load mpich\n
        '''
        # mstring  = "module unload openmpi\n"
        # mstring += "module load mpich\n"
        # mstring += "module list\n"

        mstring  = "module list\n" 

        return mstring

    def cluster_runtime(self) -> dict:
        """Runtime options for cluster."""
        #Trying to print a backtrace causes the job to hang on exit
        return {'ShowBacktrace': 0}

    def cluster_optimize(self):
        """Compiler optimisation options for frontera.
        Only MP-Gadget pays attention to this. I don't trust the compiler,
        so these are not as aggressive as usual."""
        return "-fopenmp -O2 -g -Wall -xCORE-AVX2 -Zp16 -fp-model fast=1"

    def generate_spectra_submit(self, outdir: str, threads: int = 14) -> None:
        """Generate a sample spectra_submit file, which generates artificial 
        spectra. The prefix argument is a string at the start of each line.
        It separates queueing system directives from normal comments"""
        name = os.path.basename(os.path.normpath(outdir))[-8:]

        with open(os.path.join(outdir, "spectra_submit"),'w') as mpis:
            mpis.write("#!/bin/bash\n")
            #Nodes!
            mpis.write(self._queue_directive(name, timelimit=1, nproc=1, cores=1, mpi_ranks=1))
            mpis.write("export OMP_NUM_THREADS=%d\n" % threads)
            mpis.write(str("export PYTHONPATH=$HOME/.local/lib/python3.6/"
                    "site-packages/:$PYTHONPATH\n"))
            mpis.write("python3 flux_power.py output")

    def generate_mpi_submit_one(
            self, outdir: str, extracommand: Union[str, Any] = None,
            return_str: bool = False) -> Any:
        """Generate a sample mpi_submit file for MP-GenIC.
        The prefix argument is a string at the start of each line.
        It separates queueing system directives from normal comments"""
        name: str = os.path.basename(os.path.normpath(outdir))[-8:]

        if return_str:
            mpis  = "#!/bin/bash\n"
            mpis += self._queue_directive(name, timelimit=self.timelimit, nproc=self.nproc)
            mpis += self._mpi_program(command=self.genicexe+" "+self.genicparam)

            if extracommand is not None:
                mpis += extracommand + "\n"

            return mpis

        with open(os.path.join(outdir, "mpi_submit_one"),'w') as mpis:
            mpis.write("#!/bin/bash\n")
            mpis.write(self._queue_directive(name, timelimit=self.timelimit, nproc=self.nproc, mpi_ranks=self.mpi_ranks))
            mpis.write("hostname\n")
            mpis.write("date\n")
            mpis.write(self._mpi_program(command=self.genicexe+" "+self.genicparam, threads=self.threads))
            # mpis.write(self._mpi_program(command="{} {}".format(
                  #  self.gadgetexe, self.gadgetparam)))
            mpis.write("ibrun {} {}\n".format(self.gadgetexe, self.gadgetparam))
            if extracommand is not None:
                mpis.write(extracommand+"\n")
            mpis.write("date\n")

class HypatiaClass(ClusterClass):
    """Subclass for Hypatia cluster in UCL"""
    def __init__(self, *args, cluster_name : str ="Hypatia", **kwargs) -> None:
        super().__init__(*args, cluster_name=cluster_name, **kwargs)

    def _queue_directive(self, name: Union[str, TextIO],
            timelimit: Union[float, int], nproc: int = 256, cores: int = 32,
            prefix: str = "#PBS") -> str:
        """Generate Hypatia-specific mpi_submit"""
        _ = timelimit
        qstring = prefix+" -m bae\n"
        qstring += prefix+" -r n\n"
        qstring += prefix+" -q smp\n"
        qstring += prefix+" -N "+name+"\n"
        qstring += prefix+" -M "+self.email+"\n"
        qstring += prefix+" -l nodes=1:ppn="+str(nproc)+"\n"
        #Pass environment to child processes
        qstring += prefix+" -V\n"
        return qstring

    def _mpi_program(self, command: str) -> str:
        """String for MPI program to execute. 
        Hipatia is weird because PBS_JOBID needs to be unset for the job to 
        launch."""
        #Change to current directory
        qstring = "cd $PBS_O_WORKDIR\n"

        #Don't ask me why this works, but it is necessary.
        qstring += ". /opt/torque/etc/openmpi-setup.sh\n"
        qstring += "mpirun -v -hostfile $PBS_NODEFILE -npernode {} {}\n".format(
            str(self.nproc), command)

        return qstring
