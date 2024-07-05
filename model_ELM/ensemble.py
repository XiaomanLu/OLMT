#!/usr/bin/env python

import os, sys, csv, time, math
import numpy as np
import netcdf4_functions as nffun

#Read the parameter list file
def read_parm_list(self, parm_list=''):
    os.chdir(self.OLMTdir)
    if (os.path.exists(parm_list)):
        myfile = open(parm_list,'r')
        self.ensemble_parms=[]
        self.ensemble_pfts=[]
        self.ensemble_pmin=[]
        self.ensemble_pmax=[]
        for s in myfile:
            if (not '#' in s[0:3]):
              vals = s.split()
              self.ensemble_parms.append(vals[0].strip())
              self.ensemble_pfts.append(int(vals[1].strip()))
              self.ensemble_pmin.append(float(vals[2].strip()))
              self.ensemble_pmax.append(float(vals[3].strip()))
        myfile.close()
    else:
        print('parm_list file '+parm_list+' does not exist.  Exiting')
        sys.exit(1)
    self.nparms_ensemble = len(self.ensemble_parms)

#Create the samples file
def create_samples(self,sampletype='monte_carlo',nsamples=100,parm_list=''):
    self.nsamples=nsamples
    self.samples=np.zeros((self.nparms_ensemble,self.nsamples), float)
    for i in range(0,self.nsamples):
        for j in range(0,self.nparms_ensemble):
            self.samples[j,i] = self.ensemble_pmin[j]+(self.ensemble_pmax[j]- \
                    self.ensemble_pmin[j])*np.random.rand(1)
    self.ensemble_file = 'mcsamples_'+self.caseid+'_'+str(self.nsamples)+'.txt'
    np.savetxt(self.ensemble_file,np.transpose(self.samples))

def create_ensemble_script(self, walltime=6):
    #Create the PBS script we will submit to run the ensemble
    os.chdir(self.casedir)
    self.project='CLI185'
    #Get the LD_LIBRARY_PATH from software environment
    softenv = open('software_environment.txt','r')
    for s in softenv:
        if s.split('=')[0].strip() == 'LD_LIBRARY_PATH':
            ldpath = s.split('=')[1].strip()
    softenv.close()
    npernode=int(self.xmlquery('MAX_TASKS_PER_NODE'))
    nnodes = int(np.ceil(self.np_ensemble/npernode))
    myfile = open('case.submit_ensemble','w')
    myfile.write('#!/bin/bash -e\n\n')
    myfile.write('#SBATCH -t '+str(walltime)+':00:00\n')
    myfile.write('#SBATCH -J ens_'+self.casename+'\n')
    myfile.write('#SBATCH --nodes='+str(nnodes)+'\n')  #FIX
    if (self.project != ''):
        myfile.write('#SBATCH -A '+self.project+'\n')
    myfile.write('#SBATCH -p batch\n')
    myfile.write('cd '+self.caseroot+'/'+self.casename+'\n')
    myfile.write('export LD_LIBRARY_PATH='+ldpath+'\n\n')
    myfile.write('./preview_namelists\n\n')
    myfile.write('cd '+self.OLMTdir+'\n')
    myfile.write('./manage_ensemble.py --case '+self.casename+'\n')
    myfile.close()  
    os.system('chmod u+x case.submit_ensemble')
    self.rundir_UQ = self.runroot+'/UQ/'+self.casename

