"""
compare_xsec_tables.py
Generates CSV and LaTeX comparison tables (Latest vs. Previous) for LH2 and LD2
across roadsets RS57, RS59, RS62, RS67, and RS70.
"""

import os
import csv
import numpy as np
import ROOT
from rich.console import Console

# Mute ROOT console messages and run in batch mode
ROOT.gROOT.SetBatch(True)
ROOT.gErrorIgnoreLevel = ROOT.kFatal

# ==========================================
# Configuration & File Paths
# ==========================================
ROADSETS = ["RS57", "RS59", "RS62", "RS67", "RS70"]
TARGETS = ["LH2", "LD2"]
PT_BINS = np.array([0.0, 0.32, 0.49, 0.63, 0.77, 0.95, 1.18, 1.8], dtype=float)

# Input ROOT file templates
LATEST_XSEC_TEMPLATE = "/root/github/seaquest-dy-1d-abs-xsec/src/xsec_pT_xF_mass/{rs}/All_XSec_Objects.root"
PREV_XSEC_TEMPLATE = "/root/github/seaquest-dy-1d-abs-xsec/src/xsec_pT_xF_mass/{rs}/previous_xsec_results/All_XSec_Objects.root"

LATEST_ACC_TEMPLATE = (
    "/root/github/e906-development/src/NewAcceptanceCorrection/"
    "{rs}/acceptance_mass_xF_unfolding.root"
)
PREV_ACC_PATH = (
    "~/github/e906-development/src/AcceptanceCorrection/"
    "acceptance_no_unfolding_bins/acceptance_mass_xF_unfolding.root"
)


def resolve_path(filepath):
    """
    Resolves paths reliably across container (/root) and host (/home/ckuruppu) environments.
    """
    expanded = os.path.expanduser(filepath)
    if os.path.exists(expanded):
        return expanded

    for prefix in ["/root", "/home/ckuruppu"]:
        if filepath.startswith("~/"):
            candidate = os.path.join(prefix, filepath[2:])
            if os.path.exists(candidate):
                return candidate
        elif filepath.startswith("/root/"):
            candidate = filepath.replace("/root/", f"{prefix}/", 1)
            if os.path.exists(candidate):
                return candidate
        elif filepath.startswith("/home/ckuruppu/"):
            candidate = filepath.replace("/home/ckuruppu/", f"{prefix}/", 1)
            if os.path.exists(candidate):
                return candidate
    return expanded


def find_signal_eff_hist(xsec_file, target_label):
    """
    Retrieves E_final_signal_<LH2/LD2> from TDirectory 'Kinematics/<LH2/LD2>/'.
    Includes fallback lookups in case older ROOT files used slightly different paths.
    """
    if not xsec_file or xsec_file.IsZombie():
        return None

    hist_name = f"E_final_signal_{target_label}"
    direct_path = f"Kinematics/{target_label}/{hist_name}"
    h = xsec_file.Get(direct_path)
    if h and isinstance(h, ROOT.TH1):
        return h

    # Fallback: check directory object explicitly or top-level
    kin_dir = xsec_file.Get("Kinematics")
    if kin_dir:
        tgt_dir = kin_dir.Get(target_label)
        if tgt_dir:
            h = tgt_dir.Get(hist_name)
            if h and isinstance(h, ROOT.TH1):
                return h

    h = xsec_file.Get(hist_name)
    if h and isinstance(h, ROOT.TH1):
        return h

    return None


def find_y_corrected_hist(xsec_file, target_label):
    """
    Retrieves Y_corrected_stat_<LH2/LD2> from TDirectory 'Kinematics/<LH2/LD2>/'.
    Includes fallback lookups in case older ROOT files used slightly different paths.
    """
    if not xsec_file or xsec_file.IsZombie():
        return None

    hist_name = f"Y_corrected_stat_{target_label}"
    direct_path = f"Kinematics/{target_label}/{hist_name}"
    h = xsec_file.Get(direct_path)
    if h and isinstance(h, ROOT.TH1):
        return h

    # Fallback: check directory object explicitly or top-level
    kin_dir = xsec_file.Get("Kinematics")
    if kin_dir:
        tgt_dir = kin_dir.Get(target_label)
        if tgt_dir:
            h = tgt_dir.Get(hist_name)
            if h and isinstance(h, ROOT.TH1):
                return h

    h = xsec_file.Get(hist_name)
    if h and isinstance(h, ROOT.TH1):
        return h

    return None


