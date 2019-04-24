#!/usr/bin/env python
'''
GlobusArchiver.py helps users archive data to the Campaign Store (and other Globus Endpoints)
'''
import subprocess
import shlex

from ConfigMaster import ConfigMaster



def run_cmd(cmd):
    splitcmd = shlex.split(cmd)

    # return CompleteProcess object
    return subprocess.run(splitcmd, check=True, capture_output=True)
    

def handle_configuration(cfg):
    if cfg.opt["archiveEndPoint"] = "":
        comp_proc = run_cmd(cfg.opt["archiveEndPointShellCmd"])
        EP = comp_proc["stdout"]
        if p.opt["debug"]:
            print(f"Got EndPoint via archiveEndPointShellCmd: {EP}")
        cfg.opt["archiveEndPoint"] = EP
                            

def main():
    p = ConfigMaster()
    p.setDefaultParams(defaultParams)
    p.init(__doc__)

    if p.opt["debug"]:
        print("Using these parameters")
        p.printParams()




defaultParams = """
#####################################
## GENERAL CONFIGURATION
#####################################
 
## debug ##
# Flag to output debugging information
debug = False



# Email Address
emailAddy = "prestop@ucar.edu"

# You can define the endpoint directly
archiveEndPoint = ""

# or if it is not defined, you can give a shell command that will produce it:
archiveEndPointShellCmd =  "globus endpoint search 'NCAR' --filter-owner-id 'ncar@globusid.org' | grep Campaign | cut -f1 -d' '"



#########################
#  GLOBUS CONFIGURATION
#########################



 
"""


if __name__ == "__main__":
    main()
