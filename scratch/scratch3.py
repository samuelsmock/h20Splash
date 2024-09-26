import matplotlib.pyplot as plt
import numpy as np

# Data
lo_90_g_s = [2.57, 1.84, 1.4, 1.06, 1.12, 1.21, 0.23, 0.38]
hi_130g_s = [2.85, 2.27, 1.65, 1.45, 1.5, 1.37, 0.37, 0.63]
none = [0.36, 0.28, 0.16, 1.61, 0.7, 0.42, -0.19, 0.27]

# X axis labels (index starting at 1)
x = np.arange(1, len(lo_90_g_s) + 1)

# Create a dictionary to name the sets
set_names = {
    "hi_130g_s": "130g/s - Pool Depth 11 cm (Bottom 3 Rows Covered)",
    "lo_90_g_s": "90g/s - Pool Depth 11 cm (Bottom 3 Rows Covered (group 8 and half of group 7))",
    "none": "No Recirc - Pool Depth 35 cm (Bottom 9 Rows Covered Pool Surface Halfway through Group 4)",
}

# Create the plot
bar_width = 0.25
fig, ax = plt.subplots(figsize=(10, 6))

# Plot each set next to each other
ax.bar(x, hi_130g_s, width=bar_width, label=set_names["hi_130g_s"])
ax.bar(x - bar_width, lo_90_g_s, width=bar_width, label=set_names["lo_90_g_s"])
ax.bar(x + bar_width, none, width=bar_width, label=set_names["none"])

# Titles and labels with larger and bold font, and two-line title
ax.set_title(
    'Heat Transfer Coefficient Across Row Groupings for Different\nRefrigerant Recirculation Rates and Pool Depth Comparisons', 
    fontsize=16, 
    fontweight='bold', 
    pad=20  # Adds padding between the title and the plot
)
ax.set_xlabel('Row Grouping (Starting at the top)', fontsize=14, fontweight='bold')
ax.set_ylabel('Avg. Total Heat Transfer Coefficient (kW/m2*K)', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(x)

# Add a legend
ax.legend()

# Display the plot
plt.tight_layout()
plt.show()
