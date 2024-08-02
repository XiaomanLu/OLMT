import socket, os, sys
import subprocess

#Function to return default directories for supported machines
def get_machine_info(machine_name=''):
    if (machine_name == ''):
        if ('HOSTNAME' in os.environ):
            machine_name=os.environ['HOSTNAME']
        else:
            result = subprocess.run(['hostname'], capture_output=True, text=True)
            machine_name = result.stdout
    if ('baseline' in machine_name):
        rootdir = '/gpfs/wolf2/cades/cli185/scratch/'+os.environ['USER']
        inputdata = '/gpfs/wolf2/cades/cli185/proj-shared/zdr/inputdata'
        machine = 'cades-baseline'
    elif  ('chrlogin' in machine_name or 'chrysalis' in machine_name):
        rootdir = '/lcrc/group/e3sm/'+os.environ['USER']+'/scratch'
    elif ('pm-cpu' in machine_name or 'login' in machine_name):
        rootdir = os.environ['SCRATCH']
        inputdata = '/global/cfs/cdirs/e3sm/inputdata'
        machine = 'pm-cpu'
    elif ('ubuntu' in machine_name or 'linux-generic' in machine_name):
        rootdir = os.environ['HOME']+'/models'
        inputdata = rootdir + '/inputdata'
        machine = 'linux-generic'
    else:
        print('Error:  Machine not detected.  Please specify machine name')
        sys.exit(1)
    return machine, rootdir, inputdata

def get_site_info(inputdata, sitegroup='AmeriFlux'):
    sitegroup_file = open(inputdata+'/lnd/clm2/PTCLM/'+sitegroup+'_sitedata.txt')
    siteinfo={}
    siteinfo['names'] = []
    snum=0
    for s in sitegroup_file:
        if snum > 0:
          siteinfo['names'].append(s.split(',')[0])
        snum=snum+1
    return siteinfo

#TODO:  Function to return met data path for various options
