#!/bin/bash

# Define the targets to loop through
TARGETS=("LH2" "LD2" "Flask")

echo "Starting Hodoscope Efficiency calculation for all targets..."

for TARGET in "${TARGETS[@]}"; do
    # Construct the file paths
    INPUT_FILE="/home/ckuruppu/github/seaquest-dy-1d-abs-xsec/src/reco_efficiency/RS67/merged_RS67_${TARGET}_recoeff_unfolding_new.root"
    OUTPUT_FILE="merged_RS67_3089_${TARGET}_recoeff_hodoeff_unfolding_new.root"
    
    echo "--------------------------------------------------"
    echo "Target: $TARGET"
    echo "Input:  $INPUT_FILE"
    echo "Output: $OUTPUT_FILE"
    
    # Verify the input file exists before attempting to run the python script
    if [ ! -f "$INPUT_FILE" ]; then
        echo "Error: Input file '$INPUT_FILE' not found. Skipping $TARGET..."
        continue
    fi
    
    # Execute the python script
    python3 AddHodoEffVarsToROOTFile.py \
        --input "$INPUT_FILE" \
        --output "$OUTPUT_FILE" \
        --target "$TARGET"
        
    echo "Finished processing $TARGET."
done

echo "--------------------------------------------------"
echo "All targets processed successfully."