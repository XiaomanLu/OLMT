import os, math, sys
import numpy as np
from optparse import OptionParser
import model_surrogate as models
import matplotlib
import matplotlib.pyplot as plt
from SALib.sample import saltelli
from SALib.analyze import sobol
matplotlib.use('Agg')
import matplotlib.patches as mpatches
import pandas as pd


def GSA(self, myvars, n_saltelli=8192):
    #Get parameter bounds
    pbounds = np.zeros([self.nparms_ensemble,2],float)
    for p in range(0,self.nparms_ensemble):
        print(p, self.nparms_ensemble, self.ensemble_pmin[p])
        pbounds[p,0]=self.ensemble_pmin[p]
        pbounds[p,1]=self.ensemble_pmax[p]
        
    unique_names = [f"{p}_{pft}" for p, pft in zip(self.ensemble_parms, self.ensemble_pfts)]
    problem = {
            'num_vars': self.nparms_ensemble,
            'names': unique_names,   #Should not have repeated names!!
            'bounds': pbounds
            }      
    
    print("Defined problem:")
    print("  num_vars:", problem['num_vars'])
    print("  names:", problem['names'])
    print("  bounds shape:", problem['bounds'].shape)    
    
    psamples = saltelli.sample(problem, n_saltelli)  
    surrogate_output = self.run_surrogate(psamples, myvars)     
    self.sens_main={}
    self.sens_tot={}

    for v in myvars:
        nvar = surrogate_output[v].shape[1] #e.g., nvar=11 for 11 years 
        print("check", surrogate_output[v].shape) #475135, 11
        
        self.sens_main[v] = np.zeros([self.nparms_ensemble,nvar],float)
        self.sens_tot[v]  = np.zeros([self.nparms_ensemble,nvar],float)  
        
        for i in range(0,nvar):            
            Si = sobol.analyze(problem, surrogate_output[v][:,i])       #, calc_second_order=False; It’s removing duplicates from problem['names']                         
            self.sens_main[v][:,i]=Si['S1']
            self.sens_tot[v][:,i]=Si['ST']
   


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
    fig, ax = plt.subplots(figsize=(10, 6))  
    
    # Create a dictionary to map ensemble_parms to colors
    parm_colors = {}
    color_index = 0
    colors = plt.cm.tab20.colors  # Use a colormap for distinct colors    
    
    # Plot the stacked lines
    bottom = np.zeros(my_freq)
    patches = []  # Store legend handles            
    x_pos = np.arange(my_freq)
    
    datalist = []
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
        
        # append GSA values
        datalist.append({
            'GSA_type': my_title[0:5], #main or total sensitivity
            'Output': v,
            'Parameter': f"{parm}_{pft}",
            'GSA_values': my_value[p, :].tolist()  # numpy array: GSA values for years from postproc_startyear-postproc_endyear (e.g., 2015-2024)            
        })        
    
    # Adjust the axis and labels
    # ax.set_xlim(0, my_freq)    
    ax.set_xticks(xticks)    
    ax.set_xticklabels(xticklabels)            
    ax.set_xlabel(self.postproc_freq)
    ax.set_ylabel('Sensitivity Index')
    ax.set_title(my_title)
    
    ## add legend
    patches_7 = [patch for patch in patches if '7' in patch.get_label()]
    patches_13 = [patch for patch in patches if '13' in patch.get_label()]
    # First legend (for patches_7)
    legend1 = ax.legend(
        handles=patches_7,
        loc='lower center',
        bbox_to_anchor=(0.25, 1.05),
        ncol=3,
        frameon=False 
    )
    ax.add_artist(legend1)  # <- This keeps the first legend on the plot            
    # Second legend (for patches_13)
    ax.legend(
        handles=patches_13,
        loc='lower center',
        bbox_to_anchor=(0.75, 1.05),
        ncol=3,
        frameon=False 
    )
    
    # Save the plot
    plt.tight_layout()            
    plt.savefig(my_outfile, bbox_inches='tight')
    plt.close(fig)  # Close the figure to free memory
    
    # Save datalist to df
    df = pd.DataFrame(datalist)
    return(df)
    



def Lineplot_GSA(self, myvars, caseid, site):    
    UQ_output = './UQ_output/' + self.casename + '/GSA'
    os.makedirs(UQ_output, exist_ok=True)  # Ensures the directory exists   
    
    df_all = pd.DataFrame()
    for v in myvars:  
        if v != 'taxis':                
            ## plot total sensitivity
            my_value = self.sens_tot[v]
            my_title = f'Total Sensitivity Indices for {v}: {caseid}'
            my_outfile = f'{UQ_output}/{caseid}_{site}_sens_tot_{v}_{self.postproc_freq}.png'
            df_total_sens = plot_sens_v(self, v, my_value, my_title, my_outfile)
            df_all = pd.concat([df_all, df_total_sens], ignore_index=True)

            ## plot main sensitivity
            my_value = self.sens_main[v]
            my_title = f'Main Sensitivity Indices for {v}: {caseid}'
            my_outfile = f'{UQ_output}/{caseid}_{site}_sens_main_{v}_{self.postproc_freq}.png'
            df_main_sens = plot_sens_v(self, v, my_value, my_title, my_outfile)
            df_all = pd.concat([df_all, df_main_sens], ignore_index=True)     
    
    # print(df_all)
    return(df_all)
       
            
            





