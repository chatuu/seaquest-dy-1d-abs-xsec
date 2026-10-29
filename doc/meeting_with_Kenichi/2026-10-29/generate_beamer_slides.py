#!/usr/bin/env python3
"""
Script to generate LaTeX Beamer slides for the Drell-Yan absolute
cross-section measurements progress report.
"""

OUTPUT_TEX = "dy_xsec_progress.tex"
ROADSETS = ["RS57", "RS59", "RS62", "RS67", "RS70"]


def get_preamble() -> str:
    return r"""\documentclass[aspectratio=169, 10pt]{beamer}

\usetheme{Madrid}
\usecolortheme{default}

\usepackage{graphicx}
\usepackage{multicol}
\usepackage{amsmath, amssymb}
\usepackage{booktabs}
\usepackage{hyperref}
\usepackage{xcolor}

% Safe image inclusion helper: renders plot if present, or a placeholder box if missing
\newcommand{\safeinclude}[2][\textwidth]{%
    \IfFileExists{#2}{%
        \includegraphics[width=#1]{#2}%
    }{%
        \fbox{\parbox[c][0.35\textheight][c]{#1}{\centering \tiny \textbf{File not found:}\\ \texttt{\detokenize{#2}}}}%
    }%
}

\title[DY Absolute Cross-Section]{Current status of the DY absolute cross-section measurements study}
\author[C. Kuruppu]{Chatura Kuruppu}
\institute[NMSU]{New Mexico State University}
\date{\today}

\begin{document}

% --- TITLE SLIDE ---
\begin{frame}
    \titlepage
\end{frame}

% --- DYNAMIC OUTLINE SLIDE ---
\begin{frame}{Outline}
    \tableofcontents[hideallsubsections]
\end{frame}
"""


def get_input_files_slide() -> str:
    return r"""
% ==========================================
% SECTION: INPUT FILES USED
% ==========================================
\section{Events from Runs 2 and 3 (Input Files Used)}

% --- INPUT FILES SLIDE ---
\begin{frame}{Events from runs 2 and 3 (Input Files Used)}
\textbf{Note:} Currently using all the runs saved in runs 2 and 3.
\vspace{0.3cm}
\tiny\\
\textbf{Harsha's ROOT files:} \\
\texttt{/seaquest/users/harshaka/e906\_project/e906-root-ana/work\_gpvm/scripts/results\_runFinalTree/merged\_results\_e906\_mixing/:}
\begin{multicols}{2}
\begin{itemize}
    \item \texttt{merged\_RS57\_LH2\_1\_1138.root}
    \item \texttt{merged\_RS57\_LD2\_3\_1138.root}
    \item \texttt{merged\_RS57\_Empty\_2\_1138.root}
    \item \texttt{merged\_RS59\_LH2\_1\_465.root}
    \item \texttt{merged\_RS59\_LD2\_3\_466.root}
    \item \texttt{merged\_RS59\_Empty\_2\_466.root}
    \item \texttt{merged\_RS62\_LH2\_1\_1234.root}
    \item \texttt{merged\_RS62\_LD2\_3\_1237.root}
    \item \texttt{merged\_RS62\_Empty\_2\_1234.root}
    \item \texttt{merged\_RS70\_LH2\_1\_264.root}
    \item \texttt{merged\_RS70\_LD2\_3\_266.root}
    \item \texttt{merged\_RS70\_Empty\_2\_267.root}
\end{itemize}
\end{multicols}
\textbf{Abi's ROOT files:} \\
\texttt{/seaquest/users/apun/e906\_projects/rs67\_merged\_files/:}
\begin{multicols}{1}
\begin{itemize}
    \item \texttt{merged\_RS67\_3089LH2.root}
    \item \texttt{merged\_RS67\_3089LD2.root}
    \item \texttt{merged\_RS67\_3089flask.root}
\end{itemize}
\end{multicols}

\normalsize
\end{frame}
"""


