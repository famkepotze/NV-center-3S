#imports
import numpy as np
from pathlib import Path
from ase.io import write, read
from ase.calculators.espresso import Espresso, EspressoProfile
import sys
import subprocess
from threading import Thread

base = Path("/Users/famkepotze/Desktop/3S/NV-center-3S/QuantumEspresso")

# ─────────────────────────────────────────────────────────────
# Helper import
# ─────────────────────────────────────────────────────────────
sys.path.insert(0, str(base))
from helper import supercell_size, ProgressUpdate, relax_calc


# shellscript file is programmed to loop over all supercell sizes
i = int(sys.argv[1])
selected_supercell_size = supercell_size[i]
size_label = f"{selected_supercell_size[0]}x{selected_supercell_size[1]}x{selected_supercell_size[2]}"

# ─────────────────────────────────────────────────────────────
# Paths─────────────────────────────────────────────────────────────

raw_structures_path = base / f"results/raw_structures/NV_{size_label}.xyz"

relaxed_path = base / f"results/optimized_tot_charge-1/NV_{size_label}.json"
relaxed_path.parent.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────
# Load structure
# ─────────────────────────────────────────────────────────────
atoms = read(raw_structures_path)

# ─────────────────────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────────────────────
print("Starting geometry optimisation...")
print(f"Input structure: {raw_structures_path}")

monitor = ProgressUpdate("nv_relax/espresso.pwo", mode="relax")

t = Thread(target=monitor.run)
t.start()


atoms.calc = relax_calc

try:
    energy = atoms.get_potential_energy()
    forces = atoms.get_forces()

    t.join()

    print(f"\nFinal energy : {energy:.4f} eV")
    print(f"Max force    : {np.max(np.linalg.norm(forces, axis=1)):.6f} eV/Å")

    # Save relaxed structure
    write(relaxed_path, atoms)
    print(f"Relaxed structure saved to:\n{relaxed_path}")

except Exception as e:
    print(f"\nCalculation failed: {e}")

    pwo_file = Path("nv_relax/espresso.pwo")
    if pwo_file.exists():
        print("\n--- QE OUTPUT (last 200 lines) ---\n")
        result = subprocess.run(['tail', '-n', '200', str(pwo_file)],
                                capture_output=True, text=True)
        print(result.stdout)