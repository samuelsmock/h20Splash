## Code that can handle multiple time profiles in a given day
## and will look up relavant values from pyscadea outputs if available

# note you must manually match the heat profile and pyscada path.



import pandas as pd
import numpy as np
import matplotlib.pyplot as plt  # For plotting
from datetime import datetime, timedelta
import os
import pprint as pp
from helperFunctions import innerTempEstimatorFromKnowns, innerTempEstimatorFromMaterials, \
    calculate_lmtd, preProcessProfile, preProcessPyscada
    
heatProfile_path =  "G:/My Drive/h2oSplash/Messdaten/Wärmekamera/xlsProfiles/14_02_24.xls"
pyscada_path = 'g:\My Drive\h2oSplash\Measurements\SUBS_measurement_data_2024_02_14_0000_2024_02_14_2359_daily_export_1_AbduFulful_Versuche.h5'


#  careful with this. timeAdjustPyscada seems to be just a daylight savings thing, the other
#  is maybe a constant offset from someone who first turned it on at 2:18 pm and it set to noon
timeAdjustHeatProfile = timedelta(hours=-2, minutes = -18)
timeAdjustPyscada = timedelta(hours=1)

heatProfile = preProcessProfile(heatProfile_path, timeAdjustHeatProfile)  
pyscada = preProcessPyscada(pyscada_path, heatProfile_path, timeAdjustPyscada) # currently needs both paths for date time

# currently the heat profile has columnms with date times (corrected to real local Berlin Time)
# as well as pixel samples with black body temperatures. here we try mapping these temperatures to the working 
# fluid temperature behind the plate using our helper functions

# see helperFunctions.py for more detailed usage innerTempEstimatorFromMaterials(T_IR, thermalConductivityWperMK, thicknessM)

#print ('heatProfile before ', heatProfile.head(20))



#print('heatProfile after', heatProfile.head(20))


#takes a series of heat profiles and pyscada data for the same day and creates a dictionary with times as keys and heat transfer coefficient
# lists as values. the lists are of average htx and zero indexed like so [top row, row 1-2, row 3-4, row 5-6, row 7-8, row 9-10, row 11-12, row 13-14]
# there is an option to apply a transform function to the IR profile which should take as an input the outside IR temp and return
# an estimate for the working fluid temperature

