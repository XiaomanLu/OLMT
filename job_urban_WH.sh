#!/bin/bash 
#SBATCH --nodes=1 
#SBATCH --ntasks=20     #Total tasks for n nodes
#SBATCH --account=CLI185 
#SBATCH --time=24:00:00 
#SBATCH --partition=batch_ccsi 
#SBATCH --job-name="GSA_WH" 
#SBATCH --output=GSA_WH.out 
#SBATCH --error=GSA_WH.err 

module load nco
module load python/3.11-anaconda3 
source activate myenv 

cd ${SLURM_SUBMIT_DIR} 
python manage_ensemble_postproc_Knoxville.py 20250610 WH

