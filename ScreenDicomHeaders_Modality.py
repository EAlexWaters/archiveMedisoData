# -*- coding: utf-8 -*-
"""
Created on 1/28/2022 15:21:29 2022

@author: Alex Waters
Northwestern University

This script is designed for use with DICOM data from a Mediso NanoScan micro PET/CT system.
It assumes data has been copied off the drive (not exported via a DICOM server interface)
and is structured as a single parent folder (the source folder) containing numerous subfolders,
each of which contains all the DICOM files for a single study. 

The script iterates over the subfolders, exports a parameter log listing study parameters as 
well as parameters for each individual scan, and optionally creates a .7z archive of each 
subfolder with a human-readable name.

The script is designed to be used to archive data for cold storage.

Inputs: 
    src_dir:  directory containing subdirectories of unsorted DICOM files
    dest_dir: output location for parameter files and .7z archives
    create_zips: set to True if you wish to create .7z archives and False to create only parameter files

"""


import os
import csv
import pydicom  # pydicom is using the gdcm package for decompression
import subprocess # needed to run 7-zip

# path to 7z executable
exe_7z = "C:\\Program Files\\7-Zip\\7z.exe"

def readCTParamsAndCreateArchive(src_dir, dest_dir, create_zips = True):

    # get list of study directories and iterate over them
    study_dirs = os.listdir(src_dir)
    for this_dir in study_dirs:
        # list dicom files in the current study this_directory and capture patient specific information from the first file
        files = os.listdir(os.path.join(src, this_dir))
        print("processing directory: " + this_dir)
        dcm_1 = os.path.join(src, this_dir, files[0])
        first_dcm = pydicom.dcmread(
            dcm_1, force=True, stop_before_pixels=True)
        patientName = first_dcm.get("PatientName").family_name
        project = first_dcm[0x0009, 0x10d5].value
        acq_date = str(first_dcm.get("SeriesDate", "NA"))
        acq_time = str(first_dcm.get("SeriesTime", "NA"))
        seriesNum = first_dcm.get("SeriesNumber", "NA")

        filename = "_".join([patientName, project])
        filepath = os.path.join(dest,filename)
        print("Outputting to: " + filename + '.csv')
        refPhys = first_dcm.get(
            "ReferringPhysicianName").family_comma_given()
        operator = first_dcm.get(
            "PerformingPhysicianName").family_comma_given()
        project = first_dcm[0x0009, 0x10d5].value
        species = first_dcm.get("PatientSpeciesDescription", "NA")
        sex = first_dcm.get("PatientSex", "NA")
        breed = first_dcm.get("PatientBreedDescription", "NA")
        comments = first_dcm.get("PatientComments", "NA")


        # Example.csv gets created in the current working directory
        with open(filepath+'.csv', 'w', newline='') as csvfile:
            # for each study, initialize a csv file to hold scan parameters.
            scan_writer = csv.writer(csvfile)

            # At the beginning of the file, record patient information
            scan_headers = ('Patient Name', 'PI', 'Operator',
                            'Project', 'Species', 'Sex', 'Breed', 'Comments')
            first_row = (patientName, refPhys, operator,
                         project, species, sex, breed, comments)
            scan_writer.writerow(scan_headers)
            scan_writer.writerow(first_row)
            scan_writer.writerow(("",))

            # write new headers for the table of scan parameters
            scan_headers = ('Series Number', 'Acquisition Date', 'Acquisition Time', 'Modality', 'Image Type', 'kVp', 'Current', 'Pixel Spacing',
                            'Slice Thickness', 'Dist. Source to detector', 'Dist. Source to object', 'Zoom factor','Rotations', 'Rows','Columns', 'Radionuclide', 'Radiopharmaceutical', 'Inj. Dose', 'Meas. Time', 'Inj. time', 'Applied activity (in Bq?)','Protocol Name', 'Series Description', 'First filename')
            scan_writer.writerow(scan_headers)

            # the first scan in any study should be CT.
            study_modality = 'CT'
            
            # iterate over all dicom files in the study
            for file in files:
                next_dcm = pydicom.dcmread(os.path.join(
                    src, this_dir, file), force=True, stop_before_pixels=True)

                

                # if the current dicom file has an instance number of 0 (single frame) or 1 (first in a series)
                # then it is the start of a new scan. capture its scan parameters and write them to the file.
                instance = next_dcm.get("InstanceNumber", "NA")
                if (instance == '0') or (instance == '1'):
                    #print(next_dcm)
                    seriesNum = next_dcm.get("SeriesNumber", "")
                    modality = next_dcm.get("Modality", "")
                    acq_date = str(next_dcm.get("SeriesDate", ""))
                    acq_time = str(next_dcm.get("SeriesTime", ""))
                    
                    pix_space = str(next_dcm.get("PixelSpacing", ""))
                    protocolName = str(next_dcm.get("ProtocolName", ""))
                    seriesDesc = str(next_dcm.get("SeriesDescription", ""))
                    rows = next_dcm[0x0028, 0x0010].value
                    cols = next_dcm[0x0028, 0x0011].value

                    # Set dummy values for variables that are only defined for some types of scans
                    current = ''
                    dist_src_det = ''
                    dist_src_pt = ''
                    zoom = ''
                    rotations = ''
                    slice_thk = ''
                    kvp = ''
                    radionuclide = ''
                    radiopharm = ''
                    inj_dose=''
                    inj_time=''
                    meas_time=''
                    appl_activity=''
                    
                    imageType = next_dcm.get("ImageType", "NA")

                    if 'PT' in modality:
                        study_modality = 'PET'
                        print("Found a PET study")
                        # this is real hairy because it involves several layers of nested dicom tags
                        radionuclide = next_dcm[0x0054,0x0016][0][0x0054,0x0300][0][0x0008,0x0104].value
                        radiopharm = next_dcm[0x0054,0x0016][0][0x0054,0x0304][0][0x0008,0x0104].value
                        inj_dose=str(next_dcm[0x0054,0x0016][0][0x0009,0x10f2].value) + ' ' + str(next_dcm[0x0054,0x0016][0][0x0009,0x10fa].value)
                        inj_time=next_dcm[0x0054,0x0016][0][0x0018,0x1078].value
                        meas_time=next_dcm[0x0054,0x0016][0][0x0009,0x10ee].value
                        appl_activity=next_dcm[0x0054,0x0016][0][0x0018,0x1074].value

                    else:
                        if 'LOCALIZER' not in imageType:
                            dist_src_det = next_dcm[0x0018, 0x1110].value
                            dist_src_pt = next_dcm[0x0018, 0x1111].value
                            

                        if 'PROJECTION' in imageType:
                            current = next_dcm[0x0018, 0x9330].value
                            rotations = next_dcm[0x0009, 0x1037].value
                            slice_thk = str(next_dcm.get("SliceThickness", ""))
                            zoom = int(dist_src_det/dist_src_pt)
                            
                        if 'AXIAL' not in imageType:
                            kvp = str(next_dcm.get("KVP", ""))

                    next_scan_row = (seriesNum, acq_date, acq_time, modality, imageType[-1], kvp, current,
                                     pix_space, slice_thk, dist_src_det, dist_src_pt, zoom,rotations,rows,cols,radionuclide, radiopharm, inj_dose, meas_time, inj_time, appl_activity, protocolName, seriesDesc, file)
                    scan_writer.writerow(next_scan_row)
                
                    
        os.replace(os.path.join(dest,filename+'.csv'), os.path.join(dest,filename + '_' + study_modality+'.csv'))
        
        if create_zips:
            zip_filename = os.path.join(dest,filename + '_' + study_modality+'.7z')
            print("creating archive " + zip_filename)
            zip_command_1 = '"' + exe_7z + '"' + " a -t7z \"" + zip_filename + "\" \"" + os.path.join(src, this_dir) + "\" -mx=7"
            zip_command_2 = '"' + exe_7z + '"' + " a -t7z \"" + zip_filename + "\" \"" + os.path.join(dest,filename + '_' + study_modality+'.csv') + "\" -mx=7"
            print(zip_command_1)
            print(zip_command_2)
            subprocess.call(zip_command_1)
            subprocess.call(zip_command_2)





        
 
# user specified parameters
src = "E:\Data_current\Analysis\PETCT_Archive_Example"
dest = "E:\Data_current\Analysis\PETCT_Archive_Example_Output"



readCTParamsAndCreateArchive(src, dest, False)





# Copyright 2022 Alex Waters

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), 
# to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, 
# and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS 
# IN THE SOFTWARE.
