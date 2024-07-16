import netcdf4_functions as nffun
import socket, os, sys, csv, time, math, numpy
import re, subprocess
import pickle
from datetime import datetime
from .makepointdata import makepointdata
from .set_histvars import *
from .ensemble import *
from .get_fluxnet_obs import *
from .surrogate_NN import *
from .run_GSA import *
from .MCMC import *

class ELMcase():
  def __init__(self,caseid='',compset='ICBELMBC',suffix='',site='',sitegroup='AmeriFlux', \
            res='',tstep=1,np=1,nyears=1,startyear=-1, machine='', \
            exeroot='', modelroot='', runroot='',caseroot='',inputdata='', \
            region_name='', lat_bounds=[-90,90],lon_bounds=[-180,180], \
            namelist_options=[],casename=''):

      if (casename != ''):
        #get case information from pre-existing pkl file:
        print('Loading '+casename)
        #Load case object
        case_file=open('pklfiles/'+casename+'.pkl','rb')
        myinstance=pickle.load(case_file)
        for k in myinstance.__dict__.keys():
          setattr(self, k, getattr(myinstance, k))
      else:
        self.model_name='elm'
        self.modelroot=modelroot
        self.inputdata_path = inputdata
        self.runroot=runroot
        self.caseroot=caseroot
        self.exeroot=exeroot
        self.OLMTdir = os.getcwd()
        #Set default resolution (site or regional)
        self.site=site
        if (res == ''):
          if (site == ''):
              self.res='r05_r05'
              #Defined rectangular region
          else:
              self.res='ELM_USRDAT'
        else:
          self.res=res
        self.region = 'region'
        if (region_name != ''):
          self.region = region_name
        self.lat_bounds=lat_bounds
        self.lon_bounds=lon_bounds
        self.sitegroup=sitegroup
        #Set the default case id prefix to the current date
        if (caseid == ''):
          current_date = datetime.now()
          # Format the date as YYYYMMDD
          self.caseid = current_date.strftime('%Y%m%d')
        else:
          self.caseid = caseid
        self.project=''
        self.get_machine(machine=machine)
        self.compiler=''
        self.pio_version=2
        self.compset=compset
        self.case_suffix=suffix   #used for ad_spinup and trans
        #Custom surface/domain info
        self.surffile = ''
        self.pftdynfile = ''
        self.parm_file = ''
        self.fates_paramfile = ''
        self.nopftdyn=False
        self.domainfile = ''
        self.run_n = nyears
        if (startyear == -1):
          if '1850' in self.compset:
              self.startyear=1
          elif '20TR' in self.compset or 'trans' in suffix:
              self.startyear=1850
          else:
              self.startyear=2000
        else:
           self.startyear=startyear
        #Number of processors
        self.np = np
        #Timestep in hours
        self.tstep = tstep
        self.has_finidat = False
        self.cppdefs=''
        self.srcmods=''
        self.output={}
        self.obs={}
        self.obs_err={}
        self.surrogate={}
        self.postproc_vars=[]
        self.postproc_startyear=-1
        self.postproc_endyear=9999
        self.namelist_options=namelist_options

  def setup_ensemble(self, sampletype='monte_carlo',parm_list='', ensemble_file='', \
          np_ensemble=64, nsamples=100):
    read_parm_list(self, parm_list=parm_list)
    if (ensemble_file == ''):
      create_samples(self, sampletype=sampletype, parm_list=parm_list,nsamples=nsamples)
    else:
      self.ensemble_file = ensemble_file
      self.samples = np.transpose(np.loadtxt(ensemble_file))
      self.nsamples = np.shape(self.samples)[1]
    self.np_ensemble=np_ensemble
    create_ensemble_script(self)
    #Variables for surrogate model
    self.pscaler={}
    self.yscaler={}

  def get_machine(self,machine=''):
    if (machine == ''):
      hostname = socket.gethostname()
      if ('baseline' in hostname):
        self.machine = 'cades-baseline'
    else:
      self.machine=machine
    self.noslurm=False
    if ('linux' in self.machine or 'ubuntu' in self.machine):
        self.noslurm=True
    self.queue='batch'
    if ('baseline' in self.machine):
        self.project='CLI185'
    elif ('chrysalis' in self.machine):
        self.project='e3sm'
        self.queue='debug'

  def get_model_directories(self):
    if (not os.path.exists(self.modelroot)):
      print('Error:  Model root '+self.modelroot+' does not exist.')
      sys.exit(1)
    #if (not os.path.exists(self.inputdata_path)):
    #  print('Error:  Input data directory '+self.inputdata_path+' does not exist.')
    #  sys.exit(1)
    if (not os.path.exists(self.runroot)):
      print('Error: Run root '+self.runroot+' does not exist.')
      sys.exit(1)
    if (not os.path.exists(self.caseroot)):
      print('Error: Run root '+self.caseroot+' does not exist.')
      sys.exit(1)  
    #if (not os.path.exists(self.exeroot)):
    #  print('No exeroot specified.  Setting to: '+self.runroot+'
    print('Model root directory: '+self.modelroot)
    if (self.inputdata_path != ''):
      print('Input data directory: '+self.inputdata_path)
    print('Run root directory:   '+self.runroot)
    print('Case root directory:  '+self.caseroot)

  def get_forcing(self,metdir='',mettype=''):
    #Get the forcing type and directory
    if (metdir == ''):
        if (self.site != '' and (mettype == '' or mettype == 'site')):
          #Assume the user wants to use site data and set default path
          self.forcing='site'
          self.metdir = self.inputdata_path+'/atm/datm7/CLM1PT_data/1x1pt_'+self.site
        elif (mettype == 'gswp3-daymet4'):
          print('Setting met type to gswp3-daymet4')
          self.forcing='gswp3-daymet4'
          self.metdir='/gpfs/wolf2/cades/cli185/proj-shared/zdr/Daymet_GSWP3_4KM_TESSFA/netcdf/'
        elif (mettype != ''):
          #Met type specified but not metdir.  Get location from metinfo.txt
          self.forcing=mettype
          metinfo = open(self.OLMTdir+'/metinfo.txt','r')
          for s in metinfo:
              if s.split(':')[0] == mettype:
                  self.metdir = self.inputdata_path+'/'+s.split(':')[1].strip()
                  if (self.is_bypass()):
                      self.metdir = self.metdir+'/cpl_bypass_full'
          metinfo.close()
        else:
          #No site, mettype or metdir specified.  Default to GSWP3
          print('No site, mettype or metdir specified.  Defaulting to GSWP3')
          self.forcing='gswp3'
          self.metdir = self.inputdata_path+'/atm/datm7/atm_forcing.datm7.GSWP3.0.5d.v2.c180716'
          if (self.is_bypass()):
              self.metdir = self.metdir+'/cpl_bypass_full'
    else:
        #Met data directory provided.  Get met type.
        if (self.site != '' and mettype == ''):
            self.forcing='site'
        else:
            self.forcing=mettype
            if mettype == '':
              print('Error: When specifying metdir, Must also specify met type (e.g. gswp3)')
              sys.exit(1)
        self.metdir=metdir
    self.get_metdata_year_range()

  def is_bypass(self):
    #Determine whether this is a coupler bypass case from compset name
    if ('CBCN' in self.compset or 'ICB' in self.compset or 'CLM45CB' in self.compset):
      return True
    else:
      return False

  def get_namelist_variable(self,vname):
    #Get the default namelist variable from case directory
    #Must be done AFTER the case.setup
    nfile = open(self.casedir+'/Buildconf/elmconf/lnd_in')
    for line in nfile:
        if (vname in line):
            value = line.split('=')[1]
    return value[:-1]   #avoid new line character

  def set_param_file(self):
    #set the ELM parameter file
    if (self.parm_file == ''):
      #Get parameter filename from case directory
      self.parm_file = self.get_namelist_variable('paramfile')
    #Copy the parameter file to the temp directory 
    os.system('cp '+self.parm_file+' '+self.OLMTdir+'/temp/clm_params.nc')
    #TODO - add metadata to the copied file about original filename

  def set_CNP_param_file(self,filename=''):
    if (filename == ''):
        self.CNPparm_file = self.get_namelist_variable('fsoilordercon')
    else:
        self.CNPparm_file = filename
    os.system('cp '+self.CNPparm_file+' '+self.OLMTdir+'/temp/CNP_parameters.nc')

  def set_fates_param_file(self):
    if (self.fates_paramfile == ''):
        self.fates_paramfile = self.get_namelist_variable('fates_paramfile')
    os.system('cp '+self.fates_paramfile+' '+self.OLMTdir+'/temp/fates_paramfile.nc')

  def set_finidat_file(self, finidat_case='', finidat_year=0, finidat=''):
      if (finidat_case != ''):
        self.finidat_yst = str(10000+finidat_year)[1:]
        self.finidat = self.runroot+'/'+finidat_case+'/run/'+ \
          finidat_case+'.elm.r.'+self.finidat_yst+'-01-01-00000.nc'
        self.finidat_year = finidat_year
      elif (finidat != ''):
        self.finidat = finidat
        self.finidat_year = int(finidat[-19:-15])
        self.finidat_yst=str(10000+finidat_year)[1:]
      self.has_finidat=True

