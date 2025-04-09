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
        self.sens_main[v] = np.zeros([self.nparms_ensemble,nvar],float)
        self.sens_tot[v]  = np.zeros([self.nparms_ensemble,nvar],float)  
        
        for i in range(0,nvar):            
            Si = sobol.analyze(problem, surrogate_output[v][:,i])       #, calc_second_order=False; It’s removing duplicates from problem['names']                         
            self.sens_main[v][:,i]=Si['S1']
            self.sens_tot[v][:,i]=Si['ST']
   

'''
## simple version without distinguishable legends
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


## plots with complex legends
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