def ensemble_copy(self, ens_num):

  gst=str(100000+int(ens_num))

  # create ensemble directory from original case 
  orig_dir = str(os.path.abspath(self.runroot)+'/'+self.casename+'/run')
  ens_dir  = os.path.abspath(self.runroot)+'/UQ/'+self.casename+'/g'+gst[1:]
		
  os.system('mkdir -p '+self.runroot+'/UQ/'+self.casename+'/g'+gst[1:]+'/timing/checkpoints')
  os.system('cp  '+orig_dir+'/*_in* '+ens_dir)
  os.system('cp  '+orig_dir+'/*nml '+ens_dir)
  if (not ('CB' in self.casename)):
    os.system('cp  '+orig_dir+'/*stream* '+ens_dir)
  os.system('cp  '+orig_dir+'/*.rc '+ens_dir)
  os.system('cp  '+orig_dir+'/surf*.nc '+ens_dir)
  os.system('cp  '+orig_dir+'/domain*.nc '+ens_dir)
  os.system('cp  '+orig_dir+'/*para*.nc '+ens_dir)


  # loop through all filenames, change directories in namelists, change parameter values
  for f in os.listdir(ens_dir):
    if (os.path.isfile(ens_dir+'/'+f) and (f[-2:] == 'in' or f[-3:] == 'nml' or 'streams' in f)):
        myinput=open(ens_dir+'/'+f)
        myoutput=open(ens_dir+'/'+f+'.tmp','w')
        for s in myinput:
            if ('fates_paramfile' in s):
                paramfile_orig = ((s.split()[2]).strip("'"))
                if (paramfile_orig[0:2] == './'):
                  paramfile_orig = orig_dir+'/'+paramfile_orig[2:]
                paramfile_new  = ens_dir+'/fates_params_'+gst[1:]+'.nc'
                os.system('cp '+paramfile_orig+' '+paramfile_new)
                os.system('nccopy -3 '+paramfile_new+' '+paramfile_new+'_tmp')
                os.system('mv '+paramfile_new+'_tmp '+paramfile_new)
                myoutput.write(" fates_paramfile = '"+paramfile_new+"'\n")
                fates_paramfile = ens_dir+'/fates_params_'+gst[1:]+'.nc'
            elif ('paramfile' in s):
                paramfile_orig = ((s.split()[2]).strip("'"))
                if (paramfile_orig[0:2] == './'):
                   paramfile_orig = orig_dir+'/'+paramfile_orig[2:]
                paramfile_new  = ens_dir+'/clm_params_'+gst[1:]+'.nc'
                os.system('cp '+paramfile_orig+' '+paramfile_new)
                os.system('nccopy -3 '+paramfile_new+' '+paramfile_new+'_tmp')
                os.system('mv '+paramfile_new+'_tmp '+paramfile_new)
                myoutput.write(" paramfile = '"+paramfile_new+"'\n")
                pftfile = ens_dir+'/clm_params_'+gst[1:]+'.nc'
            elif ('ppmv' in s and 'co2' in self.ensemble_parms):
                myoutput.write(" co2_ppmv = "+str(parm_values[pnum_co2])+'\n')
            elif ('fsoilordercon' in s):
                CNPfile_orig = ((s.split()[2]).strip("'"))
                if (CNPfile_orig[0:2] == './'):
                   CNPfile_orig  = orig_dir+'/'+CNPfile_orig[2:]
                CNPfile_new  = ens_dir+'/CNP_parameters_'+gst[1:]+'.nc'
                os.system('cp '+CNPfile_orig+' '+CNPfile_new)
                os.system('nccopy -3 '+CNPfile_new+' '+CNPfile_new+'_tmp')
                os.system('mv '+CNPfile_new+'_tmp '+CNPfile_new)
                myoutput.write(" fsoilordercon = '"+CNPfile_new+"'\n")
                CNPfile = ens_dir+'/CNP_parameters_'+gst[1:]+'.nc'
            elif ('fsurdat =' in s):
                surffile_orig = ((s.split()[2]).strip("'"))
                if (surffile_orig[0:2] == './'):
                  surffile_orig = orig_dir+'/'+surffile_orig[2:]
                surffile_new = ens_dir+'/surfdata_'+gst[1:]+'.nc'
                os.system('cp '+surffile_orig+' '+surffile_new)
                os.system('nccopy -3 '+surffile_new+' '+surffile_new+'_tmp')
                os.system('mv '+surffile_new+'_tmp '+surffile_new)
                myoutput.write(" fsurdat = '"+surffile_new+"'\n")
                surffile = ens_dir+'/surfdata_'+gst[1:]+'.nc'
            elif ('finidat = ' in s):
                finidat_file_orig = ((s.split()[2]).strip("'"))
                if (finidat_file_orig.strip() != ''):
                   finidat_file_new  = ens_dir+'/'+(finidat_file_orig.split('/')[-1:])[0]
                   if (finidat_file_orig[0:2] == './'):
                      finidat_file_orig = orig_dir+'/'+finidat_file_orig[2:]
                   #get finidat files from previous ensemble cases if available
                   if (('1850' in self.casename or 'CROP' in self.casename) and not ('ad_spinup' in self.casename) and not \
                          ('trans' in self.casename or '20TR' in self.casename)): 
                      finidat_file_path = os.path.abspath(self.runroot)+'/UQ/'+self.casename.replace('CNP','CN')+'_ad_spinup/g'+gst[1:]
                      if (os.path.exists(finidat_file_path)):
                            finidat_file_orig = finidat_file_path+'/*.'+self.model_name+'.r.*.nc'
                            os.system('python adjust_restart.py --rundir '+finidat_file_path+' --casename '+ \
                                self.casename.replace('CNP','CN')+'_ad_spinup')
                   if ('20TR' in self.casename):
                      if ( not ('CO2' in self.casename)):
                          finidat_file_path = os.path.abspath(self.runroot)+'/UQ/'+self.casename.replace('20TR','1850')+ \
                                          '/g'+gst[1:]
                          if (os.path.exists(finidat_file_path)):
                              finidat_file_orig = finidat_file_path+'/*.'+self.model_name+'.r.*.nc'
                              os.system('rm '+finidat_file_path+'/*ad_spinup*.'+self.model_name+'.r.*.nc')
                      else: 
                          finidat_file_path = os.path.abspath(self.runroot)+'/UQ/'+self.casename[:-5]+ \
                                          '/g'+gst[1:]
                          if (os.path.exists(finidat_file_path)):
                              finidat_file_orig = finidat_file_path+'/*.'+self.model_name+'.r.*.nc'
                              os.system('rm '+finidat_file_path+'/*1850*.'+self.model_name+'.r.*.nc')
                   if ('trans' in self.casename):
                      finidat_file_path = os.path.abspath(self.runroot)+'/UQ/'+self.casename.replace('_trans','')+ \
                                       '/g'+gst[1:]
                      if (os.path.exists(finidat_file_path)):
                          finidat_file_orig = finidat_file_path+'/*.'+self.model_name+'.r.*.nc'
                          os.system('rm '+finidat_file_path+'/*ad_spinup*.'+self.model_name+'.r.*.nc')
                   os.system('cp '+finidat_file_orig+' '+finidat_file_new)
                   myoutput.write(" finidat = '"+finidat_file_new+"'\n")
                else:
                   myoutput.write(s)
            elif ('logfile =' in s):
                os.system('date +%y%m%d-%H%M%S > mytime'+str(ens_num))
                mytinput=open('./mytime'+str(ens_num),'r')
                for st in mytinput:
                    timestr = st.strip()
                mytinput.close()
                os.system('rm mytime'+str(ens_num))
                myoutput.write(s.replace('`date +%y%m%d-%H%M%S`',timestr))
            else:
                myoutput.write(s.replace(orig_dir,ens_dir))
        myoutput.close()
        myinput.close()
        os.system(' mv '+ens_dir+'/'+f+'.tmp '+ens_dir+'/'+f)

  pnum = 0
  CNP_parms = ['ks_sorption', 'r_desorp', 'r_weather', 'r_adsorp', 'k_s1_biochem', 'smax', 'k_s3_biochem', \
             'r_occlude', 'k_s4_biochem', 'k_s2_biochem']

  fates_seed_zeroed=[False,False]
  pnum=0
  parm_values = self.samples[:,ens_num-1]
  parm_indices = self.ensemble_pfts
  for p in self.ensemble_parms:
    if ('INI' in p):
      if ('BGC' in self.casename):
         scalevars = ['soil3c_vr','soil3n_vr','soil3p_vr']
      else:
         scalevars = ['soil4c_vr','soil4n_vr','soil4p_vr']
      sumvars = ['totsomc','totsomp','totcolc','totcoln','totcolp']
      for v in scalevars:
         myvar = nffun.getvar(finidat_file_new, v)
         myvar = parm_values[pnum] * myvar
         ierr = nffun.putvar(finidat_file_new, v, myvar)
    elif (p == 'lai'):
      myfile = surffile
      param = nffun.getvar(myfile, 'MONTHLY_LAI')
      param[:,:,:,:] = parm_values[pnum]
      ierr = nffun.putvar(myfile, 'MONTHLY_LAI', param)
    elif (p != 'co2'):
      if (p in CNP_parms):
         myfile= CNPfile
      elif ('fates' in p):
         myfile = fates_paramfile
      else:
         myfile = pftfile
      param = nffun.getvar(myfile,p)
      if (('fates_prt' in p and 'stoich' in p) or ('fates_turnover' in p and 'retrans' in p)):
        #this is a 2D parameter.
         param[parm_indices[pnum] % 12 , parm_indices[pnum] / 12] = parm_values[pnum]
         param[parm_indices[pnum] % 12 , parm_indices[pnum] / 12] = parm_values[pnum]
      elif ('fates_hydr_p50_node' in p or 'fates_hydr_avuln_node' in p or 'fates_hydr_kmax_node' in p or \
            'fates_hydr_pitlp_node' in p or 'fates_hydr_thetas_node' in p):
         param[parm_indices[pnum] / 12 , parm_indices[pnum] % 12] = parm_values[pnum]
         param[parm_indices[pnum] / 12 , parm_indices[pnum] % 12] = parm_values[pnum]
      elif ('fates_leaf_long' in p or 'fates_leaf_vcmax25top' in p):
         param[0,parm_indices[pnum]] = parm_values[pnum]
      #elif (p == 'fates_seed_alloc'):
      #    if (not fates_seed_zeroed[0]):
      #       param[:]=0.
      #       fates_seed_zeroed[0]=True
      #    param[parm_indices[pnum]] = parm_values[pnum]
      #elif (p == 'fates_seed_alloc_mature'):
      #    if (not fates_seed_zeroed[1]):
      #       param[:]=0.
      #       fates_seed_zeroed[1]=True
      #    param[parm_indices[pnum]] = parm_values[pnum]             
      elif (p == 'dayl_scaling' or p == 'vcmaxse'):
        os.system('ncap2 -O -s "'+p+' = flnr" '+myfile+' '+myfile)
        print('Creting netcdf variable for '+p)
        param = nffun.getvar(myfile,'flnr')
        param[:] = parm_values[pnum]
      elif (p == 'psi50'):
        param[:,parm_indices[pnum]] = parm_values[pnum]
      elif (parm_indices[pnum] > 0):
         param[parm_indices[pnum]] = parm_values[pnum]
      elif (parm_indices[pnum] == 0):
         try:
           param[:] = parm_values[pnum]
         except:
           param = parm_values[pnum]
      ierr = nffun.putvar(myfile, p, param)
      #if ('fr_flig' in p):
      #   param=nffun.getvar(myfile, 'fr_fcel')
      #   param[parm_indices[pnum]]=1.0-parm_values[pnum]-parm_values[pnum-1]
      #   ierr = nffun.putvar(myfile, 'fr_fcel', param)
    pnum = pnum+1

  #ensure FATES seed allocation paramters sum to one
  #if (fates_seed_zeroed[0]):
  #  param = nffun.getvar(myfile,'fates_seed_alloc')
  #  param2 = nffun.getvar(myfile,'fates_seed_alloc_mature')
  #  for i in range(0,12):
  #    if (param[i] + param2[i] > 1.0):
  #      sumparam= param[i]+param2[i]
  #      param[i]  = param[i]/sumparam
  #      param2[i] = param2[i]/sumparam
  #  ierr = nffun.putvar(myfile, 'fates_seed_alloc', param)      
  #  ierr = nffun.putvar(myfile, 'fates_seed_alloc_mature', param2)



### END ###
