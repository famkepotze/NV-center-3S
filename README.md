in scripts:

1.build structures.ipynb 
make an Nv center unit cell of 1x1x1, 2x2x2 or 3x3x3 and save to results/raw_structures.

2.geometry_optimalisation.py
relaxes these structures using QEpsuedopotentials, results are saved in results/relaxed_structures/tot_charge-1

3. calculate_dos.py
runs SCF, NCH and then calculates the DOS, results are saved in results/dos_tot_tcharge-1.

in shellscripts 
run_geometryoptimalsiation.sh & run_calcaulte_dos.sh 
are used to run a bacth of supercell ixixi where 1 =1, 2 and 3.

in helper.py
supporting snippets are stroed, f.e. calcualtor setups and a logger class ProgressUpdate. 


## TODO list
- Geometry optimalisation of supercells with total charge -1
    - 1x1x1
    - 2x2x2
    - 3x3x3

- DOS caluculations of supercells with total charge -1
    - 1x1x1
    - 2x2x2
    - 3x3x3

- Try with FHI-aims, VASP and GPAW


# NV-center-3S
A search for a simple DFT tool which can be run locally to investiagte the energy levels &amp; quantum states with ion the negatively charged Nitrogen Vacancy (NV-) center in diamonds. 

# create conda env
conda create -n 3S
conda install -c conda-forge ase
conda install jupyter
conda install python 3.11

# install Xcode developers tools
xcode-select --install

# install via compiler homebrew 
brew install gcc open-mpi fftw

# change directory to source code QE
cd ~/Downloads/qe-7.5

# configure
./configure CC=gcc FC=gfortran MPIF90=mpif90




