"""
generate_master_tex.py
Generates a standalone master LaTeX document that includes all roadset comparison
tables in ascending order (RS57 -> RS70), with LH2 first and LD2 second.
"""

import os
import sys

ROADSETS = ["RS57", "RS59", "RS62", "RS67", "RS70"]
TARGETS = ["LH2", "LD2"]
MASTER_TEX_FILENAME = "All_Comparison_Tables.tex"


def main():
    lines = [
        r"\documentclass[11pt, letterpaper]{article}",
        r"\usepackage[margin=0.75in]{geometry}",
        r"\usepackage{longtable}",
        r"\usepackage{array}",
        r"\usepackage{amsmath, amssymb}",
        r"\usepackage{hyperref}",
        r"\hypersetup{colorlinks=true, linkcolor=blue, urlcolor=blue}",
        r"",
        r"\title{\textbf{Drell-Yan Signal Efficiency and Acceptance Comparison Tables \\ (RS57 -- RS70)}}",
        r"\date{\today}",
        r"",
        r"\begin{document}",
        r"\maketitle",
        r"\tableofcontents",
        r"\clearpage",
        r"",
    ]

    missing_files = []

    # 1. Per-Roadset Tables in Ascending Order (RS57 -> RS70), LH2 first then LD2
    for rs in ROADSETS:
        lines.append(rf"\section{{Roadset {rs} Comparison Tables}}")
        for target in TARGETS:
            tex_file = f"Table_Comparison_{rs}_{target}.tex"
            lines.append(rf"\subsection{{{rs} -- {target} Target}}")
            if os.path.exists(tex_file):
                lines.append(rf"\input{{{tex_file}}}")
            else:
                missing_files.append(tex_file)
                lines.append(rf"\textbf{{Warning: File \texttt{{{tex_file}}} not found.}}")
            lines.append(r"")
        lines.append(r"\clearpage")
        lines.append(r"")

    # 2. Combined All-Roadset Summary Tables (LH2 first, then LD2)
    lines.append(r"\section{Combined All-Roadset Comparison Tables (RS57 -- RS70)}")
    for target in TARGETS:
        tex_file = f"Table_Comparison_{target}.tex"
        lines.append(rf"\subsection{{Combined {target} Target (All Roadsets)}}")
        if os.path.exists(tex_file):
            lines.append(rf"\input{{{tex_file}}}")
        else:
            missing_files.append(tex_file)
            lines.append(rf"\textbf{{Warning: File \texttt{{{tex_file}}} not found.}}")
        lines.append(r"\clearpage")
        lines.append(r"")

    lines.append(r"\end{document}")

    with open(MASTER_TEX_FILENAME, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"✔ Generated master LaTeX file: {MASTER_TEX_FILENAME}")
    if missing_files:
        print("⚠ Warning: The following .tex table files were not found in the current directory:")
        for mf in missing_files:
            print(f"  - {mf}")
        sys.exit(1)


if __name__ == "__main__":
    main()