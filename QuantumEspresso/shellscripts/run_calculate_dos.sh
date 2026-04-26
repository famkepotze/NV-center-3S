#!/bin/bash

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

PYTHON="/Users/famkepotze/anaconda3/bin/python"
SCRIPT="/Users/famkepotze/Desktop/3S/NV-center-3S/QuantumEspresso/scripts/3.calculate_dos.py"

BASE="/Users/famkepotze/Desktop/3S/NV-center-3S/QuantumEspresso"

# ─────────────────────────────────────────────
# LOOP OVER SUPERCELLS
# ─────────────────────────────────────────────

for i in 1 2 3
do
    echo ""
    echo "======================================"
    echo "Running supercell size: $i"
    echo "======================================"

    OUTPUT="$BASE/results/dos_tot_charge-1/NV_${i}x${i}x${i}.json"

    # ── SKIP IF EXISTS ──
    if [ -f "$OUTPUT" ]; then
        echo "✔ Output exists → skipping NV_${i}x${i}x${i}"
        continue
    fi

    # ── RUN CALCULATION ──
    echo "Starting calculation for NV_${i}x${i}x${i}..."

    $PYTHON $SCRIPT $i

    # optional: check exit status
    if [ $? -ne 0 ]; then
        echo "❌ Calculation failed for NV_${i}x${i}x${i}"
        exit 1
    fi

    echo "✔ Finished NV_${i}x${i}x${i}"
done

echo ""
echo "🎉 All calculations complete."