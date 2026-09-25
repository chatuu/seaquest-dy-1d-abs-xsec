import numpy as np
import uproot
import awkward as ak
import ROOT
from scipy.interpolate import interp1d
import argparse
import os
import importlib.util

# ==========================================
# ROOT Configuration
# ==========================================
ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetPalette(ROOT.kBird)

# ==========================================
# CONFIGURATION
# ==========================================

# Path to the external cuts script
CUTS_SCRIPT_PATH = "~/github/seaquest-dy-1d-abs-xsec/src/core/chuck_cuts_2111-v42.py"

# --- TOGGLES ---
# Set to False to skip covariance matrix generation and speed up the script
GENERATE_COVAR_MATRIX = True

# Limit the covariance matrix size to prevent Out-Of-Memory errors
max_covar_samples_per_bin = 5000 

# Binning Definitions (Match your analysis)
mass_bins_np = np.array([3.9, 4.2, 4.5, 4.8, 5.1, 5.4, 5.7, 6.0, 6.3, 6.6, 6.9, 7.5, 8.8, 10.0], dtype=float)
xf_bins_np = np.round(np.arange(-0.05, 1.0, 0.05), 2)

# ==========================================
# EXTERNAL MODULE LOADER
# ==========================================
def load_external_cuts(filepath):
    """Dynamically loads a python file as a module (handles paths and hyphens in filenames)."""
    full_path = os.path.expanduser(filepath)
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Cannot find the cuts script at: {full_path}")
    
    spec = importlib.util.spec_from_file_location("chuck_cuts_module", full_path)
    cuts_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cuts_module)
    return cuts_module

# ==========================================
# ERROR PROPAGATION & CORRELATION LOGIC
# ==========================================
def get_bounds_vectorized(vals, ref_array):
    vals = np.asarray(vals)
    ref_array = np.asarray(ref_array)
    diff = vals[:, None] - ref_array[None, :]
    
    mask_lower = (diff >= 0)
    lower_candidates = np.where(mask_lower, ref_array[None, :], -np.inf)
    idx_lower = np.argmax(lower_candidates, axis=1)
    val_lower = ref_array[idx_lower]
    no_lower = np.all(~mask_lower, axis=1)
    idx_lower[no_lower] = 0 
    val_lower[no_lower] = ref_array[0]

    mask_upper = (diff <= 0)
    upper_candidates = np.where(mask_upper, ref_array[None, :], np.inf)
    idx_upper = np.argmin(upper_candidates, axis=1)
    val_upper = ref_array[idx_upper]
    no_upper = np.all(~mask_upper, axis=1)
    idx_upper[no_upper] = len(ref_array) - 1
    val_upper[no_upper] = ref_array[-1]
    
    return val_lower, idx_lower, val_upper, idx_upper

def calculate_recoeff_and_error(d1_vals, x_curve, y_curve, y_err_low, y_err_high):
    d1_vals = np.array(d1_vals)
    f_linear = interp1d(x_curve, y_curve, kind='linear', fill_value="extrapolate")
    track_effi = f_linear(d1_vals)
    
    d_minus, idx_d_minus, d_plus, idx_d_plus = get_bounds_vectorized(d1_vals, x_curve)
    
    e_effi_minus = y_err_low[idx_d_minus]  
    e_effi_plus  = y_err_high[idx_d_plus]  
    
    d2 = d1_vals 
    delta_d = d_plus - d_minus
    mask_exact = (delta_d == 0)
    recoeff_error = np.zeros_like(track_effi)
    
    safe_delta_d = np.where(mask_exact, 1.0, delta_d) 
    
    variance = (
        ((d_plus - d2)**2) * (e_effi_minus**2) + 
        ((d2 - d_minus)**2) * (e_effi_plus**2)
    ) / (safe_delta_d**2)
    
    recoeff_error[~mask_exact] = np.sqrt(variance[~mask_exact])
    recoeff_error[mask_exact] = e_effi_minus[mask_exact] 
    
    return track_effi, recoeff_error, idx_d_minus

