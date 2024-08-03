import sys
sys.path.append('..')
import model_ELM
from OLMTutils import get_machine_info, get_site_info
import os
import numpy as np


#Get default directories, automatically detect machine if machine_name=''
machine, rootdir, inputdata = get_machine_info(machine_name='')

#set rootdir and inputdata below if you want to override defaults
caseroot= rootdir+'/e3sm_cases'
runroot = rootdir+'/e3sm_run'
#TODO:  add option to clone repository
modelroot = os.environ['HOME']+'/models/E3SM'  #Existing E3SM code directory

#We are going to use a pre-built executable. Set exeroot='' to build 
exeroot = '~/models/e3sm_run/20240802_AU-How_ICB1850CNRDCTCBC_ad_spinup/bld/'

#----------------------Required inputs---------------------------------------------
sites = 'US-MOz'           #Site or list of sites (6-character FLUXNET ID) or 'all for all sites in group
sitegroup = 'AmeriFlux'    #Sites defined in <inputdata>/lnd/clm2/PTCLM/<sitegroup>_sitedata.txt
mettype = 'site'           #Site or reanalysis product
case_suffix = ''           #Identifier for cases (leave blank if none)

use_cpl_bypass = True     #Coupler bypass for meteorology
use_SP         = False     #Use Satellite phenolgy mode (doesn't yet work with FATES-SP)
use_fates      = False     #Use FATES compsets
fates_nutrient = True      #Use FATES nutrient (parteh_mode = 2)

nyears_ad      =   40     #number of years for ad spinup
nyears_final   =   40      #number of years for final spinup OR for SP run
nyears_trans   =   40      #number of years for transient run 
                           #  If -1, the final year will be the last year of forcing data.
run_startyear  = 1850      #Starting year for transient run OR for SP run


#---------------------Optional inputs via namelist variables------------------------
#Define a dictionary to handle namelist options.
#note:  use surffile, domainfile, pftdynfile, metdir instead of the standard namelist variables for those files.
#case_options['option'] = value or [value1, value2, value3] if applying different options to different compsets
case_options={} 
#case_options['fates_paramfile'] = inputdata+'/lnd/clm2/paramdata/fates_params_api.32.0.0_pft1_c231215.nc'
#case_options['hist_mfilt']  = '365,365'
#case_options['hist_nhtfrq'] = '-24,-24'


#--------------------ensemble options------------------------------------------------

parm_list      = 'parm_list_example' #'parm_list_fatesUQ' #'parm_list_example' #'parm_list_FATES'    #Set parameter list (leave blank for no ensemble)
nsamples       =  12    #number of samples to run
np_ensemble    =   6    #number of ensemble numbers to run in parallel (MUST be <= nsamples)
ensemble_file  = ''     #File containing samples (if blank, OLMT will generate one)
postproc_vars  = ['FPSN','EFLX_LH_TOT']  #Variables to automatically post-process
postproc_startyear = 1880
postproc_endyear   = 1889
postproc_freq      = 'annual'   #Can be daily, monthly, annual

#----------------------Define treatment cases ----------------------------------------
#Treatmeant cases will use the same compset as the last case, and will inherit case_options
#Specify additional options for treatments as a list (one for each desired treatment)
nyears_treatment=[0]
treatment_options={}

#---------------End of user input -----------------------------------------------------

#Check to see if all reqested sites exist
siteinfo = get_site_info(inputdata, sitegroup=sitegroup)
if not isinstance(sites,list):
    sites=[sites]
if sites[0] == 'all':
    sites = siteinfo['names']
    print('Running all sites in '+sitegroup+' site group:')
    print(siteinfo['names'])
else:
    for s in sites:
        if not (s in siteinfo['names']):
            print(s+' not in '+sitegroup+' site group. Exiting.')
            print('Available sites: ',siteinfo['names'])
            sys.exit(1)
    print('Running site(s): ', sites)

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
elif ((mettype != 'site' or 'PR-LUQ' in sites) and nyears_trans != 0):
    twophase=True       #if using DATM and reanalysis, split into 2 cases

#TODO - move construction of compset lists to a function (in OLMTinfo)
compsets=[]
suffix=[]
startyear=[]
nyears=[]
if (use_SP):
  compsets.append(compset_type+'ELMBC')
  suffix.append('')
  startyear.append(run_startyear)
  nyears.append(nyears_final)
  depends=[-1]
else:
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
    startyear.append(run_startyear)
    nyears.append(nyears_trans)
  depends = np.cumsum(np.ones([len(compsets)],int))-2
if (twophase):                            #add the phase 2 compset and case info
    compsets.append(compset_type+'20TR'+compset_base)  #Transient phase 2
    nyears.append(nyears[-1])
    suffix.append('phase2')
    depends = np.append(depends, depends[-1]+1)
    startyear.append(run_startyear)

