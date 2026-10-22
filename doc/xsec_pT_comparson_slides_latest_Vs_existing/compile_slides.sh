#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Generate the .tex file
echo "Generating LaTeX source..."
python3 generate_beamer.py

# Ensure pdflatex is available
if ! command -v pdflatex &> /dev/null
then
    echo "pdflatex could not be found. Please ensure TeX Live or MiKTeX is installed."
    exit 1
fi

# Compile the LaTeX document (Run twice for page numbers and references)
echo "Compiling PDF (Pass 1)..."
pdflatex -interaction=nonstopmode comparison_slides.tex > /dev/null

echo "Compiling PDF (Pass 2)..."
pdflatex -interaction=nonstopmode comparison_slides.tex > /dev/null

echo "--------------------------------------------------"
echo "Success! Presentation compiled to: comparison_slides.pdf"

# Optional cleanup of LaTeX auxiliary files
rm -f comparison_slides.aux comparison_slides.log comparison_slides.nav comparison_slides.out comparison_slides.snm comparison_slides.toc