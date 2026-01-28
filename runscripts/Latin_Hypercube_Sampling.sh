#!/bin/bash

# ## run bash in terminal
# chmod +x Latin_Hypercube_Sampling.sh
# ./Latin_Hypercube_Sampling.sh

set -euo pipefail
N=24

SURFDATA_DIR="/gpfs/wolf2/cades/cli185/proj-shared/ywo/E3SM/inputdata/lnd/clm2/PTCLM/1x1pt_KNX-SD"
OUTDIR_BASE="/gpfs/wolf2/cades/cli185/proj-shared/lux5/Project3_Urban/e3sm_run"
RUNNAME_BASE="20260127_SD_ICBELMBC"

PYTHONFILE="/gpfs/wolf2/cades/cli185/proj-shared/lux5/Project3_Urban/OLMT/runscripts/run_Knoxville_T_CO2_SP.py"

for i in $(seq -f "%02g" 9 24); do
    printf "\n\n===== OAT run %s =====\n" "$i"

    # -----------------------------
    # 1. Replace surfdata
    # -----------------------------
    SURF_IN="${SURFDATA_DIR}/surfdata_r20_OAT_${i}.nc"
    SURF_RUN="${SURFDATA_DIR}/surfdata_r20.nc"

    [[ -f "$SURF_IN" ]] || { printf "Missing %s\n" "$SURF_IN"; exit 1; }
    cp "$SURF_IN" "$SURF_RUN"

    # -----------------------------
    # 2. Clean previous default case
    # -----------------------------
    DEFAULT_CASE="${OUTDIR_BASE}/${RUNNAME_BASE}"
    rm -rf "$DEFAULT_CASE"

    # -----------------------------
    # 3. Submit job
    # -----------------------------
    printf "r\n" | python "$PYTHONFILE" SD

    # -----------------------------
    # 4. Wait for lnd.log to appear
    # -----------------------------
    printf "\n\nWaiting for lnd.log to be created...\n"

    while ! ls "${DEFAULT_CASE}"/run/lnd.log.* >/dev/null 2>&1; do
        sleep 30
    done

    LOGFILE=$(ls "${DEFAULT_CASE}"/run/lnd.log.* | head -n 1)
    printf "Found LOGFILE: %s\n" "$LOGFILE"

    # -----------------------------
    # 5. Wait for ELM completion
    # -----------------------------
    printf "Waiting for ELM to finish...\n"

    while ! grep -q "Successfully wrote out restart data" "$LOGFILE"; do
        sleep 60
    done

    # -----------------------------
    # 6. Rename case directory
    # -----------------------------
    OUTDIR="${OUTDIR_BASE}/${RUNNAME_BASE}_${i}"
    rm -rf "$OUTDIR"
    mv "$DEFAULT_CASE" "$OUTDIR"

    printf "===== Finished OAT run %s =====\n" "$i"
done







