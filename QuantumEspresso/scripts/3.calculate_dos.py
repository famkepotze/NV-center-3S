#imports
import numpy as np
from pathlib import Path
from ase.io import write, read
from ase.calculators.espresso import Espresso, EspressoProfile
import subprocess
import matplotlib.pyplot as plt
import sys
from threading import Thread


base = Path("/Users/famkepotze/Desktop/3S/NV-center-3S/QuantumEspresso")

# ─────────────────────────────────────────────────────────────
# Helper import
# ─────────────────────────────────────────────────────────────
sys.path.insert(0, str(base))
from helper import supercell_size, ProgressUpdate, relax_calc, scf_calc, nscf_calc

# shellscript file is programmed to loop over all supercell sizes
i = int(sys.argv[1])
selected_supercell_size = supercell_size[i]
size_label = f"{selected_supercell_size[0]}x{selected_supercell_size[1]}x{selected_supercell_size[2]}"


#─────────────────────────────────────────────────────────────
# Paths─────────────────────────────────────────────────────────────
#input
relaxed_path = base / f"results/optimized_tot_charge-1/NV_{size_label}.json"

#output
dos_path = base / f"results/dos_tot_charge-1/NV_{size_label}.json"
dos_path.parent.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────
# Load structure
# ─────────────────────────────────────────────────────────────
atoms = read(relaxed_path)

# ============================================================
# 2. SCF
# ============================================================
atoms = read(relaxed_path)

print("Running SCF...")
atoms.calc = scf_calc
atoms.get_potential_energy()

# ============================================================
# 3. NSCF (for DOS)
# ============================================================

print("Running NSCF...")
atoms.calc = nscf_calc
atoms.get_potential_energy()

# ============================================================
# 4. DOS.x
# ============================================================
dos_input = """
&DOS
 prefix = 'espresso'
 outdir = './out'
 fildos = 'nv.dos'
 Emin = -10.0,
 Emax = 10.0,
 DeltaE = 0.01,
/
"""

with open("dos.in", "w") as f:
    f.write(dos_input)

print("Running DOS.x...")
subprocess.run(
    f"{dos_path} < dos.in > dos.out",
    shell=True
)

# ============================================================
# 5. PLOT DOS
# ============================================================
print("Plotting DOS...")

data = np.loadtxt("nv.dos", skiprows=1)

energy = data[:, 0]
dos = data[:, 1]

plt.figure()
plt.plot(energy, dos)
plt.axvline(0)  # Fermi level
plt.xlabel("Energy (eV)")
plt.ylabel("DOS")
plt.title("NV- DOS")
plt.show()