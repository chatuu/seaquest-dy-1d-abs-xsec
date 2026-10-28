#!/usr/bin/env bash
set -e

PYTHON_SCRIPT="generate_comparison_slides.py"
TEX_FILE="compare_RS57_yields.tex"
PDF_FILE="${TEX_FILE%.tex}.pdf"

echo "1. Generating Beamer LaTeX file..."
python3 "$PYTHON_SCRIPT"

echo "2. Compiling PDF with pdflatex (Pass 1/2)..."
pdflatex -interaction=nonstopmode "$TEX_FILE" > /dev/null

echo "3. Compiling PDF with pdflatex (Pass 2/2)..."
pdflatex -interaction=nonstopmode "$TEX_FILE" > /dev/null

echo "4. Cleaning up auxiliary LaTeX files..."
rm -f *.aux *.log *.nav *.out *.snm *.toc

echo "Done! Output saved to: $PDF_FILE"