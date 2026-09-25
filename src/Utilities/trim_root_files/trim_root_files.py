import uproot
import awkward as ak
import argparse
import os
import importlib.util

def load_cut_module():
    """Dynamically loads the cuts module since the filename contains a hyphen."""
    cuts_path = os.path.expanduser("~/github/seaquest-dy-1d-abs-xsec/src/core/chuck_cuts_2111-v42.py")
    spec = importlib.util.spec_from_file_location("chuck_cuts", cuts_path)
    chuck_cuts = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(chuck_cuts)
    return chuck_cuts

def sanitize_for_uproot(data_dict):
    """
    Finds numpy arrays with 'object' dtypes (usually strings or jagged vectors)
    and converts them to Awkward arrays so Uproot can safely write them.
    """
    sanitized = {}
    for key, val in data_dict.items():
        if hasattr(val, 'dtype') and val.dtype == 'O':
            try:
                # Convert the object array into a strict Awkward layout
                sanitized[key] = ak.from_iter(val)
            except Exception as e:
                print(f"   [Warning] Could not convert branch '{key}', skipping. Error: {e}")
        else:
            sanitized[key] = val
    return sanitized

def main():
    parser = argparse.ArgumentParser(description="Apply chuck cuts to SeaQuest root files.")
    parser.add_argument("--input", required=True, help="Absolute path to the input ROOT file")
    parser.add_argument("--output", required=True, help="Absolute path to the output ROOT file")
    args = parser.parse_args()

    chuck_cuts = load_cut_module()

    print(f"-> Opening: {os.path.basename(args.input)}")
    with uproot.open(args.input) as infile:
        tree_result = infile["result"]
        tree_result_mix = infile["result_mix"]

        # Apply cuts to both trees with the requested parameters
        print(f"   Applying cuts to 'result' in {os.path.basename(args.input)}...")
        filtered_result = chuck_cuts.apply_cuts(
            tree_result, 
            is_mc=False, 
            lower_mass_cut=2.0, 
            upper_mass_cut=10.0, 
            upper_pT2_cut=7.0
        )

        print(f"   Applying cuts to 'result_mix' in {os.path.basename(args.input)}...")
        filtered_result_mix = chuck_cuts.apply_cuts(
            tree_result_mix, 
            is_mc=False, 
            lower_mass_cut=2.0, 
            upper_mass_cut=10.0, 
            upper_pT2_cut=7.0
        )

    # Clean up object dtypes before writing
    print(f"   Sanitizing arrays for writing...")
    safe_result = sanitize_for_uproot(filtered_result)
    safe_result_mix = sanitize_for_uproot(filtered_result_mix)

    # Uproot recreate automatically creates TTrees when assigned a dictionary
    print(f"-> Saving to: {os.path.basename(args.output)}")
    with uproot.recreate(args.output) as outfile:
        outfile["result"] = safe_result
        outfile["result_mix"] = safe_result_mix

    print(f"✓ Finished processing: {os.path.basename(args.input)}\n")

if __name__ == "__main__":
    main()