import numpy as np
import matplotlib.pyplot as plt
import os

# Define the directory containing the files
data_dir = "/home/ckuruppu/github/seaquest-dy-1d-abs-xsec/src/reco_efficiency/global_efficiency_curves/"

# Define the files, their legend labels, and formatting options (color, marker)
datasets = [
    ("rs67_lh2_eff_D1.npz", "New LH2", "blue", "o"),
    ("rs67_ld2_eff_D1.npz", "New LD2", "red", "s"),
    ("interpolation_data_d1.npz", "Existing", "green", "^")
]

# Initialize the plot canvas
plt.figure(figsize=(10, 6))

# Loop through each dataset and plot
for filename, label, color, marker in datasets:
    filepath = os.path.join(data_dir, filename)
    
    # Load the .npz file
    with np.load(filepath) as data:
        x = data['x']
        y = data['y']
        y_err_low = data['y_error_low']
        y_err_high = data['y_error_high']
    
    # Matplotlib expects asymmetric errors as a 2xN array: [lower_errors, upper_errors]
    y_err = [y_err_low, y_err_high]
    
    # Plot data with error bars
    plt.errorbar(
        x, y, 
        yerr=y_err, 
        fmt=marker,        # Marker style 
        color=color,       # Line and marker color
        label=label,       # Legend label
        capsize=4,         # Width of the caps on error bars
        linestyle='None',  # Remove connecting lines between points
        alpha=0.8
    )

# Format the plot
plt.xlabel("D1 Occupancy", fontsize=14)
plt.ylabel("Efficiency", fontsize=14)
plt.title("Reconstruction Efficiency vs. D1 Occupancy", fontsize=16)
plt.legend(loc="best", fontsize=12)
plt.grid(True, linestyle="--", alpha=0.5)

# Adjust layout and save the plot
plt.tight_layout()
output_file = "efficiency_comparison_d1.pdf"
#plt.savefig(output_file, dpi=300)
plt.savefig(output_file)

print(f"Plot successfully saved as: {output_file}")

# Display the plot
plt.show()