def find_acceptance_hist(acc_file, target_label, var_key="pT"):
    """
    Locates the 1D pT acceptance histogram using the same lookup hierarchy as analyzer.py.
    """
    if not acc_file or acc_file.IsZombie():
        return None

    dir_candidates = ["Integrated_pT", "Integrated_pt", "pT"]
    var_variants = [var_key, var_key.lower(), var_key.upper()]

    target_candidates = [target_label]
    if target_label == "LD2":
        target_candidates.append("LH2")

    # 1. Search candidate TDirectories
    for dname in dir_candidates:
        acc_dir = acc_file.Get(dname)
        if not acc_dir:
            continue
        for tgt in target_candidates:
            for v in var_variants:
                for hname in [
                    f"h_ratio_{tgt}_Integrated_{v}",
                    f"h_ratio_{tgt}_{v}",
                    f"h_acc_{tgt}_{v}",
                ]:
                    h = acc_dir.Get(hname)
                    if h and isinstance(h, ROOT.TH1) and not isinstance(h, ROOT.TH2):
                        return h

        if hasattr(acc_dir, "GetListOfKeys"):
            for tgt in target_candidates:
                for key in acc_dir.GetListOfKeys():
                    obj = key.ReadObj()
                    if (
                        isinstance(obj, ROOT.TH1)
                        and not isinstance(obj, ROOT.TH2)
                        and tgt.lower() in obj.GetName().lower()
                    ):
                        return obj

    # 2. Search top-level keys
    if hasattr(acc_file, "GetListOfKeys"):
        for tgt in target_candidates:
            for v in var_variants:
                for hname in [
                    f"h_ratio_{tgt}_Integrated_{v}",
                    f"h_ratio_{tgt}_{v}",
                    f"h_acc_{tgt}_{v}",
                ]:
                    h = acc_file.Get(hname)
                    if h and isinstance(h, ROOT.TH1) and not isinstance(h, ROOT.TH2):
                        return h

    return None


def get_bin_val_and_err(hist, bin_idx, bin_center, n_expected_bins):
    """
    Extracts (value, error) for a 1-indexed ROOT bin, falling back to FindBin(bin_center)
    if the histogram bin count differs.
    """
    if not hist:
        return None, None
    b = bin_idx if hist.GetNbinsX() == n_expected_bins else hist.FindBin(bin_center)
    return float(hist.GetBinContent(b)), float(hist.GetBinError(b))


def format_cell_csv(latest_val, latest_err, prev_val, prev_err, precision=6):
    """
    Formats a CSV cell with Latest +/- Error on the top line and
    (Previous +/- Error) on the bottom line.
    """
    top_str = (
        f"{latest_val:.{precision}f} +/- {latest_err:.{precision}f}"
        if latest_val is not None
        else "N/A"
    )
    bot_str = (
        f"({prev_val:.{precision}f} +/- {prev_err:.{precision}f})"
        if prev_val is not None
        else "(N/A)"
    )
    return f"{top_str}\n{bot_str}"


def format_cell_tex(latest_val, latest_err, prev_val, prev_err, precision=6):
    """
    Formats a LaTeX cell using an inline tabular environment so the latest value
    sits on top and the previous value sits in parentheses below.
    """
    top_str = (
        f"${latest_val:.{precision}f} \\pm {latest_err:.{precision}f}$"
        if latest_val is not None
        else "N/A"
    )
    bot_str = (
        f"$({prev_val:.{precision}f} \\pm {prev_err:.{precision}f})$"
        if prev_val is not None
        else "(N/A)"
    )
    return f"\\begin{{tabular}}{{@{{}}c@{{}}}}{top_str} \\\\ {bot_str}\\end{{tabular}}"


def write_csv_table(filename, rows):
    """Writes the extracted rows to a CSV file."""
    headers = [
        "RoadID",
        "pT bin [GeV]",
        "Average Final Signal Efficiency <E_signal>",
        "Y_corrected",
        "Acceptance Correction",
    ]
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for r in rows:
            writer.writerow(
                [
                    r["roadset"],
                    r["pt_bin"],
                    r["eff_csv"],
                    r["ycorr_csv"],
                    r["acc_csv"],
                ]
            )


