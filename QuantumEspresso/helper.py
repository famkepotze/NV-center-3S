import time
import re
from pathlib import Path
import numpy as np
from pathlib import Path
from ase.io import write, read
from ase.calculators.espresso import Espresso, EspressoProfile
import sys
import subprocess
from threading import Thread



# ─────────────────────────────────────────────────────────────
# QE setup
# ─────────────────────────────────────────────────────────────
qe_path = Path("/Users/famkepotze/Desktop/3S/qe-7.5")

pw_path = qe_path / "bin/pw.x"
pseudo_dir = qe_path / "pseudo"
dos_path = qe_path / "bin/dos.x"



profile = EspressoProfile(
    command=str(pw_path),
    pseudo_dir=str(pseudo_dir)
)

pseudopotentials = {
    'C': 'C.pbe-n-rrkjus_psl.1.0.0.UPF',
    'N': 'N.pbe-n-rrkjus_psl.1.0.0.UPF'
}

# ============================================================
# RELAXATION
# ============================================================



relax_calc = Espresso(
    profile=profile,
    pseudopotentials=pseudopotentials,
    input_data={
        'control': {
            'calculation': 'relax',
            'pseudo_dir': str(pseudo_dir),
            'outdir': './out',
            'tprnfor': True,
        },
        'system': {
            'ecutwfc': 60,
            'ecutrho': 480,
            'nspin': 2,
            'tot_magnetization': 2,
            'tot_charge': -1,   # NV-
            'occupations': 'smearing',
            'smearing': 'mv',
            'degauss': 0.01,
        },
        'electrons': {
            'conv_thr': 1e-8,
            'mixing_beta': 0.3,
        },
        'ions': {
            'ion_dynamics': 'bfgs',
        },
    },
    kpts=(2, 2, 2),
    directory='nv_relax'
)


base = Path("/Users/famkepotze/Desktop/3S/NV-center-3S/QuantumEspresso")
shared_outdir = str(base / "results/dos_tot_charge-1/out")

scf_calc = Espresso(
    profile=profile,
    pseudopotentials=pseudopotentials,
    input_data={
        'control': {
            'calculation': 'scf',
            'pseudo_dir': str(pseudo_dir),
            'outdir': shared_outdir,  # absolute
        },
        'system': {
            'ecutwfc': 60,
            'ecutrho': 480,
            'nspin': 2,
            'tot_magnetization': 2,
            'tot_charge': -1,
            'nbnd': 200,
            'occupations': 'tetrahedra',
        },
        'electrons': {'conv_thr': 1e-8},
    },
    kpts=(4, 4, 4),
    directory=str(base / 'nv_scf')
)

nscf_calc = Espresso(
    profile=profile,
    pseudopotentials=pseudopotentials,
    input_data={
        'control': {
            'calculation': 'nscf',
            'pseudo_dir': str(pseudo_dir),
            'outdir': shared_outdir,  # same absolute path
        },
        'system': {
            'ecutwfc': 60,
            'ecutrho': 480,
            'nspin': 2,
            'tot_magnetization': 2,
            'tot_charge': -1,
            'nbnd': 200,
            'occupations': 'tetrahedra',
        },
        'electrons': {'conv_thr': 1e-8},
    },
    kpts=(6, 6, 6),
    directory=str(base / 'nv_nscf')
    
)


class ProgressUpdate:
    def __init__(self, pwo_path, mode="scf", interval=5):
        self.pwo_path = Path(pwo_path)
        self.mode = mode
        self.interval = interval

        self.last_scf_iter = -1
        self.last_energy = None
        self.ionic_step = 0

    def parse(self, text):
        lines = text.splitlines()

        # --- SCF iteration ---
        for line in reversed(lines):
            if "iteration #" in line:
                try:
                    it = int(line.split()[2])
                    if it != self.last_scf_iter:
                        self.last_scf_iter = it
                        print(f"[LOGGER] Iteration: {it}")
                    break
                except:
                    pass

        # --- Energy ---
        for line in reversed(lines):
            if "!    total energy" in line:
                try:
                    energy = float(line.split()[-2])
                    if self.last_energy is not None:
                        dE = energy - self.last_energy
                        print(f"[LOGGER] Energy: {energy:.6f}  ΔE={dE:.2e}")
                    else:
                        print(f"[LOGGER] Energy: {energy:.6f}")
                    self.last_energy = energy
                    break
                except:
                    pass

        # --- Ionic steps (relax only) ---
        if self.mode == "relax":
            ionic_steps = len(re.findall(r"Entering BFGS Geometry Optimization", text))
            if ionic_steps != self.ionic_step:
                self.ionic_step = ionic_steps
                print(f"[LOGGER] Ionic step: {self.ionic_step}")

    def run(self):
        print("LOGGER] QE Progress Monitor started...\n")

        while True:
            if self.pwo_path.exists():
                with open(self.pwo_path, "r") as f:
                    text = f.read()

                self.parse(text)

                if "convergence has been achieved" in text:
                    print("\nLOGGER] SCF Converged!")
                    break

                if "End of BFGS Geometry Optimization" in text:
                    print("\nLOGGER] Relaxation Finished!")
                    break

            time.sleep(self.interval)


## variables

supercell_size = {
    1: (1, 1, 1),  # Size of the supercell (1x1x1)
    2: (2, 2, 2),  # Size of the supercell (2x2x2)
    3: (3, 3, 3)   # Size of the supercell (3x3x3)
}