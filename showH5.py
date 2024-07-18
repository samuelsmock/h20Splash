import h5py
### File to print all datasets to begin to explore options

# Open the HDF5 file
file_path = '/Users/sunshinedaydream/Documents/h2oSplash/Measurements/SUBS_measurement_data_2024_06_11_0000_2024_06_11_2359_daily_export_3_SamMeasurements.h5'
with h5py.File(file_path, 'r') as file:
    # Print the names of datasets in the file
    print("Datasets in the file:")
    def print_attrs(name, obj):
        print(name)
    file.visititems(print_attrs)

    ### Investigate the structure of a single dataset
    dataset = file['/T_EDo']
    
    # Print dataset shape and dtype
    print("Dataset shape:", dataset.shape)
    print("Dataset dtype:", dataset.dtype)