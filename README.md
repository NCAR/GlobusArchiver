# GlobusArchiver
GlobusArchiver.py is a python utility to archive local data via Globus.  Originally designed for the Campaign Store, but it could be used with
any globus endpoint.  

**NOTE: Instructions assume bash shell**

## Requires
* Python 3.6 or greater
* ConfigMaster  (installed via manage_externals -- see instructions below)
* A personal globus account (instructions below)
* Globus Python SDK (globus_sdk)
* Globus CLI
* GlobusConnectPersonal

# Creating a Globus Account
You can find [instructions for creating a personal globus account on the CISL website](https://www2.cisl.ucar.edu/resources/storage-and-file-systems/globus-file-transfers).  

# Installing

## Installing the Globus CLI and globusconnectpersonal
The Globus CLI is available in RAL via the /usr/local anaconda install:
```
/usr/local/anaconda3/bin/globus
```

If you have a conda installation (e.g. on a mac), you can install like this:
```
conda config --add channels conda-forge
conda install globus-sdk
conda install globus-cli
```


You will need globusconnectpersonal installed to start your own local endpoint.  I had SNAT install it in:
* /opt/globusconnectpersonal


The instructions that follow assume these two programs are in your path.  

Here is one way you can add the globus CLI, globus SDK and globusconnectpersonal to your path.

```
echo export PATH=/usr/local/anaconda3/bin:\$PATH:/opt/globusconnectpersonal > ~/.globus_env
```
now you can source this file to set your environment
```
. ~/.globus_env
```
or add it to your .bashrc so your path is always set.

A "quickstart guide" to using Globus Connect Personal is given below, but you can also find more [information about Globus Connect Personal online](https://www.globus.org/globus-connect-personal).

## Installing the Globus Python SDK
To run GlobusArchiver.py, you will need the Globus Python SDK installed.  In RAL this is available as part of the anaconda3 installation:`/usr/local/anaconda3/lib/python3.7/site-packages/glob`

As long as you have write permissions in your python3 environment, you can also install it yourself using pip.  Instructions online are straightforward:
https://globus-sdk-python.readthedocs.io/en/stable/installation/

## Keeping the Campaign Store Endpoint Active
By default the Campaign Store is only active for 24 hours.  You can extend this to 30 days and automate your activation.
  
  First request a certificate by following the instructions on this [CISL web page](https://www2.cisl.ucar.edu/resources/storage-and-file-systems/configuring-globus-unattended-workflows).

When you run the gcert command, part of the output will say something like:
```
Globus certificate created in /glade/u/home/prestop!
```

look in that directory, and you will find a file named something like `.prestop-globus.cert`

You can activate your endpoint using `globus endpoint activate`, but first you need to make globus available on cheyenne:
```
module load python
ncar_pylib
```

Now you can activate your endpoint for 31 days using your certificate
```
globus endpoint activate --delegate-proxy /glade/u/home/prestop/.prestop-globus.cert --force --proxy-lifetime 744 6b5ab960-7bbf-11e8-9450-0a6d4e044368
```

You can confirm the 30 day expiration of your endpoint with this command:
```
globus endpoint activate 6b5ab960-7bbf-11e8-9450-0a6d4e044368`
```
Now that you have a certificate you can automate the activation via a line in your crontab.  You can run this on any machine that has globus installed:
```
0    0    25    *    *    /usr/local/anaconda3/bin/globus endpoint activate --delegate-proxy /home/prestop/.prestop-globus.cert --force --proxy-lifetime 744 6b5ab960-7bbf-11e8-9450-0a6d4e044368 > /home/prestop/logs/globus-activate.log  2>&1
```

## Installing GlobusArchiver

After you have cloned the GlobusArchiver repository, you can run checkout_externals to get any external dependencies:

To get the required dependencies, run the following:
```
./manage_externals/checkout_externals
```

# Using the Globus with the Campaign Store

## login to globus
You can do this from the command line:
```
globus login
```

## Configure your local accesible directories

You will need to edit ~/.globusonline/lta/config-paths to configure which local directories are accessible via your personal endpoint.  If you are using GlobusArchiver to create TAR files, be sure to include your tmp directory in this file, because this is where tar files will be staged before sending.   [Details are online.](https://docs.globus.org/faq/globus-connect-endpoints/#how_do_i_configure_accessible_directories_on_globus_connect_personal_for_linux)

## Create your local endpoint
You only need to do this once.  Once you have your local endpoint created it persists.  You can check to see if you have a global endpoint already using the globus endpoint search:
```
globus endpoint search --filter-scope my-endpoints
```

You need to "create", "setup" and then "start" your endpoint:
```
# set this to whatever you want - I am using the name of the machine I am on.
export LOCAL_EP_NAME=$(uname -n)

globus login --no-local-server

# storing this output in a log file for ease of grepping later
globus endpoint create --personal $LOCAL_EP_NAME > local_endpoint.log

# get local setup ID, and local endpoint ID
export LOCAL_SETUP_ID=$(grep Setup local_endpoint.log | rev | cut -f1 -d' ' | rev)
export LOCAL_EP_ID=$(globus endpoint search $LOCAL_EP_NAME | grep $LOCAL_EP_NAME | cut -f1 -d' ')

# setup local personal endpoint
globusconnectpersonal  -setup $LOCAL_SETUP_ID
 
# start the GCP server
globusconnectpersonal -start &
```

You can check that your local endpoint is working:
```
globus ls ${LOCAL_EP_ID}:/path/to/local/files
```

## Keeping globusconnectpersonal running
You need to keep globusconnectpersonal running on every machine you want to have automated transfers on.  One way to do this is to use the [start_GCP.sh](https://github.com/NCAR/GlobusArchiver/blob/master/helper/start_GCP.sh) script that is in the helper directory in this repository.  Here is an example line for your crontab:
```
# make sure GCP is running
*/5 *   *    *    *      start_GCP.sh >> $LOG_DIR/start_gcp.cron.log 2>&1
```

## Running GlobusArchiver.py
If you used Archiver.pl in the past, you can use Archiver2GA.py (found in the helper subdirectory), to convert your old Archiver.pl configuration files to GlobusArchiver.py configuration files.

If you do not have an old Archiver.pl configuration file, you will need to create one from scratch.
First you will want to use the "print_params" argument to create a default configuration file for GlobusArchiver.py   

ConfigMaster treats your configuration file like a python module, and python requires no periods in the configuration name (except the .py), so **please use underscore or dash as separators in your configuration name.**

```
GlobusArchiver.py --print_params > GlobusArchiver_my_project.py
```

Now edit your configuration file.  You will likely need to edit the archive-items dictionary.

Finally run GlobusArchiver.py with your configuration file.  The first time you run GlobusArchiver.py, I recommmend you run interactively from the command line, and redirect the log to a file.  This will help keep debug and status message from obscuring prompts for authentication.

```
GlobusArchiver.py -c GlobusArchiver_my_project.py -l MyArchive.log -d DEBUG
```

You will probably get prompted to authenticate your globus account.  If you have not already activated the Campaign Store endpoint, you will also get prompted for that.

## The GlobusArchiver.py configuration file

GlobusArchiver.py is self-documenting.  Running --print_params will get you the latest version of the configuration file. 
The configuration file has comments to explain how GlobusArchiver works.  Here is the output of GlobusArchiver.py --print_params as of October 10, 2019:

```python
$ ./GlobusArchiver.py --print_params
#!/usr/bin/env python


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
fromEmail = emailAddresses[0]

# Format of email subject line. Can refer to errors, archiveDate, configFile, and host
#  notated in curly braces.
emailSubjectFormat = "{errors} with GlobusArchiver on {host} - {configFile} - {archiveDate}"

# format of date timestamp in email subject. This format will be used to substitute
# {archiveDate} in the emailSubjectFormat
emailSubjectDateFormat = "%Y/%m/%d"


#####################################
##  AUTHENTICATION          
#####################################

# You can define the endpoint directly  
# This default value is the NCAR CampaignStore 
# the value was obtained by running:
# $ globus endpoint search 'NCAR' --filter-owner-id 'ncar@globusid.org' | grep Campaign | cut -f1 -d' ' 


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
```

# Running GlobusArchiver.py from crontab
You can run GlobusArchiver.py from cron.   I use a simple script (found in the helper subdir) [run_GlobusArchiver.sh](https://github.com/NCAR/GlobusArchiver/blob/master/helper/start_GCP.sh).  You can call it from cron like this:
```
30 1 * * * run_GlobusArchiver.sh /home/prestop/archiverConfs/GA_CONF-hrrr-ak.py | /rap/bin/LogFilter -d ~/logs -p GlobusArchiver -i hrrr-ak
```
NOTE: This pipe only sends stdout to LogFilter.  Stderr will not get redirected, so make sure you have your MAILTO set correctly in your crontab.


# Troubleshooting
## Syntax Error (python version problem)
If you are using a version of python prior to 3.6, you will get a syntax error when you try to run.  Something like this:

```
home/lisag/git/GlobusArchiver/GlobusArchiver.py --config /home/lisag/archiving_config/old_config_files/Globus_Archiver_CONVWX_HOST_1directory_that_works.py  -d VERBOSE -l /home/lisag/logs/20191014_1_directory_test.log
  File "/home/lisag/git/GlobusArchiver/GlobusArchiver.py", line 50
    print(f"{os.path.basename(__file__)} needs ConfigMaster to run.")
````

This is because python can't parse the f-string.  You need to make sure that the python in your path is version >= 3.6.

