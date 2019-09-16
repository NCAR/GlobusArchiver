#!/usr/bin/env python

import sys

def subDateStrings(s):
  #print(s)
  s = s.replace("DATEYYYY","%Y")
  s = s.replace("DATEJJJ","%j")
  s = s.replace("DATEMMDD","%m%d")
  s = s.replace("DATEYYYYMMDD","%Y%m%d")
  #print(s)
  return s


def main():
   
  input_file = sys.argv[1]


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
            
            

      
  with open(input_file, "r") as in_file:
    item = 0
    for line in in_file:

      if "<archiveItem>" in line:
            print(f'"item-{item}:"')
            print("{")

      if "<source>" in line:
        source = subDateStrings(line.replace("<source>","").replace("</source>","")).rstrip()
        print(f'"source": "{source}"')

      if "<destination>" in line:
        destination = subDateStrings(line.replace("<destination>","").replace("</destination>","")).rstrip()
        print(f'"destination": "{destination}"')

      if "<cdDirTar>" in line:
        cdDirTar = subDateStrings(line.replace("<cdDirTar>","").replace("</cdDirTar>","")).rstrip()
        print(f'"cdDirTar": "{cdDirTar}"')

      if "<expectedNumFiles>" in line:
        expectedNumFiles = line.replace("<expectedNumFiles>","").replace("</expectedNumFiles>","").rstrip()
        print(f'"expectedNumFiles": {expectedNumFiles}')

      if "<expectedFileSize>" in line:
        expectedFileSize = line.replace("<expectedFileSize>","").replace("</expectedFileSize>","").rstrip()
        print(f'"expectedFileSize": {expectedFileSize}')


       
        

      if "</archiveItem>" in line:
            print("}")
            item += 1

      
            
          
    
        
if __name__ == "__main__":
    main()

                                                                                                                
