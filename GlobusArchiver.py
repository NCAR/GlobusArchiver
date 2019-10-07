#!/usr/bin/env python
'''
GlobusArchiver.py helps users archive data to the Campaign Store (and other Globus Endpoints)
'''

import sys
if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3.6 or later")
if sys.version_info[0] == 3 and sys.version_info[1] < 6:
    raise Exception("Must be using Python 3.6 or later")

######################
# PYTHON LIB IMPORTS
#####################
import subprocess
import shlex
import os
import json
import time
import webbrowser
import ssl
import threading
import glob
import copy
import enum
import smtplib
import email
import pprint
import datetime
import socket
import random
import string
import shutil

##################
# GLOBUS IMPORTS
##################
import globus_sdk

#####################
# CONFIG MASTER STUFF
#####################
import logging

# manage externals
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'configmaster'))
try:
    from ConfigMaster import ConfigMaster
except  ImportError:
    print(f"{os.path.basename(__file__)} needs ConfigMaster to run.")
    print(f"Plase review README.md for details on how to run manage_externals")
    exit(1)

defaultParams = """

######################################
#          GLOBUS CONFIGURATION
######################################


# Imports used in the configuration file
import os
import socket
import datetime


#####################################
## GENERAL CONFIGURATION
#####################################
 
###############  TEMP DIR   ##################

# tempDir is used for:
#     - Staging Location for .tar Files
# Default, $TMPDIR if it is defined, otherwise $HOME if defined, otherwise '.'.
tempDir = os.path.join(os.getenv("TMPDIR",os.getenv("HOME",".")), "GlobusArchiver-tmp")

# You may want to keep the tmp area around for debugging
cleanTemp = True

###############  EMAIL   ##################

# Deliver a report to these email addresses
# Use a list of 3-tuples  ("name", "local-part", "domain")
emailAddresses = [("Paul Prestopnik", "prestop", "ucar.edu")] 

# This is the email address that will be used in the "from" field
fromEmail = emailAddresses[0];


#####################################
##  AUTHENTICATION          
#####################################

# You can define the endpoint directly  
# This default value is the NCAR CampaignStore 
# the value was obtained by running:
# $ globus endpoint search 'NCAR' --filter-owner-id 'ncar@globusid.org' | grep Campaign | cut -f1 -d'      
archiveEndPoint = "6b5ab960-7bbf-11e8-9450-0a6d4e044368"

# The refresh token is what lets you use globus without authenticating every time.  We store it in a local file.
# !!IMPORTANT!!!
# You need to protect your Refresh Tokens. 
# They are an infinite lifetime credential to act as you.
# Like passwords, they should only be stored in secure locations.
# e.g. placed in a directory where only you have read/write access
globusTokenFile = os.path.join(os.path.expanduser("~"),".globus-ral","refresh-tokens.json")


####################################
## ARCHIVE RUN CONFIGURATION
####################################

#########  Archive Date/Time  #################
#
# This is used to set the date/time of the Archive.
# The date/time can be substituted into all archive-item strings, by using
# standard strftime formatting.

# This value is added (so use a negaative number to assign a date in the past) 
# to now() to find the archive date/time.
archiveDayDelta=-2

# If this is set, it overrides the archiveDayDelta.  If you want to use
# archiveDayDelta to set the Archive Date/Time, make sure this is 
# set to an empty string.  This string must be parseable by one of the
# format strings defined in archiveDateTimeFormats.
archiveDateTimeString=""

# You can add additional strptime
archiveDateTimeFormats=["%Y%m%d","%Y%m%d%H","%Y-%m-%dT%H:%M:%SZ"]

# Set to False to process data but don't actually submit the tasks to Globus
submitTasks = True

# Number of seconds to wait to see if transfer completed
# Report error if it doesn't completed after this time
# Default is 21600 (6 hours)
transferStatusTimeout = 21600

####################################
## ARCHIVE ITEM CONFIGURATION
####################################

# TODO: transfer-args are currently ignored

# doZip is optional, and defaults to False
# transferLabel is optional, and defaults to the item key + "-%Y%m%d"
# tar_filename is optional and defaults to "".  TAR is only done if tar_filename is a non-empty string
# transferArgs is a placeholder and not yet implemented.

# use sync_level to specify when files are overwritten:

# "exists"   - If the destination file is absent, do the transfer.
# "size"     - If destination file size does not match the source, do the transfer.
# "mtime"    - If source has a newer modififed time than the destination, do the transfer.
# "checksum" - If source and destination contents differ, as determined by a checksum of their contents, do the transfer. 

archiveItems = {
"icing-cvs-data":
       {
       "source": "/d1/prestop/backup/test1",
       "destination": "/gpfs/csfs1/ral/nral0003",
       "transferArgs": "--preserve-mtime",
       "transferLabel": "icing_cvs_data_%Y%m%d",
       "doZip": False,
       "sync_level" : "mtime"

       },
"icing-cvs-data2":
       {
       "source": "/d1/prestop/backup/test2",
       "destination": "/gpfs/csfs1/ral/nral0003",
       "transferArgs": "--preserve-mtime",
       "transferLabel": "icing_cvs_data_%Y%m%d",
       "doZip": False,
       "tarFileName": "test2.tar",
       "cdDirTar": "/d1/prestop/backup",
       "expectedNumFiles": 3,
       "expectedFileSize": 1024
       }
}
"""
########################################
# Copied from https://github.com/globus/native-app-examples/blob/master/utils.py
import logging
import os
import ssl
import threading