'''
## stackplots with simple legends
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
        plt.legend(self.ensemble_parms, bbox_to_anchor = (1.2, 0.5))
        plt.savefig(self.OLMTdir+'/plots/sens_main_'+v+'.png')
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
        plt.legend(self.ensemble_parms, bbox_to_anchor = (1.2, 0.5))
        plt.savefig(self.OLMTdir+'/plots/sens_tot_'+v+'.png')
'''

'''
## stackplots with sophiscated legends
def plot_GSA(self, myvars, caseid, site):
    UQ_output = './UQ_output/' + self.casename + '/GSA'
    os.makedirs(UQ_output, exist_ok=True)  # Ensures the directory exists   
    
    for v in myvars:
        if v != 'taxis':
            # Create the figure and axis
            fig, ax = plt.subplots(figsize=(10, 6))  # Larger figure for better visualization            
            nvar = self.sens_main[v].shape[1]
            x_pos = np.arange(nvar)
            
            # Define distinct colors and patterns
            colors = plt.cm.tab20.colors  # Use a colormap for distinct colors
            hatches = ['/', '\\', '|', '-', '+', 'x', 'o', 'O', '.', '*']  # Patterns
            
            # Plot the stacked bars
            bottom = np.zeros(nvar)
            patches = []  # Store legend handles
            
            for p in range(self.nparms_ensemble):
                color = colors[p % len(colors)]
                hatch = hatches[p % len(hatches)]
                bar = ax.bar(
                    x_pos, 
                    self.sens_main[v][p, :], 
                    bottom=bottom, 
                    color=color, 
                    hatch=hatch, 
                    edgecolor='black'
                )
                bottom += self.sens_main[v][p, :]
                
                # Create a legend entry
                patches.append(mpatches.Patch(facecolor=color, hatch=hatch, edgecolor='black', label=self.ensemble_parms[p] + str(self.ensemble_pfts[p])))
            
            # Adjust the axis and labels
            ax.set_xticks(x_pos)
            ax.set_xticklabels([f'Var {i+1}' for i in range(nvar)], rotation=45)
            ax.set_ylabel('Sensitivity Index')
            ax.set_title(f'Main Sensitivity Indices for {v}')
            
            # Place legend outside the plot
            ax.legend(
                handles=patches, 
                loc='upper left', 
                bbox_to_anchor=(1, 1), 
                title='Parameters'
            )
            
            # Save the plot
            plt.tight_layout()
            plt.savefig(f'{UQ_output}/{caseid}_{site}_sens_main_{v}.png', bbox_inches='tight')
            plt.close(fig)  # Close the figure to free memory

            #Plot total sensitivity
            fig, ax = plt.subplots(figsize=(10, 6))  # Larger figure for better visualization
            # Plot the stacked bars
            bottom = np.zeros(nvar)
            patches = []  # Store legend handles            

            for p in range(self.nparms_ensemble):                
                color = colors[p % len(colors)]
                hatch = hatches[p % len(hatches)]
                bar = ax.bar(
                    x_pos,
                    self.sens_tot[v][p, :],
                    bottom=bottom,
                    color=color,
                    hatch=hatch,
                    edgecolor='black'
                )
                bottom += self.sens_tot[v][p, :]

                # Create a legend entry
                patches.append(mpatches.Patch(facecolor=color, hatch=hatch, edgecolor='black', label=self.ensemble_parms[p] + str(self.ensemble_pfts[p])))

            # Adjust the axis and labels
            ax.set_xticks(x_pos)
            ax.set_xticklabels([f'Var {i+1}' for i in range(nvar)], rotation=45)
            ax.set_ylabel('Sensitivity Index')
            ax.set_title(f'Total Sensitivity Indices for {v}')

            # Place legend outside the plot
            ax.legend(
                handles=patches,
                loc='upper left',
                bbox_to_anchor=(1, 1),
                title='Parameters'
            )

            # Save the plot
            plt.tight_layout()            
            plt.savefig(f'{UQ_output}/{caseid}_{site}_sens_tot_{v}.png', bbox_inches='tight')
            plt.close(fig)  # Close the figure to free memory
'''
