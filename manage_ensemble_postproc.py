#!/usr/bin/env python
import sys,os, time
import numpy as np
import subprocess
import pickle
import model_ELM
from optparse import OptionParser

#Python code used to manage the ensemble simulations 
#  and perform post-processing of model output.

parser = OptionParser()

caseid='20250320'
#caseid='FACE_r241231_CalibrationMCMC_RD'
#caseid2='FACE_r240107_CalibrationMCMCe_RD'
compset='ICB20TRCNPRDCTCBC'
suffix=''
site='WH'
UQ_only = True # True - re-generate the "output" dict and overwrite pklfile; 
               # False - directly read from pklfile
casename=caseid+'_'+site+'_'+compset #+'_'+suffix

#Make sure to back up the old pkl files before this step!
#Create case object
if (not UQ_only):
  # suffix=suffix,
 mycase = model_ELM.ELMcase(caseid=caseid,compset=compset,site=site, \
         sitegroup='KNX', machine='cases-baseline', \
         runroot='/gpfs/wolf2/cades/cli185/proj-shared/lux5/Project3_Urban/e3sm_run', \
         caseroot='/gpfs/wolf2/cades/cli185/proj-shared/lux5/Project3_Urban/e3sm_cases', \
            )

 mycase.casename=caseid+'_'+site+'_'+compset #+'_'+suffix
 mycase.startyear=2014   #Starting year of run; doesn't have to be same as actual run
 mycase.run_n=11         #Number of years for the run (to post process)
 mycase.postproc_pfts=[7,13]  #PFTs to postprocess
 mycase.postproc_vars=['TLAI','TLAI_pft','QVEGE_pft']
 mycase.postproc_startyear=2014    #Starting year to postprocess/calibrate
 mycase.postproc_endyear= 2024
 mycase.postproc_freq = 'annual'
 mycase.read_parm_list('/gpfs/wolf2/cades/cli185/proj-shared/lux5/Project3_Urban/OLMT/runscripts/parm_file_Knoxville')
 # is in OLMT/parm_files
 samples_file='/gpfs/wolf2/cades/cli185/proj-shared/lux5/Project3_Urban/OLMT/parm_samples/mcsamples_20250320_4000.txt'
 mycase.samples = (np.loadtxt(samples_file,)).transpose()
 mycase.nsamples=40 # 00
 mycase.np_ensemble=mycase.samples.shape[0]
 mycase.npernode=128
 mycase.obs={}
 mycase.obs_err={}
 mycase.OLMTdir='/gpfs/wolf2/cades/cli185/proj-shared/lux5/Project3_Urban/OLMT'
 ##Observed annual values
 ##mycase.obs['NPP_correct'] = [1012.9007,1055.66746,932.6698191,1127.148001,1206.003218,1021.637006,661.6474994,947.9261663,1037.09508,902.2175763,1129.619381,940.5005198]
 ##mycase.obs['NUP']= [7.77, 8.773333333, 7.253333333, 8.996666667, 9, 8.316666667, 5.163333333, 8.766666667, 9.756666667, 8.323333333,-9999,-9999]
 #Standard deviations for observations
 ##mycase.obs_err['NPP_correct'] = [67.45164946, 80.42778834, 71.76473908, 15.70954181, 26.08409962, 66.81685992, 59.20860584, 28.58625255, 63.15291502, 79.78907243, 72.94812833, 71.98398705]
 ##mycase.obs_err['NUP'] = [0.3935733731, 0.5490699207, 0.4948512683, 0.1897659377, 0.4903060269, 0.6721689602, 0.4733685433, 0.3570869798, 0.6961880333, 0.8348319858,-9999,-9999]
 mycase.pscaler={}
 mycase.yscaler={}
 mycase.rundir_UQ = mycase.runroot+'/UQ/'+mycase.casename
else:
 myfile=open('./pklfiles/'+casename+'.pkl','rb')
 mycase=pickle.load(myfile)
 #myfile2=open('./pklfiles/'+casename2+'.pkl','rb')
 #mycase2=pickle.load(myfile2)

postproc_only = True
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

#Train surrogate models

##mycase.postproc_vars.append('NPP_response')
##mycase.output['NPP_response'] = mycase2.output['NPP_correct'] - mycase.output['NPP_correct']
#Create a new variable "NPP_response" that is the differece between eCO2 (mycase2) and aCO2 (mycase1) NPP
##mycase.postproc_vars.append('NPP_response')
##mycase.output['NPP_response'] = mycase2.output['NPP_correct'] - mycase.output['NPP_correct']
#Add the data for this variable to be used in calibration
##mycase.obs['NPP_response'] = [74.51825141, \
##262.4690799, \
##260.8185289, \
##320.2143628, \
##334.8027339, \
##277.0862578, \
##267.9204289, \
##332.4450538, \
##349.5163926, \
##332.9064781, \
##355.4904338, \
##191.3458051]
##mycase.obs_err['NPP_response'] = [139.369053, \
##145.1765813, \
##104.0828343, \
##39.98227572, \
##67.97362259, \
##109.2344479, \
##163.6981652, \
##92.41676215, \
##141.423613, \
##201.1801581, \
##194.9031354, \
##196.5207146]

# break out the individual PFTs here
mycase.train_surrogate(['TLAI_pft7','TLAI_pft13','TLAI','QVEGE_pft7','QVEGE_pft13'])

#run GSA
mycase.GSA(['TLAI_pft7']) # will break out into individual pft outputs
#plot GSA
mycase.plot_GSA(['TLAI_pft7'])

#Save postprocessed output
mycase.create_pkl(outdir=mycase.OLMTdir+'/pklfiles/')

#Set intial values for parameters
##parms=((np.array(mycase.ensemble_pmax)+np.array(mycase.ensemble_pmin))/2)

#Run MCMC for the 2 varibles of interest
##mycase.MCMC(parms, ['NPP_response','NPP_correct'], 100000)