def write_tex_table(filename, rows, target_label, roadset_label=None):
    """Writes the extracted rows to a LaTeX longtable file."""
    title_scope = f"{target_label} ({roadset_label})" if roadset_label else target_label
    label_scope = f"{target_label}_{roadset_label}" if roadset_label else target_label

    tex_lines = [
        r"{\footnotesize",
        r"\renewcommand{\arraystretch}{1.35}",
        r"\begin{longtable}{|c|c|c|c|c|}",
        rf"\caption{{Comparison of Latest vs.\ Previous Signal Efficiency, Corrected Yield, and Acceptance Correction for {title_scope}. Each cell displays the latest value $\pm$ error on top and the previous value in parentheses below.}} \label{{tab:eff_acc_comp_{label_scope}}} \\",
        r"\hline",
        r"\textbf{RoadID} & \textbf{$p_{T}$ bin [GeV]} & \textbf{$\langle E_{\mathrm{signal}} \rangle$} & \textbf{$Y_{\mathrm{corrected}}$} & \textbf{Acceptance Correction} \\",
        r"\hline",
        r"\endfirsthead",
        r"\multicolumn{5}{c}{{\bfseries \tablename\ \thetable{} -- continued from previous page}} \\",
        r"\hline",
        r"\textbf{RoadID} & \textbf{$p_{T}$ bin [GeV]} & \textbf{$\langle E_{\mathrm{signal}} \rangle$} & \textbf{$Y_{\mathrm{corrected}}$} & \textbf{Acceptance Correction} \\",
        r"\hline",
        r"\endhead",
        r"\hline \multicolumn{5}{|r|}{{Continued on next page}} \\ \hline",
        r"\endfoot",
        r"\hline",
        r"\endlastfoot",
    ]

    prev_rs = None
    for r in rows:
        if prev_rs is not None and r["roadset"] != prev_rs:
            tex_lines.append(r"\hline")
        tex_lines.append(
            f"{r['roadset']} & {r['pt_bin']} & {r['eff_tex']} & {r['ycorr_tex']} & {r['acc_tex']} \\\\ \\hline"
        )
        prev_rs = r["roadset"]

    tex_lines.append(r"\end{longtable}")
    tex_lines.append(r"}")

    with open(filename, "w") as f:
        f.write("\n".join(tex_lines) + "\n")


