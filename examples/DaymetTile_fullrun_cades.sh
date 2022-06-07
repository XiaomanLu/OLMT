#!/bin/sh -f

## a script to run OLMT (https://github.com/dmricciuto/OLMT.git, branch 'Arctic-userpft'), for simulation using GSWP3_daymet driving forcing and 
## specific domain/surface dataset (generated by 'makepointdata.py'). 

# 1) E3SM input data root directory

E3SM_INPUT=/lustre/or-scratch/cades-ccsi/proj-shared/project_acme/e3sm_inputdata

# 2) E3SM model directory. Please clone/checkout E3SM branch: 
## https://github.com/E3SM-Project/E3SM.git, branch 'fmyuan/lnd/ELM-highres'
E3SM_ROOT=~/models/E3SM

# 3) GSWP3-daymet datasets
## GSWP3-daymet forcing - 'cpl_bypass_full/', and, relevant files - 'domain.nc', 'surfdata.nc', and 'surfdata.pftdyn.nc'.
USER_METDIR=/nfs/data/ccsi/f9y/GSWP3_daymet/TILES_KXTN/cpl_bypass_full

DAYMETTILE=TILES_KXTN

# 4) (optional) case root and run root directories
CASE_ROOT=/lustre/or-scratch/cades-ccsi/f9y/cases
RUN_ROOT=/lustre/or-scratch/cades-ccsi/scratch/f9y

# 5) run the following from OLMT directory. NOTE: modify '--machine xxx', '--compiler xxx', '--mpilib xxx', and '--np xx', as what machine and environmental settings for E3SM. ' --no_submit' implies cases will not submit for running, so it's optional. 

python ./global_fullrun.py \
 --caseidprefix ELM-${DAYMETTILE} \
 --nyears_ad_spinup 200 --nyears_final_spinup 600 --tstep 1 \
 --machine cades --compiler gnu --mpilib openmpi \
 --walltime 48 \
 --cpl_bypass --spinup_vars \
 --gswp3 --daymet4 \
 --model_root ${E3SM_ROOT} \
 --caseroot ${CASE_ROOT} \
 --nopointdata \
 --metdir ${USER_METDIR} \
 --domainfile ${USER_METDIR}/domain.nc \
 --surffile ${USER_METDIR}/surfdata.nc \
 --landusefile ${USER_METDIR}/surfdata.pftdyn.nc \
 --np 160 \
 --ccsm_input ${E3SM_INPUT} \
 --runroot ${RUN_ROOT}