def get_event_selection_slide() -> str:
    return r"""
% ==========================================
% SECTION: EVENT SELECTION USED
% ==========================================
\section{Event Selection Used (DocDB 2111-V42 \& Fiducial Cuts)}

\begin{frame}{Event Selection Used: Chuck Cuts (DocDB 2111-V42) \& Fiducial Cuts}
\scriptsize
\textbf{Chuck Cuts (\texttt{DocDB2111-V42})} with \texttt{beam\_offset} $= 1.6\text{ cm}$ and mass \texttt{cut} $= 4.2\text{ GeV}/c^2$:
\vspace{-0.15cm}
\begin{columns}[T, onlytextwidth]
    % Left Column: Dimuon & Single Track Cuts
    \begin{column}{0.49\textwidth}
        \begin{block}{\scriptsize Dimuon Cuts (\texttt{dimuon\_cut\_2111\_v42})}
            \tiny
            \begin{itemize}
                \item \textbf{Vertex:} $|dx| < 0.25$, $|dy - 1.6| < 0.22$, $-280 < dz < -5\text{ cm}$
                \item \textbf{Transverse Vertex:} $dx^2 + (dy - 1.6)^2 < 0.06\text{ cm}^2$
                \item \textbf{Momentum:} $|dp_x| < 1.8$, $|dp_y| < 2.0$, $dp_x^2 + dp_y^2 < 5.0\text{ (GeV}/c)^2$, $38 < dp_z < 116\text{ GeV}/c$
                \item \textbf{Kinematics:} $4.2 < \text{mass} < 8.8\text{ GeV}/c^2$, $-0.1 < x_F < 0.95$, $0.05 < x_T \le 0.58$, $|\cos\theta| < 0.5$
                \item \textbf{Fit \& Separation:} $|\text{trackSeparation}| < 270\text{ cm}$, $\chi^2_{\text{dimuon}} < 18$
            \end{itemize}
        \end{block}

        \begin{block}{\scriptsize Single Track Cuts (\texttt{track1\_cut} \& \texttt{track2\_cut}, $i=1,2$)}
            \tiny
            \begin{itemize}
                \item \textbf{Target/Dump $\chi^2$:} $\chi^2_{i,\text{target}} < 15$, $\chi^2_{i,\text{target}} < 1.5\chi^2_{i,\text{upstream}}$, $\chi^2_{i,\text{target}} < 1.5\chi^2_{i,\text{dump}}$
                \item \textbf{Track Quality:} $\text{nHits}_i > 13$, $\chi^2_i / (\text{nHits}_i - 5) < 12$, $-320 < z_{i,v} < -5\text{ cm}$
                \item \textbf{Apertures:} $x_{i,t}^2 + (y_{i,t} - 1.6)^2 < 320$, $16 < x_{i,d}^2 + (y_{i,d} - 1.6)^2 < 1100\text{ cm}^2$
                \item \textbf{Station 1 \& 3:} $9 < p_{z,i}^{\text{st1}} < 75$, $|p_{y,i}^{\text{st1}}| > 0.02\text{ GeV}/c$, $y_{i,\text{st1}}/y_{i,\text{st3}} < 1$, $y_{i,\text{st1}} \cdot y_{i,\text{st3}} > 0$
                \item \textbf{$\Delta p$ Matching:} $||p_{x,i}^{\text{st1}} - p_{x,i}^{\text{st3}}| - 0.416| < 0.008$, $|p_{y,i}^{\text{st1}} - p_{y,i}^{\text{st3}}| < 0.008$, $|p_{z,i}^{\text{st1}} - p_{z,i}^{\text{st3}}| < 0.08$
            \end{itemize}
        \end{block}
    \end{column}

    % Right Column: Combined Tracks, Occupancy, and Fiducial Cuts
    \begin{column}{0.49\textwidth}
        \begin{block}{\scriptsize Track Pair Cuts (\texttt{tracks\_cut\_2111\_v42})}
            \tiny
            \begin{itemize}
                \item $|\chi^2_{1,\text{target}} + \chi^2_{2,\text{target}} - \chi^2_{\text{dimuon}}| < 2.0$
                \item $y_{1,\text{st3}} \cdot y_{2,\text{st3}} < 0$ (opposite top/bottom halves, no beam offset)
                \item $\text{nHits}_1 + \text{nHits}_2 > 29$ and $\text{nHits1St1} + \text{nHits2St1} > 8$
                \item $|x_{1,\text{st1}} + x_{2,\text{st1}}| < 42\text{ cm}$
            \end{itemize}
        \end{block}

        \begin{block}{\scriptsize Occupancy Cuts (\texttt{occ\_cut\_2111\_v42})}
            \tiny
            \begin{itemize}
                \item $D_1 < 400$, $D_2 < 400$, $D_3 < 400$, and $D_1 + D_2 + D_3 < 1000$
                \item \textit{Note:} Intensity cuts (\texttt{intensity\_cut\_2111\_v42}) are not applied.
            \end{itemize}
        \end{block}

        \begin{alertblock}{\scriptsize Additional Fiducial Cut Applied}
            \tiny
            In addition to the Chuck cuts above, we apply the kinematic fiducial cut:
            \[
                (4.2 < \text{mass} < 8.8\text{ GeV}/c^2) \ \& \ (0.0 < x_F < 0.8) \ \& \ (0 < p_T < 1.8\text{ GeV}/c)
            \]
        \end{alertblock}
    \end{column}
\end{columns}
\normalsize
\end{frame}
"""


