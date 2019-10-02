# Archiver2GA.py

Simple helper script to convert Archiver.pl config files to GlobusArchiver.py config files.  Translates source, dir, expected file num, expected file size, cdDirTar, and tarFileName from XML to python syntax and swaps DATEXXX for % date formatting.

This is not a turnkey solution.   It gets you started, and can be very helpful with long config files, but the user will still need to edit the file by hand.  I recommend using like this:

./Archiver2GA.py old_config.conf > new_config.py

./GlobusArchiver.py --print_params > my_config.py

then by hand copy and paste from new_config.py into my_config.py

