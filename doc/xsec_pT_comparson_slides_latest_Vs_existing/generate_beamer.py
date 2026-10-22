import os

# ==========================================
# Configuration
# ==========================================
TEX_FILENAME = "comparison_slides.tex"
#IMAGE_DIR = "~/github/seaquest-dy-1d-abs-xsec/src/xsec_pT/RS67/latest_Vs_existing_comparison/Comparison_Plots/"
IMAGE_DIR = "~/github/seaquest-dy-1d-abs-xsec/src/xsec_pT/RS67/xsec_pT_comparison_plots_latest_Vs_existing/Comparison_Plots/"
AUTHOR = "Chatura Kuruppu"
AFFILIATION = "New Mexico State University"
DATE = r"\today"  # LaTeX will automatically use today's date

def generate_latex():
    # Helper to create a side-by-side slide
    def make_double_slide(title, img_left, img_right, cap_left="Total", cap_right="Mix"):
        template = r"""
\begin{frame}{__TITLE__}
    \begin{columns}
        \begin{column}{0.5\textwidth}
            \centering
            \textbf{__CAP_LEFT__}\\
            \includegraphics[width=\textwidth,height=0.75\textheight,keepaspectratio]{__IMG_LEFT__}
        \end{column}
        \begin{column}{0.5\textwidth}
            \centering
            \textbf{__CAP_RIGHT__}\\
            \includegraphics[width=\textwidth,height=0.75\textheight,keepaspectratio]{__IMG_RIGHT__}
        \end{column}
    \end{columns}
\end{frame}
"""
        return template.replace("__TITLE__", title)\
                       .replace("__CAP_LEFT__", cap_left)\
                       .replace("__CAP_RIGHT__", cap_right)\
                       .replace("__IMG_LEFT__", img_left)\
                       .replace("__IMG_RIGHT__", img_right)

    # Helper to create a single image slide
    def make_single_slide(title, img_center):
        template = r"""
\begin{frame}{__TITLE__}
    \centering
    \includegraphics[width=0.7\textwidth,height=0.8\textheight,keepaspectratio]{__IMG_CENTER__}
\end{frame}
"""
        return template.replace("__TITLE__", title)\
                       .replace("__IMG_CENTER__", img_center)

    # --- LaTeX Preamble & Static Slides ---
    latex_doc = r"""\documentclass[aspectratio=169]{beamer}
\usetheme{Madrid}
\usecolortheme{default}

\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{booktabs}

% Note the double curly braces are required by LaTeX for graphicspath
\graphicspath{{__IMAGE_DIR__/}}

\title{Cross-Section Comparison: Latest vs Existing using RS67}
\author{__AUTHOR__}
\institute{__AFFILIATION__}
\date{__DATE__}

\begin{document}

\begin{frame}
    \titlepage
\end{frame}

% --- Slide 01: Input ROOT Files ---
\begin{frame}{Input ROOT Files Used}
    \textbf{Data Files:}
    \begin{itemize}
        \item \texttt{merged\_RS67\_3089\_LH2.root}
        \item \texttt{merged\_RS67\_3089\_LD2.root}
        \item \texttt{merged\_RS67\_3089\_Flask.root}
    \end{itemize}
    \vspace{0.2cm}
    
    \textbf{MC Files (Acceptance Correction):}
    \begin{itemize}
        \item \texttt{rs67\_lh2\_acc.root}
        \item \texttt{rs67\_ld2\_acc.root}
    \end{itemize}
    \vspace{0.2cm}

    \textbf{MC Files (Reconstruction Efficiency):}
    \begin{itemize}
        \item \texttt{rs67\_lh2\_eff.root}
        \item \texttt{rs67\_ld2\_eff.root}
    \end{itemize}
\end{frame}

% --- Slide 02: Event Selection ---
\begin{frame}{Event Selection (chuck\_cuts\_2111-v42)}
    \small
    \textbf{Dimuon Kinematics \& Quality:}
    \begin{itemize}
        \item $4.2 < M_{\mu\mu} < 8.8$ GeV (or dynamically adjusted)
        \item $-0.1 < x_F < 0.95$ (Standard integration window $0.0 \leq x_F < 0.80$)
        \item $0.05 < x_T \leq 0.58$, $|\cos\theta| < 0.5$
        \item Target-dump vertex separation: $z_{vtx} \in (-280, -5)$ cm
        \item Transverse momentum bounds \& $\chi^2_{\mu\mu} < 18$
    \end{itemize}
    \textbf{Single Track Quality:}
    \begin{itemize}
        \item $9 < p_{z,st1} < 75$ GeV, Total Hits $> 13$
        \item $\chi^2_{target} < 15$, Target \& Dump spatial back-tracking matching
        \item $p_T$ kick match across FMAG ($\approx 0.416$ GeV)
    \end{itemize}
    \textbf{Combinatorial \& Occupancy:}
    \begin{itemize}
        \item Opposite half tracking ($y_{1,st3} \times y_{2,st3} < 0$)
        \item St1 total hits $> 8$, Overall total hits $> 29$
        \item Chamber Multiplicity: $D_1, D_2, D_3 < 400$ and $20 \leq D_1 < 385$
    \end{itemize}
\end{frame}
"""

    # Inject variables into the preamble
    latex_doc = latex_doc.replace("__IMAGE_DIR__", IMAGE_DIR)\
                         .replace("__AUTHOR__", AUTHOR)\
                         .replace("__AFFILIATION__", AFFILIATION)\
                         .replace("__DATE__", DATE)

    # --- Slides 03, 04, 05: Reco Efficiency ---
    latex_doc += make_double_slide("Reconstruction Efficiency Comparison (LH2)", "Comparison_E_total_reco_LH2.pdf", "Comparison_E_mix_reco_LH2.pdf")
    latex_doc += make_double_slide("Reconstruction Efficiency Comparison (LD2)", "Comparison_E_total_reco_LD2.pdf", "Comparison_E_mix_reco_LD2.pdf")
    latex_doc += make_double_slide("Reconstruction Efficiency Comparison (Flask)", "Comparison_E_total_reco_Flask.pdf", "Comparison_E_mix_reco_Flask.pdf")

    # --- Slides 06, 07, 08: Final Efficiency ---
    latex_doc += make_double_slide("Final Efficiency Comparison (LH2)", "Comparison_E_total_final_LH2.pdf", "Comparison_E_mix_final_LH2.pdf")
    latex_doc += make_double_slide("Final Efficiency Comparison (LD2)", "Comparison_E_total_final_LD2.pdf", "Comparison_E_mix_final_LD2.pdf")
    latex_doc += make_double_slide("Final Efficiency Comparison (Flask)", "Comparison_E_total_final_Flask.pdf", "Comparison_E_mix_final_Flask.pdf")

    # --- Slide 09: Signal Efficiency LH2 vs LD2 ---
    latex_doc += make_double_slide("Signal Efficiency Comparison (LH2 vs LD2)", "Comparison_E_final_signal_LH2.pdf", "Comparison_E_final_signal_LD2.pdf", "LH2 Target", "LD2 Target")

    # --- Slide 10: Signal Efficiency Flask ---
    latex_doc += make_single_slide("Signal Efficiency Comparison (Flask)", "Comparison_E_final_signal_Flask.pdf")

    # --- Slide 11: Cross-Section Comparison ---
    latex_doc += make_double_slide("Single Differential Cross-Section Comparison", "Comparison_CrossSection_LH2_geom_vs_pT.pdf", "Comparison_CrossSection_LD2_geom_vs_pT.pdf", "LH2 Target", "LD2 Target")

    latex_doc += r"\end{document}"

    # Write to file
    with open(TEX_FILENAME, "w") as f:
        f.write(latex_doc)
        
    print(f"Successfully generated {TEX_FILENAME}")

if __name__ == "__main__":
    generate_latex()