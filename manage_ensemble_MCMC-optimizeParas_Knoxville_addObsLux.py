#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 23 12:18:33 2026

@author: x5l
"""

    
#%% add to MCMC
from utils.analysis import get_obs_var, get_daily_obs_Ttree
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
### read obs data
upscale_method = "all_site" #options:['all_site', 'site_level']; 

# DIR = '/Users/x5l/ORNL Dropbox/Xiaoman Lu/Oak_Research_Materials/Project3_Urban/Data/observations/ET/'
DIR = PATH_OBS + '/ET/'
obs_file = DIR+f'sapflow_{upscale_method}_average_k.csv'
obs_upper_file = DIR+f'sapflow_{upscale_method}_average_k_upper_bound.csv'
obs_lower_file = DIR+f'sapflow_{upscale_method}_average_k_lower_bound.csv'

obs_Ttree = get_daily_obs_Ttree(obs_file)
obs_Ttree_upper = get_daily_obs_Ttree(obs_upper_file)
obs_Ttree_lower = get_daily_obs_Ttree(obs_lower_file)  

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