#!/usr/bin/env bash
set -e

PYTHON_SCRIPT="generate_beamer_slides.py"
TEX_FILE="dy_xsec_progress.tex"
PDF_FILE="${TEX_FILE%.tex}.pdf"
LOG_FILE="${TEX_FILE%.tex}.log"

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
if ! pdflatex -interaction=nonstopmode "${TEX_FILE}" > /dev/null; then
    echo "[ERROR] pdflatex failed on Pass 1. Showing last 25 lines of ${LOG_FILE}:"
    tail -n 25 "${LOG_FILE}"
    exit 1
fi

echo "========================================================"
echo " Step 3: Running pdflatex (Pass 2/2 - updating Outline)..."
echo "========================================================"
if ! pdflatex -interaction=nonstopmode "${TEX_FILE}" > /dev/null; then
    echo "[ERROR] pdflatex failed on Pass 2. Showing last 25 lines of ${LOG_FILE}:"
    tail -n 25 "${LOG_FILE}"
    exit 1
fi

# Optional cleanup of auxiliary LaTeX files
rm -f *.aux *.log *.nav *.out *.snm *.toc

echo "========================================================"
echo " Done! Output presentation saved to: ${PDF_FILE}"
echo "========================================================"