#!/usr/bin/env bash
set -e

PYTHON_SCRIPT="generate_beamer_slides.py"
TEX_FILE="dy_xsec_progress.tex"
PDF_FILE="${TEX_FILE%.tex}.pdf"

echo "========================================================"
echo " Step 1: Generating LaTeX Beamer file via python3..."
echo "========================================================"
python3 "${PYTHON_SCRIPT}"

if [[ ! -f "${TEX_FILE}" ]]; then
    echo "[ERROR] ${TEX_FILE} was not created. Aborting."
    exit 1
fi

echo "========================================================"
echo " Step 2: Running pdflatex (Pass 1/2 - building TOC)..."
echo "========================================================"
pdflatex -interaction=nonstopmode "${TEX_FILE}" > /dev/null

echo "========================================================"
echo " Step 3: Running pdflatex (Pass 2/2 - updating Outline)..."
echo "========================================================"
pdflatex -interaction=nonstopmode "${TEX_FILE}" > /dev/null

# Optional cleanup of auxiliary LaTeX files
rm -f *.aux *.log *.nav *.out *.snm *.toc

echo "========================================================"
echo " Done! Output presentation saved to: ${PDF_FILE}"
echo "========================================================"