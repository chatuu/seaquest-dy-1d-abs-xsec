#!/bin/bash

# Define directories
BASE_DIR="$HOME/github/seaquest-dy-1d-abs-xsec"
INPUT_DIR="$BASE_DIR/root_files/data/master_files"
OUTPUT_DIR="$BASE_DIR/root_files/data/chuck_cuts_applied_for_unfolding"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Define the target ROOT files
FILES=(
    "merged_RS67_3089_LH2.root"
    "merged_RS67_3089_LD2.root"
    "merged_RS67_3089_Flask.root"
)

echo "Starting parallel processing of ${#FILES[@]} ROOT files..."

# Loop over files and run the Python script in the background
for FILE in "${FILES[@]}"; do
    INPUT_PATH="$INPUT_DIR/$FILE"
    OUTPUT_PATH="$OUTPUT_DIR/truncated_${FILE}"
    
    # Run the python script in the background (&)
    python3 trim_root_files.py --input "$INPUT_PATH" --output "$OUTPUT_PATH" &
done

# Wait for all background jobs to complete
wait

echo "All ROOT files successfully processed and saved to $OUTPUT_DIR"