def generate_covariance_matrix_per_bin(events_cut, loc_data_array, recoeff_error_array, target_name, tree_name):
    tree_label = "mix" if tree_name == "result_mix" else "total"
    out_dir = f"CovarianceMatrices_{target_name}_{tree_label}"
    os.makedirs(out_dir, exist_ok=True)
    
    print(f"    -> Generating per-bin Covariance Matrices (Saving to '{out_dir}/')...")
    
    mass_vals = np.asarray(events_cut["mass"])
    xf_vals = np.asarray(events_cut["xF"])
    
    inner_correl = 1.0
    neighbor_correl = 1.0

    bins_processed = 0
    
    for i_m in range(len(mass_bins_np) - 1):
        m_low, m_high = mass_bins_np[i_m], mass_bins_np[i_m+1]
        
        for i_x in range(len(xf_bins_np) - 1):
            x_low, x_high = xf_bins_np[i_x], xf_bins_np[i_x+1]
            
            mask = (mass_vals >= m_low) & (mass_vals < m_high) & (xf_vals >= x_low) & (xf_vals < x_high)
            
            locs_in_bin = loc_data_array[mask]
            errs_in_bin = recoeff_error_array[mask]
            
            N = len(locs_in_bin)
            if N == 0:
                continue 
                
            bins_processed += 1
            n_samples = min(N, max_covar_samples_per_bin)
            
            locs = locs_in_bin[:n_samples]
            errs = errs_in_bin[:n_samples]
            
            diff_matrix = np.abs(locs[:, None] - locs[None, :])
            correl_matrix = np.zeros((n_samples, n_samples))
            correl_matrix[diff_matrix == 0] = inner_correl      
            correl_matrix[diff_matrix == 1] = neighbor_correl   
        
            covar_matrix = correl_matrix * np.outer(errs, errs)
            
            hist_name = f"covar_{target_name}_{tree_label}_xf{i_x}_m{i_m}"
            hist_title = f"{target_name} ({tree_label}) Covariance | M: [{m_low:.1f}, {m_high:.1f}) xF: [{x_low:.2f}, {x_high:.2f});Event i;Event j"
            
            h_cov = ROOT.TH2D(hist_name, hist_title, n_samples, 0, n_samples, n_samples, 0, n_samples)
            h_cov.SetStats(0)
            h_cov.GetXaxis().CenterTitle()
            h_cov.GetYaxis().CenterTitle()
            h_cov.GetXaxis().SetTitleOffset(1.2)
            h_cov.GetYaxis().SetTitleOffset(1.2)

            nonzero_i, nonzero_j = np.nonzero(covar_matrix)
            for i, j in zip(nonzero_i, nonzero_j):
                h_cov.SetBinContent(int(i) + 1, int(j) + 1, float(covar_matrix[i, j]))

            c = ROOT.TCanvas(f"c_{hist_name}", "", 800, 800)
            c.SetRightMargin(0.15) 
            h_cov.Draw("COLZ")
            
            pdf_filename = f"{out_dir}/CovarianceMatrix_{target_name}_{tree_label}_XfBin_{i_x}_MassBin_{i_m}.pdf"
            c.SaveAs(pdf_filename)
            c.Close()
            
    print(f"    -> Finished. Saved {bins_processed} covariance matrices to {out_dir}/.")

