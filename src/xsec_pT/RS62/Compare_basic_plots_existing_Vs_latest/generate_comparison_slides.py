#!/usr/bin/env python3
import os
import re

# Expand '~' to full absolute paths for pdflatex compatibility
new_dir = os.path.expanduser("~/github/seaquest-dy-1d-abs-xsec/src/xsec_pT/RS62")
old_dir = os.path.expanduser("~/github/seaquest-dy-1d-abs-xsec/src/xsec_pT/RS62/previous_xsec_results")

output_tex = "compare_RS62_yields.tex"


def load_and_format_tex_table(filepath):
    """
    Reads a .tex table file and converts 'longtable' into a full-width resized 'tabular'
    so that 10-column systematic tables stack cleanly top-and-bottom on a Beamer slide.
    """
    if not os.path.exists(filepath):
        escaped = os.path.basename(filepath).replace("_", r"\_")
        return rf"\vspace{{0.5cm}}\textbf{{\color{{red}}Missing file:}} \texttt{{{escaped}}}\vspace{{0.5cm}}"

    with open(filepath, "r") as f:
        content = f.read()

    if r"\begin{longtable}" in content and r"\endlastfoot" in content:
        col_match = re.search(r"\\begin\{longtable\}\{([^}]+)\}", content)
        col_spec = col_match.group(1) if col_match else "|c|c|c|c|c|c|c|c|c|c|"

        # Extract header block between first \hline and \endfirsthead
        pre_firsthead = content.split(r"\endfirsthead")[0]
        first_hline_idx = pre_firsthead.find(r"\hline")
        header_block = pre_firsthead[first_hline_idx:].strip() if first_hline_idx != -1 else r"\hline"

        # Extract data rows between \endlastfoot and \end{longtable}
        body_block = content.split(r"\endlastfoot")[1].split(r"\end{longtable}")[0].strip()

        return (
            r"\resizebox{0.95\textwidth}{!}{%" + "\n"
            r"\setlength{\tabcolsep}{4pt}" + "\n"
            rf"\begin{{tabular}}{{{col_spec}}}" + "\n"
            f"{header_block}\n"
            f"{body_block}\n"
            r"\end{tabular}%" + "\n"
            r"}"
        )

    return rf"\resizebox{{0.95\textwidth}}{{!}}{{\input{{{filepath}}}}}"