def get_d1_efficiency_curves_slide() -> str:
    base_dir = "/root/github/seaquest-dy-1d-abs-xsec/src/reco_efficiency/global_efficiency_curves"
    plots = [
        ("Previous Global Curve (All RS)", f"{base_dir}/GlobalEfficiencyCurve.pdf"),
        ("RS57 Efficiency Curve", f"{base_dir}/rs57_avg_eff_D1.pdf"),
        ("RS59 Efficiency Curve", f"{base_dir}/rs59_avg_eff_D1.pdf"),
        ("RS62 Efficiency Curve", f"{base_dir}/rs62_avg_eff_D1.pdf"),
        ("RS67 Efficiency Curve", f"{base_dir}/rs67_avg_eff_D1.pdf"),
        ("RS70 Efficiency Curve", f"{base_dir}/rs70_avg_eff_D1.pdf"),
    ]

    slide = r"""
% ==========================================
% SECTION: NEW RECONSTRUCTION EFFICIENCY CORRECTION (D1-10)
% ==========================================
\section{New Reconstruction Efficiency Correction (D1-10)}

\begin{frame}{New Reconstruction Efficiency Correction (D1-10)}
\centering
\begin{columns}[T, onlytextwidth]
"""
    # Row 1 (first 3 plots)
    for title, path in plots[:3]:
        slide += f"""    \\begin{{column}}{{0.32\\textwidth}}
        \\centering
        \\textbf{{\\tiny {title}}}\\\\[0.1cm]
        \\safeinclude[0.92\\textwidth]{{{path}}}
    \\end{{column}}
"""
    slide += r"""\end{columns}
\vspace{0.15cm}
\begin{columns}[T, onlytextwidth]
"""
    # Row 2 (next 3 plots)
    for title, path in plots[3:]:
        slide += f"""    \\begin{{column}}{{0.32\\textwidth}}
        \\centering
        \\textbf{{\\tiny {title}}}\\\\[0.1cm]
        \\safeinclude[0.92\\textwidth]{{{path}}}
    \\end{{column}}
"""
    slide += r"""\end{columns}
\end{frame}
"""
    return slide


