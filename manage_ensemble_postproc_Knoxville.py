#!/usr/bin/env python
#Python code used to manage the ensemble simulations and perform post-processing of model output.
import sys,os, time
import numpy as np
import subprocess
import pickle
import model_ELM
import warnings
warnings.filterwarnings("ignore")

#get the node file and parse
def get_nodelist():
    mynodes=[]
    nodelist=os.environ['SLURM_JOB_NODELIST'].split('xxx')
    print(nodelist)
    for n in nodelist:
      if ('[' in n):
          node_prefix=n.split('[')[0]
          nodelist2=n.split('[')[1].split(',')
          for n2 in nodelist2:
            if ('-' in n2):
              firstnode=n2.split('-')[0]
              lastnode=n2.split('-')[1].strip(']')
              for nn in range(int(firstnode),int(lastnode)+1):
                if ('baseline' in mycase.machine):
                  nstr = str(nn)
                else:
                  nstr = str(10000+nn)[1:]
                mynodes.append(node_prefix+nstr)
            else:
                if ('baseline' in mycase.machine):
                  nstr=str(n2)
                else:
                  nstr=str(10000+n2)[1:]
                mynodes.append(node_prefix+nstr)
      else:
          mynodes.append(n)
    return mynodes

def get_node_submit(pactive,process_nodes,mynodes):
    node_submit=0
    for n in range(0,len(mynodes)):
         ctn=0    #Counter for active processes on each node
         for p in range(0,len(processes)):
                if pactive[p] == 1 and process_nodes[p] == n:
                    ctn=ctn+1
         if (ctn < mycase.npernode/mycase.np):
             #If this node is not full, submit
             node_submit=n
    return(node_submit)

def check_run_success(n):
    success=False
    jobst = str(100000+n)
    rundir = mycase.runroot+'/UQ/'+mycase.casename+'/g'+jobst[1:]
    yst = str(10000+mycase.startyear+mycase.run_n)[1:]
    if (os.path.isfile(rundir+'/'+mycase.casename+'.elm.r.'+yst+'-01-01-00000.nc')):
        success=True
        print(success)
    return success

def active_processes(processes,process_jobnum,process_hang):
    """Returns the number of processes that are still running."""
    pactive=[]
    n=0
    for process in processes:
        if process.poll() is None:  # None means the process is still running
            #Check if final restart file created
            pactive.append(1)
            if (check_run_success(process_jobnum[n])):
                process_hang[n] = process_hang[n]+1
            if (process_hang[n] > 30):
                process.kill()  # Force kill the process
        else:
            pactive.append(0)
            #Post-process ensemble member if it hasn't yet been done
            if (mycase.postprocessed[n] == 0):
                print(n, check_run_success(process_jobnum[n]))
                if (check_run_success(process_jobnum[n])):
                    ierr = postprocess_ensemble(process_jobnum[n])
                else:
                    print('Ensemble member '+str(process_jobnum[n])+ \
                            'Failed to complete')
                mycase.postprocessed[n] = 1
        n=n+1
    return pactive

def postprocess_ensemble(n):
    #Postprocess
    if (mycase.postproc_vars != []):
        for v in mycase.postproc_vars:
          hnum=0
          mypfts=[0]
          if ('_pft' in v):
              #PFT level outputs requested
              hnum=1
              mypfts=mycase.postproc_pfts
          for p in mypfts:
            if (mycase.postproc_freq == 'daily'):  #default
              mycase.postprocess(v, ens_num=n,startyear=mycase.postproc_startyear, \
                    endyear=mycase.postproc_endyear,index=p,hnum=hnum)
            elif (mycase.postproc_freq == 'monthly'):  #monthly
              mycase.postprocess(v, ens_num=n,startyear=mycase.postproc_startyear, \
                    endyear=mycase.postproc_endyear,index=p,hnum=hnum, dailytomonthly=True)
            elif (mycase.postproc_freq == 'annual'):  #annual
              mycase.postprocess(v, ens_num=n,startyear=mycase.postproc_startyear, \
                    endyear=mycase.postproc_endyear,index=p,hnum=hnum, annualmean=True)
    return 0





####################################################### MAIN #######################################################

# Dynamic paras
caseid='20250320'
site='WH'
UQ_only = True # True - directly read from pklfile.
# False - re-generate the "output" dict and overwrite pklfile. Using "sbatch job_urban.sh" after "conda deactivate"!!!


# fixed paras
PATH_URBAN = '/gpfs/wolf2/cades/cli185/proj-shared/lux5/Project3_Urban/'
compset='ICB20TRCNPRDCTCBC'
suffix=''
casename=caseid+'_'+site+'_'+compset            
postproc_only = True


