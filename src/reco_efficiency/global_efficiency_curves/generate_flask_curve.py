import numpy as np
import os
import matplotlib.pyplot as plt

def calculate_average_efficiency(file_lh2, file_ld2, output_file):
    print(f"Loading LH2 data from: {file_lh2}")
    data_lh2 = np.load(file_lh2)
    x_lh2 = data_lh2['x']
    y_lh2 = data_lh2['y']
    err_low_lh2 = data_lh2['y_error_low']
    err_high_lh2 = data_lh2['y_error_high']

    print(f"Loading LD2 data from: {file_ld2}")
    data_ld2 = np.load(file_ld2)
    x_ld2 = data_ld2['x']
    y_ld2 = data_ld2['y']
    err_low_ld2 = data_ld2['y_error_low']
    err_high_ld2 = data_ld2['y_error_high']

    # 1. Check if the x-axis (D1 values) match exactly
    if not np.array_equal(x_lh2, x_ld2):
        raise ValueError("The D1 binning (x-arrays) in the two files do not match! Cannot trivially average them.")

    # 2. Calculate the average efficiency
    print("Calculating average efficiency...")
    y_avg = (y_lh2 + y_ld2) / 2.0

    # 3. Propagate the uncertainties (assuming independent samples)
    print("Propagating uncertainties...")
    err_low_avg = 0.5 * np.sqrt(err_low_lh2**2 + err_low_ld2**2)
    err_high_avg = 0.5 * np.sqrt(err_high_lh2**2 + err_high_ld2**2)

    # 4. Save to a new .npz file
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    np.savez(output_file, 
             x=x_lh2, 
             y=y_avg, 
             y_error_low=err_low_avg, 
             y_error_high=err_high_avg)
    
    print(f"\nSuccess! Averaged efficiency curve saved to: {output_file}")

    # 5. (Optional) Generate a quick plot to visually verify the result
    plot_file = output_file.replace('.npz', '.pdf')
    print(f"Generating visual comparison plot: {plot_file}")
    
    plt.figure(figsize=(10, 6))
    
    # Plot LH2
    plt.errorbar(x_lh2, y_lh2, yerr=[err_low_lh2, err_high_lh2], 
                 fmt='o', markersize=4, label='LH2', alpha=0.5, capsize=2)
    # Plot LD2
    plt.errorbar(x_ld2, y_ld2, yerr=[err_low_ld2, err_high_ld2], 
                 fmt='s', markersize=4, label='LD2', alpha=0.5, capsize=2)
    # Plot Average
    plt.errorbar(x_lh2, y_avg, yerr=[err_low_avg, err_high_avg], 
                 fmt='^', markersize=5, color='black', label='Average (LH2+LD2)', capsize=3)

    plt.xlabel("D1 Value")
    plt.ylabel("Reconstruction Efficiency")
    plt.title("Reconstruction Efficiency: LH2 vs LD2 vs Average")
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig(plot_file)
    plt.close()
    
    print("Plot generation complete.")

if __name__ == "__main__":
    # Define input and output paths
    base_dir = "./"
    
    file_lh2 = os.path.join(base_dir, "rs67_lh2_eff_D1.npz")
    file_ld2 = os.path.join(base_dir, "rs67_ld2_eff_D1.npz")
    output_file = os.path.join(base_dir, "rs67_avg_eff_D1.npz")
    
    # Check if files exist before running
    if not os.path.exists(file_lh2):
        print(f"Error: Could not find {file_lh2}")
    elif not os.path.exists(file_ld2):
        print(f"Error: Could not find {file_ld2}")
    else:
        calculate_average_efficiency(file_lh2, file_ld2, output_file)