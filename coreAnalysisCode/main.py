#
#This code brings together the core functionality of helperFunctions.py and heatTeransferMultiXLS
# to process multiple days (and everz piscture in every day all at once) Be careful to properly list input and outputs
#  
import pandas as pd
import numpy as np
import os
import pprint as pp
from datetime import timedelta
from helperFunctions import innerTempEstimatorFromKnowns, preProcessProfile, preProcessPyscada, calculate_lmtd, innerTempFromHandWaving
from heatTransferMultiXLS import rowHeatTransferAsDict

# Paths
heatProfile_folder = "G:/My Drive/h2oSplash/Messdaten/Wärmekamera/xlsProfiles"
pyscada_folder = "G:/My Drive/h2oSplash/Measurements"

# Output folder
output_folder = "C:/Users/Admin/Documents/python/h20Splash/results/heatTransferByRow"
temperature_samples_folder = "G:/My Drive/h2oSplash/IRCamera/1D_temperature_samples_SS"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Time adjustments
timeAdjustHeatProfile = timedelta(hours=-2, minutes=-18)
timeAdjustPyscada = timedelta(hours=1)

# Loop through all xls files in heatProfiles folder
for heatProfile_file in os.listdir(heatProfile_folder):
    if heatProfile_file.endswith(".xls"):
        # Extract date from the heat profile file name (assuming the format dd_mm_yy.xls)
        heatProfile_date = os.path.splitext(heatProfile_file)[0]  # Strip ".xls" to get the date

        # Build full path to heat profile file
        heatProfile_path = os.path.join(heatProfile_folder, heatProfile_file)

        # Try to find the corresponding pyscada .h5 file in pyscadaMeasurements folder
        pyscada_file_pattern = f"SUBS_measurement_data_20{heatProfile_date[-2:]}_{heatProfile_date[3:5]}_{heatProfile_date[:2]}_0000_20{heatProfile_date[-2:]}_{heatProfile_date[3:5]}_{heatProfile_date[:2]}_2359_daily_export_1_AbduFulful_Versuche.h5"
        pyscada_path = os.path.join(pyscada_folder, pyscada_file_pattern)

        # Check if the corresponding pyscada file exists
        if not os.path.exists(pyscada_path):
            print(f"Cannot find pyscada file for {heatProfile_date}")
            continue

        # Preprocess heat profile and pyscada data
        heatProfile = preProcessProfile(heatProfile_path, timeAdjustHeatProfile)
        pyscada = preProcessPyscada(pyscada_path, heatProfile_path, timeAdjustPyscada)

        # Calculate heat transfer coefficients and save results THIS IS WHERE TO PUT THE TRANFORM FUNCTION
        output = rowHeatTransferAsDict(heatProfile, pyscada, innerTempFromHandWaving)
        
        # make another directory with samples only
        output_samples_only = {}

        for timestamp, values in output.items():
            output_samples_only[timestamp] = values['Temperature Samples for each row [in, out]:']

        # Save output to a text file with the same date as the .xls file
        output_file_name = heatProfile_date + ".txt"
        output_sample_name = heatProfile_date+ '_sample.txt'

        file_path_samples = os.path.join(temperature_samples_folder, output_sample_name)
        file_path = os.path.join(output_folder, output_file_name)

        with open(file_path, 'w') as file:
            pp.pprint(output, stream=file)

        with open(file_path_samples, 'w') as file:
            pp.pprint(output_samples_only, stream=file)

        print(f"Processed and saved: {output_file_name}")