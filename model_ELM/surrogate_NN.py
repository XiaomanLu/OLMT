from netCDF4 import Dataset
from sklearn.neural_network import MLPRegressor
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os, math, sys
import numpy as np
#from mpi4py import MPI
import pickle
from optparse import OptionParser
from sklearn import preprocessing
from sklearn.model_selection import GridSearchCV

def train_surrogate(self,myvars):
 self.nobs={}
 for var in myvars:
  nparms = self.nparms_ensemble
  ntrain = int(self.nsamples*0.8)
  nval   = int(self.nsamples-ntrain)
  nqoi   = len(self.obs[var][:])
  self.nobs[var] = nqoi

  ytrain = self.output[var][:,0:ntrain].transpose()
  ptrain = self.samples[:,0:ntrain].transpose()
  good = np.where(ytrain[:,1].squeeze() > -9999)[0]
  ytrain = ytrain[good,:].copy()
  ptrain = ptrain[good,:].copy()
  ntrain = ptrain.shape[0]

  yval = self.output[var][:,ntrain:].transpose()
  pval = self.samples[:,ntrain:].transpose()
  good = np.where(yval[:,1].squeeze() > -9999)[0]
  yval = yval[good,:].copy()
  pval = pval[good,:].copy()
  nval = pval.shape[0]

  pscaler      = preprocessing.StandardScaler().fit(ptrain)
  ptrain_norm = pscaler.transform(ptrain)
  pval_norm   = pscaler.transform(pval)
   
  yscaler = preprocessing.StandardScaler().fit(ytrain)
  ytrain_norm = yscaler.transform(ytrain)
  yval_norm = yscaler.transform(yval)

  param_grid = {
    'hidden_layer_sizes': [(200,100), (120,80,40), (240,120,60)],
    'max_iter': [200, 500],
    'activation': ['tanh', 'relu'],
    'solver': ['adam','lbfgs'],
    'alpha': [0.0001,0.01,0.05],
    'learning_rate': ['constant','adaptive'],
  }
  clf = MLPRegressor(solver='adam')
  grid = GridSearchCV(clf, param_grid, n_jobs= -1, cv=5)
  grid.fit(ptrain_norm, ytrain_norm)

  ypredict_train = yscaler.inverse_transform(grid.predict(ptrain_norm)) 
  ypredict_val   = yscaler.inverse_transform(grid.predict(pval_norm))
  for qoi in range(0,nqoi):
      print(qoi, np.corrcoef(ytrain.astype(float)[:,qoi], ypredict_train.astype(float)[:,qoi])[0,1]**2)
  print()
  for qoi in range(0,nqoi):
      print(qoi, np.corrcoef(yval.astype(float)[:,qoi], ypredict_val.astype(float)[:,qoi])[0,1]**2)
  self.surrogate[var]=grid
  self.pscaler[var]=pscaler
  self.yscaler[var]=yscaler

def run_surrogate(self,parms,myvars):
  surrogate_output={}
  for var in myvars:
    parms_norm = self.pscaler[var].transform(parms)
    surrogate_output[var] = self.yscaler[var].inverse_transform(self.surrogate[var].predict(parms_norm))
  return surrogate_output


