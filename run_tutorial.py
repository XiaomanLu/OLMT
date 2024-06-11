from model_ELM import ELMcase
import os
import numpy as np

#Define directories
caseroot='/gpfs/wolf2/cades/cli185/scratch/zdr/e3sm_cases'
runroot='/gpfs/wolf2/cades/cli185/scratch/zdr/e3sm_run'
inputdata='//gpfs/wolf2/cades/cli185/proj-shared/zdr/inputdata'
modelroot=os.environ['HOME']+'/models/E3SM'

#We are going to use a pre-built executable. Set exeroot='' to build 
exeroot='/gpfs/wolf2/cades/cli185/scratch/zdr/e3sm_run/20240611_US-UMB_ICB1850CNRDCTCBC_ad_spinup/bld/'

#Information needed to construct a multi-case run
compsets = ['ICB1850CNRDCTCBC','ICB1850CNPRDCTCBC','ICB20TRCNPRDCTCBC']
suffix   = ['_ad_spinup','','']      #Identifer suffix
nyears   = [60,60,164]               #number of years to run each case
depends  = [-1,0,1]                  #Case dependency (-1 = no dependency)
cases={}

#Region containing California (change if desired)
lat_bounds = [32,42]
lon_bounds = [-125,-114]
numprocs   = 1   #number of processors per simulation.  Must be <= number of land gridcells
np_ensemble = 32 #number of ensemble numbers to run in parallel
site='US-UMB'
mettype='site'
parm_list='parm_list_firetune'

ncases = len(compsets)  #how many cases we are running
jobnum = np.zeros(len(compsets),int)  #list of submitted job ids

for c in range(0,ncases):
  cases[c] = ELMcase(caseid='',compset=compsets[c], site=site, \
        caseroot=caseroot,runroot=runroot,inputdata=inputdata,modelroot=modelroot, \
        machine='cades-baseline',exeroot=exeroot, suffix=suffix[c], lat_bounds=lat_bounds, \
        lon_bounds = lon_bounds, nyears=nyears[c], np=numprocs, res='hcru_hcru')

  #Create the case
  cases[c].create_case()
  #Get forcing information
  cases[c].get_forcing(mettype=mettype)
  #Set the initial data file (if depends on previous case)
  if (depends[c] >= 0):
      #Set the initial data file from the last year of the prev case
      finidat_year = nyears[depends[c]]+1
      if ('20TR' in cases[depends[c]].compset or 'trans' in cases[depends[c]].compset):
          finidat_year = 1850+nyears[depends[c]]
      cases[c].set_finidat_file(finidat_case=cases[depends[c]].casename, \
              finidat_year=finidat_year)
  #Set up the case
  cases[c].setup_case()
  #If first case, extract the surface and domain files for the region of interest
  if (c == 0):
    cases[c].setup_domain_surfdata(makesurfdat=True,makedomain=True)
    cases[c].setup_ensemble(parm_list=parm_list,np_ensemble=np_ensemble,nsamples=100)
  else:
    cases[c].setup_ensemble(parm_list=parm_list,np_ensemble=np_ensemble,ensemble_file=cases[c-1].ensemble_file)
  #If transient case, make the pftdyn file
  if (c == 2):
    cases[c].setup_domain_surfdata(makepftdyn=True)
  #Build the case
  cases[c].build_case()
  #Submit the case
  if (depends[c] < 0):  #no dependency
    jobnum[c] = cases[c].submit_case()
    #Set exeroot for subsequent cases so we don't have to rebuild
    exeroot = cases[c].exeroot
  else:
    jobnum[c] = cases[c].submit_case(depend=jobnum[depends[c]])

