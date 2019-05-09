#!/usr/bin/env python
'''
GlobusArchiver.py helps users archive data to the Campaign Store (and other Globus Endpoints)
'''


import sys    
if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3.5 or later")
if sys.version_info[0] == 3 and sys.version_info[1] < 5:
    raise Exception("Must be using Python 3.5 or later")



import subprocess
import shlex
import os

##################
# GLOBUS IMPORTS
##################
import globus_sdk


#####################
# CONFIG MASTER STUFF
#####################
import logging

# manage externals
sys.path.append('configmaster')
try:
    from ConfigMaster import ConfigMaster
except  ImportError:
    print(f"{os.path.basename(__file__)} needs ConfigMaster to run.")
    print(f"Plase review README.md for details on how to run manage_externals")
    exit(1)

########################################################
# global constants
########################################################

# 
CLIENT_ID = ""


########################################################
# Function definitions
########################################################

def run_cmd(cmd):
    '''
    runs a command with blocking

    returns a CompletedProcess instance 
        - you can get to stdout with .stdout.decode('UTF-8').strip('\n') 
    '''
    logging.debug(f"running command: {cmd}")
    
    # I know you shouldn't use shell=True, but splitting up a piped cmd into
    # multiple separate commands is too much work right now.
    # TODO: https://stackoverflow.com/questions/13332268/how-to-use-subprocess-command-with-pipes
    # https://stackoverflow.com/questions/295459/how-do-i-use-subprocess-popen-to-connect-multiple-processes-by-pipes
    if '|' in cmd:
        return subprocess.run(cmd, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        splitcmd = shlex.split(cmd)
        return subprocess.run(splitcmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
def handle_configuration(cfg):
    if cfg.opt["archiveEndPoint"] == "":
        comp_proc = run_cmd(cfg.opt["archiveEndPointShellCmd"])
        #print(comp_proc)
        # stdout comes back as a series of octets, so decode to a normal string and strip endline
        EP = comp_proc.stdout.decode('UTF-8').strip('\n')
        logging.debug(f"Got EndPoint via archiveEndPointShellCmd: {EP}")
        cfg.opt["archiveEndPoint"] = EP


# TODO: can we check if the local endpoint already exists? 
# what if you run two copies of this script at once?
def createLocalEndpoint(cfg):
    ''' create endpoint based on personalEndpoing configuration. '''

    
    personalEPLogFIle = "./personal_EP.log"

    cmd = f"globus endpoint create --personal {p.opt['personalEndpoint']} > {personalEPLogFile}"
    run_cmd(cmd)
    logging.info("Created a personal endpoint - {p.opt['personalEndpoint']}")

    cmd = f"grep Setup {personalEPLogFile} | rev | cut -f1 -d' ' | rev"
    setup_proc = run_cmd(cmd)
    setup_id = setup_proc.stdout.decode('UTF-8').strip('\n')
    logging.info(f"Got personal endpoint setup ID: {setup_id}");

    cmd = f"globus endpoint search '{p.opt['personalEndpoint']}' | grep khaba | cut -f1 -d' '"
    endpoint_proc = run_cmd(cmd)
    endpoint_id = endpoint_proc.stdout.decode('UTF-8').strip('\n')
    logging.info(f"Got personal endpoint ID: {endpoint_id}")

    cmd = f"/opt/globusconnectpersonal-2.3.6/globusconnectpersonal  -setup {setup_id}"
    setup_ep_proc = run_cmd(cmd)
    logging.info(f"started globus connect personal")
    logging.debug(f"stdout: {setup_ep_proc.stdout.decode('UTF-8').strip('\n')}")
    logging.debug(f"stderr: {setup_ep_proc.stderr.decode('UTF-8').strip('\n')}")

    
    
    return (setup_id, endpoint_id)

def startPersonalServer():

    cmd = f"/opt/globusconnectpersonal-2.3.6/globusconnectpersonal -start &"
    run_cmd(cmd)
    
def stopPersonalServer():
    cmd = f"/opt/globusconnectpersonal-2.3.6/globusconnectpersonal -stop &"
    run_cmd(cmd)


def getRefreshToken(cfg, client):
    client.oauth2_start_flow(refresh_tokens=True)

    authorize_url = client.oauth2_get_authorize_url()
    print('Please go to this URL and login: {0}'.format(authorize_url))

    auth_code = input(
    'Please enter the code you get after login here: ').strip()
    token_response = client.oauth2_exchange_code_for_tokens(auth_code)

    # QUESTION - why do I have two different resource servers?
    
    #globus_auth_data = token_response.by_resource_server['auth.globus.org']
    globus_transfer_data = token_response.by_resource_server['transfer.api.globus.org']

    # most specifically, you want these tokens as strings
    #AUTH_TOKEN = globus_auth_data['access_token']
    #TRANSFER_TOKEN = globus_transfer_data['access_token']
    refresh_token = globus_transfer_data["refresh_token"]

    return refresh_token
    

def getGlobusAuthorizer(cfg, client):

    rt = cfg.["refreshToken"]
    if rt = "":
        rt = getRefreshToken(cfg)

    # a GlobusAuthorizer is an auxiliary object we use to wrap the token. In
    # more advanced scenarios, other types of GlobusAuthorizers give us
    # expressive power
    #authorizer = globus_sdk.AccessTokenAuthorizer(TRANSFER_TOKEN)

    authorizer = globus_sdk.RefreshTokenAuthorizer(refresh_token, client)

    return authorizer

    

def main():
    p = ConfigMaster()
    p.setDefaultParams(defaultParams)
    p.init(__doc__)

    print(f"Starting {os.path.basename(__file__)}")

    logging.info(f"Using this configuration:")
    for line in p.getParamsString().splitlines():
        logging.info(f"\t{line}")
 
    handle_configuration(p)

    print(p.opt["archiveEndPoint"])


    # connect to globus
    client = globus_sdk.NativeAppAuthClient(CLIENT_ID)
    
    getGlobusAuthorizer(p, client)
    


   

defaultParams = """

# Imports used in the configuration file
import os
import socket

#####################################
## GENERAL CONFIGURATION
#####################################

 
## debug ##

# Email Address
emailAddy = "prestop@ucar.edu"

# You can define the endpoint directly
archiveEndPoint = ""

# or if it is not defined, you can give a shell command that will produce it:
archiveEndPointShellCmd =  "globus endpoint search 'NCAR' --filter-owner-id 'ncar@globusid.org' | grep Campaign | cut -f1 -d' '"

# The name of your local endpoint
import socket
personalEndpoint = socket.gethostname()





# You can set a refresh token directly in a configuration file
# You can also set an environment variable $REFRESH_TOKEN
# !!IMPORTANT!!!
# You need to protect your Refresh Tokens. 
# They are an infinite lifetime credential to act as you.
# Like passwords, they should only be stored in secure locations.
# e.g. placed in a 

globusTokenFile = os.path.join(os.path.expanduser("~"),".globus-ral","refresh-tokens.json")

#########################
#  GLOBUS CONFIGURATION
#########################



 
"""


if __name__ == "__main__":
    main()
