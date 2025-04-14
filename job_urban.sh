#!/bin/bash 
#SBATCH --nodes=2 
#SBATCH --ntasks=20     #Total tasks for n nodes
#SBATCH --account=CLI185 
#SBATCH --time=24:00:00 
#SBATCH --partition=batch_ccsi 
#SBATCH --job-name="GSA_CL" 
#SBATCH --output=GSA_CL.out 
#SBATCH --error=GSA_CL.err 

module load nco
module load python/3.11-anaconda3 
source activate myenv 

cd ${SLURM_SUBMIT_DIR} 
python manage_ensemble_postproc_Knoxville.py
<<<<<<< HEAD

=======
>>>>>>> d2e84d283083e80179aabf0501128df668937253
