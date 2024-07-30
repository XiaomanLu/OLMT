#Python utilities for reading and writing variables to a netcdf file
#  using Scientific Python OR scipy, whichever available
import numpy as np

def getncvar(self, fname, varname):
    from netCDF4 import Dataset
    nffile = Dataset(fname,"r")
    if varname in nffile.variables:
      varvals = nffile.variables[varname][:]
    else:
      print('Warning: '+varname+' not in '+fname)
      #raise ValueError('"%s" not in %s'%(varname,fname))
      varvals=[-1]
    nffile.close()
    return varvals

def putncvar(self, fname, varname, varvals, addvar=False):
    from netCDF4 import Dataset
    import numpy as np
    nffile = Dataset(fname,"a")
    if (varname in nffile.variables):
      nffile.variables[varname][...] = varvals
      ierr = 0
    else:
      if (addvar):
        #Currently only works for scalars
        newvar = nffile.createVariable(varname, np.float64, ('allpfts',))
        newvar[:] = varvals
        ierr = 0
      else:
        raise ValueError('"%s" not in %s'%(varname,fname))
        ierr = 1
    nffile.close()
    return ierr
