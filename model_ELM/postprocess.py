from netCDF4 import Dataset
import os,glob
import numpy as np
import matplotlib.pyplot as plt

def do_dailytomonthly(values):
    dayspermonth=[31,28,31,30,31,30,31,31,30,31,30,31]
    npoints = len(values)
    nmonths = int(npoints/365*12)
    values_out = np.zeros([nmonths],float)
    index=0
    for m in range(0,nmonths):
        mind = m % 12
        values_out[m] = np.mean(values[index:index+dayspermonth[mind]])
        index = index+dayspermonth[mind]
    return values_out

def do_monthlytoannual(values):
    dayspermonth=[31,28,31,30,31,30,31,31,30,31,30,31]
    npoints = len(values)
    nyears = int(npoints/12)
    values_out = np.zeros([nyears],float)
    for y in range(0,nyears):
        values_out[y] = np.sum(values[y*12:(y+1)*12]*dayspermonth)/365
    return values_out

def do_timeaverage(values, nav):
   npoints = len(values)
   values_out = np.zeros([int(npoints/nav)],float)
   for t in range(0,int(npoints/nav)):
       values_out[t] = np.mean(values[t*nav:(t+1)*nav])
   return values_out


def postprocess(self, var, index=0, gindex=0, startyear=-1, endyear=9999, hnum=0, \
        dailytomonthly=False, annualmean=False,  meanseasonalcycle=False, \
        xindex=0,yindex=0, ens_num=0, plot=False):
    if (ens_num > 0):
        gst = str(100000+ens_num)[1:]
        rundir = self.rundir_UQ+'/g'+gst
    else:
        rundir = self.rundir
    os.chdir(rundir)
    lnd_in = open('./lnd_in')
    #Get history file info from lnd_in
    for s in lnd_in:
        if (s.split('=')[0].strip() == 'hist_mfilt'):
            hist_mfilt = int((s.split('=')[1].strip()).split(',')[hnum].strip())
        if (s.split('=')[0].strip() == 'hist_nhtfrq'):
            hist_nhtfrq = int((s.split('=')[1].strip()).split(',')[hnum].strip())
    lnd_in.close()
    if (hist_nhtfrq == 0):
      nperyear=12
    else:
      nperyear = abs(8760/hist_nhtfrq)
    file_list_all = np.sort(glob.glob(self.casename+'.elm.h'+str(hnum)+'.*.nc'))
    file_list = []
    #Filter the requested years
    for f in file_list_all:
        if (hist_nhtfrq == 0):
            yr = int(f.split('-')[-2][-4:])
        else:
            yr = int(f.split('-')[-4][-4:])
        if (startyear < 0):
            startyear = yr
        if (endyear >= 9999):
            lastyr = yr
        if (yr >= startyear and yr <= endyear):
            file_list.append(f)
    if (endyear >= 9999):
        endyear=lastyr
        if (nperyear != 12):
          #If not monthly files, ignore the last file (it only represents a single timestep)
          file_list = file_list[:-1]
    os.system('ncrcat -O -v '+var+' '+' '.join(file_list)+' '+var+'.nc')
    myoutput = Dataset(var+'.nc','r')
    if (myoutput[var][:].ndim == 4):
      #2D output with vertical structure
      values = myoutput[var][:,index,yindex,xindex]
    elif (myoutput[var][:].ndim == 3):
      #2D output or 1D output with vertical structure (currently assumes 1D)
      values = myoutput[var][:,index,gindex]
    else:
      #1D output (unstructured grid)
      values = myoutput[var][:,gindex]
    if (dailytomonthly and hist_nhtfrq == -24):
      values_out = do_dailytomonthly(values)
      nperyear_out = 12
    elif (annualmean):
      if (hist_nhtfrq == 0):
          values_out = do_monthlytoannual(values)
      else:
          if (nperyear >= 1):
            values_out = do_timeaverage(values, int(nperyear))
      nperyear_out = 1
    else:
        values_out = values[:]
        nperyear_out = nperyear
    self.output[var]=values_out
    self.output['taxis'] = np.zeros([len(values_out)],float)
    for t in range(0,len(values_out)):
        self.output['taxis'][t] = startyear+t/nperyear_out
    if (ens_num > 0):
      #write the processed data to text for faster postprocessing of the ensemble.
      os.system('mkdir -p postprocessed')
      np.savetxt('./postprocessed/'+var+'_'+str(startyear)+'-'+str(endyear)+'.txt',self.output[var][:])
    if (plot):
        plt.plot(self.output['taxis'],self.output[var],'k')
        plt.legend([var])
        plt.show()
