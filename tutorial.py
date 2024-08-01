from model_ELM import ELMcase
import matplotlib.pyplot as plt

#When the ensemble is complete, we can load the postprocess information 
#and surrogate model
mycase=ELMcase(casename='20240731_PR-LUQ_I1850ELMFATES_ad_spinup')

#Sensitivity analysis plot
mycase.plot_GSA(['FATES_VEGC'])

#Plot the ensemble
plt.plot(mycase.output['FATES_VEGC'])
plt.savefig('FATES_VEGC.png')

#Calibration
mycase.obs(['FATES_VEGC'])=xxxxx

mycase.MCMC
