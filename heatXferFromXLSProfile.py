

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt  # For plotting

profilePath = "G:/My Drive/h2oSplash/Messdaten/Wärmekamera/bouncedTIFFs/profile.xls" 


#measured evap temp
T_ERa = 15.5
# measured inlet and outlet
t_OEi = 19.5
t_0Eo = 15.5

# later helps precisely locate the centers of rows
KnownLenManifoldPixels = 277

#Chilling Volume in liters minute
V_OEx_1 = 6 #in m3/hr
areaPerRow = 0.53

# Step 1: Read the CSV without headers
df = pd.read_excel(profilePath, header =1)


#an empty list that will eventually hold 13 values for estimates of heat transfer coefficients
heatTransferlist = []

if 'Index' in df.columns:
    # Pivot the DataFrame based on the 'Pix3el' column
    # Set 'Index' as index to prepare for transposing
    
    print('df columns:', df.columns)
   
    # Step 2: Find the index of the absolute minimum in the 'L1_1' column
    min_index = df['L1'].idxmin()
    max_index = df['L1'].idxmax()

    # Step 3: Keep all rows starting from the minimum value's index
    df_trimmed = df.loc[min_index:max_index]
    
    # Display the pivoted DataFrame

pixelsPerRow = int(len(df_trimmed)/13)

print('pixels per row of pipe used in calculations:', pixelsPerRow)
print('distrance from minimum measurement to maximum measurement:', len(df_trimmed))

df_trimmed['nextRowVal'] = df_trimmed['L1'].shift(-2*pixelsPerRow)
df_trimmed['singleRowHeatXfer'] = V_OEx_1*(1000/3600) * 4.186 * (df_trimmed['nextRowVal']-df_trimmed['L1'])


print(df_trimmed.head())


def rowHeaTransferCoefficient(row):
    #cant calculat the first 13 rows
    if (pd.isna(row['nextRowVal'])):
        return 0
    else:
        LMTD = row['L1']-row['nextRowVal']/(np.log((row['L1'] - T_ERa)/(row['nextRowVal']-T_ERa)))
        heatTransferCoeff = row['singleRowHeatXfer']/(areaPerRow*LMTD)

        return heatTransferCoeff

df_trimmed['heatTransCoeffCalc'] = df_trimmed.apply(lambda row: rowHeaTransferCoefficient(row), axis = 1)
print(df_trimmed.head())

#takes in a continuous list of pixel and temperature values and discretizes to average htx in groups of 2 rows
def rowHeatTransferAsList(df, inletT, outletT, evapTemp, numRows, flowRateM2Perhr, areaPerRow):
    pixelsPerRow = int(len(df) / numRows)  # Ensure integer division
    df.set_index('Index', inplace=True)

    outputHeatXferCoeffs = []
    for i in range(0, int(numRows / 2)):
        # Correct indexing with int() and safe iloc access
      
        tempOut = df.iloc[int(2 * i * pixelsPerRow) - pixelsPerRow]['L1'] if i > 0 else outletT
        tempIn = df.iloc[int((2 * i) * pixelsPerRow + pixelsPerRow)]['L1'] if i < int(numRows / 2) - 1 else inletT

        # Correct precedence in LMTD calculation
        LMTD = (tempIn - tempOut) / (np.log((tempIn - evapTemp) / (tempOut - evapTemp)))
        heatTransferQ = flowRateM2Perhr * (1000 / 3600) * 4.186 * (tempIn - tempOut)
        heatXferCoeff = heatTransferQ / (LMTD * 2 * areaPerRow)
        outputHeatXferCoeffs.insert(0, heatXferCoeff)
    
    return outputHeatXferCoeffs


print('here they are!', rowHeatTransferAsList(df_trimmed, 20, 15.5, 15.5,14, 6, 0.53))


def plot_dataframe(df, x_column, y_columns):
    
    """
    Function to plot multiple y columns against a single x column in a DataFrame.
    
    Parameters:
    df (DataFrame): The pandas DataFrame containing the data.
    x_column (str): The column name for the x-axis.
    y_columns (list of str): A list of column names to plot on the y-axis.
    """
    plt.figure(figsize=(10, 6))
    
    # Plot each y_column against the x_column
    for y_column in y_columns:
        if y_column in df.columns:
            plt.plot(df[x_column], df[y_column], label=y_column)
        else:
            print(f"Warning: {y_column} not found in the DataFrame.")
    
    # Adding titles and labels
    plt.title(f'Plot of {", ".join(y_columns)} vs {x_column}')
    plt.xlabel(x_column)
    plt.ylabel('Values')
    
    # Adding a legend
    plt.legend()
    
    # Display the plot
    plt.grid(True)
    plt.show()

#plot_dataframe(df_trimmed, 'Index', [ 'L1', 'heatTransCoeffCalc', 'singleRowHeatXfer'])