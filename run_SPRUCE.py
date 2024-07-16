import model_ELM
import os
import numpy as np

#Define directories
caseroot='/gpfs/wolf2/cades/cli185/scratch/zdr/e3sm_cases'
runroot='/gpfs/wolf2/cades/cli185/scratch/zdr/e3sm_run'
inputdata='/gpfs/wolf2/cades/cli185/proj-shared/zdr/inputdata'
modelroot='/ccsopen/home/zdr/models/E3SM-Peatlands'

#We are going to use a pre-built executable. Set exeroot='' to build 
exeroot=''
exeroot='/gpfs/wolf2/cades/cli185/scratch/zdr/e3sm_run/20240715_US-SPR_ICB1850CNRDCTCBC_ad_spinup/bld'

#Information needed to construct a multi-case run
#Spinup and transient cases

site = 'US-SPR'

#Define 3 standard cases (ad spinup, regular spinup, transient through 2015)
compsets = ['ICB1850CNRDCTCBC','ICB1850CNPRDCTCBC','ICB20TRCNPRDCTCBC']
suffix   = ['_ad_spinup','','']      #Identifer suffix
nyears   = [200,250,165]             #number of years to run each case
depends  = [-1,0,1]                  #Case dependency (-1 = no dependency)
metdir   = ['/gpfs/wolf2/cades/cli185/proj-shared/zdr/inputdata/SPRUCE_data/', \
            '/gpfs/wolf2/cades/cli185/proj-shared/zdr/inputdata/SPRUCE_data/', \
            '/gpfs/wolf2/cades/cli185/proj-shared/zdr/inputdata/SPRUCE_data/']
pftdynfile=['','','/gpfs/wolf2/cades/cli185/proj-shared/zdr/inputdata/SPRUCE_data/pftdyn/surfdata.pftdyn_plot07.nc']
startyear = [1,1,1850]

#Define treatments and plots
treatments=['TAMB','T0.00','T2.25','T4.50','T6.75','T9.00','T0.00eCO2','T2.25eCO2', \
        'T4.50eCO2','T6.75eCO2','T9.00eCO2']
plots=[7,6,20,13,8,17,19,11,4,16,10]  #Plot numbers corresponding to each treatment
#Add Treatment cases
for p in range(0,len(plots)):
    compsets.append('ICB20TRCNPRDCTCBC')
    suffix.append('_'+treatments[p])
    nyears.append(7)        #Each treatment case runs 2015-2021
    startyear.append(2015)
    depends.append(2)       #Depends on transient case (all treatment cases can run in parallel)
    plotstr = str(100+plots[p])[1:]
    metdir.append(metdir[0]+'/plot'+plotstr)  #Each case has its own met data directory
    #Each case has its own dynamic PFT file
    pftdynfile.append('/gpfs/wolf2/cades/cli185/proj-shared/zdr/inputdata/SPRUCE_data/pftdyn/surfdata.pftdyn_plot'+plotstr+'.nc')

#Custom parameter file
parm_file = '/ccsopen/home/zdr/models/OLMT/clm_params_SPRUCE_20231120_spruceroot.nc'

#______________________________________________________________________________________

cases={}
ncases = len(compsets)  #how many cases we are running
jobnum = np.zeros(len(compsets),int)  #list of submitted job ids

for c in range(0,ncases):
  cases[c] = model_ELM.ELMcase(caseid='',compset=compsets[c], site=site, \
        caseroot=caseroot,runroot=runroot,inputdata=inputdata,modelroot=modelroot, \
        machine='cades-baseline',exeroot=exeroot, suffix=suffix[c], \
        res='hcru_hcru', nyears=nyears[c], startyear=startyear[c])
  cases[c].humhol=True    #Turn on SPRUCE hummock-hollow

  #Create the case
  cases[c].create_case()
  #Set the custom parameter file
  cases[c].parm_file = parm_file
  #Get forcing information
  cases[c].get_forcing(mettype='site',metdir=metdir[c])
  #If first case, extract the surface and domain files for region of interest
  #Set the initial data file (if depends on previous case)
  if (depends[c] >= 0):
      #Set the initial data file from the last year of the prev case
      finidat_year = cases[depends[c]].run_n+1
      if ('20TR' in cases[depends[c]].compset or 'trans' in cases[depends[c]].compset):
          finidat_year = 1850+cases[depends[c]].run_n
      cases[c].set_finidat_file(finidat_case=cases[depends[c]].casename, \
              finidat_year=finidat_year)
  #Set up the case
  cases[c].setup_case(pftdynfile=pftdynfile[c])
  if (c == 0):
    cases[c].setup_domain_surfdata(makesurfdat=True,makedomain=True)
  #Build the case
  cases[c].build_case()
  #Submit the case
  if (depends[c] < 0):  #no dependency
    jobnum[c] = cases[c].submit_case()
    #Set exeroot for subsequent cases so we don't have to rebuild
    exeroot = cases[c].exeroot
  else:
    jobnum[c] = cases[c].submit_case(depend=jobnum[depends[c]])

