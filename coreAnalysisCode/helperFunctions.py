# <Helper functions to be used in heatTransferMultiXLS.py
# 
# Among these functions are preprocessing tasks for xls files exported from IRBIS 3, preprocessing for
# .h5 files from Pyscada and code to take a Infrared reading and estimate the temperature on the other side of the plate
# using known internal/external pairs or the physical properties of the materials


import h5py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt  # For plotting
from datetime import datetime, timedelta
import os
import pprint as pp
from scipy.optimize import fsolve

# The idea of this function is to take a pair of known IR camera readings at the outlet-inlet elbows
# to build an estimate of the thermal conductivity of the elbow material and apply it to the plate. This assumes
# the materials are the same and currently assumes the same emissivity, which needs to be adjusted for paint etc.
# 
# thickness ratio is less than one if we assume the materials are the the same but the reference material is thinner
# As an example, our elbow is about 4mm thick galvanized steel, the plate is about 9mm thick, so the second argument would be 4/9
def innerTempEstimatorFromKnowns(T_IR):
    knownOutletPairs = [[16.7, 16.1], [21.5, 21.2]] # must be manually looked up using timeGraph and Irbis (accounting for time difference)
    thicknessRatio= 4/9
    thicknessElbow = 0.04
    #convert to kelvin
    T_IR = T_IR + 273.15
    knownOutletPairs = [[value + 273.15 for value in sublist] for sublist in knownOutletPairs]


    kOverXSum = 0
    epsilonSigma = 0.95 * 5.67e-8
    T_amb = 20 + 273.15

    # First calculate the average of known internal and external values at the chilled water outlet
    for pair in knownOutletPairs:
        kOverXSum += (epsilonSigma * (T_amb**4 - pair[0]**4)) / (pair[0] - pair[1])
       
    kOverXAvg = kOverXSum / len(knownOutletPairs)
    #print ('k is about equal to ', kOverXAvg* thicknessElbow)

    # Define the heat balance equation to solve
    def heat_balance(T_0Eo):
        return kOverXAvg * thicknessRatio * (T_IR - T_0Eo) - epsilonSigma * (T_amb**4 - T_IR**4)

    # Make an initial guess
    T_0EoGuess = T_IR * 0.95

    # Solve and return the result in celsius
    return fsolve(heat_balance, T_0EoGuess)[0] - 273.15

# the idea of this function is to estimate temperatures based on values for emissivity, convective heat transfer coefficient,
# and thermal conductivity from the literature, this needs considerable work to get sensical answers 
def innerTempEstimatorFromMaterials(T_IR):

    thermalConductivityWperMK = 50
    thicknessM = 0.009
    #convert to kelvin
    T_IR = T_IR + 273.15
    
    epsilonSigma = 0.95 * 5.67e-8 #about 95% emissivity

    T_amb = 20 + 273.15

    # Define the heat balance equation to solve
    def heat_balance(T_0Eo):
        return  (thermalConductivityWperMK/thicknessM) * (T_IR - T_0Eo) - epsilonSigma * (T_amb**4 - T_IR**4)

    # Make an initial guess
    T_0EoGuess = T_IR * 0.95

    # Solve and return the result in celsius
    return fsolve(heat_balance, T_0EoGuess)[0] - 273.15

# simply a totally adhoc way of getting
def innerTempFromHandWaving(T_IR):
    T_IR = T_IR +273
    T_IR_1, T_h20_1 = 16.8 +273.1, 15.4+273.1  # First known point
    T_IR_2, T_h20_2 = 21.7+273.1, 20.1+273.1  # Second known point
    # T_IR = a * y^4 + y + b
    # Rearrange to solve for y
    # a * y^4 + y + b - T_IR = 0
    # This is a nonlinear equation that needs to be solved numerically

    def find_a_b(T_IR_1, T_h20_1, T_IR_2, T_h20_2):
        # Set up the system of linear equations
        # T_IR_1 = a * T_h20_1^4 + T_h20_1 + b
        # T_IR_2 = a * T_h20_2^4 + T_h20_2 + b
        
        # Coefficients matrix for the system [ [T_h20_1^4, 1], [T_h20_2^4, 1] ]
        A = np.array([[T_h20_1**4, 1], [T_h20_2**4, 1]])
        
        # Right-hand side vector [T_IR_1 - T_h20_1, T_IR_2 - T_h20_2]
        B = np.array([T_IR_1 - T_h20_1, T_IR_2 - T_h20_2])
        
        # Solve for a and b
        a, b = np.linalg.solve(A, B)
        
        return a, b

    a, b = find_a_b(T_IR_1, T_h20_1, T_IR_2, T_h20_2)

    def equation(y):
        return a * y**4 + y + b - T_IR
    
    # Use fsolve to find y for the given T_IR
    T_h20_initial_guess = 283  # A reasonable initial guess
    T_h20_solution = fsolve(equation,  T_h20_initial_guess)
    
    return T_h20_solution[0] -273