def get_reco_efficiency_comparison_slides(target: str) -> str:
    slides = f"""
% ==========================================
% SECTION: LATEST VS EXISTING RECO EFFICIENCIES ({target})
% ==========================================
\\section{{Latest Vs Existing Reconstruction Efficiencies ({target})}}
"""
    for rs in ROADSETS:
        if rs != "RS67":
            latest_path = f"/root/github/seaquest-dy-1d-abs-xsec/src/xsec_pT/{rs}/E_final_signal_{target}.pdf"
            existing_path = f"/root/github/seaquest-dy-1d-abs-xsec/src/xsec_pT/{rs}/previous_xsec_results/E_final_signal_{target}.pdf"
        else:
            latest_path = f"/root/github/seaquest-dy-1d-abs-xsec/src/xsec_pT/{rs}/E_final_signal_{target}.pdf"
            existing_path = f"/root/github/e906-development/src/xsec_pT/RS67/E_final_signal_{target}.pdf"

        slides += f"""
\\subsection{{{rs} ({target})}}
\\begin{{frame}}{{{rs}: Latest Vs Existing Reconstruction Efficiencies ({target})}}
\\begin{{columns}}[T, onlytextwidth]
    \\begin{{column}}{{0.49\\textwidth}}
        \\centering
        \\textbf{{\\scriptsize Latest Efficiency ({rs} {target})}}\\\\[0.15cm]
        \\safeinclude[0.95\\textwidth]{{{latest_path}}}
    \\end{{column}}
    \\begin{{column}}{{0.49\\textwidth}}
        \\centering
        \\textbf{{\\scriptsize Existing Efficiency ({rs} {target})}}\\\\[0.15cm]
        \\safeinclude[0.95\\textwidth]{{{existing_path}}}
    \\end{{column}}
\\end{{columns}}
\\end{{frame}}
"""
    return slides


def get_acceptance_correction_slides() -> str:
    slides = r"""
% ==========================================
% SECTION: ACCEPTANCE CORRECTIONS
% ==========================================
\section{Acceptance Corrections (LH2 \& LD2)}
"""
    for rs in ROADSETS:
        if rs != "RS67":
            lh2_path = (
                f"/root/github/e906-development/src/NewAcceptanceCorrection/{rs}/"
                f"Existing_Vs_Latest_Acceptance_Comparison/"
                f"Compare_Latest_Vs_Existing_LH2_Acceptance_pT_All_Mass_xF.pdf"
            )
            ld2_path = (
                f"/root/github/e906-development/src/NewAcceptanceCorrection/{rs}/"
                f"Existing_Vs_Latest_Acceptance_Comparison/"
                f"Compare_Latest_Vs_Existing_LD2_Acceptance_pT_All_Mass_xF.pdf"
            )
        else:
            lh2_path = (
                f"/root/github/e906-development/src/Existing_Vs_Latest_Acceptance_Comparison/Compare_Latest_Vs_Existing_LH2_Acceptance_pT_All_Mass_xF.pdf"
            )
            ld2_path = (
                f"/root/github/e906-development/src/Existing_Vs_Latest_Acceptance_Comparison/Compare_Latest_Vs_Existing_LD2_Acceptance_pT_All_Mass_xF.pdf"
            )
        # lh2_path = (
        #     f"/root/github/e906-development/src/NewAcceptanceCorrection/{rs}/"
        #     f"Existing_Vs_Latest_Acceptance_Comparison/"
        #     f"Compare_Latest_Vs_Existing_LH2_Acceptance_pT_All_Mass_xF.pdf"
        # )
        # ld2_path = (
        #     f"/root/github/e906-development/src/NewAcceptanceCorrection/{rs}/"
        #     f"Existing_Vs_Latest_Acceptance_Comparison/"
        #     f"Compare_Latest_Vs_Existing_LD2_Acceptance_pT_All_Mass_xF.pdf"
        # )

        slides += f"""
\\subsection{{{rs} Acceptance Corrections}}
\\begin{{frame}}{{{rs} Acceptance Corrections}}
\\begin{{columns}}[T, onlytextwidth]
    \\begin{{column}}{{0.49\\textwidth}}
        \\centering
        \\textbf{{\\scriptsize LH2 ({rs})}}\\\\[0.15cm]
        \\safeinclude[0.95\\textwidth]{{{lh2_path}}}
    \\end{{column}}
    \\begin{{column}}{{0.49\\textwidth}}
        \\centering
        \\textbf{{\\scriptsize LD2 ({rs})}}\\\\[0.15cm]
        \\safeinclude[0.95\\textwidth]{{{ld2_path}}}
    \\end{{column}}
\\end{{columns}}
\\end{{frame}}
"""
    return slides