ensemble=False
if (parm_list != ''):
    ensemble=True


#TODO:  Add treatment cases

print('Machine: '+machine)
print('Run root directory:  '+runroot)
print('Case root directory: '+caseroot)
print('Input data directory: '+inputdata)
print('Model root directory: '+modelroot+'\n')

print('\nELM simulation info:')
multisite_scripts=[]
for c in range(0,len(compsets)):
    print('Compset '+str(c+1)+': '+compsets[c])
    print('   Simulation starting year: '+str(startyear[c]))
    if (nyears[c] > 0):
        print('   Simulation length:        '+str(nyears[c]))
        print('\n')
    multisite_scripts.append('')
if (ensemble):
    print('Ensemble size:  '+str(nsamples))
    print('Parameter list: '+parm_list+'\n')

nsites = len(sites)
jobnum = np.zeros(len(compsets),int)  #list of submitted job ids

for site in sites:
  cases={}
  ncases = len(compsets)  #how many cases we are running
  scriptdir=os.getcwd()

  for c in range(0,ncases):
    mysuffix = '_'.join(filter(None,[suffix[c],case_suffix]))

    cases[c] = model_ELM.ELMcase(caseid='',compset=compsets[c], site=site, \
        caseroot=caseroot,runroot=runroot,inputdata=inputdata,modelroot=modelroot, \
        machine=machine, exeroot=exeroot, suffix=mysuffix,  \
        res='hcru_hcru', nyears=nyears[c],startyear=startyear[c])

    #Create the case
    cases[c].create_case()
    cases[c].case_options={}
    #Get the namelist options for this case
    for key in case_options:
        if isinstance(case_options[key], list):
            cases[c].case_options[key] = case_options[key][c]
        else:
            cases[c].case_options[key] = case_options[key]
    #Other options
    cases[c].fates_nutrient=fates_nutrient
    #Set the custom parameter files
    if ('fates_paramfile' in case_options):
      cases[c].fates_paramfile = case_options['fates_paramfile']
    if ('paramfile' in case_options):
      cases[c].paramfile = case_options['paramfile']

    #Get forcing information
    print('Getting forcing information')
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

    #Set postprocessing variables for ensemble
    if ((ncases == 1 or '20TR' in compsets[c] or 'trans' in compsets[c]) and ensemble):
      cases[c].postproc_vars = postproc_vars
      cases[c].postproc_startyear = postproc_startyear
      cases[c].postproc_endyear = postproc_endyear
      cases[c].postproc_freq = postproc_freq
    else:
      cases[c].postproc_vars=[]

    #Set up the case (surface, domain and pftdata)
    print('Setting up case for site: '+site)
    cases[c].setup_case()
    if (c == 0):
      #Get the surface and domain data 
      cases[c].setup_domain_surfdata(makesurfdat=True,makedomain=True)
      if (ensemble and site == sites[0]):
        cases[c].setup_ensemble(parm_list=parm_list,np_ensemble=np_ensemble,nsamples=nsamples)
        ensemble_file = cases[c].ensemble_file
    elif (ensemble):
      #Set up ensemble file using the file generated in the first site and case
      cases[c].setup_ensemble(parm_list=parm_list,np_ensemble=np_ensemble,ensemble_file=ensemble_file)
    if (c == 2 and not use_fates):
      #Get the dynamic PFT data
      cases[c].setup_domain_surfdata(makepftdyn=True)

    #Build the case
    print('Building case')
    cases[c].build_case()
    
    #Submit the case
    print('Submitting case')
    jobnum_depend=-1
    if (depends[c] >= 0):
        jobnum_depend = jobnum[depends[c]]
    #Set exeroot for all subsequent cases/sites so we don't have to rebuild
    if (depends[c] < 0 and site == sites[0]):
        exeroot = cases[c].exeroot
    if (site == sites[nsites-1] or ensemble):
        jobnum[c] = cases[c].submit_case(depend=jobnum_depend, \
            ensemble=ensemble,multisite_script=multisite_scripts[c])
    elif (nsites > 1 and site == sites[0]):
        multisite_scripts[c] = cases[c].create_multisite_script(sites, scriptdir)
    #Return to script directory
    os.chdir(scriptdir)


#archive this script (based on name of first case)
archive_fname='./archive/'+cases[0].casename.replace('_ad_spinup','')
archive_fname=archive_fname.replace('1850','').replace('20TR','')+'_'+machine
if (nsites > 1):
    archive_fname = archive_fname.replace(site,'multisite')
os.system('mkdir -p archive')
if (ensemble):
    archive_fname = archive_fname+'_ensemble'
os.system('cp '+__file__+' '+archive_fname+'.py')