#-----------------------------------------------------------------------------------------
  def create_case(self, machine='',casename=''):
    if (casename == ''):
      #construct default casename
      if (self.site == ''):
        self.casename = self.caseid+'_'+self.region+'_'+self.compset+self.case_suffix
      else:
        self.casename = self.caseid+'_'+self.site+"_"+self.compset+self.case_suffix
    else:
        self.casename = casename
    self.casedir = os.path.abspath(self.caseroot+'/'+self.casename)
    if (os.path.exists(self.casedir)):
      print('Warning:  Case directory exists')
      var = input('proceed (p), remove old (r), or exit (x)? ')
      if var[0] == 'r':
        os.system('rm -rf '+self.casedir)
      if var[0] == 'x':
         sys.exit(1)    
    print("CASE directory is: "+self.casedir)
    #create the case
    walltime=2
    timestr=str(int(float(walltime)))+':'+str(int((float(walltime)- \
                                     int(float(walltime)))*60))+':00'
    #IF the resolution is user defined (site), we will first create a case with 
    #original resolution to get them correct domain, surface and land use files.
    cmd = './create_newcase --case '+self.casedir+' --mach '+self.machine+' --compset '+ \
           self.compset+' --res '+self.res+' --walltime '+timestr+' --handle-preexisting-dirs u'
    if (self.project != ''):
      cmd = cmd+' --project '+self.project
    if (self.compiler != ''):
      cmd = cmd+' --compiler '+self.compiler
    #ADD MPILIB OPTION HERE
    if ('FATES' in self.compset):
      cmd = cmd+' --mpilib mpi-serial'  
    cmd = cmd+' > '+self.OLMTdir+'/create_newcase.log'
    os.chdir(self.modelroot+'/cime/scripts')
    result = os.system(cmd)
    if (os.path.isdir(self.casedir)):
      print(self.casename+' created.  See create_newcase.log for details')
      os.system('mv '+self.OLMTdir+'/create_newcase.log '+self.casedir)
    else:
      print('Error:  runcase.py Failed to create case.  See create_newcase.log for details')
      sys.exit(1)
    os.chdir(self.casedir)
    if (self.inputdata_path == ''):
      self.inputdata_path=self.xmlquery('DIN_LOC_ROOT')
      print('Input directory not specified.')
      print('Setting to machine default: '+self.inputdata_path)
    self.rundir = self.runroot+'/'+self.casename+'/run'
    self.dobuild = False
    if (self.exeroot == ''):
        self.dobuild = True
        self.exeroot = self.runroot+'/'+self.casename+'/bld'

  def setup_domain_surfdata(self,makedomain=False,makesurfdat=False,makepftdyn=False, \
          surffile='',domainfile='',pftdynfile=''):
     #------Make domain, surface data and pftdyn files ------------------
    os.chdir(self.OLMTdir)
    mysimyr=1850

    if (surffile == '' and makesurfdat):
      self.makepointdata(self.surfdata_global)
    if (domainfile == '' and makedomain):
      self.makepointdata(self.domain_global)
    if (pftdynfile == '' and makepftdyn and not (self.nopftdyn)):
      self.makepointdata(self.pftdyn_global)
    if (domainfile != ''):
      print('\n -----INFO: using user-provided DOMAIN')
      print('surface data file: '+ domainfile)
    if (surffile != ''):
      print('\n -----INFO: using user-provided SURFDATA')
      print('surface data file: '+ surffile)  
    if (pftdynfile != ''):
      print('\n -----INFO: using user-provided 20th landuse data file')
      print('20th landuse data file: '+pftdynfile+"'\n")

  def get_metdata_year_range(self):
    #get site year information
    sitedatadir = os.path.abspath(self.inputdata_path+'/lnd/clm2/PTCLM')
    os.chdir(sitedatadir)
    if (self.site != ''):
      if (self.is_bypass):
        #Get met data year range from all_hourly file
        mydata = Dataset(self.metdir+'/all_hourly.nc','r')
        self.met_startyear = mydata['start_year'][0]
        self.met_endyear   = mydata['end_year'][0]
        mydata.close()
      else:
        #TODO:  use file list for datm files to determine year range
        AFdatareader = csv.reader(open(self.sitegroup+'_sitedata.txt',"r"))
        for row in AFdatareader:
          if row[0] == self.site:
            self.met_startyear = int(row[6])
            self.met_endyear   = int(row[7])
            self.met_alignyear = int(row[8])
            if len(row) == 10:
                self.timezone = int(row[9])
      self.nyears_spinup=self.met_endyear-self.met_startyear+1
    if (self.forcing != 'site'):
        #Assume reanalysis
        self.met_startyear = 1901
        if ('daymet' in self.forcing):
            self.met_startyear = 1980
            self.met_endyear = 1999
        if ('Qian' in self.forcing):
            self.met_startyear = 1948
        endyear = self.met_startyear+20-1
        if ('20TR' in self.casename or 'trans' in self.casename):
            self.met_endyear = 2014
        self.nyears_spinup=20
    #force run length to be multiple of spinup
    if (not '20TR' in self.compset and not 'trans' in self.casename):
      while (self.run_n % self.nyears_spinup != 0):
        self.run_n = self.run_n+1

  def xmlchange(self, variable, value='', append=''):
      os.chdir(self.casedir)
      if (value != ''):
        os.system('./xmlchange '+variable+'='+value)
      elif (append != ''):
        os.system('./xmlchange --append '+variable+'='+append)

  def xmlquery(self, variable):
      result = subprocess.run(['./xmlquery','--value',variable], stdout=subprocess.PIPE)
      return result.stdout.decode('utf-8')

  def setup_case(self, surffile='', domainfile='', pftdynfile=''):
    os.chdir(self.casedir)
    #env_build
    self.xmlchange('SAVE_TIMING',value='FALSE')
    self.xmlchange('EXEROOT',value=self.exeroot)
    self.xmlchange('PIO_VERSION',value=str(self.pio_version))
    self.xmlchange('MOSART_MODE',value='NULL')
    #if (self.debug):
    #  self.xmlchange('DEBUG',value='TRUE')
    #-------------- env_run.xml modifications -------------------------
    self.xmlchange('RUNDIR',value=self.rundir)
    self.xmlchange('DIN_LOC_ROOT',value=self.inputdata_path)
    self.xmlchange('DIN_LOC_ROOT_CLMFORC',value=self.inputdata_path+'/atm/datm7/')    
    #define mask and resoultion
    if (self.site != ''):
      self.xmlchange('ELM_USRDAT_NAME',value='1x1pt_'+self.site)
    if ('ad_spinup' in self.casename):
      self.xmlchange('ELM_BLDNML_OPTS',append="'-bgc_spinup on'")
    #if (self.use_hydrstress or 'PHS' in selfcompset):
    #    self.xmlchange('ELM_BLDNML_OPTS',append='-hydrstress')
    self.xmlchange('RUN_STARTDATE',value=str(self.startyear)+'-01-01')
    #turn off archiving
    self.xmlchange('DOUT_S',value='FALSE')
    #datm options
    if (not self.is_bypass()):
      if (not 'site' in self.forcing):
        self.xmlchange('DATM_MODE',value='CLMCRUNCEP') 
      else:
        self.xmlchange('DATM_MODE',value='CLM1PT') 
        self.xmlchange('DATM_CLMNCEP_YR_START',value=str(self.met_startyear))
        self.xmlchange('DATM_CLMNCEP_YR_END',value=str(self.met_endyear))
    #Change simulation timestep
    if (float(self.tstep) != 0.5):
      self.xmlchange('ATM_NCPL',value=str(int(24/float(self.tstep))))

    if (self.has_finidat):
      self.xmlchange('RUN_REFDATE',value=self.finidat_yst+'-01-01')
    #adds capability to run with transient CO2
    if ('20TR' in self.casename or 'trans' in self.casename):
      self.xmlchange('CCSM_BGC',value='CO2A')
      self.xmlchange('ELM_CO2_TYPE','diagnostic')
    
    comps = ['ATM','LND','ICE','OCN','CPL','GLC','ROF','WAV','ESP','IAC']
    for c in comps:
      self.xmlchange('NTASKS_'+c,value=str(self.np))
      self.xmlchange('NTHRDS_'+c,value='1')

    self.xmlchange('STOP_OPTION',value='nyears')
    self.xmlchange('STOP_N',value=str(self.run_n))
    self.xmlchange('REST_N',value=str(self.run_n))
    if (self.site == ''):
        self.xmlchange('REST_N',value='20')

    # user-defined PFT numbers (default is 17)
    #if (options.maxpatch_pft != 17):
    #  print('resetting maxpatch_pft to '+str(options.maxpatch_pft))
    #  xval = subprocess.check_output('./xmlquery --value CLM_BLDNML_OPTS', cwd=casedir, shell=True)
    #  xval = '-maxpft '+str(options.maxpatch_pft)+' '+xval
    #  os.system("./xmlchange CLM_BLDNML_OPTS = '" + xval + "'")

    # for spinup and transient runs, PIO_TYPENAME is pnetcdf, which now not works well
    if('mac' in self.machine or 'cades' in self.machine or 'linux' in self.machine): 
      self.xmlchange('PIO_TYPENAME',value='netcdf')

    if (self.has_finidat):
        self.customize_namelist(variable='finidat',value="'"+self.finidat+"'")
    #Setup the new case
    result = os.system('./case.setup > case_setup.log')
    if (result > 0):
        print('Error: runcase.py failed to setup case')
        sys.exit(1)
    #get the default parameter files for the case
    self.set_param_file()
    self.set_CNP_param_file()
    #get the default surface and domain files (to pass to makepointdata)
    #Note:  This requires setting a supported resolution
    self.surfdata_global = self.get_namelist_variable('fsurdat')
    self.domain_global   = self.get_namelist_variable('fatmlndfrc')
    if ('20TR' in self.casename or 'trans' in self.casename):
        self.pftdyn_global = self.get_namelist_variable('flanduse_timeseries')
    #Set custom surface data information
    if (surffile==''):
        surffile = self.rundir+'/surfdata.nc'
    if (pftdynfile==''):
       pftdynfile = self.rundir+'/surfdata.pftdyn.nc'
    self.customize_namelist(variable='do_budgets',value='.false.')
    self.customize_namelist(variable='fsurdat',value="'"+surffile+"'")
    if ('20TR' in self.casename or 'trans' in self.casename):
      if (self.nopftdyn):
          self.customize_namelist(variable='flanduse_timeseries',value='')
      else:
          self.customize_namelist(variable='flanduse_timeseries',value="'"+pftdynfile+"'")
      self.customize_namelist(variable='check_finidat_fsurdat_consistency',value='.false.')
      self.customize_namelist(variable='check_finidat_year_consistency',value='.false.')
      self.set_histvars()
    else:
      self.set_histvars(spinup=True)
    self.customize_namelist(variable='paramfile',value="'"+self.rundir+"/clm_params.nc'")
    self.customize_namelist(variable='fsoilordercon',value="'"+self.rundir+"/CNP_parameters.nc'")
    #Fates options - TODO add nutrient/parteh options
    if ('ED' in self.compset or 'FATES' in self.compset):
        self.set_fates_param_file()
        self.customize_namelist(variable='fates_paramfile',value="'"+self.fates_paramfile+"'")
        #if (self.fates_logging):
        #    self.customize_namelist(variable='use_fates_logging',value='.true.')
    self.customize_namelist(variable='nyears_ad_carbon_only',value='25')
    self.customize_namelist(variable='spinup_mortality_factor',value='10')
    if (self.is_bypass()):
        #if using coupler bypass, need to add the following
        self.customize_namelist(variable='metdata_type',value="'"+self.forcing+"'")
        self.customize_namelist(variable='metdata_bypass',value="'"+self.metdir+"'")
        self.customize_namelist(variable='co2_file', value="'"+self.inputdata_path+"/atm/datm7/CO2/fco2_datm_rcp4.5_1765-2500_c130312.nc'")
        self.customize_namelist(variable='aero_file', value="'"+self.inputdata_path+"/atm/cam/chem/" \
                +"trop_mozart_aero/aero/aerosoldep_rcp4.5_monthly_1849-2104_1.9x2.5_c100402.nc'")
    #add user namelist options
    if (self.namelist_options):
        for n in self.namelist_options:
            self.customize_namelist(variable=n.split('=')[0], value=n.split('=')[1])
    #set domain file information
    if (domainfile == ''):
      self.xmlchange('ATM_DOMAIN_PATH',value='"\${RUNDIR}"')
      self.xmlchange('LND_DOMAIN_PATH',value='"\${RUNDIR}"')
      self.xmlchange('ATM_DOMAIN_FILE',value='domain.nc')
      self.xmlchange('LND_DOMAIN_FILE',value='domain.nc')
    else:
      domainpath = '/'.join(domainfile.split('/')[:-1])
      domainfilename = domainfile.split('/')[-1]
      self.xmlchange('ATM_DOMAIN_PATH',value=domainpath)
      self.xmlchange('LND_DOMAIN_PATH',value=domainpath)
      self.xmlchange('ATM_DOMAIN_FILE',value=domainfilename)
      self.xmlchange('LND_DOMAIN_FILE',value=domainfilename)

    #global CPPDEF modifications
    if (self.is_bypass()):
      macrofiles=['./Macros.make','./Macros.cmake']
      for f in macrofiles:
          if (os.path.isfile(f)):
            infile  = open(f)
            outfile = open(f+'.tmp','a')  
            for s in infile:
              if ('CPPDEFS' in s and self.is_bypass()):
                 stemp = s[:-1]+' -DCPL_BYPASS\n'
                 outfile.write(stemp)
              elif ('llapack' in s):
                 outfile.write(s.replace('llapack','llapack -lgfortran'))
              else:
                 outfile.write(s.replace('mcmodel=medium','mcmodel=small'))
            infile.close()
            outfile.close()
            os.system('mv '+f+'.tmp '+f)
      if (os.path.isfile("./cmake_macros/universal.cmake")):
        os.system("echo 'string(APPEND CPPDEFS \" -DCPL_BYPASS\")' >> cmake_macros/universal.cmake")
    if (self.cppdefs != ''):
      #use for HUM_HOL, MARSH, HARVMOD, other cppdefs
      for cppdef in self.cppdefs.split(','):
         print("Turning on "+cppdef+" modification\n")
         self.xmlchange('ELM_CONFIG_OPTS',append='" -cppdefs -D'+cppdef+'"')
    if (self.srcmods != ''):
      if (os.path.exists(self.srcmods) == False):
        print('Invalid srcmods directory.  Exiting')
        sys.exit(1)
      os.system('cp -r '+self.srcmods+'/* '+self.casedir+'/SourceMods')

  def customize_namelist(self, namelist_file='', variable='', value=''):
    output = open("user_nl_elm",'a')
    if (namelist_file != ''):
        mynamelist = open(namelist_file,'r')
        for s in mynamelist:
            output.write(s)
    else:
        output.write(' '+variable+' = '+value+'\n')
    output.close()

  def build_case(self, clean=True):
      os.chdir(self.casedir)
      #If using DATM, set the resolution to ELM_USRDAT
      if (not self.is_bypass()):
        #assume single point
        self.xmlchange('LND_GRID',value='ELM_USRDAT')
        self.xmlchange('ATM_GRID',value='ELM_USRDAT')
        self.xmlchange('LND_NX',value='1')
        self.xmlchange('LND_NY',value='1')
        self.xmlchange('ATM_NX',value='1')
        self.xmlchange('ATM_NY',value='1')
        result = os.system('./case.setup')
      if (self.dobuild):
        if (clean):
          os.system('./case.build --clean-all')
        result = os.system('./case.build')
        if (result > 0):
          print('Error:  Failed to build case.  Aborting')
          print('See '+os.getcwd()+'/case_build.log for details')
          sys.exit(1)
      else:
        self.xmlchange('BUILD_COMPLETE',value='TRUE')
      #If using DATM, customize the stream files
      if (not self.is_bypass()):
          self.modify_datm_streamfiles()
      #Copy customized parameter, surface and domain files to run directory
      os.system('mkdir -p temp')
      os.system('cp '+self.OLMTdir+'/temp/*param*.nc '+self.rundir)
      if (self.domainfile == ''):
         os.system('cp '+self.OLMTdir+'/temp/domain.nc '+self.rundir)
      if (self.surffile == ''):
         cmd = 'cp '+self.OLMTdir+'/temp/surfdata.nc '+self.rundir
         execute = subprocess.call(cmd, shell=True)
      if ('20TR' in self.compset and self.pftdynfile =='' and not(self.nopftdyn)):
         os.system('cp '+self.OLMTdir+'/temp/surfdata.pftdyn.nc '+self.rundir)

  def modify_datm_streamfiles(self):
    #stream file modifications for datm runs
    #Datm mods/ transient CO2 patch for transient run (datm buildnml mods)
    if (not self.is_bypass()):
      os.chdir(self.casedir)
      myinput  = open('./Buildconf/datmconf/datm_in')
      myoutput = open('user_nl_datm','w')
      for s in myinput:
          if ('streams =' in s):
              if ('trans' in self.casename or '20TR' in self.compset):
                  mypresaero = '"datm.streams.txt.presaero.trans_1850-2000 1850 1850 2000"'
                  myco2      = ', "datm.streams.txt.co2tseries.20tr 1766 1766 2010"'
              elif ('1850' in self.compset):
                  mypresaero = '"datm.streams.txt.presaero.clim_1850 1 1850 1850"'
                  myco2=''
              else:
                  mypresaero = '"datm.streams.txt.presaero.clim_2000 1 2000 2000"'
                  myco2=''
              if (self.site == ''):
                  myoutput.write(' streams = "datm.streams.txt.CLMCRUNCEP.Solar '+str(self.met_alignyear)+ \
                                     ' '+str(self.met_startyear)+' '+str(self.met_endyear)+'  ", '+ \
                                     '"datm.streams.txt.CLMCRUNCEP.Precip '+str(self.met_alignyear)+ \
                                     ' '+str(self.met_startyear)+' '+str(self.met_endyear)+'  ", '+ \
                                     '"datm.streams.txt.CLMCRUNCEP.TPQW '+str(self.met_alignyear)+ \
                                     ' '+str(self.met_startyear)+' '+str(self.met_endyear)+'  ", '+mypresaero+myco2+ \
                                     ', "datm.streams.txt.topo.observed 1 1 1"\n')
              else:
                  myoutput.write(' streams = "datm.streams.txt.CLM1PT.ELM_USRDAT '+str(self.met_alignyear)+ \
                                     ' '+str(self.met_startyear)+' '+str(self.met_endyear)+'  ", '+mypresaero+myco2+ \
                                     ', "datm.streams.txt.topo.observed 1 1 1"\n')
          elif ('streams' in s):
              continue  #do nothing
          elif ('taxmode' in s):
              #if (options.cruncep or options.cruncepv8):
              #    taxst = "taxmode = 'cycle', 'cycle', 'cycle', 'extend', 'extend'"
              #else:
              taxst = "taxmode = 'cycle', 'extend', 'extend'"
              if ('trans' in self.casename or '20TR' in self.compset):
                  taxst = taxst+", 'extend'"
              myoutput.write(taxst+'\n')
          else:
              myoutput.write(s)
      myinput.close()
      myoutput.close()
      #Modify aerosol deposition file
      if (not self.is_bypass() and self.site != ''):
        if ('1850' in self.compset):
          myinput  = open('./Buildconf/datmconf/datm.streams.txt.presaero.clim_1850')
          myoutput = open('./user_datm.streams.txt.presaero.clim_1850','w')
          for s in myinput:
              if ('aerosoldep_monthly' in s):
                  myoutput.write('            aerosoldep_monthly_1849-2006_1.9x2.5_c090803.nc\n')
              else:
                  myoutput.write(s)
          myinput.close()
          myoutput.close()
      #Modify CO2 file
      if ('20TR' in self.compset):
          myinput  = open('./Buildconf/datmconf/datm.streams.txt.co2tseries.20tr')
          myoutput = open('./user_datm.streams.txt.co2tseries.20tr','w')
          for s in myinput:
              if ('.nc' in s):
                  myoutput.write('      '+self.inputdata_path+"/atm/datm7/CO2/fco2_datm_rcp4.5_1765-2500_c130312.nc\n")
              else:
                  myoutput.write(s)
          myinput.close()
          myoutput.close()
      #reverse directories for CLM1PT and site
      if (self.forcing == 'site'):
          myinput  = open('./Buildconf/datmconf/datm.streams.txt.CLM1PT.ELM_USRDAT')
          myoutput = open('./user_datm.streams.txt.CLM1PT.ELM_USRDAT','w')
          for s in myinput:
              if ('CLM1PT_data' in s):
                  temp = s.replace('CLM1PT_data', 'TEMPSTRING')
                  s    = temp.replace('1x1pt'+'_'+self.site, 'CLM1PT_data')
                  temp  =s.replace('TEMPSTRING', '1x1pt'+'_'+self.site)
                  myoutput.write(temp)
              elif (('ED' in self.compset or 'FATES' in self.compset) and 'FLDS' in s):
