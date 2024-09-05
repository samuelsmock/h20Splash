import os
from PIL import Image
import numpy as np
from scipy.interpolate import interp1d

# Original temperature intervals and corresponding colors
correct_temperatures_original = [23, 22.75, 22.5, 22.25, 22, 21.75, 21.5, 21.25, 21, 20.75, 20.5, 20.25, 20, 19.75, 19.5, 19.25, 19, 18.75, 18.5, 18.25, 18, 17.75, 17.5, 17.25, 17, 16.75, 16.5, 16.25, 16, 15.75, 15.5, 15.25, 15]
color_samples_original = np.array([
    [255, 255, 255],  # 23°C
    [247, 211, 251],  # 22.75°C
    [239, 168, 247],  # 22.5°C
    [235, 109, 243],  # 22.25°C
    [231,  50, 240],  # 22°C
    [232,  79, 202],  # 21.75°C
    [234, 108, 165],  # 21.5°C
    [232,  83, 104],  # 21.25°C
    [231,  58,  44],  # 21°C
    [233,  90,  46],  # 20.75°C
    [235, 122,  47],  # 20.5°C
    [238, 155,  55],  # 20.25°C
    [242, 188,  64],  # 20°C
    [245, 220,  73],  # 19.75°C
    [248, 252,  83],  # 19.5°C
    [153, 173,  53],  # 19.25°C
    [ 58,  94,  23],  # 19°C
    [ 72, 142,  53],  # 18.75°C
    [ 87, 190,  84],  # 18.5°C
    [ 70, 155, 136],  # 18.25°C
    [ 53, 121, 188],  # 18°C
    [ 40,  97, 214],  # 17.75°C
    [ 28,  72, 240],  # 17.5°C
    [ 21,  59, 206],  # 17.25°C
    [ 15,  45, 172],  # 17°C
    [ 37,  58, 149],  # 16.75°C
    [ 58,  71, 126],  # 16.5°C
    [ 62,  68,  96],  # 16.25°C
    [ 65,  65,  65],  # 16°C
    [ 58,  71, 126],  # 15.75°C
    [ 40,  45, 126],  # 15.5°C
    [ 30,  38, 136],  # 15.25°C
    [ 20,  20, 140],  # 15°C (darkest blue)
])

# Interpolating the color map
correct_temperatures_extended = np.arange(15, 23, 0.02)
f_red = interp1d(correct_temperatures_original, color_samples_original[:, 0], kind='linear')
f_green = interp1d(correct_temperatures_original, color_samples_original[:, 1], kind='linear')
f_blue = interp1d(correct_temperatures_original, color_samples_original[:, 2], kind='linear')
color_samples_extended = np.stack([f_red(correct_temperatures_extended),
                                   f_green(correct_temperatures_extended),
                                   f_blue(correct_temperatures_extended)], axis=-1).astype(int)

# Function to calculate Euclidean distance between two RGB values
def rgb_distance(rgb1, rgb2):
    return np.sqrt(np.sum((rgb1 - rgb2) ** 2))

# Define the folder paths
input_folder = 'g:/My Drive/h2oSplash/IRCamera/Thermal_Image_Analysis_RR/cropped_images'
output_folder = 'g:/My Drive/h2oSplash/IRCamera/Thermal_Image_Analysis_RR/single_band'

# Ensure the output folder exists
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Get sorted BMP files from the folder
sorted_filenames = sorted([f for f in os.listdir(input_folder) if f.endswith(".bmp")])

# Loop through all BMP files
for filename in sorted_filenames:
    image_path = os.path.join(input_folder, filename)
    img = Image.open(image_path)
    img_np = np.array(img)

    # Create a temperature array based on the image size
    temp_array = np.zeros((img_np.shape[0], img_np.shape[1]), dtype=np.float32)

    # Calculate temperature for each pixel
    for y in range(img_np.shape[0]):
        for x in range(img_np.shape[1]):
            rgb_value = img_np[y, x, :3]
            closest_temp_idx = np.argmin([rgb_distance(rgb_value, color) for color in color_samples_extended])
            temp_array[y, x] = correct_temperatures_extended[closest_temp_idx]

    # Save as TIFF with actual temperature values (no scaling)
    output_tiff_path = os.path.join(output_folder, filename.replace('.bmp', '.tiff'))
    temp_image = Image.fromarray(temp_array.astype(np.float32))  # Ensure the array is in 32-bit float format
    
    # Save as a 32-bit floating-point TIFF
    temp_image.save(output_tiff_path, format="TIFF", bits=32)

print("Processing completed, single-band TIFF files with actual temperature values saved.")