def get_all_roadsets_xsec_comparison_slides() -> str:
    lh2_latest = "/root/github/seaquest-dy-1d-abs-xsec/src/xsec_pT/CrossSection_AllRoadsets_LH2_geom_vs_pT.pdf"
    lh2_existing = "/root/github/e906-development/src/xsec_pT/RS57-70_individual_roadsets/AllRoadsets_Overlay_LH2_geom.pdf"

    ld2_latest = "/root/github/seaquest-dy-1d-abs-xsec/src/xsec_pT/CrossSection_AllRoadsets_LD2_geom_vs_pT.pdf"
    ld2_existing = "/root/github/e906-development/src/xsec_pT/RS57-70_individual_roadsets/AllRoadsets_Overlay_LD2_geom.pdf"

    return f"""
% ==========================================
% SECTION: CROSS-SECTION COMPARISON ALL ROADSETS
% ==========================================
\\section{{Cross-Section Comparison All Roadsets (LH2 \\& LD2)}}

\\subsection{{LH2 Cross-Section Comparison All Roadsets}}
\\begin{{frame}}{{LH2 Cross-Section Comparison All Roadsets}}
\\begin{{columns}}[T, onlytextwidth]
    \\begin{{column}}{{0.49\\textwidth}}
        \\centering
        \\textbf{{\\scriptsize Latest (LH2 All Roadsets)}}\\\\[0.15cm]
        \\safeinclude[0.95\\textwidth]{{{lh2_latest}}}
    \\end{{column}}
    \\begin{{column}}{{0.49\\textwidth}}
        \\centering
        \\textbf{{\\scriptsize Existing (LH2 All Roadsets)}}\\\\[0.15cm]
        \\safeinclude[0.95\\textwidth]{{{lh2_existing}}}
    \\end{{column}}
\\end{{columns}}
\\end{{frame}}

\\subsection{{LD2 Cross-Section Comparison All Roadsets}}
\\begin{{frame}}{{LD2 Cross-Section Comparison All Roadsets}}
\\begin{{columns}}[T, onlytextwidth]
    \\begin{{column}}{{0.49\\textwidth}}
        \\centering
        \\textbf{{\\scriptsize Latest (LD2 All Roadsets)}}\\\\[0.15cm]
        \\safeinclude[0.95\\textwidth]{{{ld2_latest}}}
    \\end{{column}}
    \\begin{{column}}{{0.49\\textwidth}}
        \\centering
        \\textbf{{\\scriptsize Existing (LD2 All Roadsets)}}\\\\[0.15cm]
        \\safeinclude[0.95\\textwidth]{{{ld2_existing}}}
    \\end{{column}}
\\end{{columns}}
\\end{{frame}}
"""


def generate_latex_file():
    content = [
        get_preamble(),
        get_input_files_slide(),
        get_event_selection_slide(),
        get_d1_efficiency_curves_slide(),
        get_reco_efficiency_comparison_slides("LH2"),
        get_reco_efficiency_comparison_slides("LD2"),
        get_acceptance_correction_slides(),
        get_all_roadsets_xsec_comparison_slides(),
        "\n\\end{document}\n",
    ]

    with open(OUTPUT_TEX, "w", encoding="utf-8") as f:
        f.write("".join(content))

    print(f"[INFO] Successfully generated LaTeX Beamer file: {OUTPUT_TEX}")


if __name__ == "__main__":
    generate_latex_file()