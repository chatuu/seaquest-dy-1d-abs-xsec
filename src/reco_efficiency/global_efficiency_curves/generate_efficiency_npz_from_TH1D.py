import uproot
import numpy as np

def convert_root_to_npz(root_filename, hist_name, output_filename):
    # Open the ROOT file
    with uproot.open(root_filename) as file:
        # Access the TH1D histogram
        hist = file[hist_name]
        
        # Extract x-axis (D1) bin centers
        # You could also use hist.axes[0].edges() if you need bin boundaries
        x = hist.axes[0].centers()
        
        # Extract y-axis (efficiency) values
        y = hist.values()
        
        # Extract errors. 
        # TH1D histograms store symmetric errors by default (sqrt of variance).
        errors = hist.errors()
        y_error_low = errors
        y_error_high = errors
        
        # Save the extracted numpy arrays into an .npz file
        np.savez(output_filename, 
                 x=x, 
                 y=y, 
                 y_error_low=y_error_low, 
                 y_error_high=y_error_high)
        
        print(f"Data successfully extracted and saved to {output_filename}")
        print(f"Keys in .npz: ['x', 'y', 'y_error_low', 'y_error_high']")
        print(f"Number of data points: {len(x)}")

if __name__ == "__main__":
    # Define your filenames and histogram name here
    #ROOT_FILE = "/root/github/e906-development/ROOTFiles/Kenichi/rs67_lh2_eff.root"
    ROOT_FILE = "/root/github/seaquest-dy-1d-abs-xsec/root_files/MC/Kenichi/rs57_ld2_eff.root"
    #HISTOGRAM_NAME = "h1_eff_D1"
    #HISTOGRAM_NAME = "h1_eff_D1-10"
    HISTOGRAM_NAME = "h1_eff_D1-10"

    #OUTPUT_FILE = "/root/github/e906-development/src/NewReconstructionEfficiency/RS67/LH2/GlobalEfficiencyCurve/rs67_lh2_eff_D1.npz"
    OUTPUT_FILE = "/root/github/seaquest-dy-1d-abs-xsec/src/reco_efficiency/global_efficiency_curves/rs57_ld2_eff_D1.npz"
    
    convert_root_to_npz(ROOT_FILE, HISTOGRAM_NAME, OUTPUT_FILE)