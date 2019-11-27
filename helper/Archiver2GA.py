#!/usr/bin/env python

import sys
import os
import re
from subprocess import Popen, PIPE

valid_programs = ['aap',
                  'hap',
                  'jntp',
                  'nral0003',
                  'nsap',
                  'wsap',
                  ]


def subDateStrings(s):
    # print(s)
    s = s.replace("DATEYYYYMMDD", "%Y%m%d")
    s = s.replace("DATEYYYY", "%Y")
    s = s.replace("DATEJJJ", "%j")
    s = s.replace("DATEMMDD", "%m%d")
    # print(s)
    return s


def getDefaultParam():
    globus_script = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'GlobusArchiver.py')
    process = Popen([globus_script, '--print_params'], stdout=PIPE)
    (output, err) = process.communicate()
    return output.decode('utf-8')


def print_usage():
        print("USAGE:")
        print("\tArchiver2GA.py input_file [ral_program]")
        print("\n\tral_program is used to replace /RAPDMG in destinations")
        print(f"\tvalid values for ral_program = {valid_programs}\n")

def main():

    if len(sys.argv) < 2:
        print_usage()        
        sys.exit(1)
    
    input_file = sys.argv[1]

    program = None
    if len(sys.argv) > 2:
        program = sys.argv[2]
        if program not in valid_programs:
            print(f"program: {program} is not valid.")
            print_usage()
            sys.exit(1)
            

    # archiveItems = {
    #  "hrrr-ak-wrfnat-data":
    # {
    #  "source": "/d1/ifigen/data/data/grib/HRRR-AK-wrfnat/%Y%m%d",
    #  "destination": "/gpfs/csfs1/ral/nral0003/RAPDMG/grib/HRRR-AAAK-wrfnat/%Y%m%d",
    #  "expectedNumFiles": 200,
    # },
    #  "hrrr-ak-wrfprs-data":
    #  {
    #    "source": "/d1/ifigen/data/data/grib/HRRR-AK-wrfprs/%Y%m%d",
    #    "destination": "/gpfs/csfs1/ral/nral0003/RAPDMG/grib/HRRR-AAAK-wrfprs/%Y%m%d",
    #    "expectedNumFiles": 200,
    #  }
    #
    # }

    # <source>/d1/ldm/data/GOES-16/ABI/L2/FULL_DISK/VAA/DATEYYYYDATEJJJ</source>

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
        # if doStaging is set for all items, set it for each unless that item has doStaging = false
        # default value in Archiver.pl was True, so set this to true unless overridden
        doStagingAll = True
        # if doZip is set for all items, set it for each unless that item has doZip = false
        # default value in Archiver.pl was True, so set this to true unless overridden
        doZipAll = True
        # if skipUnderscoreFiles is set for all items, set it for each unless that item has skipUnderscoreFiles = false
        skipUnderscoreFilesAll = False
        # same for warningLevel
        warningLevelAll = False
        # get email address
        verificationEmail = None

        tempDir = None
        
        for line in in_file:

            # replace /RAPDMG with the new path to the RAPDMG area
            if program in valid_programs:
                if '/RAPDMG/projects' in line:
                    line = line.replace('/RAPDMG/projects', f'/gpfs/csfs1/ral/{program}')
                elif '/RAPDMG' in line:
                    line = line.replace('/RAPDMG', f'/gpfs/csfs1/ral/{program}')

            # get tmp dir
            if "<tmpDir>" in line:
                tempDir = line.replace("<tmpDir>",'').replace('</tmpDir>','').rstrip()
                
            # get email address
            if "<verificationEmail>" in line:
                verificationEmail = line.replace('<verificationEmail>', '').replace('</verificationEmail>', '').rstrip()

            if "<archiveItem>" in line:
                output += f'"item-{item}":\n'
                output += ' ' * indent + "{\n"
                inItem = True
                # keep track if doZip and skipUnderscoreFiles was set in this archiveItem so we know to override
                # it with global  or not
                doStagingIsSet = False
                doZipIsSet = False
                skipUnderscoreFilesIsSet = False
                warningLevelIsSet = False

                # starting a new item, so set everything to None
                source = None
                destination = None
                tarFilename = None
                cdDirTar = None
                cdDir = None

            if "<source>" in line:
                source = subDateStrings(line.replace("<source>", "").replace("</source>", "")).rstrip()
                output += ' ' * indent + f'"source": "{source}",\n'

            if "<destination>" in line:
                destination = subDateStrings(line.replace("<destination>", "").replace("</destination>", "")).rstrip()
                # output += ' ' * indent + f'"destination": "{destination}",\n'

            if "<tarFilename>" in line:
                tarFilename = subDateStrings(line.replace("<tarFilename>", "").replace("</tarFilename>", "")).rstrip()
                output += ' ' * indent + f'"tarFileName": "{tarFilename}",\n'

            # cdDirTar and cdDir are aliases for the same thing, so set either
            # item to cdDirTar.    cdDir for non tar archiving is going away.
            if "<cdDirTar>" in line:
                cdDirTar = subDateStrings(line.replace("<cdDirTar>", "").replace("</cdDirTar>", "")).rstrip()
                #output += ' ' * indent + f'"cdDirTar": "{cdDirTar}",\n'

            if "<cdDir>" in line:
                cdDirTar = subDateStrings(line.replace("<cdDir>", "").replace("</cdDir>", "")).rstrip()
                #output += ' ' * indent + f'"cdDirTar": "{cdDirTar}",\n'

            if "<expectedNumFiles>" in line:
                expectedNumFiles = line.replace("<expectedNumFiles>", "").replace("</expectedNumFiles>", "").rstrip()
                output += ' ' * indent + f'"expectedNumFiles": {expectedNumFiles},\n'

            if "<expectedFileSize>" in line:
                expectedFileSize = line.replace("<expectedFileSize>", "").replace("</expectedFileSize>", "").rstrip()
                output += ' ' * indent + f'"expectedFileSize": {expectedFileSize},\n'

                # comment, dataType, and dataFormat have no effect in GlobusArchiver.py, but this information could be
                # useful to the user so we will preserve it
            if "<comment>" in line:
                comment = line.replace("<comment>", "").replace("</comment>", "").rstrip()
                output += ' ' * indent + f'"comment": "{comment}",\n'

            if "<dataType>" in line:
                dataType = line.replace("<dataType>", "").replace("</dataType>", "").rstrip()
                output += ' ' * indent + f'"dataType": "{dataType}",\n'

            if "<dataFormat>" in line:
                dataFormat = line.replace("<dataFormat>", "").replace("</dataFormat>", "").rstrip()
                output += ' ' * indent + f'"dataFormat": "{dataFormat}",\n'

            if "<warningLevel>" in line:
                warningLevel = line.replace("<warningLevel>", "").replace("</warningLevel>", "").rstrip()
                # if outside archiveItem, this line is global warningLevel
                if not inItem:
                    warningLevelAll = warningLevel
                else:
                    output += ' ' * indent + f'"warningLevel": {warningLevel},\n'
                    warningLevelIsSet = True

                
            if "<doStaging>" in line:
                doStaging = line.replace("<doStaging>", "").replace("</doStaging>", "").rstrip()
                doStaging = False if doStaging.lower() == 'false' else True

                # if outside archiveItem, this line is global doStaging
                if not inItem:
                    doStagingAll = doStaging
                else:
                    output += ' ' * indent + f'"doStaging": {doStaging},\n'
                    doStagingIsSet = True

            if "<doZip>" in line:
                doZip = line.replace("<doZip>", "").replace("</doZip>", "").rstrip()
                doZip = False if doZip.lower() == 'false' else True

                # if outside archiveItem, this line is global doZip
                if not inItem:
                    doZipAll = doZip
                else:
                    output += ' ' * indent + f'"doZip": {doZip},\n'
                    doZipIsSet = True

            if "<skipUnderscoreFiles>" in line:
                skipUnderscoreFiles = line.replace("<skipUnderscoreFiles>", "").replace("</skipUnderscoreFiles>",
                                                                                        "").rstrip()
                skipUnderscoreFiles = False if skipUnderscoreFiles.lower() == 'false' else True

                # if outside archiveItem, this line is global skipUnderscoreFiles
                if not inItem:
                    skipUnderscoreFilesAll = skipUnderscoreFiles
                else:
                    output += ' ' * indent + f'"skipUnderscoreFiles": {skipUnderscoreFiles},\n'
                    skipUnderscoreFilesIsSet = True

            if "</archiveItem>" in line:
                if not tarFilename:
                    if cdDirTar:
                        # last element is added to destination in GlobusArchiver, but need to put rest of the path on the destination here
                        # this is a change in functionality between Archiver.pl and GlobusArchiver.py
                        branch_and_leaf = source.replace(cdDirTar, '').lstrip(os.path.sep)
                        (branch, leaf) = os.path.split(branch_and_leaf)
                        destination = os.path.join(destination, branch)

                    #else:
                    #    leaf = os.path.basename(ii['source'].rstrip(os.path.sep))
                    #    destination = os.path.join(ii['destination'], leaf)

                # if(os.path.isfile(ii['source']):
                #   destination = os.path.join(ii['destination'], leaf)
                else: 
                    if cdDirTar:
                        output += ' ' * indent + f'"cdDirTar": "{cdDirTar}",\n'
                output += ' ' * indent + f'"destination": "{destination}",\n'
                # if doStaging was not set in this item but it was set for all, set doStaging to global doStaging
                if not doStagingIsSet and doStagingAll:
                    output += ' ' * indent + f'"doStaging": {doStagingAll},\n'
                    
                # if doZip was not set in this item but it was set for all, set doZip to global doZip
                if not doZipIsSet and doZipAll:
                    output += ' ' * indent + f'"doZip": {doZipAll},\n'

                # if skipUnderscoreFiles was not set in this item but it was set to for all, set to global
                if not skipUnderscoreFilesIsSet and skipUnderscoreFilesAll:
                    output += ' ' * indent + f'"skipUnderscoreFiles": {skipUnderscoreFilesAll},\n'

                # same for warningLevel
                if not warningLevelIsSet and warningLevelAll:
                    output += ' ' * indent + f'"warningLevel": {warningLevelAll},\n'

                output += ' ' * indent + "},\n"
                item += 1
                # reset booleans that pertain to a given archiveItem
                inItem = False
                doStagingIsSet = False
                doZipIsSet = False
                skipUnderscoreFilesIsSet = False
                warningLevelIsSet = False

    # replace default values for archiveItems with converted items from input file
    match = re.match(r'.*archiveItems\s=\s\{(.*)\}\n.*', defaultParam, re.DOTALL)
    if not match:
        print('NOTE: Could not parse default param file. Output is only archiveItems contents')
        print(output)
        exit(0)

    defaultParam = defaultParam.replace(match.group(1), '\n' + output)

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

    #print(f"tempDir = {tempDir}")
    #print(f"defaultParams = {defaultParam}")
    if tempDir is not None:  
        match = re.search(r'tempDir\s=\s(.*)', defaultParam)#, re.DOTALL)
        #print(f"match = {match.group(1)}")
        if match:
            defaultParam = defaultParam.replace(match.group(1), f'"{tempDir}"')

        
    print(defaultParam)


if __name__ == "__main__":
    main()
