import socket, os, sys

#Function to return default directories for supported machines
def get_machine_info(machine_name=''):
    if (machine_name == ''):
        machine_name=os.environ['HOSTNAME']
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
    else:
        print('Error:  Machine not detected.  Please specify machine name')
        sys.exit(1)
    return machine, rootdir, inputdata
