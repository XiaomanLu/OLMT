import sys
sys.path.append('..')
import model_ELM
import os
import numpy as np

#Define directories
machine = 'cades-baseline'
caseroot='/gpfs/wolf2/cades/cli185/scratch/zdr/e3sm_cases'
runroot='/gpfs/wolf2/cades/cli185/scratch/zdr/e3sm_run'
#inputdata='/gpfs/wolf2/cades/cli185/world-shared/e3sm/inputdata'
inputdata='/gpfs/wolf2/cades/cli185/proj-shared/zdr/inputdata'
modelroot='/ccsopen/home/zdr/models/E3SM'

#We are going to use a pre-built executable. Set exeroot='' to build 
#exeroot='/gpfs/wolf2/cades/cli185/scratch/zdr/e3sm_run/20240729_PR-LUQ_I1850CNRDCTCBC_ad_spinup/bld'
exeroot = '/gpfs/wolf2/cades/cli185/scratch/zdr/e3sm_run/20240729_US-MOz_IELMFATES/bld'

#----------------------Required inputs---------------------------------------------
site = 'PR-LUQ'            #6-character FLUXNET ID
mettype = 'site'           #Site or reanalysis product

use_cpl_bypass = False     #Coupler bypass for meteorology
use_fates      = True      #Use FATES compsets
fates_nutrient = False     #Use FATES nutrient (parteh_mode = 2)

nyears_ad      = 40       #number of years for ad spinup
nyears_final   = 40       #number of years for final spinup 
nyears_trans   = -1       #number of years for transient run 
                          #If -1, the final year will be the last year of forcing data.

#---------------------Optional inputs via namelist variables------------------------
#Define a dictionary to handle namelist options.
#note:  use surffile, domainfile, pftdynfile, metdir instead of the standard namelist variables for those files.
#namelist_options['option'] = value 
case_options={} 
case_options['fates_paramfile'] = inputdata+'/lnd/clm2/paramdata/fates_params_api.32.0.0_pft1_c231215.nc'
case_options['hist_mfilt']  = 365
case_options['hist_nhtfrq'] = -24


#--------------------ensemble options------------------------------------------------

parm_list      = '' #'parm_list_FATES'    #Set parameter list (leave blank for no ensemble)
np_ensemble    = 128   #number of ensemble numbers to run in parallel
nsamples       = 256  #number of samples to run
ensemble_file = ''     #File containing samples (if blank, OLMT will generate one)
postproc_vars=['FPSN','EFLX_LH_TOT']  #Variables to automatically post-process
postproc_startyear = 2000
postproc_endyear   = 2005
postproc_freq      = 'annual'   #Can be daily, monthly, annual

#----------------------Define treatment cases ----------------------------------------
#Treatmeant cases will use the same compset as the last case, and will inherit case_options
#Specify additional options for treatments as a list (one for each desired treatment)
nyears_treatment=[0]
treatment_options={}


#---------------End of user input -----------------------------------------------------

#Construct the list of compsets and suppring information
compset_type="I"
if (use_cpl_bypass):
    compset_type='ICB'
#Construct the list of compsets and supporting information
twophase=False
compset_base='CNPRDCTCBC'
if (use_fates):
    compset_base='ELMFATES'
compset_type="I"
if (use_cpl_bypass):
    compset_type='ICB'
elif ((mettype != 'site' or 'PR-LUQ' in site) and nyears_trans != 0):
    twophase=True       #if using DATM and reanalysis, split into 2 cases

#Define 3 standard cases (ad spinup, regular spinup, transient)
compsets=[]
suffix=[]
startyear=[]
nyears=[]
if (nyears_ad > 0):
    compsets.append(compset_type+'1850'+compset_base.replace('CNP','CN'))  #ad_spinup
    suffix.append('ad_spinup')
    startyear.append(1)
    nyears.append(nyears_ad)
if (nyears_final > 0):
    compsets.append(compset_type+'1850'+compset_base)  #Final spinup
    suffix.append('')
    startyear.append(1)
    nyears.append(nyears_final)
