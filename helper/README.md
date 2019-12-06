# Archiver2GA.py

Simple helper script to convert Archiver.pl config files to GlobusArchiver.py config files.  Translates source, dir, expected file num, expected file size, cdDirTar, tarFileName, and more from XML to python syntax and swaps DATEXXX for % date formatting.

This is almost a turnkey solution.   It might be incomplete in areas, but should get you 90%+ of the way there.

Usage:
			
./Archiver2GA.py old_config.conf [ral_program] > new_config.py

ral_program is used to replace /RAPDMG in destinations

# Globus_Archiver_rerun_archive_date_range.py

Simple wrapper script to execute Globus_Archiver.py over a range of dates.  Useful for filling in gaps in an archive
when the automated process fails for a period of time.  Needs a little customization for each user.
