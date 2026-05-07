# imports
import numpy as np
from pathlib import Path
from ase.io import write, read
from ase.calculators.espresso import Espresso, EspressoProfile
import subprocess
import matplotlib.pyplot as plt
import sys
import shutil
import json 


base = Path("/Users/famkepotze/Desktop/3S/NV-center-3S/QuantumEspresso")

sys.path.insert(0, str(base))
from helper import supercell_size, scf_calc, nscf_calc

i = int(sys.argv[1])
selected_supercell_size = supercell_size[i]
size_label = f"{selected_supercell_size[0]}x{selected_supercell_size[1]}x{selected_supercell_size[2]}"

QE_BIN       = Path("/Users/famkepotze/Desktop/3S/qe-7.5/bin")
shared_outdir = str(base / f"results/dos/out{size_label}")


# After importing from helper, override the outdir on both calculators:
scf_calc.parameters['outdir']  = shared_outdir
nscf_calc.parameters['outdir'] = shared_outdir

def outdir_complete():
    save = Path(shared_outdir) / "pwscf.save" / "data-file-schema.xml"
    return save.exists()

relaxed_path  = base / f"results/optimized_tot_charge-1/NV_{size_label}.json"
dos_output_dir = base / "results/dos"
dos_output_dir.mkdir(parents=True, exist_ok=True)

scf_dir  = Path(scf_calc.directory)
nscf_dir = Path(nscf_calc.directory)

def outdir_complete(calc_dir):
    """Return True if QE has written save files to shared_outdir."""
    save = Path(shared_outdir) / "pwscf.save" / "data-file-schema.xml"
    return save.exists()

# ============================================================
# Load structure
# ============================================================

atoms = read(relaxed_path)

def get_nbnd(atoms, tot_charge=-1, extra_factor=1.3):
    valence = {'C': 4, 'N': 5, 'H': 1, 'O': 6}
    nelec = sum(valence[a.symbol] for a in atoms) - tot_charge
    return int(np.ceil((nelec / 2) * extra_factor))

nbnd = get_nbnd(atoms)
print(f"Using nbnd = {nbnd} for {size_label}")
scf_calc.parameters['nbnd']  = nbnd
nscf_calc.parameters['nbnd'] = nbnd

# ============================================================
# SCF
# ============================================================
if outdir_complete(scf_dir):
    print("SCF already done — skipping.")
else:
    print("Running SCF...")
    atoms.calc = scf_calc
    atoms.get_potential_energy()
    print("SCF complete.")

# ============================================================
# NSCF
# ============================================================
nscf_pwo = dos_output_dir / f"NV_{size_label}_nscf.pwo"

if nscf_pwo.exists():
    print("NSCF already done — skipping.")
else:
    print("Running NSCF...")
    nscf_calc.write_inputfiles(atoms, properties=["energy", "forces"])
    result = subprocess.run(
        [str(QE_BIN / "pw.x"), "-in", "espresso.pwi"],
        cwd=nscf_dir,
        capture_output=True,
        text=True
    )
    # Always save the output log
    (nscf_dir / "espresso.pwo").write_text(result.stdout)

    if result.returncode != 0:
        print("NSCF failed:")
        print(result.stdout[-3000:])
        print(result.stderr)
        raise RuntimeError("NSCF calculation failed")

    # Save input/output to results dir
    shutil.copy(nscf_dir / "espresso.pwi", dos_output_dir / f"NV_{size_label}_nscf.pwi")
    shutil.copy(nscf_dir / "espresso.pwo", nscf_pwo)
    print("NSCF complete.")

# ============================================================
# DOS
# ============================================================
dos_file     = nscf_dir / "nv.dos"
dos_saved    = dos_output_dir / f"NV_{size_label}.dos"

if dos_saved.exists():
    print("DOS already done — skipping dos.x.")
    # Use saved copy if local is missing
    if not dos_file.exists():
        shutil.copy(dos_saved, dos_file)
else:
    dos_input = f"""\
&DOS
 prefix = 'pwscf'
 outdir = '{shared_outdir}'
 fildos = 'nv.dos'
 Emin = -10.0,
 Emax = 10.0,
 DeltaE = 0.01,
/
"""
    (nscf_dir / "dos.in").write_text(dos_input)

    print("Running dos.x...")
    result = subprocess.run(
        [str(QE_BIN / "dos.x"), "-in", "dos.in"],
        cwd=nscf_dir,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print("dos.x failed:")
        print(result.stdout[-3000:])
        print(result.stderr)
        raise RuntimeError("dos.x failed")

    # Save to results dir
    shutil.copy(dos_file, dos_saved)
    print("DOS complete.")


# ============================================================
# Plot
# ============================================================
# ============================================================
# Load DOS data
# ============================================================
data   = np.loadtxt(dos_file, skiprows=1)
energy = data[:, 0]
dos    = data[:, 1]

# ============================================================
# Plot
# ============================================================
plt.figure()
plt.plot(energy, dos)
plt.axvline(0, color='gray', linestyle='--', label='Fermi level')
plt.xlabel("Energy (eV)")
plt.ylabel("DOS")
plt.title(f"NV$^-$ DOS ({size_label})")
plt.legend()
plt.tight_layout()

plot_file = dos_output_dir / f"NV_{size_label}_dos.png"
plt.savefig(plot_file, dpi=150)
plt.close()

# Save plot
plot_file = dos_output_dir / f"NV_{size_label}_dos.png"
plt.savefig(plot_file, dpi=150)
plt.close()

# Save energy and forces to JSON
results = {
    "size_label": size_label,
    "energy_eV": energy.tolist(),
    "dos": dos.tolist(),
}
json_file = dos_output_dir / f"NV_{size_label}.json"
with open(json_file, "w") as f:
    json.dump(results, f)

print(f"Saved: {plot_file.name}")
print(f"Saved: {json_file.name}")