try:
    import http.client as http_client
except ImportError:
    import httplib as http_client

try:
    from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
except ImportError:
    from http.server import HTTPServer, BaseHTTPRequestHandler

try:
    import Queue
except ImportError:
    import queue as Queue

try:
    from urlparse import urlparse, parse_qs
except ImportError:
    from urllib.parse import urlparse, parse_qs


def enable_requests_logging():
    http_client.HTTPConnection.debuglevel = 4

    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger('requests.packages.urllib3')
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True


def is_remote_session():
    return os.environ.get('SSH_TTY', os.environ.get('SSH_CONNECTION'))


class RedirectHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'You\'re all set, you can close this window!')

        code = parse_qs(urlparse(self.path).query).get('code', [''])[0]
        self.server.return_code(code)

    def log_message(self, format, *args):
        return


class RedirectHTTPServer(HTTPServer, object):

    def __init__(self, listen, handler_class, https=False):
        super(RedirectHTTPServer, self).__init__(listen, handler_class)

        self._auth_code_queue = Queue.Queue()

        if https:
            self.socket = ssl.wrap_socket(
                self.socket, certfile='./ssl/server.pem', server_side=True)

    def return_code(self, code):
        self._auth_code_queue.put_nowait(code)

    def wait_for_code(self):
        return self._auth_code_queue.get(block=True)


