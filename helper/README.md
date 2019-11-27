# Archiver2GA.py

Simple helper script to convert Archiver.pl config files to GlobusArchiver.py config files.  Translates source, dir, expected file num, expected file size, cdDirTar, tarFileName, and more from XML to python syntax and swaps DATEXXX for % date formatting.

This is almost a turnkey solution.   It might be incomplete in areas, but should get you 90%+ of the way there.

Usage:
			
./Archiver2GA.py old_config.conf [ral_program] > new_config.py

ral_program is used to replace /RAPDMG in destinations