def calculate_lmtd(temp_in_hot, temp_out_hot, temp_in_cold, temp_out_cold):
    """
    Calculate the Log Mean Temperature Difference (LMTD).
    
    Parameters:
    temp_in_hot (float): Hot fluid inlet temperature (°C or K)
    temp_out_hot (float): Hot fluid outlet temperature (°C or K)
    temp_in_cold (float): Cold fluid inlet temperature (°C or K)
    temp_out_cold (float): Cold fluid outlet temperature (°C or K)
    
    Returns:
    float: The LMTD in the same unit as the input temperatures.
    """
    delta_T1 = temp_in_hot - temp_out_cold
    delta_T2 = temp_out_hot - temp_in_cold
    
    # Handle cases where delta_T1 equals delta_T2 to avoid division by zero
    if delta_T1 == delta_T2:
        return delta_T1
    
    lmtd = (delta_T1 - delta_T2) / np.log(delta_T1 / delta_T2)
    
    return lmtd

def preProcessProfile(df_path, timeAdjust):
    # Extract the date from the file name
    file_name = os.path.basename(df_path)
    date_str = file_name.split('.')[0]  # Assuming file name is in the form dd.mm.yy.xls
    print(date_str)
    date_format = pd.to_datetime(date_str, format='%d_%m_%y')
    
    # Load the data into a DataFrame
    df = pd.read_excel(df_path, header=1)

    # Drop the 'Pixel' column
    df = df.drop(columns=['Pixel'])

    # Set 'Time' as the index and transpose the DataFrame
    df_pivot = df.set_index('Time').T

    # Drop the 'Milliseconds' row
    df_pivot = df_pivot.drop(index='Milliseconds')

    # Rename the first column as 'Index'
    df_pivot.columns.name = 'Index'

    # Convert comma to period and strings to floats in the DataFrame
    df_pivot = df_pivot.map(lambda x: float(str(x).replace(',', '.')))

    # Combine the date with time to create datetime objects for column names
    df_pivot.columns = [pd.to_datetime(f"{date_format.date()} {time_str}") for time_str in df_pivot.columns]
    
    
    #adjust by the time correction if it is given
    if(timeAdjust):
        newColumns =[]
        for col in df_pivot.columns:
            if isinstance(col, pd.Timestamp):  # Check if the column name is a datetime object
                newColumns.append(col + timeAdjust)
            else:
                newColumns.append(col) 
        df_pivot.columns = newColumns

    # Identify the first time column (the first column after 'Index')
    first_time_column = df_pivot.columns[0]

    # Start here:
    min_index = df_pivot[first_time_column].idxmin()
    df_trimmed = df_trimmed = df_pivot.loc[min_index:]
    max_index = df_trimmed[first_time_column].idxmax()
    
    # Keep all rows between the minimum and maximum value's index
    df_trimmed = df_trimmed.iloc[:max_index]

    #df_trimmed.plot()
    plt.show()
    # Drop any rows that have been fully filtered out (all NaNs)
    df_trimmed = df_trimmed.dropna(how='all')

    return df_trimmed

# takes a folder with pyscada data and a specific heatProfile_path and attempts to find 
# the data matching that day. If not it returns null
def preProcessPyscada(df_path, heatProfile_path, timeAdjust):

    with h5py.File(df_path, 'r') as file:
        time_data = file['/time'][:]
        data_dict = {key: file[key][:] for key in file.keys()}
            
    # Convert floating point time to time of day in seconds
    time_of_day_seconds = (time_data - time_data[0]) * 24 * 3600
    
    #note we are using date information from the profile data, this always takes precedent and is used to look up pyscada data
    #rather than the other way around
    file_name = os.path.basename(heatProfile_path)
    date_str = file_name.split('.')[0]  # Get the '14_02_24' part

    # Split into day, month, year and convert the year to full year format
    day, month, year = date_str.split('_')
    full_year = f"20{year}"  # Convert '24' to '2024'

    # Create the datetime object using the extracted date
    start_datetime = datetime(int(full_year), int(month), int(day))

    time_datetimes = [start_datetime + timedelta(seconds=sec) for sec in time_of_day_seconds]

    # Create a DataFrame with all variables
    data = pd.DataFrame(data_dict)
    data['time'] = time_datetimes   
    if (timeAdjust):
        data['time'] = data['time'] + timeAdjust 
    return data             

print('estimate based on calibration:', innerTempEstimatorFromKnowns(16.2),
      'estimate based on materials:', innerTempEstimatorFromMaterials(16.2),
      'estimate based on hand waving', innerTempFromHandWaving(16.6)) 