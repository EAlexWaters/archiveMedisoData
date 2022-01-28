# screenDICOMHeaders

This script is designed for use with DICOM data from a Mediso NanoScan micro PET/CT system.
It assumes data has been copied off the drive (not exported via a DICOM server interface)
and is structured as a single parent folder (the source folder) containing numerous subfolders,
each of which contains all the DICOM files for a single study. 

The script iterates over the subfolders, exports a parameter log listing study parameters as 
well as parameters for each individual scan, and optionally creates a .7z archive of each 
subfolder with a human-readable name.

The script is designed to be used to archive data for cold storage.
