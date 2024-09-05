

import pandas as pd

profilePath = "G:/My Drive/h2oSplash/Messdaten/Wärmekamera/bouncedTIFFs/prrofile.csv" 


#measured evap temp
T_ERa = 15.5
#Chilling Volume in liters minute
V_OEx_1 = 6
areaPerRow = 0.53

# Step 1: Read the CSV without headers
df_raw = pd.read_csv(profilePath, sep=';')

#keep track of the name in row1 column 1
name =""
# Step 2: Check if the first row, second column is empty (indexing starts from 0)
if len(df_raw.columns) == 1:
    # Step 3: Re-read the CSV, skipping the first row and using the second row as the header
    df = pd.read_csv(profilePath, sep=',', header=1)
    name = df_raw.iloc[[0,0]]
    
else:
    # If first row contains valid data, keep as-is
    df = pd.read_csv(profilePath, sep=';')

# Display the first few rows to verify
if 'Pixel' in df.columns:
    # Pivot the DataFrame based on the 'Pix3el' column
    # Set 'Pixel' as index to prepare for transposing
    
    print('df columns:', df.columns)
    # Extract the value in the 'Time' column where 'Pixel' equals 'L1_1'
    time_value = df.loc[df['Pixel'] == 'L1_1', 'Time'].values[0]

    # Display the extracted time value
    print(f"Extracted Time Value: {time_value}")

    # Drop the 'Time' and 'Milliseconds' columns
    df = df.drop(columns=['Time', 'Milliseconds'])
    df = df.set_index('Pixel')
    # Transpose the DataFrame so that the pixel values (1, 2, 3, ...) become rows
    df_transposed = df.T
    
    # Step 1: Drop the 'Time' and 'Milliseconds' values or any non numeric
   
    # Step 2: Find the index of the absolute minimum in the 'L1_1' column
    min_index = df_transposed['L1_1'].idxmin()
    max_index = df_transposed['L1_1'].idxmax()

    # Step 3: Keep all rows starting from the minimum value's index
    df_trimmed = df_transposed.loc[min_index:max_index]
    
    # Display the pivoted DataFrame

pixelsPerRow = len(df_trimmed)/13

df_trimmed['nextRowVal'] = df_trimmed['L1_1'].shift[-1*pixelsPerRow]

print(df_trimmed.head())

def rowHeaTransferCoefficient(row):
    #cant calculat the first 13 rows
    if (row) <13:
        return 0
    else:
        LMTD = col.iloc[row]-col.iloc[row+pixelsPerRow]/(np.log(col.iloc[row] - T_ERa)/np.log(col.iloc[row+pixelsPerRow]-T_ERa))
        heatTransferRateQ = V_OEx_1*(100/6) * 4.186 * (col.iloc[row+pixelsPerRow]-col.iloc[row])
        heatTransferCoeff = heatTransferRateQ/(areaPerRow*LMTD)

        return heatTransferCoeff

df_trimmed['heatTransCoeffCalc'] = df_trimmed.apply(lambda row: rowHeaTransferCoefficient(row.name, df_final['L1_1'], pixelsPerRow,areaPerRow, V_OEx_1))


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

plot_dataframe(df_final, 'Pixel', ['heatTransCoeffCalc', 'L1_1'])