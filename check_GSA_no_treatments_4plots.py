#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 19 22:29:11 2025

@author: x5l
"""
import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg')
import matplotlib.patches as mpatches
import pandas as pd            
import pickle
from matplotlib import rcParams    
rcParams['font.size'] = 10
rcParams['axes.titlesize'] = 14

from utils.constants import SITE_LIST, site_plotID_dict, SITE_SHORTNAME


def get_mon_avg_arossyrs(self, my_value):            
    # Calculate monthly averages  
    my_freq = 12
    my_value_out = np.zeros((self.nparms_ensemble, my_freq))
    
    for p in range(self.nparms_ensemble):
        for m in range(my_freq):
            my_value_out[p, m] = np.mean(my_value[p, m::my_freq])            
    return(my_freq, my_value_out)



def get_daily_avg_acrossyrs(self, my_value):       
    my_freq = 365
    my_value_out = np.zeros((self.nparms_ensemble, my_freq))  # or 366 if you include Feb 29
    
    # create daily time index
    dates = pd.date_range(start=f'{self.postproc_startyear}-01-01', end=f'{self.postproc_endyear}-12-31', freq='D')
    # dates = pd.date_range(start=f'2014-01-01', end='2024-12-31', freq='D')
    df = pd.DataFrame({'date': dates})
    df = df[~((df['date'].dt.month == 2) & (df['date'].dt.day == 29))] #drop Feb 29
    df['month_day'] = df['date'].dt.strftime('%m-%d')
        
    for p in range(self.nparms_ensemble):        
        df['value'] = my_value[p, :]            
        daily_means = df.groupby('month_day')['value'].mean().values
        my_value_out[p, :] = daily_means
    return(my_freq, my_value_out)


def plot_sens_v(self, v, my_value, my_title, my_outfile):            
    ## pre-processed data to mean during postproc_freq
    if self.postproc_freq=="annual":
        my_freq, my_value = my_value.shape[1], my_value  
        xticks = np.arange(my_freq)             
        xticklabels = range(self.postproc_startyear, self.postproc_endyear+1)                
    elif self.postproc_freq=="monthly":
        my_freq, my_value = get_mon_avg_arossyrs(self, my_value)
        xticks = np.arange(my_freq) 
        xticklabels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    elif self.postproc_freq=="daily":
        my_freq, my_value = get_daily_avg_acrossyrs(self, my_value)  
        xticks = np.arange(30,360,30) - 1  
        xticklabels = np.arange(30,360,30)        
    # print("check dims:", self.postproc_freq, my_freq, my_value.shape)              
    
    # Plot sensitivity
    # fig, ax = plt.subplots(figsize=(10, 6))  
    
    # Create a dictionary to map ensemble_parms to colors
    parm_colors = {}
    color_index = 0
    colors = plt.cm.tab20.colors  # Use a colormap for distinct colors    
    
    # Plot the stacked lines
    bottom = np.zeros(my_freq)
    patches = []  # Store legend handles            
    x_pos = np.arange(my_freq)
    
    for p in range(self.nparms_ensemble):
        parm = self.ensemble_parms[p]
        if parm not in parm_colors:
            parm_colors[parm] = colors[color_index % len(colors)]
            color_index += 1
    
        color = parm_colors[parm]
        hatch = '///' if self.ensemble_pfts[p] == 7 else None
    
        ax.fill_between(
            x_pos,
            bottom,
            bottom + my_value[p, :],
            color=color,
            hatch=hatch,
            alpha=0.5,
            edgecolor='gray'
        )
        bottom += my_value[p, :]
    
        # Create a legend entry
        label = f"{parm}{self.ensemble_pfts[p]}" 
        patches.append(mpatches.Patch(facecolor=color, hatch=hatch, edgecolor='gray', label=label))
        
        # to order the sensivity among paramers based on multi-year mean sensitivity
        pft = self.ensemble_pfts[p]
        # print(my_title, ",", v, ",", f"{parm}_{pft}", ",", np.nanmean(my_value[p, :]))  
        
    
    # Adjust the axis and labels
    # ax.set_xlim(0, my_freq)    
    ax.set_xticks(xticks)    
    ax.set_xticklabels(xticklabels)            
    # ax.set_xlabel(self.postproc_freq)
    ax.set_ylabel('Sensitivity Index')
    # ax.set_title(my_title)
    
    return patches
       
   
    

def Lineplot_GSA(self, myvars, caseid, site):    
    UQ_output = './UQ_output/' + self.casename + '/GSA'
    os.makedirs(UQ_output, exist_ok=True)  # Ensures the directory exists   
    
    for v in myvars:  
        if v != 'taxis':   
            if sens_type == "sens_tot":             
                ## plot total sensitivity
                my_value = self.sens_tot[v]
                my_title = f'Total Sensitivity Indices for {v}: {caseid}'                
                patches = plot_sens_v(self, v, my_value, my_title, '')
                
            elif sens_type=="sens_main":            
                ## plot main sensitivity
                my_value = self.sens_main[v]
                my_title = f'Main Sensitivity Indices for {v}: {caseid}'            
                patches = plot_sens_v(self, v, my_value, my_title, '')
    return patches
            

### MAIN
DIR = '/gpfs/wolf2/cades/cli185/proj-shared/lux5/Project3_Urban/OLMT/'
pkl_dir = DIR + '/pklfiles/'
my_postproc_vars_pft = ['H2OSOI'] #QVEGT_pft7
sens_type = 'sens_main'

fig, axes = plt.subplots(2, 2, figsize=(12, 7), sharex=True, sharey=True)
for site_name in SITE_LIST:
    print(site_name)
    i = site_plotID_dict[site_name]
    
    ax = axes.flat[i]
    ax.set_title(site_name)    
    
    site_shortname = SITE_SHORTNAME[site_name]   
    caseid = f'20250530_{site_shortname}'    
    
    pklfile = pkl_dir + f'{caseid}_{site_shortname}_ICB20TRCNPRDCTCBC.pkl'     
    myfile = open(pklfile, 'rb')
    mycase=pickle.load(myfile)    
    patches = Lineplot_GSA(mycase, my_postproc_vars_pft, caseid, site_shortname)
    
    
## add legend
if True:
    patches_7 = [patch for patch in patches if '7' in patch.get_label()]
    patches_13 = [patch for patch in patches if '13' in patch.get_label()]
    # First legend (for patches_7)
    legend1 = plt.legend(
        handles=patches_7,
        loc='upper center',
        bbox_to_anchor=(-0.6, 2.75),
        ncol=4,
        frameon=False 
    )
    ax.add_artist(legend1)  # <- This keeps the first legend on the plot            
    # Second legend (for patches_13)
    plt.legend(
        handles=patches_13,
        loc='upper center',
        bbox_to_anchor=(0.48, 2.75),
        ncol=4,
        frameon=False 
    )
    
    
# save    
fig.subplots_adjust(left=0.09, right=0.99, bottom=0.09, top=0.8, wspace=0.1, hspace= 0.2)    
my_outfile = DIR + f'/check_GSA_no_treatments_4plots_{sens_type}_{my_postproc_vars_pft[0]}_{mycase.postproc_freq}.png'    
plt.savefig(my_outfile, bbox_inches='tight')