#              if (('ED' in compset or 'FATES' in compset) and 'FLDS' in s):
                  print('Not including FLDS in atm stream file')
              else:
                  myoutput.write(s)
          myinput.close()
          myoutput.close()

      # run preview_namelists to copy user_datm.streams.... to CaseDocs
      if os.path.exists(os.path.abspath(self.modelroot)+'/cime/scripts/Tools/preview_namelists'):
        os.system(os.path.abspath(self.modelroot)+'/cime/scripts/Tools/preview_namelists')
      else:
        os.system(os.path.abspath(self.modelroot)+'/cime/CIME/Tools/preview_namelists')

  def submit_case(self,depend=-1,ensemble=False):
    #Create a pickle file of the model object for later use
    #Keep a copy in the case directory and OLMT directory
    self.create_pkl(outdir=self.casedir)
    self.create_pkl(outdir=self.OLMTdir+'/pklfiles')

    mysubmit='sbatch'
    #Submit the case with dependency if requested
    #Return the job id
    if (ensemble):
        #Create the PBS script
        create_ensemble_script(self)
        scriptfile = './case.submit_ensemble'
    else:
        scriptfile = './case.submit'
    os.chdir(self.casedir)
    if (depend > 0 and not self.noslurm):
      if (ensemble):
          cmd = [mysubmit,'--dependency=afterok:'+str(depend),scriptfile]
      else:
          cmd = [scriptfile,'--prereq',str(depend)]
    else:
      if (ensemble and not self.noslurm):
          cmd = [mysubmit,scriptfile]
      else:
          cmd = [scriptfile]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output = result.stdout.strip()
    if (not self.noslurm):
      jobnum = int(output.split()[-1])
      print('submitted '+str(jobnum))
    else:
      jobnum=0
    os.chdir(self.OLMTdir)
    return jobnum

  def create_pkl(self, outdir='./pklfiles'):
    os.chdir(self.OLMTdir)
    os.system('mkdir -p pklfiles')
    with open(outdir+'/'+self.casename+'.pkl','wb') as file_out:
        pickle.dump(self, file_out)


# Dynamically import and add methods to ELMcase
def _add_methods_from_module(module):
    for name in dir(module):
        if not name.startswith("_"):
            try:
              method = getattr(module, name)
              if callable(method):
                setattr(ELMcase, name, method)
            except Exception as e:
                print(f"Error adding method {name}: {e}")

# Import modules and add their functions as methods to CLMcase
from . import ensemble, makepointdata, netcdf4_functions, set_histvars, postprocess, get_fluxnet_obs, \
        surrogate_NN, run_GSA, MCMC

_add_methods_from_module(ensemble)
_add_methods_from_module(makepointdata)
_add_methods_from_module(netcdf4_functions)
_add_methods_from_module(set_histvars)
_add_methods_from_module(postprocess)
_add_methods_from_module(get_fluxnet_obs)
_add_methods_from_module(surrogate_NN)
_add_methods_from_module(run_GSA)
_add_methods_from_module(MCMC)
