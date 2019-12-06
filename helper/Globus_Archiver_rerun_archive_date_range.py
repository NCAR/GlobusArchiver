#!/usr/bin/env python

# *=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*
# ** Copyright UCAR (c) 1992 - 2019
# ** University Corporation for Atmospheric Research(UCAR)
# ** National Center for Atmospheric Research(NCAR)
# ** Research Applications Program(RAP)
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
# ** All rights reserved. Licenced use only.
# ** Do not copy or distribute without authorization.
# *=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*

import os, sys
import string
import time
import calendar
from optparse import OptionParser

def gen_date_list(begin_date, end_date):
    """Generates a list of dates of the form yyyymmdd from a being date to end date
    Inputs:
      begin_date -- such as "20070101"
      end_date -- such as "20070103"
    Returns:
      date_list -- such as ["20070101","20070102","20070103"]
    """
    begin_tm = time.strptime(begin_date, "%Y%m%d")
    end_tm = time.strptime(end_date, "%Y%m%d")
    begin_tv = calendar.timegm(begin_tm)
    end_tv = calendar.timegm(end_tm)
    date_list = []
    for tv in range(begin_tv, end_tv+86400, 86400):
        date_list.append(time.strftime("%Y%m%d", time.gmtime(tv)))
    return date_list                         


def main():
    
    usage_str = " %prog begin_date end_date \n\tNote: begin_date and end_date should be in the format YYYYMMDD"
    parser = OptionParser(usage = usage_str)

    (options, args) = parser.parse_args()

    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(2)

    begin_date = args[0]
    end_date = args[1]

    mydatelist = gen_date_list(begin_date, end_date)

    # *** Modify for where you want the log file to go ***
    log_dir = "/home/youruserid/logs/"

    for mydate in mydatelist:
        # *** Modify for your path to GlobusArchiver.py, config file/path, and LogFilter instance name.
        command = "/path/to/your/GlobusArchiver/GlobusArchiver.py --archiveDateTimeString %s --config /path/to/your/Globus_Archiver_config_file.py | LogFilter -d %s -p Globus_Archiver.py_servername_rerun" % (mydate, log_dir)
        print(command)
        ret = os.system(command)
        if ret != 1:
            print("Error sending up to Globus")

if __name__ == "__main__":

   main()
             