if (nyears_trans != 0):
    compsets.append(compset_type+'20TR'+compset_base)  #Transient
    suffix.append('')
    startyear.append(1850)
    nyears.append(nyears_trans)
depends = np.cumsum(np.ones([len(compsets)],int))-2
if (twophase):                            #add the phase 2 compset and case info
    compsets.append(compset_type+'20TR'+compset_base)  #Transient phase 2
    nyears.append(nyears[2])
    suffix.append('phase2')
    np.append(depends, depends[-1]+1)
    startyear.append(1850)

ensemble=False
if (parm_list != ''):
    ensemble=True
#To do:  Add treatment cases


cases={}
ncases = len(compsets)  #how many cases we are running
jobnum = np.zeros(len(compsets),int)  #list of submitted job ids

scriptdir=os.getcwd()
for c in range(0,ncases):
  cases[c] = model_ELM.ELMcase(caseid='',compset=compsets[c], site=site, \
        caseroot=caseroot,runroot=runroot,inputdata=inputdata,modelroot=modelroot, \
        machine=machine, exeroot=exeroot, suffix=suffix[c],  \
        res='hcru_hcru', nyears=nyears[c],startyear=startyear[c])

  #Create the case
  cases[c].create_case()
  cases[c].case_options = case_options
  cases[c].fates_nutrient=fates_nutrient
  #Set the custom parameter files
  if ('fates_paramfile' in case_options):
    cases[c].fates_paramfile = case_options['fates_paramfile'][c]
  if ('paramfile' in case_options):
    cases[c].paramfile = case_options['paramfile'][c]

  #Get forcing information
  if ('phase2' in suffix[c]):
      #Set the starting year from the last case
      cases[c].startyear = cases[c-1].startyear+cases[c-1].run_n
  cases[c].get_forcing(mettype=mettype)

  #Set the initial data file (if depends on previous case)
  cases[c].dependcase=''
  if (depends[c] >= 0):
      #Set the iniial data file from the last year of the prev case
      finidat_year = cases[depends[c]].run_n+1
      if ('20TR' in cases[depends[c]].compset or 'trans' in cases[depends[c]].compset):
          finidat_year = 1850+cases[depends[c]].run_n
      cases[c].set_finidat_file(finidat_case=cases[depends[c]].casename, \
              finidat_year=finidat_year)
      cases[c].dependcase = cases[depends[c]].casename

  #Set postprocessing variables
  if (ncases == 1 or '20TR' in compsets[c] or 'trans' in compsets[c]):
    cases[c].postproc_vars = postproc_vars
    cases[c].postproc_startyear = postproc_startyear
    cases[c].postproc_endyear = postproc_endyear
    cases[c].postproc_freq = postproc_freq
  else:
    cases[c].postproc_vars=[]

  #Set up the case (surface, domain and pftdata
  cases[c].setup_case()
  if (c == 0):
    #Get the surface and domain data 
    cases[c].setup_domain_surfdata(makesurfdat=True,makedomain=True)
    if (ensemble):
      cases[c].setup_ensemble(parm_list=parm_list,np_ensemble=np_ensemble,nsamples=nsamples)
  elif (ensemble):
    #Set up ensemble file using the file generated in the first case
    cases[c].setup_ensemble(parm_list=parm_list,np_ensemble=np_ensemble,ensemble_file=cases[c-1].ensemble_file)
  if (c == 2):
    #Get the dynamic PFT data
    cases[c].setup_domain_surfdata(makepftdyn=True)
  #Build the case
  cases[c].build_case()
  #Submit the case
  if (depends[c] < 0):  #no dependency
    jobnum[c] = cases[c].submit_case(ensemble=ensemble)
    #Set exeroot for subsequent cases so we don't have to rebuild
    exeroot = cases[c].exeroot
  else:
    jobnum[c] = cases[c].submit_case(depend=jobnum[depends[c]],ensemble=ensemble)
  #Return to script directory
  os.chdir(scriptdir)
