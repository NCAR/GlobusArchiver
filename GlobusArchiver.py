#!/usr/bin/env python
'''
GlobusArchiver.py helps users archive data to the Campaign Store (and other Globus Endpoints)
'''

import sys
if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3.6 or later")
if sys.version_info[0] == 3 and sys.version_info[1] < 6:
    raise Exception("Must be using Python 3.6 or later")

import main_globus_archiver

if __name__ == "__main__":
    main_globus_archiver.main()