def start_local_server(listen=('', 4443)):
    server = RedirectHTTPServer(listen, RedirectHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    return server


#####################################
# ConfigMaster 
#####################################
p = ConfigMaster()
p.setDefaultParams(defaultParams)
p.init(__doc__)

########################################################
# global constants
########################################################
CLIENT_ID = "f70debeb-31cc-40c0-8d65-d747641428b4"
REDIRECT_URI = 'https://auth.globus.org/v2/web/auth-code'
SCOPES = ('openid email profile '
          'urn:globus:auth:scope:transfer.api.globus.org:all')

###########################
# Global for the email
###########################
email_msg = email.message.EmailMessage()
email_errors = 0
email_warnings = 0


########################################################
# Function definitions
########################################################
def safe_mkdirs(d):
    logging.info(f"making dir: {d}")
    if not os.path.exists(d):
        try:
            os.makedirs(d, 0o700)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise


def run_cmd(cmd):
    '''
    runs a command with blocking

    returns a CompletedProcess instance 
        - you can get to stdout with .stdout.decode('UTF-8').strip('\n') 
    '''
    logging.debug(f"running command: {cmd}")

    # I know you shouldn't use shell=True, but splitting up a piped cmd into
    # multiple separate commands is too much work right now.
    # shell=True is also required if using wildcards
    # TODO: https://stackoverflow.com/questions/13332268/how-to-use-subprocess-command-with-pipes
    # https://stackoverflow.com/questions/295459/how-do-i-use-subprocess-popen-to-connect-multiple-processes-by-pipes
    try:
        if '|' in cmd or ';' in cmd or '*' in cmd or '?' in cmd:
            return subprocess.run(cmd, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  encoding='utf-8')
        else:
            splitcmd = shlex.split(cmd)
            return subprocess.run(splitcmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  encoding='utf-8')

    except subprocess.CalledProcessError:
        logging.error(f'Command returned non-zero exit status: {cmd}.')
        return None


def parse_archive_date_time():
    # Set dateTime based on archiveDayDelta
    archive_date_time = datetime.datetime.now() + datetime.timedelta(days=p.opt["archiveDayDelta"])

    # If archiveDateTimeString is set, then try to use that to set dateTime
    if p.opt["archiveDateTimeString"]:
        for format in p.opt["archiveDateTimeFormats"]:
            logging.debug(f"Checking {p.opt['archiveDateTimeString']} for format {format}")
            try:
                archive_date_time = datetime.datetime.strptime(p.opt["archiveDateTimeString"], format)
            except ValueError:
                continue

            return archive_date_time

        # if not matched, error and exit
        logging.error(f"--archiveDateTimeString value ({p.opt['archiveDateTimeString']}) did not match any "
                      f"--archiveDateTimeFormats items: {p.opt['archiveDateTimeFormats']}")
        exit(1)

    return archive_date_time


def add_tar_groups_info():
    for item, item_info in p.opt["archiveItems"].items():
        # for each tar'd item, first assume it is the last/only item in this tar file.
        if item_info.get("tar_filename"):
            item_info["last_tar_in_group"] = True

        # Now look at all other archive items and see if they are TARing to the same target
        past_this_item = False
        for item2, item_info2 in p.opt["archiveItems"].items():
            if item == item2:
                past_this_item = True
                continue
            if not item_info2.get("tar_filename"):
                continue
            if past_this_item and item_info["tar_filename"] == item_info2["tar_filename"]:
                item_info["last_tar_in_group"] = False


def add_transfer_label():
    for item, item_info in p.opt["archiveItems"].items():
        if item_info.get("transferLabel"):
            item_info["transfer_label"] = item_info["transferLabel"]
        else:
            item_info["transfer_label"] = item + "_%y%m%d"


def randomword(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


def handle_configuration():
    # TODO: do some error checking for user.
    #     i.e. no duplicate keys in archiveItems, what else?

    archive_date_time = parse_archive_date_time()
    logging.info(f"ARCHIVE DATE TIME: {archive_date_time}")

    # I think we can do this.   Let's use snake_case vs. CamelCase to distinguish between
    # values we are just storing in p.opt vs. actual config params.
    p.opt["archive_date_time"] = archive_date_time

    add_tar_groups_info()
    add_transfer_label()

    # if p.opt["archiveEndPoint"] == "":
    # comp_proc = run_cmd(p.opt["archiveEndPointShellCmd"])
    # print(comp_proc)
    # stdout comes back as a series of octets, so decode to a normal string and strip endline
    # EP = comp_proc.stdout.decode('UTF-8').strip('\n')
    # logging.debug(f"Got EndPoint via archiveEndPointShellCmd: {EP}")
    # p.opt["archiveEndPoint"] = EP
    # logging.debug("")

    logging.debug("After handle_configuration(), configuration looks like this:")
    logging.debug(f"{p.opt}")

    # add random subdir to tmp dir
    p.opt["tempDir"] = os.path.join(p.opt["tempDir"], randomword(8))


def load_tokens_from_file(filepath):
    """Load a set of saved tokens."""
    logging.info(f"Attempting load of tokens from {filepath}")
    with open(filepath, 'r') as f:
        tokens = json.load(f)

    return tokens


def save_tokens_to_file(filepath, tokens):
    """Save a set of tokens for later use."""
    safe_mkdirs(os.path.dirname(filepath))
    logging.info(f"Attempting save of tokens to {filepath}")
    with open(filepath, 'w') as f:
        json.dump(tokens, f)
    # TODO: make sure mode is set restrictively on this file


def update_tokens_file_on_refresh(token_response):
    """
    Callback function passed into the RefreshTokenAuthorizer.
    Will be invoked any time a new access token is fetched.
    """
    save_tokens_to_file(p.opt["globusTokenFile"], token_response.by_resource_server)


def do_native_app_authentication(client_id, redirect_uri,
                                 requested_scopes=None):
    """
    Does a Native App authentication flow and returns a
    dict of tokens keyed by service name.
    """
    client = globus_sdk.NativeAppAuthClient(client_id=client_id)
    # pass refresh_tokens=True to request refresh tokens
    client.oauth2_start_flow(requested_scopes=requested_scopes,
                             redirect_uri=redirect_uri,
                             refresh_tokens=True)

    url = client.oauth2_get_authorize_url()

    print(f'\n\nAuthorization needed.  Please visit this URL:\n{url}\n')

    if not is_remote_session():
        webbrowser.open(url, new=1)

    auth_code = input('Enter the auth code: ').strip()

    token_response = client.oauth2_exchange_code_for_tokens(auth_code)

    # return a set of tokens, organized by resource server name
    return token_response.by_resource_server


def get_transfer_client():
    tokens = None
    try:
        # if we already have tokens, load and use them
        tokens = load_tokens_from_file(p.opt["globusTokenFile"])
    except:
        pass

    if not tokens:
        # if we need to get tokens, start the Native App authentication process
        tokens = do_native_app_authentication(CLIENT_ID, REDIRECT_URI, SCOPES)

        try:
            save_tokens_to_file(p.opt["globusTokenFile"], tokens)
        except:
            pass

    transfer_tokens = tokens['transfer.api.globus.org']

    auth_client = globus_sdk.NativeAppAuthClient(client_id=CLIENT_ID)

    authorizer = globus_sdk.RefreshTokenAuthorizer(
        transfer_tokens['refresh_token'],
        auth_client,
        access_token=transfer_tokens['access_token'],
        expires_at=transfer_tokens['expires_at_seconds'],
        on_refresh=update_tokens_file_on_refresh)

    transfer = globus_sdk.TransferClient(authorizer=authorizer)

    myproxy_lifetime = 720  # in hours.  What's the maximum?
    try:
        r = transfer.endpoint_autoactivate(p.opt["archiveEndPoint"], if_expires_in=3600)
        while (r["code"] == "AutoActivationFailed"):
            print("Endpoint requires manual activation, please use your UCAS name/password for this activation. "
                  "You can activate via the command line or via web browser:\n"
                  "WEB BROWSER -- Open the following URL in a browser to activate the "
                  "endpoint:")
            print(f"https://app.globus.org/file-manager?origin_id={p.opt['archiveEndPoint']}")
            print("CMD LINE -- run this from your shell: ")
            print(
                f"globus endpoint activate --myproxy --myproxy-lifetime {myproxy_lifetime} {p.opt['archiveEndPoint']}")
            input("Press ENTER after activating the endpoint:")
            r = transfer.endpoint_autoactivate(p.opt["archiveEndPoint"], if_expires_in=3600)

    except globus_sdk.exc.GlobusAPIError as ex:
        print("endpoint_autoactivation failed.")
        print(ex)
        if ex.http_status == 401:
            sys.exit('Refresh token has expired. '
                     'Please delete refresh-tokens.json and try again.')
        else:
            raise ex
    return transfer


def do_transfers(transfer):
    # print out a directory listing from an endpoint
    # print("Looking at archive end point")
    # for entry in transfer.operation_ls(p.opt["archiveEndPoint"], path='/~/'):
    #    print(entry['name'] + ('/' if entry['type'] == 'dir' else ''))

    # revoke the access token that was just used to make requests against
    # the Transfer API to demonstrate that the RefreshTokenAuthorizer will
    # automatically get a new one
    # auth_client.oauth2_revoke_token(authorizer.access_token)
    # Allow a little bit of time for the token revocation to settle
    # time.sleep(1)
    # Verify that the access token is no longer valid
    # token_status = auth_client.oauth2_validate_token(
    #    transfer_tokens['access_token'])
    # assert token_status['active'] is False, 'Token was expected to be invalid.'

    # print('\nDoing a second directory listing with a new access token:')
    # for entry in transfer.operation_ls(p.opt["archiveEndPoint"], path='/~/'):
    #    print(entry['name'] + ('/' if entry['type'] == 'dir' else ''))

    local_ep = globus_sdk.LocalGlobusConnectPersonal()
    local_ep_id = local_ep.endpoint_id

    # tdata = globus_sdk.TransferData(transfer, local_ep_id, p.opt["archiveEndPoint"], label=ii["transfer_label"])
    tdata = globus_sdk.TransferData(transfer, local_ep_id, p.opt["archiveEndPoint"])

    logging.info("\nBEGINNING PROCESSING OF archiveItems")
    for item, item_info in p.opt["archiveItems"].items():
        logging.info(f"Transferring {item}")

        ii = copy.deepcopy(item_info)

        # substitute date/time strings and env variables in item info
        for ii_key in ("source", "destination" "transfer_labe", "tarFileName", "cdDirTar"):
            if ii.get(ii_key):
                ii[ii_key] = p.opt["archive_date_time"].strftime(ii[ii_key])
                ii[ii_key] = os.path.expandvars(ii[ii_key])

        # initialize number of files to 0
        ii['num_files'] = 0

        add_to_email(f"\nSOURCE:      {ii['source']}\n")
        add_to_email(f"DESTINATION: {ii['destination']}\n")

        if "*" in ii["source"] or "?" in ii["source"]:  # Is there a '*' or '?' in the source?
            logging.verbose(f"Found wildcard in source: {ii['source']}")
            expanded_sources = glob.glob(ii['source'])
            ii["glob"] = True

            if len(expanded_sources) == 0:
                log_and_email(f"Source expands to zero targets: {ii['source']}.  SKIPPING!", logging.error)
                continue

        else:
            ii["glob"] = False

        if ii.get("glob") == True and not ii.get("tarFileName"):
            # can't handle both dirs and files in a glob
            file_glob = False
            dir_glob = False
            for es in expanded_sources:
                if os.path.isfile(es):
                    file_glob = True
                if os.path.isdir(es):
                    dir_glob = True
            if file_glob and dir_glob:
                # TODO: Copied this from Archiver.pl Is this still true?  
                log_and_email(
                    f"glob: {ii['source']} expands to files and dirs.  Not allowed.  Skipping this archive item.",
                    logging.error)
                continue

            for es_ix, es in enumerate(expanded_sources):
                # skip files that start with underscore if set to skip them
                if ii.get("skipUnderscoreFiles") and es.startswith('_'):
                    continue

                ii["source"] = es

                # if not last item
                if es_ix != len(expanded_sources):
                    ii["last_glob"] = False
                else:
                    ii["last_glob"] = True
                prepare_and_add_transfer(tdata, ii)
        else:
            if not ii["glob"] and not os.path.exists(ii["source"]):
                log_and_email(f"{ii['source']} does not exist. Skipping this archive item.", logging.error)
                continue
            prepare_and_add_transfer(tdata, ii)

    # submit all tasks for transfer
    if p.opt['submitTasks']:
        submit_transfer_task(transfer, tdata)


def prepare_and_add_transfer(tdata, item_info):
    logging.info(f"\nTRANSFER -- {item_info['source']}")
    if prepare_transfer(item_info):
        # check_sizes(item_info)  -- this is done during prepare, could be refactored to here?
        add_transfer_item(tdata, item_info)


# recursively creates parents to make path
def make_globus_dir(transfer, path):
    dest_path = os.path.sep
    for element in path.split(os.path.sep):
        dest_path = os.path.join(dest_path, element)
        try:
            transfer.operation_ls(p.opt["archiveEndPoint"], dest_path)
        except globus_sdk.exc.TransferAPIError as e:
            transfer.operation_mkdir(dest_path)


def prepare_transfer(ii):
    if not ii["source"].startswith('/'):
        log_and_email(f"{item} source: {ii['source']} must be absolute.  SKIPPING!", logging.error)
        return False
    if not ii["destination"].startswith('/'):
        log_and_email(f"{item} destination: {ii['destination']} must be absolute.  SKIPPING!", logging.error)
        return False

    # error and skip if cdDirTar is not a subset of source
    if ii.get('cdDirTar') and ii['source'].find(ii['cdDirTar']) == -1:
        log_and_email(f"source {ii['source']} must contain cdDirTar ({ii['cdDirTar']}. SKIPPING!",
                      logging.error)
        return

    # Don't need this?  transfer should automatically make dirs as needed.
    # try:
    #    transfer.operation_ls(p.opt["archiveEndPoint"], path=ii["destination"])
    # except globus_sdk.exc.TransferAPIError as e:
    #    log_and_email(f"Destination path ({ii['destination']}) does not exist on archiveEndPoint. SKIPPING!",
    #        logging.error)
    #    try:
    #        transfer.operation_mkdir(p.opt["archiveEndPoint"], path=ii["destination"]])
    #    except 
    #    
    #    return False

    if ii.get("doZip"):
        cmd = "gzip "
        if os.path.isdir(ii['source']):
            cmd += "-r "
        cmd += "-S .gz ";  # force .gz suffix in case of differing gzip version
        cmd += ii['source'];
        logging.debug(f"ZIPing file via cmd: {cmd}")
        if not run_cmd(cmd):
            return False
        if os.path.isfile(ii['source']):
            ii['source'] += ".gz"

    if ii.get("tarFileName"):
        # check if input is empty directory and skip if so
        if os.path.isdir(ii['source']) and not os.listdir(ii['source']):
            log_and_email(f"Source directory is empty: {ii['source']}. SKIPPING!",
                          logging.error)
            return False

        tar_dir = os.path.join(p.opt["tempDir"], f"Item-{ii['transfer_label']}-Tar")
        safe_mkdirs(tar_dir)
        tar_path = os.path.join(tar_dir, ii["tarFileName"])
        # if cdDirTar is set, cd into that directory and create the tarball using the
        # relative path to source from cdDirTar. If source and cdDirTar are the same, use *
        if ii.get("cdDirTar"):
            cmd = f"cd {ii['cdDirTar']}; tar rf {tar_path} "
            relative_path = ii['source'].replace(ii['cdDirTar'], '').lstrip(os.path.sep)
            if relative_path == '':
                relative_path = '*'
            cmd += relative_path
        else:
            cmd = f"tar rf {tar_path} {ii['source']}"

        if ii.get("skipUnderscoreFiles"):
            cmd += " --exclude \"_*\""

        if not run_cmd(cmd):
            return False
        # created the tar file, so now set the source to the tar file 
        ii["source"] = os.path.join(tar_dir, ii["tarFileName"])

        cmd = f"tar tf {ii['source']} | wc -l"
        output = run_cmd(cmd)
        if output is None:
            return False
        logging.verbose(f"got output: {output}")
        ii["num_files"] = int(output.stdout)
    else:
        # if source is a directory, list the number of files inside
        # otherwise just increment number of files
        if os.path.isdir(ii["source"]):
            ii["num_files"] = len(os.listdir(ii["source"]))
        else:
            ii["num_files"] += 1

    # if not ii["glob"] or ii.get("tarFileName"):
    #    ii["file_size"] = os.path.getsize(ii["source"])

    if ii.get("expectedFileSize") and (not ii["glob"] or ii.get("last_glob")):
        if ii.get("file_size"):
            if ii["file_size"] < ii["expectedFileSize"]:
                log_and_email(
                    f"file_size < expectedFileSize: {ii['file_size']} < {ii['expectedFileSize']})",
                    logging.warning)
        else:
            log_and_email(
                f"expectedFileSize given, but file_size not calculated", logging.warning)

    if ii.get("expectedNumFiles") and (not ii["glob"] or ii.get("last_glob")):
        if ii.get("num_files"):
            if ii["num_files"] < ii["expectedNumFiles"]:
                log_and_email(
                    f"Item has {ii['num_files']} files but expects {ii['expectedNumFiles']} files!",
                    logging.warning)
        else:
            # this should never happen
            log_and_email(
                f"expectedNumFiles given, but num_files not calculated", logging.warning)
    return True


def add_to_email(email_str):
    global email_msg
    email_msg.set_content(email_msg.get_content() + email_str)


def log_and_email(msg_str, logfunc):
    # uses global email_msg
    global email_errors
    global email_warnings

    # add to error/warning counter to modify email subject
    if logfunc == logging.error:
        email_errors = email_errors + 1
    elif logfunc == logging.warning:
        email_warnings = email_warnings + 1

    logfunc(msg_str)
    add_to_email(logfunc.__name__.upper() + ": " + msg_str)


def add_transfer_item(tdata, ii):
    logging.verbose(f"Entering transfer_item {tdata}, {ii}")
    # get leaf dir from source, and add it to destination
    # if cdDir is set and not tarring data, set leaf
    # to source with cdDir stripped off to get any subdirectories
    # if ii.get("cdDir") and not ii.get("tarFileName"):
    #    leaf = ii['source'].replace(ii['cdDir'], '').lstrip(os.path.sep)
    # else:
    #    leaf = os.path.basename(ii['source'].rstrip(os.path.sep))

    # if we are not TARing, then we will send the leaf of the source up to the destination
    if not ii.get("tarFileName"):
        leaf = os.path.basename(ii['source'].rstrip(os.path.sep))
        destination = os.path.join(ii['destination'], leaf)
    else:
        destination = ii['destination']
    logging.debug(f"Using destination: {destination}")

    # Check if destination_dir already exists, and skip if so
    # TODO: add support to overwrite?
    # try:
    #    transfer.operation_ls(p.opt["archiveEndPoint"], path=destination)
    #    log_and_email(f"Destination {destination} already exists on archiveEndPoint.  SKIPPING!", logging.error)
    #    return
    # except globus_sdk.exc.TransferAPIError as e:
    #    if e.code != u'ClientError.NotFound':
    #        log_and_email(f"Can't ls {p.opt['archiveEndPoint']} : {destination}", logging.fatal)
    #        logging.fatal(e)
    #        return

    # create destination directory
    # try:
    #    logging.info(f"Creating destination directory {destination}")
    #    transfer.operation_mkdir(p.opt["archiveEndPoint"], destination)
    # except globus_sdk.exc.TransferAPIError as e:
    #    log_and_email(f"Can't mkdir {p.opt['archiveEndPoint']} : {destination}", logging.fatal)
    #    logging.fatal(e)
    #    return

    # TODO: set permissions for users to read dir
    #       look at https://github.com/globus/automation-examples/blob/master/share_data.py

    # print("Looking at local end point")
    # for entry in transfer.operation_ls(local_ep_id):
    #    print(f"Local file: {entry['name']}")

    if os.path.isdir(ii['source']):
        tdata.add_item(ii['source'], destination, recursive=True, sync_level=ii.get("sync_level"))
    else:
        tdata.add_item(ii['source'], destination, sync_level=ii.get("sync_level"))
    logging.debug(f"Adding TransferData item: {ii['source']} -> {destination}") 

def check_task_for_success(transfer, task_id):
    logging.debug("Waiting for transfer to complete...")
    timeout = p.opt['transferStatusTimeout']

    # wait for task to report that it completed or it timed out
    if not transfer.task_wait(task_id, timeout=timeout):
        log_and_email(f"Transfer timed out after {timeout} seconds", logging.error)
    else:
        log_and_email(f"Transfer complete.", logging.info)

def submit_transfer_task(transfer, tdata):
    try:
        logging.info(f"Submitting transfer task - {tdata}")
        task = transfer.submit_transfer(tdata)
    except globus_sdk.exc.TransferAPIError as e:
        log_and_email("Transfer task submission failed", logging.fatal)
        logging.fatal(e)
        return

    log_and_email(f"Task ID: {task['task_id']}", logging.info)
    log_and_email(f"This transfer can be monitored via the Web UI: https://app.globus.org/activity/{task['task_id']}",
                  logging.info)


    check_task_for_success(transfer, task['task_id'])

def prepare_email_msg():
    email_msg['From'] = email.headerregistry.Address(*p.opt["fromEmail"])

    to = ()
    for em in p.opt["emailAddresses"]:
        to += (email.headerregistry.Address(*em),)
    email_msg['To'] = to

    email_msg.set_content(f"This is a msg from GlobusArchiver.py.\n")


def set_email_msg_subject():
    subject = ''
    if email_errors == 0 and email_warnings == 0:
        subject = 'NO PROBLEMS with '
    else:
        if email_errors:
            subject += f'{email_errors} ERRORS '
        if email_warnings:
            subject += f'{email_warnings} WARNINGS '
        subject += 'with '

    date_formatted = p.opt["archive_date_time"].strftime('%Y-%m-%d')
    subject += f"GlobusArchiver on {socket.gethostname()} - {os.path.basename(p.getConfigFilePath())} - {date_formatted}"
    email_msg['Subject'] = subject


def send_email_msg():
    logging.info(f"Sending email to {email_msg['To']}")
    logging.debug(f"BODY: {email_msg.get_body()}")

    with smtplib.SMTP('localhost') as s:
        s.send_message(email_msg)


def main():
    logging.info(f"Starting {os.path.basename(__file__)}")

    if len(sys.argv) == 1:
        logging.info('You must supply command line arguments to run GlobusArchiver.py')
        p.parser.print_help()
        exit(0)

    pp = pprint.PrettyPrinter()
    logging.info(f"Read this configuration:")
    for line in p.getParamsString().splitlines():
        # logging.info(pp.pformat(line))
        logging.info(f"{line}")

    handle_configuration()
    prepare_email_msg()

    logging.debug(f"Using this configuration (after transformation):")
    for line in p.getParamsString().splitlines():
        logging.debug(f"\t{line}")

    transfer_client = get_transfer_client()
    do_transfers(transfer_client)

    set_email_msg_subject()
    send_email_msg()

    if p.opt["cleanTemp"] and os.path.isdir(p.opt['tempDir']):
        logging.info(f"removing temp directory tree : {p.opt['tempDir']}")
        shutil.rmtree(p.opt["tempDir"])


if __name__ == "__main__":
    main()
