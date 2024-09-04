## Code that can handle multiple time profiles in a given day
## and will look up relavant values from pyscadea outputs if available



import pandas as pd
import numpy as np
import matplotlib.pyplot as plt  # For plotting
from datetime import datetime, timedelta
import os
import pprint as pp
from helperFunctions import innerTempEstimatorFromKnowns, innerTempEstimatorFromMaterials, \
    calculate_lmtd, preProcessProfile, preProcessPyscada
    
heatProfile_path =  "G:/My Drive/h2oSplash/Messdaten/Wärmekamera/xlsProfiles/15_02_24.xls"
pyscada_path = 'g:\My Drive\h2oSplash\Measurements\SUBS_measurement_data_2024_02_15_0000_2024_02_15_2359_daily_export_1_AbduFulful_Versuche.h5'

#  careful with this. timeAdjustPyscada seems to be just a daylight savings thing, the other
#  is maybe a constant offset from someone who first turned it on at 2:18pm
timeAdjustHeatProfile = timedelta(hours=-2, minutes = -18)
timeAdjustPyscada = timedelta(hours=1)

heatProfile = preProcessProfile(heatProfile_path, timeAdjustHeatProfile)  
pyscada = preProcessPyscada(pyscada_path, timeAdjustPyscada)

#takes a series of heat profiles and pyscada data for the same day and creates a dictionary with times as keys and heat transfer coefficient
# lists as values. the lists are of average htx and zero indexed like so [top row, row 1-2, row 3-4, row 5-6, row 7-8, row 9-10, row 11-12, row 13-14]
def rowHeatTransferAsDict(heatProfile, pyscada):
    #first get a list of the times at which a heat photo was taken
    datetime_columns = [col for col in heatProfile.columns if isinstance(col, pd.Timestamp)]
    rowPixelDist = int(len(heatProfile)/15)
    outputDict = {}

    #may want to change to in datetime_columns later
    for pictureTime in heatProfile.columns:
        heatXferCoeffListU = []
        heatXferRateListQ = []
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
        
        # certain aspects of this like areas and distances are hardcoded
        for i in range(0, 8):
            #rowArea = 0
            if i == 0:
                rowArea = 0.53
                tempIn = heatProfile.iloc[rowPixelDist][pictureTime]
                tempOut = pyscadaValues['t_0Eo'] # there is no clear view to the ouput, which is whz we take an actual reading. this can also be used to do some interiopr exterior calibration later
            if i < 7 and i > 0:
                rowArea = 1.06
                tempIn = heatProfile.iloc[int(2 * i * rowPixelDist) + rowPixelDist][pictureTime]
                tempOut = heatProfile.iloc[int(2 * i * rowPixelDist) - rowPixelDist][pictureTime]
            if i == 7:
                tempIn = pyscadaValues['t_0Ei']
                tempOut = heatProfile.iloc[int(2 * i * rowPixelDist) - rowPixelDist][pictureTime]
                rowArea = 0.97

            # Correct precedence in LMTD calculation
            LMTD = calculate_lmtd(tempIn,tempOut, pyscadaValues['T_ERa'], pyscadaValues['T_ERa'])
            heatTransferQ = pyscadaValues['V_0Ex_1'] * (1000 / 3600) * 4.186 * (tempIn - tempOut)
            heatXferCoeff = heatTransferQ / (LMTD * rowArea)
            heatXferCoeffListU.append(heatXferCoeff)
            heatXferRateListQ.append(heatTransferQ)

        weights = [0.5,1,1,1,1,1,1,0.9] # weights to average based on each groups surface area
        bundleAverageCalc = sum(x * w for x, w in zip(heatXferCoeffListU, weights)) / sum(weights)
        
        heatXferCoeffFromMacros = pyscadaValues['Q_0Ex_1'] / (calculate_lmtd(pyscadaValues['t_0Ei'], pyscadaValues['t_0Eo'], pyscadaValues['T_ERa'], pyscadaValues['T_ERa']) * 7.9) #7.9 is hardcoded total area
        
        outputDict[pictureTime] = {'heatTransferCoefficientListU': heatXferCoeffListU,
                                   'Calculated Average U across the Bundle': bundleAverageCalc,
                                   'Heat Transfer Coefficient U from Macros': heatXferCoeffFromMacros,
                                   'Operation Details': pyscadaValues,
                                   'Heat Transfer Rate Q By Row': heatXferRateListQ}

    # Convert NumPy data types to their native Python equivalents for easier display
    def convert_types(obj):
        if isinstance(obj, dict):
            return {k: convert_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_types(i) for i in obj]
        elif isinstance(obj, np.generic):
            return obj.item()  # Convert NumPy scalar to native Python type
        return obj
    
    outputDict = convert_types(outputDict)
    pp.pprint(outputDict)
    
    return outputDict
        
rowHeatTransferAsDict(heatProfile, pyscada)


