#!/bin/bash 
#SBATCH --nodes=1 
#SBATCH --ntasks=20     #Total tasks for n nodes
#SBATCH --account=CLI185 
#SBATCH --time=24:00:00 
#SBATCH --partition=batch_ccsi 
#SBATCH --job-name="MCMC_CL" 
#SBATCH --output=MCMC_CL.out 
#SBATCH --error=MCMC_CL.err 

module load nco
module load python/3.11-anaconda3  

cd /gpfs/wolf2/cades/cli185/proj-shared/lux5/Project3_Urban/OLMT
~/.conda/envs/olmt/bin/python manage_ensemble_MCMC_Knoxville.py 20250613 CL

