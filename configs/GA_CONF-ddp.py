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
tempDir = "/rapdmg2/data/tmp/"

# You may want to keep the tmp area around for debugging
cleanTemp = True

###############  EMAIL   ##################

# Deliver a report to these email addresses
# Use a list of 3-tuples  ("name", "local-part", "domain")
emailAddresses = [("prestop@rap.ucar.edu", "prestop", "rap.ucar.edu")] 

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
"item-0":
    {
    "source": "/rapdmg1/data/ddp/%Y%m%d",
    "expectedFileSize": 91000000,
    "expectedNumFiles": 865,
    "tarFileName": "%Y%m%d.ddp.tar",
    "dataFormat": "ascii",
    "comment": "weather service textual data including things like METARs,",
    "warningLevel": .7,
    "doZip": True,
    "destination": "/gpfs/csfs1/ral/nral0003/LDM/ARCHIVE/%Y/%m%d",
    },
}


