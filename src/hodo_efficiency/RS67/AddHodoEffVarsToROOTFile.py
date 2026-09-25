import numpy as np
import pandas as pd
import uproot
import awkward as ak
import argparse
import sys
import os
import importlib.util
from functions import calculate_hodo_efficiency_columns

# ==========================================
# EXTERNAL MODULE LOADER
# ==========================================
def load_cut_module():
    """Dynamically loads the cuts module since the filename contains a hyphen."""
    cuts_path = os.path.expanduser("~/github/seaquest-dy-1d-abs-xsec/src/core/chuck_cuts_2111-v42.py")
    if not os.path.exists(cuts_path):
        raise FileNotFoundError(f"Cannot find the cuts script at: {cuts_path}")
        
    spec = importlib.util.spec_from_file_location("chuck_cuts", cuts_path)
    chuck_cuts = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(chuck_cuts)
    return chuck_cuts

def sanitize_for_uproot(data_dict):
    """
    Finds numpy arrays with 'object' dtypes (usually jagged vectors like std::vector)
    and converts them to Awkward arrays so Uproot can safely write them.
    """
    sanitized = {}
    for key, val in data_dict.items():
        if hasattr(val, 'dtype') and val.dtype == object:
            try:
                # Rebuild the jagged structure
                sanitized[key] = ak.from_iter(val)
            except Exception as e:
                print(f"   [Warning] Could not convert branch '{key}'. Error: {e}")
        else:
            sanitized[key] = val
    return sanitized

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--xf_min', type=float, help="Minimum xF to keep (optional)")
    parser.add_argument('--xf_max', type=float, help="Maximum xF to keep (optional)")
    parser.add_argument('--input', type=str, required=True, help="Path to input ROOT file")
    parser.add_argument('--output', type=str, required=True, help="Name of output ROOT file")
    parser.add_argument('--target', type=str, required=True, choices=["LH2", "LD2", "Flask"], help="Target type (LH2, LD2, Flask)")
    args = parser.parse_args()

    print(f"\n==========================================")
    print(f"Processing Target: {args.target}")
    print(f"Input File: {args.input}")
    print(f"Output File: {args.output}")
    print(f"==========================================")

    # Load external cut module
    print(f"-> Loading external event selection cuts...")
    chuck_cuts = load_cut_module()

    trees_to_save = {}

    print(f"-> Opening input ROOT file...")
    with uproot.open(args.input) as infile:
        
        for tree_name in ["result", "result_mix"]:
            if tree_name not in infile:
                print(f"   [Warning] Tree '{tree_name}' not found. Skipping.")
                continue
            
            print(f"\n--- Processing Tree: {tree_name} ---")
            tree = infile[tree_name]
            
            # Apply standard cuts with specified input arguments
            print("   -> Applying Chuck Cuts...")
            filtered_events = chuck_cuts.apply_cuts(
                tree, 
                is_mc=False, 
                lower_mass_cut=2.0, 
                upper_mass_cut=10.0, 
                upper_pT2_cut=7.0
            )

            # Apply xF filters if requested
            if args.xf_min is not None and args.xf_max is not None:
                print(f"   -> Applying xF filter [{args.xf_min}, {args.xf_max})...")
                xf = filtered_events["xF"]
                xf_mask = (xf >= args.xf_min) & (xf < args.xf_max)
                for key in filtered_events.keys():
                    filtered_events[key] = filtered_events[key][xf_mask]
            
            num_events = len(filtered_events["mass"]) if "mass" in filtered_events else 0
            print(f"   -> Events surviving all cuts: {num_events}")
            
            if num_events == 0:
                print(f"   [Warning] No events left for {tree_name}. Skipping efficiency calc.")
                continue

            # Convert numpy dict to pandas DataFrame for the efficiency calculation
            df_passed = pd.DataFrame(filtered_events)
            
            # Calculate hodoscope efficiencies
            df_passed = calculate_hodo_efficiency_columns(df_passed)
            
            # Convert pandas DataFrame back to a dictionary of numpy arrays
            out_dict = {col: df_passed[col].values for col in df_passed.columns}
            
            # Sanitize object dtypes (rebuilds std::vector representations)
            trees_to_save[tree_name] = sanitize_for_uproot(out_dict)

    # Write output ROOT file using Uproot mktree (classic TTree format)
    print(f"\n-> Writing output to {args.output}...")
    with uproot.recreate(args.output) as outfile:
        for t_name, safe_data in trees_to_save.items():
            print(f"   Saving tree {t_name}...")
            
            # Infer data types for TTree metadata
            branch_types = {}
            for k, v in safe_data.items():
                if isinstance(v, ak.Array):
                    branch_types[k] = v.type  # Awkward type
                else:
                    branch_types[k] = v.dtype # NumPy type
                    
            # Explicitly create TTree and fill
            outfile.mktree(t_name, branch_types)
            outfile[t_name].extend(safe_data)

    print("\nProcessing complete.")

if __name__ == "__main__":
    main()