# Structured plot sections preserving your exact requested order
sections = [
    (
        "Yield Distributions",
        [
            ("Y_total_LH2.pdf",   r"$\text{LH}_2$ Target: Total Yield (\texttt{Y\_total\_LH2.pdf})"),
            ("Y_mix_LH2.pdf",     r"$\text{LH}_2$ Target: Mixed Yield (\texttt{Y\_mix\_LH2.pdf})"),
            ("Y_total_LD2.pdf",   r"$\text{LD}_2$ Target: Total Yield (\texttt{Y\_total\_LD2.pdf})"),
            ("Y_mix_LD2.pdf",     r"$\text{LD}_2$ Target: Mixed Yield (\texttt{Y\_mix\_LD2.pdf})"),
            ("Y_total_Flask.pdf", r"Empty Flask: Total Yield (\texttt{Y\_total\_Flask.pdf})"),
            ("Y_mix_Flask.pdf",   r"Empty Flask: Mixed Yield (\texttt{Y\_mix\_Flask.pdf})"),
        ],
    ),
    (
        "Efficiency Distributions",
        [
            # LH2 Efficiency Plots
            ("E_total_reco_LH2.pdf",  r"$\text{LH}_2$ Target: Total Reco Efficiency (\texttt{E\_total\_reco\_LH2.pdf})"),
            ("E_total_hodo_LH2.pdf",  r"$\text{LH}_2$ Target: Total Hodo Efficiency (\texttt{E\_total\_hodo\_LH2.pdf})"),
            ("E_total_final_LH2.pdf", r"$\text{LH}_2$ Target: Total Final Efficiency (\texttt{E\_total\_final\_LH2.pdf})"),
            ("E_mix_reco_LH2.pdf",    r"$\text{LH}_2$ Target: Mixed Reco Efficiency (\texttt{E\_mix\_reco\_LH2.pdf})"),
            ("E_mix_hodo_LH2.pdf",    r"$\text{LH}_2$ Target: Mixed Hodo Efficiency (\texttt{E\_mix\_hodo\_LH2.pdf})"),
            ("E_mix_final_LH2.pdf",   r"$\text{LH}_2$ Target: Mixed Final Efficiency (\texttt{E\_mix\_final\_LH2.pdf})"),
            # LD2 Efficiency Plots
            ("E_total_reco_LD2.pdf",  r"$\text{LD}_2$ Target: Total Reco Efficiency (\texttt{E\_total\_reco\_LD2.pdf})"),
            ("E_total_hodo_LD2.pdf",  r"$\text{LD}_2$ Target: Total Hodo Efficiency (\texttt{E\_total\_hodo\_LD2.pdf})"),
            ("E_total_final_LD2.pdf", r"$\text{LD}_2$ Target: Total Final Efficiency (\texttt{E\_total\_final\_LD2.pdf})"),
            ("E_mix_reco_LD2.pdf",    r"$\text{LD}_2$ Target: Mixed Reco Efficiency (\texttt{E\_mix\_reco\_LD2.pdf})"),
            ("E_mix_hodo_LD2.pdf",    r"$\text{LD}_2$ Target: Mixed Hodo Efficiency (\texttt{E\_mix\_hodo\_LD2.pdf})"),
            ("E_mix_final_LD2.pdf",   r"$\text{LD}_2$ Target: Mixed Final Efficiency (\texttt{E\_mix\_final\_LD2.pdf})"),
            # Empty Flask Efficiency Plots
            ("E_total_reco_Flask.pdf",  r"Empty Flask: Total Reco Efficiency (\texttt{E\_total\_reco\_Flask.pdf})"),
            ("E_total_hodo_Flask.pdf",  r"Empty Flask: Total Hodo Efficiency (\texttt{E\_total\_hodo\_Flask.pdf})"),
            ("E_total_final_Flask.pdf", r"Empty Flask: Total Final Efficiency (\texttt{E\_total\_final\_Flask.pdf})"),
            ("E_mix_reco_Flask.pdf",    r"Empty Flask: Mixed Reco Efficiency (\texttt{E\_mix\_reco\_Flask.pdf})"),
            ("E_mix_hodo_Flask.pdf",    r"Empty Flask: Mixed Hodo Efficiency (\texttt{E\_mix\_hodo\_Flask.pdf})"),
            ("E_mix_final_Flask.pdf",   r"Empty Flask: Mixed Final Efficiency (\texttt{E\_mix\_final\_Flask.pdf})"),
            # Final Signal Efficiency Plots
            ("E_final_signal_LH2.pdf",   r"$\text{LH}_2$ Target: Final Signal Efficiency (\texttt{E\_final\_signal\_LH2.pdf})"),
            ("E_final_signal_LD2.pdf",   r"$\text{LD}_2$ Target: Final Signal Efficiency (\texttt{E\_final\_signal\_LD2.pdf})"),
            ("E_final_signal_Flask.pdf", r"Empty Flask: Final Signal Efficiency (\texttt{E\_final\_signal\_Flask.pdf})"),
        ],
    ),
    (
        r"Corrected \& Subtracted Yields",
        [
            # Corrected Yields
            ("Y_corrected_LH2.pdf",   r"$\text{LH}_2$ Target: Corrected Yield (\texttt{Y\_corrected\_LH2.pdf})"),
            ("Y_corrected_LD2.pdf",   r"$\text{LD}_2$ Target: Corrected Yield (\texttt{Y\_corrected\_LD2.pdf})"),
            ("Y_corrected_Flask.pdf", r"Empty Flask: Corrected Yield (\texttt{Y\_corrected\_Flask.pdf})"),
            # Subtracted Corrected Yields
            ("Y_corrected_Subtracted_LH2.pdf", r"$\text{LH}_2$ Target: Subtracted Corrected Yield (\texttt{Y\_corrected\_Subtracted\_LH2.pdf})"),
            ("Y_corrected_Subtracted_LD2.pdf", r"$\text{LD}_2$ Target: Subtracted Corrected Yield (\texttt{Y\_corrected\_Subtracted\_LD2.pdf})"),
        ],
    ),
    (
        r"Cross Sections \& Ratios",
        [
            ("CrossSection_LD2_geom_vs_pT.pdf",          r"$\text{LD}_2$ Cross Section vs.\ $p_T$ (\texttt{CrossSection\_LD2\_geom\_vs\_pT.pdf})"),
            ("CrossSection_LH2_geom_vs_pT.pdf",          r"$\text{LH}_2$ Cross Section vs.\ $p_T$ (\texttt{CrossSection\_LH2\_geom\_vs\_pT.pdf})"),
            ("CrossSection_Ratio_pd_2pp_vs_pT_geom.pdf", r"Cross Section Ratio $\sigma_{pd}/2\sigma_{pp}$ vs.\ $p_T$ (\texttt{CrossSection\_Ratio\_pd\_2pp\_vs\_pT\_geom.pdf})"),
            ("Combined_XSec_Ratio_vs_pT_geom.pdf",       r"Combined Cross Section \& Ratio vs.\ $p_T$ (\texttt{Combined\_XSec\_Ratio\_vs\_pT\_geom.pdf})"),
        ],
    ),
]

