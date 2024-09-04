#code to take a Infrared reading and estimate the temperature on the other side of the plate
# using known values to calibrate at the outlet
import h5py
from scipy.optimize import fsolve

def innerTempEstimatorFromKnowns(T_IR, thicknessRatio=1):
    knownOutletPairs = [[16.2, 15.48], [15.91, 14.95], [16.02, 15.03]]
    
    #convert to kelvin
    T_IR = T_IR + 273.15
    knownOutletPairs = [[value + 273.15 for value in sublist] for sublist in knownOutletPairs]


    kOverXSum = 0
    epsilonSigma = 0.95 * 5.67e-8
    T_amb = 20 + 273.15

    # First calculate the average of known internal and external values at the chilled water outlet
    for pair in knownOutletPairs:
        kOverXSum += (epsilonSigma * (T_amb**4 - pair[0]**4)) / (pair[1] - pair[0])
       
    kOverXAvg = kOverXSum / len(knownOutletPairs)
    
    # Define the heat balance equation to solve
    def heat_balance(T_0Eo):
        return kOverXAvg * thicknessRatio * (T_0Eo - T_IR) - epsilonSigma * (T_amb**4 - T_0Eo**4)

    # Make an initial guess
    T_0EoGuess = T_IR * 0.95

    # Solve and return the result in celsius
    return fsolve(heat_balance, T_0EoGuess)[0] - 273.15

def innerTempEstimatorFromMaterials(T_IR, thermalConductivityWperMK, thicknessM):
    
    #convert to kelvin
    T_IR = T_IR + 273.15
    
    epsilonSigma = 0.95 * 5.67e-8 #about 95% emissivity
    T_amb = 20 + 273.15

    # Define the heat balance equation to solve
    def heat_balance(T_0Eo):
        return (thermalConductivityWperMK/thicknessM) * (T_0Eo - T_IR) - epsilonSigma * (T_amb**4 - T_0Eo**4)

    # Make an initial guess
    T_0EoGuess = T_IR * 0.95

    # Solve and return the result in celsius
    return fsolve(heat_balance, T_0EoGuess)[0] - 273.15

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

    print('here it is', df_trimmed)
    df_trimmed.plot()
    plt.show()
    # Drop any rows that have been fully filtered out (all NaNs)
    df_trimmed = df_trimmed.dropna(how='all')

    return df_trimmed

def preProcessPyscada(df_path, timeAdjust):

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

print('estimate based on calibration:', innerTempEstimatorFromKnowns(15.87, 1),
      'estimate based on materials:', innerTempEstimatorFromMaterials(15.7, 50, 0.009)) 