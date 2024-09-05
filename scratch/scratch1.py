from PIL import Image
import numpy as np

# Load the TIFF image
image_path = 'g:\My Drive\h2oSplash\IRCamera\Thermal_Image_Analysis_RR\single_band\AA021401.tiff'
img = Image.open(image_path)

# Convert the image to a NumPy array
img_array = np.array(img)

# Check the min and max values in the image
min_value = np.min(img_array)
max_value = np.max(img_array)

print(f"Min pixel value: {min_value}")
print(f"Max pixel value: {max_value}")

# Optional: If you want to print all the unique values
unique_values = np.unique(img_array)
print(f"Unique pixel values: {unique_values}")