def main():
    console = Console()
    n_bins = len(PT_BINS) - 1

    # Open the shared previous acceptance ROOT file once
    prev_acc_resolved = resolve_path(PREV_ACC_PATH)
    f_prev_acc = None
    if os.path.exists(prev_acc_resolved):
        f_prev_acc = ROOT.TFile.Open(prev_acc_resolved, "READ")
    else:
        console.print(
            f"[bold yellow]Warning:[/bold yellow] Previous acceptance file not found at {prev_acc_resolved}"
        )

    for target in TARGETS:
        console.print(f"\n[bold cyan]Processing Target: {target}[/bold cyan]")
        all_target_rows = []

        h_prev_acc = find_acceptance_hist(f_prev_acc, target, "pT") if f_prev_acc else None

        for rs in ROADSETS:
            rs_rows = []

            latest_xsec_path = resolve_path(LATEST_XSEC_TEMPLATE.format(rs=rs))
            prev_xsec_path = resolve_path(PREV_XSEC_TEMPLATE.format(rs=rs))
            latest_acc_path = resolve_path(LATEST_ACC_TEMPLATE.format(rs=rs))

            f_lat_xsec = (
                ROOT.TFile.Open(latest_xsec_path, "READ")
                if os.path.exists(latest_xsec_path)
                else None
            )
            f_prev_xsec = (
                ROOT.TFile.Open(prev_xsec_path, "READ")
                if os.path.exists(prev_xsec_path)
                else None
            )
            f_lat_acc = (
                ROOT.TFile.Open(latest_acc_path, "READ")
                if os.path.exists(latest_acc_path)
                else None
            )

            if not f_lat_xsec:
                console.print(f"  [yellow]Missing latest XSec file:[/yellow] {latest_xsec_path}")
            if not f_prev_xsec:
                console.print(f"  [yellow]Missing previous XSec file:[/yellow] {prev_xsec_path}")
            if not f_lat_acc:
                console.print(f"  [yellow]Missing latest Acceptance file:[/yellow] {latest_acc_path}")

            h_lat_eff = find_signal_eff_hist(f_lat_xsec, target)
            h_prev_eff = find_signal_eff_hist(f_prev_xsec, target)

            h_lat_ycorr = find_y_corrected_hist(f_lat_xsec, target)
            h_prev_ycorr = find_y_corrected_hist(f_prev_xsec, target)

            h_lat_acc = find_acceptance_hist(f_lat_acc, target, "pT")

            for i_bin in range(n_bins):
                root_bin = i_bin + 1
                pt_min, pt_max = float(PT_BINS[i_bin]), float(PT_BINS[i_bin + 1])
                pt_center = 0.5 * (pt_min + pt_max)
                pt_bin_str = f"[{pt_min:.2f}, {pt_max:.2f})"

                lat_eff, lat_eff_err = get_bin_val_and_err(
                    h_lat_eff, root_bin, pt_center, n_bins
                )
                prev_eff, prev_eff_err = get_bin_val_and_err(
                    h_prev_eff, root_bin, pt_center, n_bins
                )

                lat_ycorr, lat_ycorr_err = get_bin_val_and_err(
                    h_lat_ycorr, root_bin, pt_center, n_bins
                )
                prev_ycorr, prev_ycorr_err = get_bin_val_and_err(
                    h_prev_ycorr, root_bin, pt_center, n_bins
                )

                lat_acc, lat_acc_err = get_bin_val_and_err(
                    h_lat_acc, root_bin, pt_center, n_bins
                )
                prev_acc, prev_acc_err = get_bin_val_and_err(
                    h_prev_acc, root_bin, pt_center, n_bins
                )

                row_data = {
                    "roadset": rs,
                    "pt_bin": pt_bin_str,
                    "eff_csv": format_cell_csv(
                        lat_eff, lat_eff_err, prev_eff, prev_eff_err, precision=4
                    ),
                    "eff_tex": format_cell_tex(
                        lat_eff, lat_eff_err, prev_eff, prev_eff_err, precision=4
                    ),
                    "ycorr_csv": format_cell_csv(
                        lat_ycorr, lat_ycorr_err, prev_ycorr, prev_ycorr_err, precision=4
                    ),
                    "ycorr_tex": format_cell_tex(
                        lat_ycorr, lat_ycorr_err, prev_ycorr, prev_ycorr_err, precision=4
                    ),
                    "acc_csv": format_cell_csv(
                        lat_acc, lat_acc_err, prev_acc, prev_acc_err, precision=6
                    ),
                    "acc_tex": format_cell_tex(
                        lat_acc, lat_acc_err, prev_acc, prev_acc_err, precision=6
                    ),
                }
                rs_rows.append(row_data)
                all_target_rows.append(row_data)

            # Save individual roadset tables (2 tables LH2/LD2 per roadset)
            rs_csv_name = f"Table_Comparison_{rs}_{target}.csv"
            rs_tex_name = f"Table_Comparison_{rs}_{target}.tex"
            write_csv_table(rs_csv_name, rs_rows)
            write_tex_table(rs_tex_name, rs_rows, target, roadset_label=rs)
            console.print(f"  [green]✔ Saved[/green] {rs_csv_name} and {rs_tex_name}")

            # Close per-roadset files safely
            for f_obj in (f_lat_xsec, f_prev_xsec, f_lat_acc):
                if f_obj:
                    f_obj.Close()

        # Save combined master tables across all roadsets for this target
        master_csv_name = f"Table_Comparison_{target}.csv"
        master_tex_name = f"Table_Comparison_{target}.tex"
        write_csv_table(master_csv_name, all_target_rows)
        write_tex_table(master_tex_name, all_target_rows, target)
        console.print(
            f"[bold green]✔ Saved combined tables:[/bold green] {master_csv_name} and {master_tex_name}"
        )

    if f_prev_acc:
        f_prev_acc.Close()


if __name__ == "__main__":
    main()