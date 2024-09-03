import h5py
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np
import CoolProp.CoolProp as CP

# Open the HDF5 file
file_path = ''

variables_to_plot = ['t_0Ei', 't_0Eo', 'T_ERa', 'Q_0Ex_1', 'p_ERs_1_rel', 'D_PWn1', 'p_EVo']
tubeArea = 7.9  # m2

# Function to calculate specific latent heat of vaporization
def latent_heat_vaporization(pressure_mbar):
    fluid_name = 'Water'
    input_value = pressure_mbar * 100  # Convert mbar to Pa (CoolProp uses SI units)
    h_fg = CP.PropsSI('H', 'P', input_value, 'Q', 1, fluid_name)
    return h_fg / 1000.0  # Convert to kJ/kg

def satTempFromPress(pressure_mbar):
    return (CP.PropsSI('T', 'P', pressure_mbar * 100, 'Q', 0, 'Water') - 273.15)

with h5py.File(file_path, 'r') as file:
    time_data = file['/time'][:]
    data_dict = {key: file[key][:] for key in file.keys()}
        
# Convert floating point time to time of day in seconds
time_of_day_seconds = (time_data - time_data[0]) * 24 * 3600
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
    'ReBottom': '',
    'delHe': 'kJ/kg',
    'delHs': 'kJ/kg'
}

# Calculate derived quantities
data['LMTD'] = ((data['t_0Ei'] - data['T_ERa']) - (data['t_0Eo'] - data['T_ERa'])) / np.log((data['t_0Ei'] - data['T_ERa']) / (data['t_0Eo'] - data['T_ERa']))
data['HeatTranCoeff'] = data['Q_0Ex_1'] / (data['LMTD'] * tubeArea)
data['dmrich/dt'] = 1000 * data['V_AWo'] / 3600
data['dmsump/dt'] = 1000 * data['V_ERi'] / 3600  # l/hr -> kg/s
data['dmref1/dt'] = data['dmrich/dt'] * (1 - ((data['T_HWo'] - data['T_HWi']) / (data['T_HSi'] - data['T_HSo'])))
data['delhe'] = data['p_EVo'].apply(lambda p: latent_heat_vaporization(p)/1000)
data['delhs'] = data['delhe'] * ((((data['t_2Do_1'] + 273) * (data['t_1Ai'] - data['t_0Ei'])) \
                              / ((data['t_0Ei'] + 273) * (data['t_2Do_1'] - data['t_1Ai']))) - 1)
data['satTemp'] = data['p_EVo'].apply(lambda x: satTempFromPress(x))
data['dmref2/dt'] = data['Q_0Ex_1'] / data['delhe']
data['f'] = data['dmrich/dt'] / data['dmref2/dt']
data['f'] = np.where((data['f'] >= 0) & (data['f'] <= 50), data['f'], 0)
data['ReTop'] = 2 * (data['dmsump/dt'] / 1000) / (7.68 * 0.001375)
data['ReBottom'] = 2 * ((data['dmsump/dt'] - data['dmref2/dt']) / 1000) / (7.68 * 0.001375)
data['Pool Depth (cm)'] = data['p_ERs_1_rel'] / 0.981
data['COP'] = data['Q_0Ex_1']/data['Q_2Dx_1']

# Add derived variables to the list
variables_to_plot.extend(['LMTD', 'HeatTranCoeff', 'dmrich/dt', 'dmsump/dt', 'dmref1/dt', 'f', 'ReTop', 'ReBottom'])
variables_to_plot.extend(['Pool Depth (cm)', 'delhe', 'delhs', 'satTemp'])
units['Pool Depth (cm)'] = 'cm'

# Round numerical values to 2 decimal places
data = data.round(2)
data = data[data['Q_0Ex_1'] > 10]

# Create the plotly figure
fig = make_subplots()

# Add traces for each variable to plot
for var_name in variables_to_plot:
    # Apply formatting for variables starting with 'd' and ending with '/dt'
    if var_name.startswith('d') and var_name.endswith('/dt'):
        base_name = var_name[1:-3]  # Strip leading 'd' and trailing '/dt'
        dot_letter = base_name[0]  # The letter to be dotted
        rest_of_name = base_name[1:]  # The rest of the name

        # Subscript Unicode characters
        subscripts = {'1': '\u2081', '2': '\u2082', '3': '\u2083', '4': '\u2084', '5': '\u2085', '6': '\u2086', '7': '\u2087', '8': '\u2088', '9': '\u2089', '0': '\u2080'}

        # Convert any numeric part to subscript
        subscript_name = ''.join(subscripts.get(c, c) for c in rest_of_name if c.isdigit())
        rest_of_name = ''.join(c for c in rest_of_name if not c.isdigit())  # Non-numeric part
        
        var_name_display = f"{dot_letter}\u0307{rest_of_name}{subscript_name}"  # Dot above letter and subscript
        var_name_display += f" ({units.get(var_name, '')})"
    else:
        var_name_display = f"{var_name} ({units.get(var_name, '')})"
    
    fig.add_trace(go.Scatter(x=data['time'], y=data[var_name], mode='lines', name=var_name_display))

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
