#!/bin/bash 
#SBATCH --nodes=2 
#SBATCH --ntasks=5
#SBATCH --account=CLI185 
#SBATCH --time=1:00:00 
#SBATCH --partition=batch_ccsi 
#SBATCH --job-name="GSA" 
#SBATCH --output=GSA.out 
#SBATCH --error=GSA.err 

module load python/3.11-anaconda3 
source activate myenv 

cd ${SLURM_SUBMIT_DIR} 
python manage_ensemble_postproc_Knoxville.py