# Systematic tables to compare at the end of the slides
sys_tables = [
    ("Table_Systematics_LH2.tex", r"$\text{LH}_2$ Target: Systematic Components (\texttt{Table\_Systematics\_LH2.tex})"),
    ("Table_Systematics_LD2.tex", r"$\text{LD}_2$ Target: Systematic Components (\texttt{Table\_Systematics\_LD2.tex})"),
]

latex_content = r"""\documentclass[aspectratio=169, 10pt]{beamer}
\usetheme{Madrid}
\usecolortheme{whale}
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{array}

\providecommand{\diffd}{\mathrm{d}}

\title[RS62 XSec Comparison]{RS62 Yield, Efficiency \& Cross-Section Comparison}
\subtitle{Existing vs.\ Latest Results}
\date{\today}

\begin{document}

\begin{frame}
    \titlepage
\end{frame}

\begin{frame}{Single Differential Cross-Section Formalism ($\diffd\sigma / \diffd p_T$)}
    \textbf{$\text{LH}_2$ ($pp$) Single Differential Cross Section:}
    \begin{equation}
        \frac{\diffd\sigma_{pp}}{\diffd p_{T}} = \frac{1}{\epsilon_{\text{acc}} \mathcal{L} \Delta p_{T}} 
        \left[ 
            \frac{Y^{\text{LH2}}_{\text{total}} - Y^{\text{LH2}}_{\text{mixed}}}{\langle\epsilon^{\text{LH2}}_{\text{signal}}\rangle} 
- \frac{I_{\text{LH2}}}{I_{\text{flask}}} 
            \left( \frac{Y^{\text{flask}}_{\text{total}} - Y^{\text{flask}}_{\text{mixed}}}{\langle\epsilon^{\text{flask}}_{\text{signal}}\rangle} \right)
        \right]
        \label{eq:modified_cross_section_pt}
    \end{equation}

    \vspace{0.3em}
    \textbf{$\text{LD}_2$ ($pd$) Single Differential Cross Section:}
    {\small
    \begin{eqnarray}
        \frac{\diffd\sigma_{pd}}{\diffd p_{T}} &=& \frac{1}{\epsilon_{\text{acc}} \mathcal{L} \Delta p_{T}} 
        \left(
        \left[ 
            \frac{Y^{\text{LD2}}_{\text{total}} - Y^{\text{LD2}}_{\text{mixed}}}{\langle\epsilon^{\text{LD2}}_{\text{signal}}\rangle} 
- \frac{I_{\text{LD2}}}{I_{\text{flask}}} 
            \left( \frac{Y^{\text{flask}}_{\text{total}} - Y^{\text{flask}}_{\text{mixed}}}{\langle\epsilon^{\text{flask}}_{\text{signal}}\rangle} \right)
        \right] \right. \nonumber \\
        & & \left. - \frac{T_{HD}}{T_{HH}} \frac{I_{\rm LD2}}{I_{\rm LH2}}\left[ 
            \frac{Y^{\text{LH2}}_{\text{total}} - Y^{\text{LH2}}_{\text{mixed}}}{\langle\epsilon^{\text{LH2}}_{\text{signal}}\rangle} 
- \frac{I_{\text{LH2}}}{I_{\text{flask}}} 
            \left( \frac{Y^{\text{flask}}_{\text{total}} - Y^{\text{flask}}_{\text{mixed}}}{\langle\epsilon^{\text{flask}}_{\text{signal}}\rangle} \right)
        \right]
        \right)
        \label{eq:modified_cross_section_pd_pt}
    \end{eqnarray}
    }
\end{frame}

\begin{frame}{Table of Contents}
    \tableofcontents
\end{frame}
"""

