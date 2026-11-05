#!/usr/bin/env bash
# build_tables_pdf.sh
# Generates the master LaTeX file with python3 and compiles it into a PDF with pdflatex.

set -e
#rm *.tex
#rm *.pdf
#python3 generate_master_tex.py

PYTHON_SCRIPT="generate_master_tex.py"
MASTER_TEX="All_Comparison_Tables.tex"
OUTPUT_PDF="All_Comparison_Tables.pdf"

# Optional: Run compare_xsec_tables.py first if the individual .tex tables aren't generated yet
if [ ! -f "Table_Comparison_RS57_LH2.tex" ] && [ -f "compare_xsec_tables.py" ]; then
    echo ">>> Generating individual .tex tables via compare_xsec_tables.py..."
    python3 compare_xsec_tables.py
fi

echo ">>> Running ${PYTHON_SCRIPT} to build ${MASTER_TEX}..."
python3 "${PYTHON_SCRIPT}"

echo ">>> Compiling ${MASTER_TEX} with pdflatex (Pass 1/2)..."
pdflatex -interaction=nonstopmode "${MASTER_TEX}" > /dev/null

echo ">>> Compiling ${MASTER_TEX} with pdflatex (Pass 2/2 for longtable & TOC alignment)..."
pdflatex -interaction=nonstopmode "${MASTER_TEX}" > /dev/null

# Clean up auxiliary LaTeX build artifacts
rm -f All_Comparison_Tables.aux All_Comparison_Tables.log All_Comparison_Tables.out All_Comparison_Tables.toc

echo "✔ Successfully generated ${OUTPUT_PDF}"