# ==========================================
# MAIN EXECUTION
# ==========================================
def process_file(input_root_file, output_root_file, target_name, input_npz_file):
    print(f"\n==========================================")
    print(f"Processing Target: {target_name}")
    print(f"Input ROOT File: {input_root_file}")
    print(f"Input NPZ Config: {input_npz_file}")
    print(f"Output ROOT File: {output_root_file}")
    print(f"==========================================\n")

    try:
        # Load external cut module
        print(f"Loading event selection cuts from {CUTS_SCRIPT_PATH}...")
        chuck_cuts = load_external_cuts(CUTS_SCRIPT_PATH)
        
        print(f"Loading .npz data from {input_npz_file}...")
        npz_data = np.load(input_npz_file)
        x_curve = npz_data['x']
        y_curve = npz_data['y']
        y_err_low = npz_data['y_error_low']
        y_err_high = npz_data['y_error_high']
        
        print(f"Opening input ROOT file: {input_root_file}")
        with uproot.open(input_root_file) as file:
            tree_names = ['result', 'result_mix']
            output_trees = {}
            
            for t_name in tree_names:
                if t_name not in file:
                    print(f"Warning: Tree '{t_name}' not found. Skipping.")
                    continue
                
                print(f"\nProcessing tree: {t_name}...")
                tree = file[t_name]
                
                print("  - Applying external numpy array cuts...")
                # Apply the imported function with the exact requested arguments
                events_cut = chuck_cuts.apply_cuts(
                    tree, 
                    is_mc=False, 
                    lower_mass_cut=2.0, 
                    upper_mass_cut=10.0, 
                    upper_pT2_cut=7.0
                )
                
                # events_cut is a dict mapping field names to filtered numpy arrays
                n_events = len(events_cut["mass"]) if "mass" in events_cut else 0
                print(f"  - Events after cuts: {n_events}")
                
                if n_events == 0:
                    print("  - No events passed cuts. Skipping efficiency calculations.")
                    continue
                
                # 5. Extract D1 values
                if t_name == 'result_mix':
                    if 'ptrk_D1' in events_cut and 'ntrk_D1' in events_cut:
                        d1_values = 0.5 * (events_cut['ptrk_D1'] + events_cut['ntrk_D1'])
                    else:
                        d1_values = events_cut['D1']
                else:
                    d1_values = events_cut['D1']

                # 6. Calculate efficiencies
                print(f"  - Calculating efficiencies...")
                recoeff, recoeff_error, loc_data = calculate_recoeff_and_error(
                    np.asarray(d1_values), 
                    x_curve, y_curve, y_err_low, y_err_high
                )
                
                # Add calculated columns to dictionary to be saved natively
                events_cut["recoeff"] = recoeff
                events_cut["recoeff_error"] = recoeff_error
                
                output_trees[t_name] = events_cut

                # 7. Generate the covariance matrices per bin
                if GENERATE_COVAR_MATRIX:
                    generate_covariance_matrix_per_bin(events_cut, loc_data, recoeff_error, target_name, t_name)
                else:
                    print("    -> Skipping Covariance Matrix generation (Flag is set to False).")

        # Write Output explicitly as TTrees
        if output_trees:
            print(f"\nWriting output to {output_root_file}...")
            with uproot.recreate(output_root_file) as f_out:
                for t_name, data_dict in output_trees.items():
                    print(f"  - Writing tree {t_name}...")
                    
                    sanitized_dict = {}
                    branch_types = {}
                    
                    # Sanitize object dtypes back to jagged arrays and map their types
                    for key, val in data_dict.items():
                        val_np = np.asarray(val) 
                        if val_np.dtype == object:  # NumPy object arrays
                            try:
                                awk_array = ak.from_iter(val_np)
                                sanitized_dict[key] = awk_array
                                branch_types[key] = awk_array.type  # Awkward type
                            except Exception as e:
                                print(f"    -> Warning: Could not process object branch '{key}'. Error: {e}")
                        else:
                            sanitized_dict[key] = val_np
                            branch_types[key] = val_np.dtype  # NumPy type
                            
                    # Explicitly create a classic TTree and fill it
                    f_out.mktree(t_name, branch_types)
                    f_out[t_name].extend(sanitized_dict)
                    
            print("Done! File saved successfully.")
        else:
            print("\nNo trees were processed or survived the cuts.")
            
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate ROOT Files with Reco Efficiencies")
    parser.add_argument("-i", "--input", required=True, help="Path to the input ROOT file")
    parser.add_argument("-o", "--output", required=True, help="Path to save the output ROOT file")
    parser.add_argument("-t", "--target", required=True, choices=["LH2", "LD2", "Flask"], help="Target name (LH2, LD2, Flask)")
    parser.add_argument("-c", "--config", required=True, help="Path to the configuration file (e.g., interpolation data .npz file)")
    
    args = parser.parse_args()
    
    # Pass the argument down correctly
    process_file(args.input, args.output, args.target, args.config)