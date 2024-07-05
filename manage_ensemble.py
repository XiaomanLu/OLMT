#!/usr/bin/env python
import sys,os, time
import numpy as np
import netcdf4_functions as nffun
import subprocess
import pickle
import model_ELM
from optparse import OptionParser

#Python code used to manage the ensemble simulations 
#  and perform post-processing of model output.

parser = OptionParser()


parser.add_option("--case", dest="case", default="", \
                  help="Case name")
(options, args) = parser.parse_args()

#Load case object
myfile=open('pklfiles/'+options.case+'.pkl','rb')
mycase=pickle.load(myfile)

def count_active_processes(processes):
    """Returns the number of processes that are still running."""
    active_count = 0
    for process in processes:
        if process.poll() is None:  # None means the process is still running
            active_count += 1
    return active_count

workdir = os.getcwd()

active_count = 0
processes=[]
n_job = 1

#Run the simulations 
while (n_job <= mycase.nsamples):
  if (count_active_processes(processes) < int(mycase.np_ensemble)):
    jobst = str(100000+n_job)
    rundir = mycase.runroot+'/UQ/'+mycase.casename+'/g'+jobst[1:]+'/'
    log_file_path = f"{rundir}e3sm_log.txt"
    #Copy relevant files
    mycase.ensemble_copy(n_job)
    with open(log_file_path, "w") as log_file:
       if (mycase.noslurm == False):
         command = ['srun -n 1 -c 1 '+mycase.exeroot+'/e3sm.exe']
       else:
         command = [mycase.exeroot+'/e3sm.exe']
       process = subprocess.Popen(command, shell=True, stderr=subprocess.PIPE, cwd=rundir, stdout=log_file)
       processes.append(process)
    n_job=n_job+1
  else:
    time.sleep(1)

#wait on remaining processes
for process in processes:
    process.wait()

#Postprocess
if (mycase.postproc_vars != []):
  for n in range(0,mycase.nsamples):
    for v in mycase.postproc_vars:
        if (mycase.postproc_freq == 'daily'):  #default
          mycase.postprocess(v, ens_num=n+1,startyear=mycase.postproc_startyear,endyear=mycase.postproc_endyear, \
                hnum=1)
        elif (mycase.postproc_freq == 'monthly'):  #monthly
          mycase.postprocess(v, ens_num=n+1,startyear=mycase.postproc_startyear,endyear=mycase.postproc_endyear, \
                hnum=1, dailytomonthly=True) 
        elif (mycase.postproc_freq == 'annual'):  #annual
          mycase.postprocess(v, ens_num=n+1,startyear=mycase.postproc_startyear,endyear=mycase.postproc_endyear, \
                hnum=1, annualmean=True)
#Save postprocessed output
mycase.create_pkl()