#Make sure to back up the old pkl files before this step!!!
#Create case object
if (not UQ_only):   
    mycase = model_ELM.ELMcase(caseid=caseid,compset=compset,site=site, \
            sitegroup='KNX', machine='cases-baseline', \
            runroot=PATH_URBAN+'e3sm_run', \
            caseroot=PATH_URBAN+'e3sm_cases', \
           )       
    mycase.casename=caseid+'_'+site+'_'+compset #+'_'+suffix
    mycase.startyear=2014   #Starting year of run; doesn't have to be same as actual run
    mycase.run_n=11         #Number of years for the run (to post process)
    mycase.postproc_pfts=[7,13]  #PFTs to postprocess
    mycase.postproc_vars=['TLAI','TLAI_pft','QVEGE_pft']
    mycase.postproc_startyear=2014    #Starting year to postprocess/calibrate
    mycase.postproc_endyear= 2024
    mycase.postproc_freq = 'annual'
    mycase.read_parm_list(PATH_URBAN+'OLMT/runscripts/parm_file_Knoxville')    
    samples_file=PATH_URBAN+f'OLMT/parm_samples/mcsamples_{caseid}_4000.txt'
    mycase.samples = (np.loadtxt(samples_file,)).transpose()
    mycase.nsamples=40 # 00
    mycase.np_ensemble=mycase.samples.shape[0]
    mycase.npernode=128
    mycase.obs={}
    mycase.obs_err={}
    mycase.OLMTdir=PATH_URBAN+'OLMT'    
    mycase.pscaler={}
    mycase.yscaler={}
    mycase.rundir_UQ = mycase.runroot+'/UQ/'+mycase.casename
else:
    myfile=open('./pklfiles/'+casename+'.pkl','rb')
    mycase=pickle.load(myfile)
    
    

# post-process
if (not UQ_only):
    workdir = os.getcwd()
    
    processes=[]
    process_jobnum=[]
    process_hang=[]    #Keep track of how long process has been hanging
    mycase.postprocessed=np.zeros([mycase.nsamples],int)
    n_job = 1
    if (mycase.noslurm == False):
       process_nodes = []
       mynodes = get_nodelist()
    
    #Run the simulations    
    while (n_job <= mycase.nsamples):
         pactive = active_processes(processes,process_jobnum,process_hang)
         if (sum(pactive) < int(mycase.np_ensemble)):
            jobst = str(100000+n_job)
            rundir = mycase.runroot+'/UQ/'+mycase.casename+'/g'+jobst[1:]+'/'
            log_file_path = f"{rundir}e3sm_log.txt"
            #log_file_path = '/gpfs/wolf2/cades/cli185/proj-shared/zdr/OLMT/e3sm_log.txt'
            #Copy relevant files
            if not postproc_only:
                mycase.ensemble_copy(n_job)
            with open(log_file_path, "w") as log_file:
               if (mycase.noslurm == False):
                    node_submit=get_node_submit(pactive,process_nodes,mynodes)
                    command = ['srun -n '+str(mycase.np)+' -c 1 -w '+mynodes[node_submit]+' '+mycase.exeroot+'/e3sm.exe']
                    if postproc_only:
                        command = 'ls'
                    process_nodes.append(node_submit)
               else:
                    command = [mycase.exeroot+'/e3sm.exe']
               process = subprocess.Popen(command, shell=True, stderr=subprocess.STDOUT, cwd=rundir, stdout=log_file)
               processes.append(process)
               process_jobnum.append(n_job)
               process_hang.append(0)
            n_job=n_job+1
         else:
             time.sleep(0.1)
    
    while (sum(pactive) > 0):
       pactive = active_processes(processes,process_jobnum,process_hang)
       time.sleep(0.1)

    #custom outputs (change units, sum variables, etc)
    # We can do additional processing of the output time series here. 
    ## mycase.output['NPP_correct'] = (mycase.output['FATES_NPP']-mycase.output['FATES_EXCESS_RESP'])*24*3600*365*1000
    ## mycase.output['NUP'] = (mycase.output['FATES_NH4UPTAKE']+mycase.output['FATES_NO3UPTAKE'])*24*3600*365*1000
    ## mycase.postproc_vars.append('NPP_correct')
    ## mycase.postproc_vars.append('NUP')
    mycase.create_pkl(outdir=mycase.OLMTdir+'/pklfiles/')


#------UQ -----------------------------
#Train surrogate models; break out the individual PFTs here
mycase.train_surrogate(['TLAI_pft7']) #'TLAI_pft7','TLAI_pft13','TLAI','QVEGE_pft7','QVEGE_pft13'

#run GSA (Global Sensitivity Analysis)
mycase.GSA(['TLAI_pft7']) # will break out into individual pft outputs

#plot GSA
mycase.plot_GSA(['TLAI_pft7'], caseid, site)

#Save postprocessed output
mycase.create_pkl(outdir=mycase.OLMTdir+'/pklfiles/')











