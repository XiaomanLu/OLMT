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
              nstr = str(10000+nn)
              mynodes.append(node_prefix+nstr[1:])
          else:
              nstr=str(10000+n2)
              mynodes.append(node_prefix+nstr[1:])
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
         if (ctn < mycase.npernode):
             #If this node is not full, submit
             node_submit=n
    return(node_submit)

def active_processes(processes):
    """Returns the number of processes that are still running."""
    pactive=[]
    for process in processes:
        if process.poll() is None:  # None means the process is still running
            pactive.append(1)
        else:
            pactive.append(0)
    return pactive

workdir = os.getcwd()


processes=[]
n_job = 1
if (mycase.noslurm == False):
    process_nodes = []
    mynodes = get_nodelist()

#Run the simulations 
while (n_job <= mycase.nsamples):
  pactive = active_processes(processes)
  if (sum(pactive) < int(mycase.np_ensemble)):
    jobst = str(100000+n_job)
    rundir = mycase.runroot+'/UQ/'+mycase.casename+'/g'+jobst[1:]+'/'
    log_file_path = f"{rundir}e3sm_log.txt"
    #Copy relevant files
    mycase.ensemble_copy(n_job)
    with open(log_file_path, "w") as log_file:
       if (mycase.noslurm == False):
         node_submit=get_node_submit(pactive,process_nodes,mynodes)
         command = ['srun -n 1 -c 1 -w '+mynodes[node_submit]+' '+mycase.exeroot+'/e3sm.exe']
         process_nodes.append(node_submit)
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

#Create surrogate models