for section_title, plot_list in sections:
    latex_content += f"\n\\section{{{section_title}}}\n"

    for filename, slide_title in plot_list:
        old_path = os.path.join(old_dir, filename)
        new_path = os.path.join(new_dir, filename)
        escaped_name = filename.replace("_", r"\_")

        # Build left column (Existing plot)
        if os.path.exists(old_path):
            left_graphic = rf"\includegraphics[width=\textwidth, height=0.72\textheight, keepaspectratio]{{{old_path}}}"
        else:
            left_graphic = rf"\vspace{{2cm}}\textbf{{\color{{red}}Missing file:}} \\ \texttt{{{escaped_name}}}"

        # Build right column (Latest plot)
        if os.path.exists(new_path):
            right_graphic = rf"\includegraphics[width=\textwidth, height=0.72\textheight, keepaspectratio]{{{new_path}}}"
        else:
            right_graphic = rf"\vspace{{2cm}}\textbf{{\color{{red}}Missing file:}} \\ \texttt{{{escaped_name}}}"

        frame_block = rf"""
\begin{{frame}}{{{slide_title}}}
    \begin{{columns}}[T, onlytextwidth]
        \begin{{column}}{{0.49\textwidth}}
            \centering
            \textbf{{Existing Results}}\\[0.3em]
            {left_graphic}
        \end{{column}}
        \begin{{column}}{{0.49\textwidth}}
            \centering
            \textbf{{Latest Results}}\\[0.3em]
            {right_graphic}
        \end{{column}}
    \end{{columns}}
\end{{frame}}
"""
        latex_content += frame_block

# Append Systematic Uncertainty Table comparison slides (Top: Latest, Bottom: Existing)
latex_content += "\n\\section{Systematic Uncertainties}\n"

for tex_filename, slide_title in sys_tables:
    old_tex_path = os.path.join(old_dir, tex_filename)
    new_tex_path = os.path.join(new_dir, tex_filename)

    top_table = load_and_format_tex_table(new_tex_path)
    bottom_table = load_and_format_tex_table(old_tex_path)

    table_frame = rf"""
\begin{{frame}}{{{slide_title}}}
    \centering
    \textbf{{Latest Results}}\\[0.2em]
    {top_table}

    \vspace{{0.6em}}

    \textbf{{Existing Results}}\\[0.2em]
    {bottom_table}
\end{{frame}}
"""
    latex_content += table_frame

# Append final Cross-Section Comparison slide (LH2 on left, LD2 on right)
lh2_comp_path = "/root/github/seaquest-dy-1d-abs-xsec/src/xsec_pT/RS62/temp/CrossSection_Comparison_LH2_geom_vs_pT.pdf"
ld2_comp_path = "/root/github/seaquest-dy-1d-abs-xsec/src/xsec_pT/RS62/temp/CrossSection_Comparison_LD2_geom_vs_pT.pdf"

if os.path.exists(lh2_comp_path):
    lh2_comp_graphic = rf"\includegraphics[width=\textwidth, height=0.72\textheight, keepaspectratio]{{{lh2_comp_path}}}"
else:
    escaped_lh2 = os.path.basename(lh2_comp_path).replace("_", r"\_")
    lh2_comp_graphic = rf"\vspace{{2cm}}\textbf{{\color{{red}}Missing file:}} \\ \texttt{{{escaped_lh2}}}"

if os.path.exists(ld2_comp_path):
    ld2_comp_graphic = rf"\includegraphics[width=\textwidth, height=0.72\textheight, keepaspectratio]{{{ld2_comp_path}}}"
else:
    escaped_ld2 = os.path.basename(ld2_comp_path).replace("_", r"\_")
    ld2_comp_graphic = rf"\vspace{{2cm}}\textbf{{\color{{red}}Missing file:}} \\ \texttt{{{escaped_ld2}}}"

latex_content += rf"""
\begin{{frame}}{{Cross-Section Comparison vs.\ $p_T$: $\text{{LH}}_2$ and $\text{{LD}}_2$}}
    \begin{{columns}}[T, onlytextwidth]
        \begin{{column}}{{0.49\textwidth}}
            \centering
            \textbf{{$\text{{LH}}_2$ Plot}}\\[0.3em]
            {lh2_comp_graphic}
        \end{{column}}
        \begin{{column}}{{0.49\textwidth}}
            \centering
            \textbf{{$\text{{LD}}_2$ Plot}}\\[0.3em]
            {ld2_comp_graphic}
        \end{{column}}
    \end{{columns}}
\end{{frame}}
"""

latex_content += "\n\\end{document}\n"

with open(output_tex, "w") as f:
    f.write(latex_content)

print(f"Successfully generated LaTeX file: {output_tex}")