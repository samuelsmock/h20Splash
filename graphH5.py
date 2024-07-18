import h5py
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np

# Open the HDF5 file
file_path = '/Users/sunshinedaydream/Library/CloudStorage/GoogleDrive-smock.samuel@gmail.com/My Drive/h2oSplash/Measurements/SUBS_measurement_data_2024_06_25_0000_2024_06_25_2359_daily_export_3_SamMeasurements.h5'
# file_path = '/Users/sunshinedaydream/Documents/h2oSplash/Measurements/SUBS_measurement_data_2024_06_25_0000_2024_06_25_2359_daily_export_3_SamMeasurements.h5'

variables_to_plot = ['t_0Ei', 't_0Eo', 'T_ERa', 'Q_0Ex_1', 'p_ERs_1_rel']
tubeArea = 7.9  # m2

with h5py.File(file_path, 'r') as file:
    # Read the time dataset
    time_data = file['/time'][:]

    # Read all datasets into a dictionary
    data_dict = {}
    for key in file.keys():
        data_dict[key] = file[key][:]
        
# Convert floating point time to time of day in seconds
time_of_day_seconds = (time_data - time_data[0]) * 24 * 3600

# Create datetime objects for plotting
start_datetime = datetime(2024, 6, 12)  # Adjust to your reference date
time_datetimes = [start_datetime + timedelta(seconds=sec) for sec in time_of_day_seconds]

# Create a DataFrame with all variables
data = pd.DataFrame(data_dict)
data['time'] = time_datetimes

# Define units for each variable
units = {
    't_0Ei': '°C',
    't_0Eo': '°C',
    'T_ERa': '°C',
    'Q_0Ex_1': 'kW',
    'p_ERs_1_rel': 'mbar',
    'LMTD': '°C',
    'HeatTranCoeff': 'kW/m²K',
    'dmrich/dt': 'g/s',
    'dmsump/dt': 'g/s',
    'dmref1/dt': 'g/s',
    'dmref2/dt': 'g/s',
    'f': '',
    'ReTop': '',
    'ReBottom': ''
}

# Calculate derived quantities
data['LMTD'] = ((data['t_0Ei'] - data['T_ERa']) - (data['t_0Eo'] - data['T_ERa'])) / np.log((data['t_0Ei'] - data['T_ERa']) / (data['t_0Eo'] - data['T_ERa']))
data['HeatTranCoeff'] = data['Q_0Ex_1'] / (data['LMTD'] * tubeArea)
data['dmrich/dt'] = 1000*data['V_AWo']/3600
data['dmsump/dt'] = 1000*data['V_ERi']/3600  # l/hr -> kg/s
data['dmref1/dt'] = 1000*data['dmrich/dt'] * (1-((data['T_HWi'] - data['T_HWo']) / (data['T_HSo'] - data['T_HSi'])))
data['dmref2/dt'] = 1000* data['Q_0Ex_1'] / 2400
data['f'] = data['dmrich/dt'] / data['dmref2/dt']
data['f'] = np.where((data['f'] >= 0) & (data['f'] <= 50), data['f'], 0)
data['ReTop'] = 2 * (data['dmsump/dt']/1000) / (7.68 * 0.001375)
data['ReBottom'] = 2 * ((data['dmsump/dt'] - data['dmref2/dt'])/1000) / (7.68 * 0.001375)

# Add derived variables to the list
variables_to_plot.extend(['LMTD', 'HeatTranCoeff', 'dmrich/dt', 'dmsump/dt', 'dmref2/dt', 'f', 'ReTop', 'ReBottom'])

# Add a column for Pool Depth in cm calculated from pressure
data['Pool Depth (cm)'] = data['p_ERs_1_rel'] / 0.981
variables_to_plot.append('Pool Depth (cm)')
units['Pool Depth (cm)'] = 'cm'

# Create the plotly figure
fig = make_subplots()

# Add traces for each variable to plot
for var_name in variables_to_plot:
    fig.add_trace(go.Scatter(x=data['time'], y=data[var_name], mode='lines', name=f"{var_name} ({units.get(var_name, '')})"))

# Update the layout
fig.update_layout(
    title='Variable Comparison Over Time',
    xaxis_title='Time',
    yaxis_title='Values',
    xaxis=dict(
        tickformat='%H:%M:%S',
        tickmode='auto',
        nticks=10,
    ),
    legend=dict(
        title='Variables',
        orientation='h',
        yanchor='top',
        y=1.02,
        xanchor='right',
        x=1
    ),
    hovermode='x unified'
)

# Show the plot
fig.show()
