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
from sklearn.model_selection import train_test_split, GridSearchCV

def train_surrogate(self,myvars):
 self.qoi_bad={}
 self.qoi_bad_meanval={}
 for var in myvars:
    vname=var
    nparms = self.nparms_ensemble
    nqoi   = self.output[vname].shape[0]

    # Extract outputs and samples 
    y = self.output[vname].transpose()
    p = self.samples.transpose()

    # Filter out invalid data
    valid_indices = np.where(y[:, 1].squeeze() > -9999)[0]
    y = y[valid_indices, :].copy()
    p = p[valid_indices, :].copy()

    self.qoi_bad[vname] = []
    self.qoi_bad_meanval[vname] = []
    for q in range(0,nqoi):
        if (max(y[valid_indices,q]) == min(y[valid_indices,q])):
            self.qoi_bad[vname].append(q)
            self.qoi_bad_meanval[vname].append(min(y[valid_indices,q]))

    # Split data into training and validation sets
    ptrain, pval, ytrain, yval = train_test_split(p, y, test_size=0.2, random_state=42)

    # Normalize the parameters and outputs
    pscaler      = preprocessing.StandardScaler().fit(ptrain)
    ptrain_norm = pscaler.transform(ptrain)
    pval_norm   = pscaler.transform(pval)
   
    yscaler = preprocessing.StandardScaler().fit(ytrain)
    ytrain_norm = yscaler.transform(ytrain)
    yval_norm = yscaler.transform(yval)

    param_grid = {
      'hidden_layer_sizes': [(50,), (100,), (100,50)],
      'activation': ['tanh', 'relu'],
      'solver': ['adam','lbfgs'],
      'alpha': [0.0001,0.01,0.05],
      'learning_rate': ['constant','adaptive'],
    }
    clf = MLPRegressor(max_iter=1000, early_stopping=True, validation_fraction=0.2, \
          n_iter_no_change=10, random_state=42)
    grid = GridSearchCV(clf, param_grid, n_jobs= -1, cv=5)
    grid.fit(ptrain_norm, ytrain_norm)

    self.surrogate[vname]=grid
    self.pscaler[vname]=pscaler
    self.yscaler[vname]=yscaler

    ypredict_train = yscaler.inverse_transform(grid.predict(ptrain_norm)) 
    ypredict_val   = yscaler.inverse_transform(grid.predict(pval_norm))
    print('Correlations for training data: '+vname)
    for qoi in range(0,nqoi):
      print(qoi, np.corrcoef(ytrain.astype(float)[:,qoi], ypredict_train.astype(float)[:,qoi])[0,1]**2)
    print()
    print('Correlations for testing data: '+vname)
    for qoi in range(0,nqoi):
      print(qoi, np.corrcoef(yval.astype(float)[:,qoi], ypredict_val.astype(float)[:,qoi])[0,1]**2)

def run_surrogate(self,parms,myvars):
  surrogate_output={}
  for var in myvars:
    parms_norm = self.pscaler[var].transform(parms)
    surrogate_output[var] = self.yscaler[var].inverse_transform(self.surrogate[var].predict(parms_norm))
    surrogate_output[var][:,self.qoi_bad[var]] = self.qoi_bad_meanval[var]
  return surrogate_output