def rowHeatTransferAsDict(heatProfile, pyscada, transformFunction = None):

    # if we want to apply a transormation on the IR temeratures do it now
    # this could be for instance innerTempEstimatorFromMaterials()
    if(transformFunction):
        heatProfile = heatProfile.applymap(lambda cell: transformFunction(cell))
    #first get a list of the times at which a heat photo was taken
    datetime_columns = [col for col in heatProfile.columns if isinstance(col, pd.Timestamp)]
    rowPixelDist = int(len(heatProfile)/6)
    outputDict = {}

    #may want to change to in datetime_columns later
    for pictureTime in heatProfile.columns:
        heatXferCoeffListU = []
        heatXferRateListQ = []
        sampleList = []
        #first lookup relevant values from pyscada, outputs as a data dictionary with the time and the relevant pyscada values
        def lookupValues(target_datetime):
            # Ensure 'Time' column is in datetime format
            pyscada['time'] = pd.to_datetime(pyscada['time'])

            # Find the row with the closest time to the target datetime
            closest_time_idx = (pyscada['time'] - target_datetime).abs().idxmin()

            result_dict = {
                'Closest_Time': pyscada.loc[closest_time_idx, 'time'],  # Optionally include the closest time
                'T_ERa': pyscada.loc[closest_time_idx, 'T_ERa'],
                't_0Ei': pyscada.loc[closest_time_idx, 't_0Ei'],
                't_0Eo': pyscada.loc[closest_time_idx, 't_0Eo'],
                'V_0Ex_1': pyscada.loc[closest_time_idx, 'V_0Ex_1'],
                'Q_0Ex_1': pyscada.loc[closest_time_idx, 'Q_0Ex_1']
            }
            
            printableDict = ({k: v.item() if isinstance(v, (np.generic,)) else v for k, v in result_dict.items()})
            #print(printableDict)
            # Return the dictionary
            return result_dict
            # Print or save the variables as needed
            # first look up pyscada data

        pyscadaValues = lookupValues(pictureTime) # the pyscada values for this precise moment in time

        # only perform calculations if the machine is running ie V_OEx_1 > 1
        if pyscadaValues['V_0Ex_1'] < 1:
            continue
        
        # certain aspects of this loop like areas and distances are hardcoded
        for i in range(0, 8):
            #rowArea = 0
            if i == 0:
                rowArea = 0.53
                tempIn = heatProfile.iloc[0][pictureTime]
                tempOut = pyscadaValues['t_0Eo'] # there is no clear view to the ouput, which is whz we take an actual reading. this can also be used to do some interiopr exterior calibration later
            if i < 6 and i > 0:
                rowArea = 1.06
                tempIn = heatProfile.iloc[(rowPixelDist * i)][pictureTime] #backing up by one pixel to acount for 0 index
                tempOut = heatProfile.iloc[(rowPixelDist * (i-1)) ][pictureTime]
            if i == 6:                                                  # requires a special case bc of 0 index problems
                tempIn = tempOut = heatProfile.iloc[-1][pictureTime]
                tempOut = heatProfile.iloc[(rowPixelDist * (i-1)) ][pictureTime]
            if i == 7:
                tempIn = pyscadaValues['t_0Ei']
                tempOut = heatProfile.iloc[-1][pictureTime]
                rowArea = 0.97

            # Correct precedence in LMTD calculation
            LMTD = calculate_lmtd(tempIn,tempOut, pyscadaValues['T_ERa'], pyscadaValues['T_ERa'])
            heatTransferQ = pyscadaValues['V_0Ex_1'] * (1000 / 3600) * 4.186 * (tempIn - tempOut)
            heatXferCoeff = heatTransferQ / (LMTD * rowArea)

            sampleList.append([tempIn, tempOut])
            heatXferCoeffListU.append(heatXferCoeff)
            heatXferRateListQ.append(heatTransferQ)

        weights = [0.5,1,1,1,1,1,1,0.9] # weights to average based on each groups surface area
        bundleAverageCalc = sum(x * w for x, w in zip(heatXferCoeffListU, weights)) / sum(weights)
        
        heatXferCoeffFromMacros = pyscadaValues['Q_0Ex_1'] / (calculate_lmtd(pyscadaValues['t_0Ei'], pyscadaValues['t_0Eo'], pyscadaValues['T_ERa'], pyscadaValues['T_ERa']) * 7.9) #7.9 is hardcoded total area
        
        outputDict[pictureTime] = {'Heat Transfer Coefficient List U': heatXferCoeffListU,
                                   'Calculated Average U across the Bundle': bundleAverageCalc,
                                   'Heat Transfer Coefficient U from Macros': heatXferCoeffFromMacros,
                                   'Operation Details': pyscadaValues,
                                   'Heat Transfer Rate Q By Row': heatXferRateListQ,
                                   'Temperature Samples for each row [in, out]:': sampleList}

    # Function to convert types and round floats
    def convert_types(obj):
        if isinstance(obj, dict):
            return {k: convert_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_types(i) for i in obj]
        elif isinstance(obj, np.generic):
            return round(obj.item(), 2) if isinstance(obj.item(), float) else obj.item()  # Convert NumPy scalar to native Python type and round if float
        elif isinstance(obj, float):
            return round(obj, 2)  # Round floats to 2 decimal places
        return obj

    

    # Convert NumPy data types to native Python types and round floats
    outputDict = convert_types(outputDict)
 

    # Pretty-print to check the result
    pp.pprint(outputDict)
    
    return outputDict
        

output = rowHeatTransferAsDict(heatProfile, pyscada)


# Strip the file name without the extension from the path
output_file_name = os.path.splitext(os.path.basename(heatProfile_path))[0] + ".txt"

# Specify the folder where you want to save the file
folder = "G:\My Drive\h2oSplash\IRCamera\Analysis_By_Row_Picture_SS"

# Ensure the folder exists
if not os.path.exists(folder):
    os.makedirs(folder)
file_name = output_file_name

# Full file path
file_path = os.path.join(folder, output_file_name)

# Save the dictionary to the text file
with open(file_path, 'w') as file:
    pp.pprint(output, stream=file)
