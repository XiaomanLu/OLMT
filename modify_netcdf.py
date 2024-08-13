from optparse import OptionParser
from netCDF4 import Dataset

parser = OptionParser()

parser.add_option("--filename", dest="fname", default="", \
                  help="Variable to modify")
parser.add_option("--var", dest="var", default="", \
                  help="Variable to modify")
parser.add_option("--val", dest="val", default=0, \
                  help="Value to use")
parser.add_option("--index", dest="index", default=-1, \
                  help="Index to modify")
parser.add_option("--operator", dest="operator", default='', \
                  help="Operator")
(options, args) = parser.parse_args()

print (options.fname)
myfile = Dataset(options.fname,'a')
if (options.index >= 0):
    if (options.operator == '*'):
        myfile[options.var][index] = float(options.val)*myfile[options.var][index] 
    elif (options.operator == '+'):
        myfile[options.var][index] = float(options.val)+myfile[options.var][index]
    else:
        myfile[options.var][index] = float(options.val)
else:
    if (options.operator == '*'):
        myfile[options.var][:] = float(options.val)*myfile[options.var][:]
    elif (options.operator == '+'):
        myfile[options.var][:] = float(options.val)+myfile[options.var][:]    
    else:
        myfile[options.var][:] = float(options.val)
myfile.close()
