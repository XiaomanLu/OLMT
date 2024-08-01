from model_ELM import ELMcase
import matplotlib.pyplot as plt
import numpy as np
import os

#When the ensemble is complete, we can load the postprocess information 
#and surrogate model
mycase=ELMcase(casename='20240731_PR-LUQ_I1850ELMFATES_ad_spinup')

myvars=['FATES_VEGC','FATES_NPP','EFLX_LH_TOT']
for v in myvars:
    print('Processing '+v)

    #Plot the ensemble
    plt.plot(mycase.output[v])
    plt.savefig(v+'.png')
    plt.close()

    #Prepare synthetic observations to demonstrate calibration

    #set the observations to the model result from sample 
    mysample=51
    mycase.obs[v] = mycase.output[v][:,mysample]
    #Define the "observational" error as 5% of the observed value
    mycase.obs_err[v] = mycase.obs[v]*0.05

#plot GSA
mycase.plot_GSA(myvars)
os.system('mv *.png UQ_output')


parms = (np.array(mycase.ensemble_pmin[:])+np.array(mycase.ensemble_pmax[:]))/2.0
print('Starting parameter values: ',parms)

best_parms = mycase.MCMC(parms, myvars, 100000, nburn=5000)
print('Correct parameter values : ', mycase.samples[:,mysample])
print('MCMC best parameters     : ', best_parms)


#copy plots
#os.system('cp -r UQ_output /global/cfs/cdirs/e3sm/www/'+os.environ['USER'])
#os.system('chmod -R a+rx /global/cfs/cdirs/e3sm/www/'+os.environ['USER']+'/UQ_output')


