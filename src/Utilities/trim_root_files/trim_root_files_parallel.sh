#!/bin/bash

# Define directories
BASE_DIR="$HOME/github/seaquest-dy-1d-abs-xsec"
INPUT_DIR="$BASE_DIR/root_files/data/master_files"
OUTPUT_DIR="$BASE_DIR/root_files/data/chuck_cuts_applied_for_unfolding"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Define the target ROOT files
FILES=(
    #"merged_RS57_LH2_1.root"
    #"merged_RS57_LD2_3.root"
    #"merged_RS57_Empty_2.root"
    "merged_RS59_LH2_1.root"
    "merged_RS59_LD2_3.root"
    "merged_RS59_Empty_2.root"
    "merged_RS62_LH2_1.root"
    "merged_RS62_LD2_3.root"
    "merged_RS62_Empty_2.root"
    "merged_RS70_LH2_1.root"
    "merged_RS70_LD2_3.root"
    "merged_RS70_Empty_2.root"
    # "merged_RS57_Empty_2_1138_FinalData.root"
    # "merged_RS57_LD2_3_1138_FinalData.root"
    # "merged_RS57_LH2_1_1138_FinalData.root"
    # "merged_RS59_Empty_2_466_FinalData.root"
    # "merged_RS59_LD2_3_466_FinalData.root"
    # "merged_RS59_LH2_1_465_FinalData.root"
    # "merged_RS62_Empty_2_1234_FinalData.root"
    # "merged_RS62_LD2_3_1237_FinalData.root"
    # "merged_RS62_LH2_1_1234_FinalData.root"
    # "merged_RS70_Empty_2_267_FinalData.root"
    # "merged_RS70_LD2_3_266_FinalData.root"
    # "merged_RS70_LH2_1_264_FinalData.root"
    #"merged_RS67_3089_LH2.root"
    #"merged_RS67_3089_LD2.root"
    #"merged_RS67_3089_Flask.root"
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
