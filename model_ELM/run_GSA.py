import os, math, sys
import numpy as np
from optparse import OptionParser
import model_surrogate as models
import matplotlib
import matplotlib.pyplot as plt
from SALib.sample import saltelli
from SALib.analyze import sobol
matplotlib.use('Agg')


def GSA(self, myvars, n_saltelli=8192):
    #Get parameter bounds
    pbounds = np.zeros([self.nparms_ensemble,2],float)
    for p in range(0,self.nparms_ensemble):
        print(p, self.nparms_ensemble, self.ensemble_pmin[p])
        pbounds[p,0]=self.ensemble_pmin[p]
        pbounds[p,1]=self.ensemble_pmax[p]

    problem = {
            'num_vars': self.nparms_ensemble,
            'names': self.ensemble_parms,
            'bounds': pbounds
            }
    psamples = saltelli.sample(problem, n_saltelli)

    surrogate_output = self.run_surrogate(psamples, myvars)
    self.sens_main={}
    self.sens_tot={}

    for v in myvars:
      nvar = surrogate_output[v].shape[1]
      self.sens_main[v] = np.zeros([self.nparms_ensemble,nvar],float)
      self.sens_tot[v]  = np.zeros([self.nparms_ensemble,nvar],float)
      for i in range(0,nvar):
        Si = sobol.analyze(problem, surrogate_output[v][:,i])
        self.sens_main[v][:,i]=Si['S1']
        self.sens_tot[v][:,i]=Si['ST']

def plot_GSA(self, myvars):
    for v in myvars:
      #Plot main sensitivity indices
      fig,ax = plt.subplots()
      nvar = self.sens_main[v].shape[1]
      x_pos = np.cumsum(np.ones(nvar))
      ax.bar(x_pos, self.sens_main[v][0,:], align='center', alpha=0.5)
      ax.set_xticks(x_pos)
      #ax.set_xticklabels(x_labels, rotation=45)
      bottom=self.sens_main[v][0,:]
      for p in range(1,self.nparms_ensemble):
       ax.bar(x_pos, self.sens_main[v][p,:], bottom=bottom)
       bottom=bottom+self.sens_main[v][p,:]
      plt.legend(self.ensemble_parms)
      plt.savefig('sens_main_'+v+'.pdf')
      #
      #Total sensitivity indices
      fig,ax = plt.subplots()
      ax.bar(x_pos, self.sens_tot[v][0,:], align='center', alpha=0.5)
      ax.set_xticks(x_pos)
      #ax.set_xticklabels(x_labels, rotation=45)
      bottom=self.sens_tot[v][0,:]
      for p in range(1,self.nparms_ensemble):
       ax.bar(x_pos, self.sens_tot[v][p,:], bottom=bottom)
       bottom=bottom+self.sens_tot[v][p,:]
      plt.legend(self.ensemble_parms)
      plt.savefig('sens_tot_'+v+'.png')
