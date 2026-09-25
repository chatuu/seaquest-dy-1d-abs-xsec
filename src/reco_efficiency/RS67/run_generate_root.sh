#!/bin/bash

# Directory paths setup (using $HOME for safer environment evaluation inside strings)
INPUT_DIR="$HOME/github/seaquest-dy-1d-abs-xsec/root_files/data/chuck_cuts_applied_for_unfolding/"
NPZ_DIR="$HOME/github/seaquest-dy-1d-abs-xsec/src/reco_efficiency/global_efficiency_curves/"

# Define arrays for the Roadsets and Targets
ROADSETS=("RS67")
TARGETS=("LH2" "LD2" "Flask")

# Loop over roadsets and targets
for RS in "${ROADSETS[@]}"; do
    for TARGET in "${TARGETS[@]}"; do
        INPUT_FILE=`find ${INPUT_DIR} -maxdepth 1 -type f -name "truncated_merged_*${RS}_*${TARGET}.root"`
        
        # Save output in the current script location without a path prefix
        OUTPUT_FILE="merged_${RS}_${TARGET}_recoeff_unfolding_new.root"
        
        # Map target to its specific .npz configuration file
        if [ "$TARGET" == "Flask" ]; then
            CONFIG_FILE="${NPZ_DIR}/rs67_avg_eff_D1.npz"
        elif [ "$TARGET" == "LD2" ]; then
            CONFIG_FILE="${NPZ_DIR}/rs67_ld2_eff_D1.npz"
        elif [ "$TARGET" == "LH2" ]; then
            CONFIG_FILE="${NPZ_DIR}/rs67_lh2_eff_D1.npz"
        else
            echo "Unknown target $TARGET. Skipping..."
            continue
        fi

        # Check if the input file actually exists before running
        if [ ! -f "$INPUT_FILE" ]; then
            echo "Error: Input file '$INPUT_FILE' not found. Skipping $TARGET for$RS..."
            echo "--------------------------------------------------"
            continue
        fi

        echo "Executing python script for Roadset: $RS, Target:$TARGET..."
        python3 GenerateROOTFiles_unfolding.py \
            --input "$INPUT_FILE" \
            --output "$OUTPUT_FILE" \
            --target "$TARGET" \
            --config "$CONFIG_FILE" &
            
        echo "Started processing $TARGET for$RS in background."
        echo "--------------------------------------------------"
        
    done
done

# Wait for all background python processes to finish
wait
echo "All files processed successfully."