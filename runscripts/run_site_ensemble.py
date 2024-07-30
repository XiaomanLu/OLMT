from model_ELM import ELMcase
import os
import numpy as np

#Define directories
caseroot='/lcrc/group/e3sm/ac.ricciuto/e3sm_cases'
runroot='/lcrc/group/e3sm/ac.ricciuto/e3sm_run'            #Leave blank to use machine default 
inputdata=''          #Leave blank to use machine default (DIN_LOC_ROOT)
modelroot=os.environ['HOME']+'/models/E3SM'
#Use an existing executable, or set exeroot='' to do build 
exeroot='/lcrc/group/e3sm/ac.ricciuto/e3sm_run/20240705_US-MOz_ICB1850CNRDCTCBC_ad_spinup/bld/'

site='US-MOz'      #site name
mettype='site'     #met data type
machine  = 'chrysalis'

runtype = 'BGC'
if (runtype == 'BGC'):
  compsets = ['ICB1850CNRDCTCBC','ICB1850CNPRDCTCBC','ICB20TRCNPRDCTCBC']
  suffix   = ['_ad_spinup','','']      #Identifer suffix
  nyears   = [200,200,170]               #number of years to run each case
  depends  = [-1,0,1]                  #Case dependency (-1 = no dependency)
elif (runtype == 'SP'):
  compsets = ['ICBELMBC']
  suffix = ['']
  nyears = [32]
  depends = [-1]
  startyear = 1988

#ensemble information
parm_list='parm_list_test_bgc'       #parameter list file 
np_ensemble = 512  #number of ensemble numbers to run in parallel
nsamples= 1000
ensemble_file = '' #File containing samples (if blank, OLMT will generate one)

#namelist options
namelist_options = []
#namelist_options.append("startdate_add_co2 = '18510101'")
#namelist_options.append("add_co2 = 150")

#Output variables to postprocess ensemble
postproc_vars=['GPP','EFLX_LH_TOT']
postproc_startyear = 2007
postproc_endyear   = 2011
postproc_freq      = 'monthly'   #Can be daily, monthly, annual
calibrate          = True        #get observations and fit using surrogate model

#------------------------------------------------------------------------------------------------
cases = {}
ncases = len(compsets)  #how many cases we are running
jobnum = np.zeros(len(compsets),int)  #list of submitted job ids

if (ncases > 1):
    startyear=-1  #Ignore start year if doing full spinup+transient
for c in range(0,ncases):
  cases[c] = ELMcase(caseid='',compset=compsets[c], site=site, \
        caseroot=caseroot,runroot=runroot,inputdata=inputdata,modelroot=modelroot, \
        machine=machine,exeroot=exeroot, suffix=suffix[c], nyears=nyears[c], np=1, \
        res='hcru_hcru', startyear=startyear, namelist_options=namelist_options)

  #Create the case
  cases[c].create_case()
  #Get forcing information
  cases[c].get_forcing(mettype=mettype)
  #Set the initial data file (if depends on previous case)
  if (depends[c] >= 0):
      #Set the initial data file from the last year of the prev case
      finidat_year = cases[depends[c]].run_n+1
      if ('20TR' in cases[depends[c]].compset or 'trans' in cases[depends[c]].compset):
          finidat_year = 1850+cases[depends[c]].run_n
      cases[c].set_finidat_file(finidat_case=cases[depends[c]].casename, \
              finidat_year=finidat_year)

  #Set postprocessing variables
  if (ncases == 1 or '20TR' in compsets[c] or 'trans' in compsets[c]):
    cases[c].postproc_vars = postproc_vars
    cases[c].postproc_startyear = postproc_startyear
    cases[c].postproc_endyear = postproc_endyear
    cases[c].postproc_freq = postproc_freq
    #get the fluxnet observations
    for v in postproc_vars:
      cases[c].get_fluxnet_obs(site=site,tstep=postproc_freq,ystart=postproc_startyear, \
          yend=postproc_endyear,fluxnet_var=v)
  else:
    cases[c].postproc_vars=[]
  
  cases[c].setup_case()
  #If first case, extract the surface and domain files for the region of interest
  if (c == 0):
    cases[c].setup_domain_surfdata(makesurfdat=True,makedomain=True)
    cases[c].setup_ensemble(parm_list=parm_list,np_ensemble=np_ensemble,nsamples=nsamples)
  else:
    #Set up ensemble file using the file generated in the first case
    cases[c].setup_ensemble(parm_list=parm_list,np_ensemble=np_ensemble,ensemble_file=cases[c-1].ensemble_file)
  #If transient case, make the pftdyn file
  if (c == 2):
    cases[c].setup_domain_surfdata(makepftdyn=True)
  #Build the case
  cases[c].build_case()
  #Submit the case
  if (depends[c] < 0):  #no dependency
    jobnum[c] = cases[c].submit_case(ensemble=True)
    #Set exeroot for subsequent cases so we don't have to rebuild
    exeroot = cases[c].exeroot
  else:
    jobnum[c] = cases[c].submit_case(depend=jobnum[depends[c]],ensemble=True)

