#!/usr/bin/env python

import sys
import os
import re
from subprocess import Popen, PIPE

def subDateStrings(s):
  #print(s)
  s = s.replace("DATEYYYYMMDD","%Y%m%d")
  s = s.replace("DATEYYYY","%Y")
  s = s.replace("DATEJJJ","%j")
  s = s.replace("DATEMMDD","%m%d")
  #print(s)
  return s

def getDefaultParam():
  globus_script = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'GlobusArchiver.py')
  process = Popen([globus_script, '--print_params'], stdout=PIPE)
  (output, err) = process.communicate()
  return output.decode('utf-8')

def main():

  input_file = sys.argv[1]

  program = None
  if len(sys.argv) > 2:
    program = sys.argv[2]

  #archiveItems = {
  #  "hrrr-ak-wrfnat-data":
  #{
  #  "source": "/d1/ifigen/data/data/grib/HRRR-AK-wrfnat/%Y%m%d",
  #  "destination": "/gpfs/csfs1/ral/nral0003/RAPDMG/grib/HRRR-AAAK-wrfnat/%Y%m%d",
  #  "expectedNumFiles": 200,
  #},
  #  "hrrr-ak-wrfprs-data":
  #  {
  #    "source": "/d1/ifigen/data/data/grib/HRRR-AK-wrfprs/%Y%m%d",
  #    "destination": "/gpfs/csfs1/ral/nral0003/RAPDMG/grib/HRRR-AAAK-wrfprs/%Y%m%d",
  #    "expectedNumFiles": 200,
  #  }
  #      
  #}

  #<source>/d1/ldm/data/GOES-16/ABI/L2/FULL_DISK/VAA/DATEYYYYDATEJJJ</source>

  #          <cdDirTar>/d1/ldm/data/GOES-16/ABI/L2/FULL_DISK/VAA/DATEYYYYDATEJJJ</cdDirTar>

  #          <destination>/RAPDMG/SATELLITE/GOES16/ABI/L2/FULL_DISK/DATEYYYY/DATEYYYYDATEJJJ/</destination>

  #          <tarFilename>OR_ABI-L2-FULL_DISK.VAA.DATEYYYYDATEJJJ.tar</tarFilename>

  defaultParam = getDefaultParam()

  output = ''
  indent = 4

  with open(input_file, "r") as in_file:
    # item counter
    item = 0
    # keep track if we are inside an archiveItem
    inItem = False
    # if doZip is set for all items, set it for each unless that item has doZip = false
    doZipAll = False
    # get email address
    verificationEmail = None

    for line in in_file:

      # replace /RAPDMG with the new path to the RAPDMG area
      if program and '/RAPDMG/projects' in line:
        line = line.replace('/RAPDMG/projects', f'/gpfs/csfs1/ral/{program}')

      # get email address
      if "<verificationEmail>" in line:
        verificationEmail = line.replace('<verificationEmail>', '').replace('</verificationEmail>', '').rstrip()

      if "<archiveItem>" in line:
            output += f'"item-{item}":\n'
            output += ' ' * indent + "{\n"
            inItem = True
            # keep track if doZip was set in this archiveItem so we know to override
            # it with global doZip or not
            doZipIsSet = False

      if "<source>" in line:
        source = subDateStrings(line.replace("<source>","").replace("</source>","")).rstrip()
        output += ' ' * indent + f'"source": "{source}",\n'

      if "<destination>" in line:
        destination = subDateStrings(line.replace("<destination>","").replace("</destination>","")).rstrip()
        output += ' ' * indent + f'"destination": "{destination}",\n'

      if "<tarFilename>" in line:
        tarFilename = subDateStrings(line.replace("<tarFilename>","").replace("</tarFilename>","")).rstrip()
        output += ' ' * indent + f'"tarFileName": "{tarFilename}",\n'

      if "<cdDirTar>" in line:
        cdDirTar = subDateStrings(line.replace("<cdDirTar>","").replace("</cdDirTar>","")).rstrip()
        output += ' ' * indent + f'"cdDirTar": "{cdDirTar}",\n'

      if "<expectedNumFiles>" in line:
        expectedNumFiles = line.replace("<expectedNumFiles>","").replace("</expectedNumFiles>","").rstrip()
        output += ' ' * indent + f'"expectedNumFiles": {expectedNumFiles},\n'

      if "<expectedFileSize>" in line:
        expectedFileSize = line.replace("<expectedFileSize>","").replace("</expectedFileSize>","").rstrip()
        output += ' ' * indent + f'"expectedFileSize": {expectedFileSize},\n'

      if "<doZip>" in line:
        doZip = line.replace("<doZip>","").replace("</doZip>","").rstrip()
        doZip = False if doZip.lower() == 'false' else True

        # if outside archiveItem, this line is global doZip
        if not inItem:
          doZipAll = doZip
        else:
          output += ' ' * indent + f'"doZip": {doZip},\n'
          doZipIsSet = True

      if "</archiveItem>" in line:
            # if doZip was not set in this item but it was set to for all, set doZip to global doZip
            if not doZipIsSet and doZipAll:
              output += ' ' * indent + f'"doZip": {doZipAll},\n'

            output += ' ' * indent + "},\n"
            item += 1
            # reset booleans that pertain to a given archiveItem
            inItem = False
            doZipIsSet = False

  # replace default values for archiveItems with converted items from input file
  match = re.match(r'.*archiveItems\s=\s\{(.*)\}\n.*', defaultParam, re.DOTALL)
  if not match:
    print('NOTE: Could not parse default param file. Output is only archiveItems contents')
    print(output)
    exit(0)

  defaultParam = defaultParam.replace(match.group(1), '\n'+output)

  # replace emailAddresses line if verificationEmail was found
  if verificationEmail is not None:
    match = re.match(r'.*emailAddresses\s=\s\[([^]]*)\].*', defaultParam, re.DOTALL)
    if match:
      users = verificationEmail.split(',')
      email_list = []
      for user in users:
        (username, domain) = user.strip().split('@')
        email_list.append(f'("{user}", "{username}", "{domain}")')
      defaultParam = defaultParam.replace(match.group(1), ','.join(email_list))

  print(defaultParam)

if __name__ == "__main__":
    main()

                                                                                                                
