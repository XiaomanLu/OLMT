#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 22 20:07:47 2026

@author: x5l
"""
# TIP: need to put the *.py file in the same folder as 'model_ELM'
# TIP: only ensemble analysis have outputs in pklfiles, otherwise empty.

#%% check pickles
import pickle
from glob import glob
import numpy as np

site = "CL"

Indir = '/Users/x5l/ORNL Dropbox/Xiaoman Lu/Oak_Research_Materials/Project3_Urban/Codes_Urban/OLMT/pklfiles/'
# Indir = '/gpfs/wolf2/cades/cli185/proj-shared/lux5/Project3_Urban/OLMT/pklfiles/'

# infiles = glob(Indir + '20250613_CL_CL_ICB20TRCNPRDCTCBC_T6.75eCO2.pkl') #yearly
infiles = glob(Indir + '20250328_CL_ICB20TRCNPRDCTCBC_monthly.pkl') #monthly     --- fixed as 12
# infiles = glob(Indir + '20250328_CL_ICB20TRCNPRDCTCBC_daily_TLAI_pft7.pkl') #daily --- fixed as 365
for infile in infiles:    
    myfile = open(infile, 'rb')
    mycase = pickle.load(myfile)
    myout = mycase.output  #it's a dict.    
    
    # # check myout
    # print(myout)
    print(myout.keys())    
    times = myout["taxis"]
    print(times)      
    # first_key = next(iter(myout))
    # print(first_key)
    # first_value = myout[first_key]
    
 
    ### add mycase.obs
    obs_H2OSOI_tmp = {
        "time": mycase.output["taxis"],          # 2015–2024 for ELM
        "value": np.array([                      # made-up but realistic
            0.26, 0.25, 0.24, 0.27, 0.29,
            0.31, 0.30, 0.28, 0.27, 0.26
        ]),
        "sigma": np.full(10, 0.03)               # observation uncertainty
    }
    # # check    
    # a_tmp = obs_H2OSOI_tmp['time']
    # b_tmp = obs_H2OSOI_tmp['value']
    # c_tmp = obs_H2OSOI_tmp['sigma']
    
    
    obs_QVEGT_pft7_tmp = {
        "time": mycase.output["taxis"],
        "value": np.array([
            1.1e-5, 1.0e-5, 1.2e-5, 1.15e-5, 1.3e-5,
            1.4e-5, 1.35e-5, 1.25e-5, 1.2e-5, 1.1e-5
        ]),
        "sigma": np.array([2.0e-6] * 10)
    }
    
    mycase.obs["H2OSOI"] = obs_H2OSOI_tmp
    mycase.obs["QVEGT_pft7"] = obs_QVEGT_pft7_tmp
    print(mycase.obs.keys())
    
    
    
    
#%% add to MCMC
from utils.analysis import get_obs_var
from utils.constants import PATH_OBS
import pandas as pd

SITE_LONGNAME = {
    'VA': 'VictorAshe',
    'SD': 'SEEED',
    'CL': 'Cumberland',
    'WH': 'WestHills'
}

site_name = SITE_LONGNAME[site]
timescale = "monthly"   #mycase.run_n=10, yearly; mycase.run_n=120, monthly; mycase.run_n=3650, daily


#-------------------- build obs_dict for SM10 --------------------#
varname = "SM10"
obs_SM10, obs_SM10_lower, obs_SM10_upper = get_obs_var(site_name, varname, "20250116", style = "ts_daily")     #Date is observation data folder    

if timescale == "monthly":
    obs_SM10 = obs_SM10.resample("ME").mean()
    obs_SM10_lower = obs_SM10_lower.resample("ME").mean()
    obs_SM10_upper = obs_SM10_upper.resample("ME").mean()
    sigma_SM10 = (obs_SM10_upper - obs_SM10_lower) / 2   #treat bounds as ±1σ for SM10, common use
    
    time = obs_SM10.index
    time_array = (time.year + (time.month - 1) / 12).to_numpy(dtype=np.float64)      
    value_array = obs_SM10.to_numpy(dtype=np.float64).squeeze()
    sigma_array = sigma_SM10.to_numpy(dtype=np.float64).squeeze()
    
    obs_H2OSOI = {
        "time": time_array,          
        "value": value_array,
        "sigma": sigma_array              # observation uncertainty
    }
    
    
#------------- build obs_dict for Tree transpiration ------------#   
def get_daily_obs_data(obs_file):
    obs_Ttree = pd.read_csv(obs_file) # unit: mm/day
    obs_Ttree = obs_Ttree.rename(columns={'Unnamed: 0': 'time'})

    # convert hourly to daily
    obs_Ttree['time'] = pd.to_datetime(obs_Ttree['time'])
    obs_Ttree = obs_Ttree.set_index('time')
    obs_Ttree = obs_Ttree.resample('D').mean()
    
    return(obs_Ttree)


### read obs data
upscale_method = "all_site" #options:['all_site', 'site_level']; 

# DIR = '/Users/x5l/ORNL Dropbox/Xiaoman Lu/Oak_Research_Materials/Project3_Urban/Data/observations/ET/'
DIR = PATH_OBS + '/ET/'
obs_file = DIR+f'sapflow_{upscale_method}_average_k.csv'
obs_upper_file = DIR+f'sapflow_{upscale_method}_average_k_upper_bound.csv'
obs_lower_file = DIR+f'sapflow_{upscale_method}_average_k_lower_bound.csv'

obs_Ttree = get_daily_obs_data(obs_file)
obs_Ttree_upper = get_daily_obs_data(obs_upper_file)
obs_Ttree_lower = get_daily_obs_data(obs_lower_file)  

obs_Ttree = obs_Ttree[site_name]
obs_Ttree_upper = obs_Ttree_upper[site_name]
obs_Ttree_lower = obs_Ttree_lower[site_name]


if timescale == "monthly":
    obs_Ttree = obs_Ttree.resample("ME").mean()
    obs_Ttree_lower = obs_Ttree_lower.resample("ME").mean()
    obs_Ttree_upper = obs_Ttree_upper.resample("ME").mean()
    sigma_Ttree = (obs_Ttree_upper - obs_Ttree_lower) / 4   #treat bounds as 95% CI (±2σ) for Ttree, as YPW calculate bounds based on 2σ in sapflow_processing.ipynb
    
    time = obs_Ttree.index
    time_array = (time.year + (time.month - 1) / 12).to_numpy(dtype=np.float64)      
    value_array = obs_Ttree.to_numpy(dtype=np.float64).squeeze()
    sigma_array = sigma_Ttree.to_numpy(dtype=np.float64).squeeze()
    
    obs_QVEGT_pft7 = {
        "time": time_array,          
        "value": value_array,
        "sigma": sigma_array              # observation uncertainty
    }
    
#--------------------- attach to mycase.obs --------------------#     
mycase.obs["H2OSOI"] = obs_H2OSOI
mycase.obs["QVEGT_pft7"] = obs_QVEGT_pft7






  








  
    
    
    








