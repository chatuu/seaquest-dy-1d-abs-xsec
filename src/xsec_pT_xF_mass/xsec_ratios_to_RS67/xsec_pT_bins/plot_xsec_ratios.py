#!/usr/bin/env python3
"""
plot_xsec_ratios.py
Calculates and plots single differential cross-section ratios relative to RS67
for [RS57, RS59, RS62, RS70, RS57-70] across LH2 and LD2 targets (vs pT, Mass, and xF),
and exports the pol0 best-fit ratio +/- error to CSV and LaTeX tables.
"""

import os
import sys
import csv
import math
import ROOT

# Run ROOT in batch mode to prevent canvas windows from popping up
ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
# Suppress ROOT fit info prints
ROOT.gErrorIgnoreLevel = ROOT.kWarning

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

KINEMATIC_CONFIGS = {
    "pT": {
        "top_y_title": "d#sigma/dp_{T} [nb/GeV]",
        "top_x_title": "p_{T} [GeV]",
        "bot_x_title": "p_{T} [GeV/c]",
        "log_y": False,
    },
    "Mass": {
        "top_y_title": "d#sigma/dM [nb/GeV]",
        "top_x_title": "Mass [GeV]",
        "bot_x_title": "Mass [GeV/c^{2}]",
        "log_y": True,
    },
    "xF": {
        "top_y_title": "d#sigma/dx_{F} [nb]",
        "top_x_title": "x_{F}",
        "bot_x_title": "x_{F}",
        "log_y": False,
    },
}


def resolve_base_path():
    """Locates the parent directory containing the RS* subdirectories."""
    candidates = [
        os.getcwd(),
        os.path.abspath(".."),
        SCRIPT_DIR,
        os.path.dirname(SCRIPT_DIR),
        "/root/github/seaquest-dy-1d-abs-xsec/src/xsec_pT_xF_mass",
        "/root/github/e906-development/src/xsec_pT",
    ]
    for path in candidates:
        if os.path.exists(os.path.join(path, "RS67", "All_XSec_Objects.root")):
            return path
    return os.getcwd()


def extract_data(tfile, tgt, k_name="pT"):
    """Extracts points, stat errors, and sys errors from the ROOT file for pT, Mass, or xF."""
    dir_candidates = [f"CrossSections_{tgt}_{k_name}"]
    if k_name == "pT":
        dir_candidates.insert(0, f"CrossSections_{tgt}")

    tdir = None
    for dname in dir_candidates:
        tdir = tfile.Get(dname)
        if tdir:
            break

    if not tdir:
        return None

    g_stat = tdir.Get(f"g_xsec_{tgt}_geom")
    h_sys = tdir.Get(f"h1_sys_{tgt}_geom")
    g_sys = tdir.Get(f"g_sys_{tgt}_geom")

    if not g_stat or (not h_sys and not g_sys):
        return None

    n_pts = g_stat.GetN()
    if n_pts == 0:
        return None

    points = []
    x_vals = g_stat.GetX()
    y_vals = g_stat.GetY()

    for i in range(n_pts):
        x = float(x_vals[i])
        y = float(y_vals[i])

        ex = float(g_stat.GetErrorX(i))
        ey_stat = float(g_stat.GetErrorY(i))

        if h_sys:
            bin_idx = h_sys.FindBin(x)
            ey_sys = float(h_sys.GetBinError(bin_idx))
            ex_sys = float(h_sys.GetBinWidth(bin_idx)) / 2.0
        else:
            ey_sys = float(g_sys.GetErrorY(i))
            ex_sys = float(g_sys.GetErrorX(i))

        if ex == 0.0:
            ex = ex_sys

        points.append({
            "x": x,
            "y": y,
            "ex": ex,
            "ex_sys": ex_sys,
            "ey_stat": ey_stat,
            "ey_sys": ey_sys,
        })

    return points


def compute_weighted_combined_data(base_path, roadsets, subpath, tgt, k_name="pT"):
    """
    Computes the inverse-variance weighted average across roadsets [RS57, RS59, RS62, RS67, RS70]
    when a dedicated RS57-70/All_XSec_Objects.root file is not present on disk.
    """
    rs_datasets = []
    for rs in roadsets:
        fpath = os.path.join(base_path, rs, subpath)
        if not os.path.exists(fpath):
            continue
        f = ROOT.TFile.Open(fpath, "READ")
        if not f or f.IsZombie():
            continue
        pts = extract_data(f, tgt, k_name)
        f.Close()
        if pts:
            rs_datasets.append(pts)

    if not rs_datasets:
        return None

    ref_x_list = sorted({round(pt["x"], 6) for pts in rs_datasets for pt in pts})
    combined_points = []

    for rx in ref_x_list:
        matched = []
        for pts in rs_datasets:
            for pt in pts:
                if abs(pt["x"] - rx) < 1e-4 and pt["y"] > 0 and pt["ey_stat"] > 0:
                    matched.append(pt)
                    break

        if not matched:
            continue

        weights = [1.0 / (m["ey_stat"] ** 2) for m in matched]
        w_sum = sum(weights)

        y_comb = sum(w * m["y"] for w, m in zip(weights, matched)) / w_sum
        ey_stat_comb = 1.0 / math.sqrt(w_sum)
        ey_sys_comb = sum(w * m["ey_sys"] for w, m in zip(weights, matched)) / w_sum
        ex = matched[0]["ex"]
        ex_sys = matched[0]["ex_sys"]

        combined_points.append({
            "x": matched[0]["x"],
            "y": y_comb,
            "ex": ex,
            "ex_sys": ex_sys,
            "ey_stat": ey_stat_comb,
            "ey_sys": ey_sys_comb,
        })

    return combined_points if combined_points else None


def calculate_ratio(data_num, data_den):
    """Calculates Ratio (num/den) matched by bin center and propagates total error."""
    ratio_points = []

    for pt_num in data_num:
        pt_den = next(
            (d for d in data_den if abs(d["x"] - pt_num["x"]) < 1e-4), None
        )
        if pt_den is None:
            continue

        x = pt_num["x"]
        ex = pt_num["ex"]
        y_num, y_den = pt_num["y"], pt_den["y"]

        if y_den <= 0 or y_num <= 0:
            continue

        r = y_num / y_den

        # Propagate relative statistical errors
        rel_stat_num = pt_num["ey_stat"] / y_num
        rel_stat_den = pt_den["ey_stat"] / y_den
        err_stat_r = r * math.sqrt(rel_stat_num**2 + rel_stat_den**2)

        # Propagate relative systematic errors
        rel_sys_num = pt_num["ey_sys"] / y_num
        rel_sys_den = pt_den["ey_sys"] / y_den
        err_sys_r = r * math.sqrt(rel_sys_num**2 + rel_sys_den**2)

        # Combine in quadrature for total error
        err_tot_r = math.sqrt(err_stat_r**2 + err_sys_r**2)

        ratio_points.append({
            "x": x,
            "y": r,
            "ex": ex,
            "ey_stat": err_stat_r,
            "ey_sys": err_sys_r,
            "ey_tot": err_tot_r,
        })

    return ratio_points


def create_plot(ds, reference, tgt, data_num, data_den, ratio_data, out_dir, k_name="pT"):
    """
    Generates the TCanvas with Top (Xsec) and Bottom (Ratio) TFrames with
    non-overlapping pixel-font axes, saves the PDF, and returns (best_fit_val, best_fit_err, chi2, ndf).
    """
    kcfg = KINEMATIC_CONFIGS[k_name]
    c_name = f"c_{ds}_{tgt}_{k_name}"
    c = ROOT.TCanvas(c_name, f"{ds} vs {reference} for {tgt} ({k_name})", 800, 850)

    # ------------------
    # Setup Pads (65% Top / 35% Bottom with clean margins)
    # ------------------
    pad1 = ROOT.TPad("pad1", "Top Pad", 0.0, 0.36, 1.0, 1.0)
    pad1.SetTopMargin(0.06)
    pad1.SetBottomMargin(0.15)
    pad1.SetLeftMargin(0.16)
    pad1.SetRightMargin(0.05)
    pad1.SetTickx(1)
    pad1.SetTicky(1)
    pad1.Draw()

    pad2 = ROOT.TPad("pad2", "Bottom Pad", 0.0, 0.0, 1.0, 0.36)
    pad2.SetTopMargin(0.06)
    pad2.SetBottomMargin(0.32)
    pad2.SetLeftMargin(0.16)
    pad2.SetRightMargin(0.05)
    pad2.SetTickx(1)
    pad2.SetTicky(1)
    pad2.Draw()

    # ------------------
    # Top Pad (Cross Sections)
    # ------------------
    pad1.cd()
    if kcfg["log_y"]:
        pad1.SetLogy()

    n_num = len(data_num)
    n_den = len(data_den)

    g_stat_num = ROOT.TGraphErrors(n_num)
    g_sys_num = ROOT.TGraphErrors(n_num)
    y_max_top = -1e9
    y_min_pos_top = 1e9

    for i, pn in enumerate(data_num):
        g_stat_num.SetPoint(i, pn["x"], pn["y"])
        g_stat_num.SetPointError(i, pn["ex"], pn["ey_stat"])
        g_sys_num.SetPoint(i, pn["x"], pn["y"])
        g_sys_num.SetPointError(i, pn["ex_sys"], pn["ey_sys"])
        top_err = max(pn["ey_stat"], pn["ey_sys"])
        if pn["y"] + top_err > y_max_top:
            y_max_top = pn["y"] + top_err
        if pn["y"] > 0 and pn["y"] < y_min_pos_top:
            y_min_pos_top = pn["y"]

    g_stat_den = ROOT.TGraphErrors(n_den)
    g_sys_den = ROOT.TGraphErrors(n_den)
    for i, pd in enumerate(data_den):
        g_stat_den.SetPoint(i, pd["x"], pd["y"])
        g_stat_den.SetPointError(i, pd["ex"], pd["ey_stat"])
        g_sys_den.SetPoint(i, pd["x"], pd["y"])
        g_sys_den.SetPointError(i, pd["ex_sys"], pd["ey_sys"])
        top_err = max(pd["ey_stat"], pd["ey_sys"])
        if pd["y"] + top_err > y_max_top:
            y_max_top = pd["y"] + top_err
        if pd["y"] > 0 and pd["y"] < y_min_pos_top:
            y_min_pos_top = pd["y"]

    # Styling Numerator (e.g. RS57)
    g_stat_num.SetMarkerStyle(20)
    g_stat_num.SetMarkerColor(ROOT.kBlue + 1)
    g_stat_num.SetLineColor(ROOT.kBlue + 1)

    g_sys_num.SetFillColorAlpha(ROOT.kBlue, 0.3)
    g_sys_num.SetLineColorAlpha(ROOT.kBlue, 0.0)
    g_sys_num.SetFillStyle(1001)

    # Styling Denominator (RS67)
    g_stat_den.SetMarkerStyle(24)
    g_stat_den.SetMarkerColor(ROOT.kBlack)
    g_stat_den.SetLineColor(ROOT.kBlack)

    g_sys_den.SetFillColorAlpha(ROOT.kGray + 2, 0.3)
    g_sys_den.SetLineColorAlpha(ROOT.kGray + 2, 0.0)
    g_sys_den.SetFillStyle(1001)

    mg = ROOT.TMultiGraph()
    mg.Add(g_sys_num, "2")
    mg.Add(g_sys_den, "2")
    mg.Add(g_stat_num, "PE")
    mg.Add(g_stat_den, "PE")

    mg.SetTitle("")
    mg.Draw("A")

    if kcfg["log_y"]:
        mg.SetMinimum(y_min_pos_top * 0.3 if y_min_pos_top < 1e8 else 1e-4)
        if y_max_top > 0:
            mg.SetMaximum(y_max_top * 6.0)
    else:
        mg.SetMinimum(0.0)
        if y_max_top > 0:
            mg.SetMaximum(y_max_top * 1.35)

    pad1.Update()

    # Format Top Axes using fixed pixel font (Font 43) so labels never overlap or clip
    mg.GetYaxis().SetTitle(kcfg["top_y_title"])
    mg.GetYaxis().SetTitleFont(43)
    mg.GetYaxis().SetTitleSize(22)
    mg.GetYaxis().SetTitleOffset(1.75)
    mg.GetYaxis().CenterTitle(True)
    mg.GetYaxis().SetLabelFont(43)
    mg.GetYaxis().SetLabelSize(18)
    mg.GetYaxis().SetLabelOffset(0.008)

    mg.GetXaxis().SetTitle(kcfg["top_x_title"])
    mg.GetXaxis().SetTitleFont(43)
    mg.GetXaxis().SetTitleSize(22)
    mg.GetXaxis().SetTitleOffset(1.15)
    mg.GetXaxis().CenterTitle(True)
    mg.GetXaxis().SetLabelFont(43)
    mg.GetXaxis().SetLabelSize(18)
    mg.GetXaxis().SetLabelOffset(0.008)

    leg = ROOT.TLegend(0.55, 0.65, 0.91, 0.90)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetTextFont(43)
    leg.SetTextSize(18)
    leg.AddEntry(g_stat_num, f"{ds} {tgt} (Stat.)", "pe")
    leg.AddEntry(g_sys_num, f"{ds} {tgt} (Syst.)", "f")
    leg.AddEntry(g_stat_den, f"{reference} {tgt} (Stat.)", "pe")
    leg.AddEntry(g_sys_den, f"{reference} {tgt} (Syst.)", "f")
    leg.Draw()

    # ------------------
    # Bottom Pad (Ratio)
    # ------------------
    pad2.cd()

    n_ratio = len(ratio_data)
    g_ratio = ROOT.TGraphErrors(n_ratio)

    y_min_r, y_max_r = 1e9, -1e9
    for i, p in enumerate(ratio_data):
        g_ratio.SetPoint(i, p["x"], p["y"])
        g_ratio.SetPointError(i, p["ex"], p["ey_tot"])
        if p["y"] - p["ey_tot"] < y_min_r:
            y_min_r = p["y"] - p["ey_tot"]
        if p["y"] + p["ey_tot"] > y_max_r:
            y_max_r = p["y"] + p["ey_tot"]

    g_ratio.SetMarkerStyle(20)
    g_ratio.SetMarkerColor(ROOT.kBlack)
    g_ratio.SetLineColor(ROOT.kBlack)
    g_ratio.SetTitle("")

    # Fit ratio with a constant (pol0)
    g_ratio.Fit("pol0", "SQ")
    fit_func = g_ratio.GetFunction("pol0")

    best_fit_val = float(fit_func.GetParameter(0)) if fit_func else 0.0
    best_fit_err = float(fit_func.GetParError(0)) if fit_func else 0.0
    chi2 = float(fit_func.GetChisquare()) if fit_func else 0.0
    ndf = int(fit_func.GetNDF()) if fit_func else 0

    if fit_func:
        fit_func.SetLineWidth(0)

    if best_fit_val - best_fit_err < y_min_r:
        y_min_r = best_fit_val - best_fit_err
    if best_fit_val + best_fit_err > y_max_r:
        y_max_r = best_fit_val + best_fit_err

    g_ratio.Draw("AP")

    # Add vertical headroom in the ratio pad so points and the Best Fit TLatex never collide
    if y_min_r < y_max_r:
        span = max(y_max_r - y_min_r, 0.2)
        g_ratio.SetMinimum(max(0.0, y_min_r - 0.25 * span))
        g_ratio.SetMaximum(y_max_r + 0.40 * span)

    pad2.Update()

    # Format Ratio Axes using matching pixel font (Font 43)
    g_ratio.GetYaxis().SetTitle(f"{ds} / {reference}")
    g_ratio.GetYaxis().SetNdivisions(505)
    g_ratio.GetYaxis().SetTitleFont(43)
    g_ratio.GetYaxis().SetTitleSize(22)
    g_ratio.GetYaxis().SetTitleOffset(1.75)
    g_ratio.GetYaxis().CenterTitle(True)
    g_ratio.GetYaxis().SetLabelFont(43)
    g_ratio.GetYaxis().SetLabelSize(18)
    g_ratio.GetYaxis().SetLabelOffset(0.008)

    g_ratio.GetXaxis().SetTitle(kcfg["bot_x_title"])
    g_ratio.GetXaxis().SetTitleFont(43)
    g_ratio.GetXaxis().SetTitleSize(22)
    g_ratio.GetXaxis().SetTitleOffset(2.8)
    g_ratio.GetXaxis().CenterTitle(True)
    g_ratio.GetXaxis().SetLabelFont(43)
    g_ratio.GetXaxis().SetLabelSize(18)
    g_ratio.GetXaxis().SetLabelOffset(0.012)

    pad2.Update()
    x_min = g_ratio.GetXaxis().GetXmin()
    x_max = g_ratio.GetXaxis().GetXmax()

    error_box = ROOT.TBox(
        x_min, best_fit_val - best_fit_err, x_max, best_fit_val + best_fit_err
    )
    error_box.SetFillColorAlpha(ROOT.kPink, 0.4)
    error_box.Draw("SAME")

    best_fit_line = ROOT.TLine(x_min, best_fit_val, x_max, best_fit_val)
    best_fit_line.SetLineColor(ROOT.kRed)
    best_fit_line.SetLineWidth(2)
    best_fit_line.Draw("SAME")

    g_ratio.Draw("P SAME")

    latex = ROOT.TLatex()
    latex.SetNDC()
    latex.SetTextFont(43)
    latex.SetTextSize(20)
    latex.SetTextColor(ROOT.kRed)
    latex.DrawLatex(0.20, 0.82, f"Best fit: {best_fit_val:.3f} #pm {best_fit_err:.3f}")

    # Preserve pT filename convention and append _Mass / _xF for additional kinematics
    if k_name == "pT":
        out_file = os.path.join(out_dir, f"Ratio_{ds}_vs_{reference}_{tgt}.pdf")
    else:
        out_file = os.path.join(out_dir, f"Ratio_{ds}_vs_{reference}_{tgt}_vs_{k_name}.pdf")

    c.SaveAs(out_file)
    c.Close()

    return best_fit_val, best_fit_err, chi2, ndf


def export_tables(fit_results, datasets, reference, out_dir, label_suffix=""):
    """
    Writes CSV and LaTeX tables of the pol0 best-fit cross-section ratios +/- error
    for each roadset and target (LH2, LD2).
    """
    available_kinematics = [
        k for k in KINEMATIC_CONFIGS.keys() if any(k == r["kinematic"] for r in fit_results)
    ]
    if not available_kinematics:
        return

    # 1. Master CSV containing all kinematics and roadsets
    csv_all_path = os.path.join(out_dir, f"Table_CrossSection_Ratios_vs_{reference}{label_suffix}.csv")
    with open(csv_all_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Kinematic",
            "Roadset Ratio",
            "LH2 Best Fit",
            "LH2 Error",
            "LH2 Ratio +/- Error",
            "LD2 Best Fit",
            "LD2 Error",
            "LD2 Ratio +/- Error",
        ])

        for k_name in available_kinematics:
            for ds in datasets:
                lh2_entry = next(
                    (
                        r for r in fit_results
                        if r["kinematic"] == k_name and r["dataset"] == ds and r["target"] == "LH2"
                    ),
                    None,
                )
                ld2_entry = next(
                    (
                        r for r in fit_results
                        if r["kinematic"] == k_name and r["dataset"] == ds and r["target"] == "LD2"
                    ),
                    None,
                )
                if not lh2_entry and not ld2_entry:
                    continue

                lh2_val = f"{lh2_entry['val']:.4f}" if lh2_entry else "N/A"
                lh2_err = f"{lh2_entry['err']:.4f}" if lh2_entry else "N/A"
                lh2_str = f"{lh2_entry['val']:.3f} +/- {lh2_entry['err']:.3f}" if lh2_entry else "N/A"

                ld2_val = f"{ld2_entry['val']:.4f}" if ld2_entry else "N/A"
                ld2_err = f"{ld2_entry['err']:.4f}" if ld2_entry else "N/A"
                ld2_str = f"{ld2_entry['val']:.3f} +/- {ld2_entry['err']:.3f}" if ld2_entry else "N/A"

                writer.writerow([
                    k_name,
                    f"{ds} / {reference}",
                    lh2_val,
                    lh2_err,
                    lh2_str,
                    ld2_val,
                    ld2_err,
                    ld2_str,
                ])
    print(f"  [Saved CSV]   {csv_all_path}")

    # 2. Per-Kinematic CSV and LaTeX Tables + Combined LaTeX Table
    tex_all_path = os.path.join(out_dir, f"Table_CrossSection_Ratios_vs_{reference}{label_suffix}.tex")
    combined_tex_lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        rf"\caption{{Best-fit cross-section ratios ($\text{{RS}} / \text{{{reference}}}$) from constant (\texttt{{pol0}}) fits across roadsets for $\text{{LH}}_2$ and $\text{{LD}}_2$ targets.}}",
        rf"\label{{tab:xsec_ratios_vs_{reference.lower()}{label_suffix}}}",
        r"\begin{tabular}{|c|c|c|c|}",
        r"\hline",
        r"\textbf{Kinematic Variable} & \textbf{Roadset Ratio} & \textbf{$\text{LH}_2$ Best Fit ($\pm$ Error)} & \textbf{$\text{LD}_2$ Best Fit ($\pm$ Error)} \\",
        r"\hline",
    ]

    for k_name in available_kinematics:
        k_csv_path = os.path.join(
            out_dir, f"Table_CrossSection_Ratios_vs_{reference}_{k_name}{label_suffix}.csv"
        )
        k_tex_path = os.path.join(
            out_dir, f"Table_CrossSection_Ratios_vs_{reference}_{k_name}{label_suffix}.tex"
        )

        k_tex_lines = [
            r"\begin{table}[htbp]",
            r"\centering",
            rf"\caption{{Best-fit single differential cross-section ratios vs.\ {k_name} ($\text{{RS}} / \text{{{reference}}}$) for $\text{{LH}}_2$ and $\text{{LD}}_2$ targets.}}",
            rf"\label{{tab:xsec_ratios_{k_name.lower()}_vs_{reference.lower()}{label_suffix}}}",
            r"\begin{tabular}{|c|c|c|}",
            r"\hline",
            r"\textbf{Roadset Ratio} & \textbf{$\text{LH}_2$ Best Fit ($\pm$ Error)} & \textbf{$\text{LD}_2$ Best Fit ($\pm$ Error)} \\",
            r"\hline",
        ]

        with open(k_csv_path, "w", newline="") as kf:
            kwriter = csv.writer(kf)
            kwriter.writerow([
                "Roadset Ratio",
                "LH2 Best Fit",
                "LH2 Error",
                "LH2 (Best Fit +/- Error)",
                "LD2 Best Fit",
                "LD2 Error",
                "LD2 (Best Fit +/- Error)",
            ])

            for ds in datasets:
                lh2_entry = next(
                    (
                        r for r in fit_results
                        if r["kinematic"] == k_name and r["dataset"] == ds and r["target"] == "LH2"
                    ),
                    None,
                )
                ld2_entry = next(
                    (
                        r for r in fit_results
                        if r["kinematic"] == k_name and r["dataset"] == ds and r["target"] == "LD2"
                    ),
                    None,
                )
                if not lh2_entry and not ld2_entry:
                    continue

                lh2_tex = (
                    f"${lh2_entry['val']:.3f} \\pm {lh2_entry['err']:.3f}$"
                    if lh2_entry
                    else "---"
                )
                ld2_tex = (
                    f"${ld2_entry['val']:.3f} \\pm {ld2_entry['err']:.3f}$"
                    if ld2_entry
                    else "---"
                )

                kwriter.writerow([
                    f"{ds} / {reference}",
                    f"{lh2_entry['val']:.4f}" if lh2_entry else "N/A",
                    f"{lh2_entry['err']:.4f}" if lh2_entry else "N/A",
                    f"{lh2_entry['val']:.3f} +/- {lh2_entry['err']:.3f}" if lh2_entry else "N/A",
                    f"{ld2_entry['val']:.4f}" if ld2_entry else "N/A",
                    f"{ld2_entry['err']:.4f}" if ld2_entry else "N/A",
                    f"{ld2_entry['val']:.3f} +/- {ld2_entry['err']:.3f}" if ld2_entry else "N/A",
                ])

                k_tex_lines.append(f"{ds} / {reference} & {lh2_tex} & {ld2_tex} \\\\")
                k_tex_lines.append(r"\hline")

                k_label_tex = "$p_T$" if k_name == "pT" else ("Mass" if k_name == "Mass" else "$x_F$")
                combined_tex_lines.append(
                    f"{k_label_tex} & {ds} / {reference} & {lh2_tex} & {ld2_tex} \\\\"
                )
                combined_tex_lines.append(r"\hline")

        k_tex_lines.extend([
            r"\end{tabular}",
            r"\end{table}",
        ])
        with open(k_tex_path, "w") as ktf:
            ktf.write("\n".join(k_tex_lines) + "\n")

        print(f"  [Saved Table] {k_csv_path}")
        print(f"  [Saved LaTeX] {k_tex_path}")

    combined_tex_lines.extend([
        r"\end{tabular}",
        r"\end{table}",
    ])
    with open(tex_all_path, "w") as tf:
        tf.write("\n".join(combined_tex_lines) + "\n")
    print(f"  [Saved LaTeX] {tex_all_path}")


def run_suite(base_path, subpath, out_dir, label_suffix=""):
    """Processes all datasets, targets, and kinematics for a given ROOT file subpath."""
    datasets = ["RS57", "RS59", "RS62", "RS70", "RS57-70"]
    individual_roadsets = ["RS57", "RS59", "RS62", "RS67", "RS70"]
    reference = "RS67"
    targets = ["LH2", "LD2"]

    den_file_path = os.path.join(base_path, reference, subpath)
    if not os.path.exists(den_file_path):
        return

    os.makedirs(out_dir, exist_ok=True)
    fit_results = []

    f_den = ROOT.TFile.Open(den_file_path, "READ")
    if not f_den or f_den.IsZombie():
        print(f"[!] Could not open reference file: {den_file_path}")
        return

    for k_name in KINEMATIC_CONFIGS.keys():
        for ds in datasets:
            for tgt in targets:
                data_den = extract_data(f_den, tgt, k_name)
                if not data_den:
                    continue

                num_file_path = os.path.join(base_path, ds, subpath)
                data_num = None

                if os.path.exists(num_file_path):
                    f_num = ROOT.TFile.Open(num_file_path, "READ")
                    if f_num and not f_num.IsZombie():
                        data_num = extract_data(f_num, tgt, k_name)
                        f_num.Close()
                elif ds == "RS57-70":
                    data_num = compute_weighted_combined_data(
                        base_path, individual_roadsets, subpath, tgt, k_name
                    )

                if not data_num:
                    print(f"  [!] Missing data for {ds} ({tgt}, {k_name}). Skipping...")
                    continue

                print(f"Processing ({k_name}): {ds} vs {reference} for {tgt}...")
                ratio_data = calculate_ratio(data_num, data_den)
                if not ratio_data:
                    continue

                best_val, best_err, chi2, ndf = create_plot(
                    ds, reference, tgt, data_num, data_den, ratio_data, out_dir, k_name
                )

                fit_results.append({
                    "kinematic": k_name,
                    "dataset": ds,
                    "reference": reference,
                    "target": tgt,
                    "val": best_val,
                    "err": best_err,
                    "chi2": chi2,
                    "ndf": ndf,
                })

    f_den.Close()

    if fit_results:
        export_tables(fit_results, datasets, reference, out_dir, label_suffix)


def main():
    base_path = resolve_base_path()
    print(f"Using base directory: {base_path}")

    # 1. Process latest All_XSec_Objects.root files -> ./ratio_plots/
    run_suite(
        base_path=base_path,
        subpath="All_XSec_Objects.root",
        out_dir="ratio_plots",
        label_suffix="",
    )

    # 2. Process previous_xsec_results/All_XSec_Objects.root files (if present) -> ./ratio_plots_previous/
    prev_subpath = os.path.join("previous_xsec_results", "All_XSec_Objects.root")
    if os.path.exists(os.path.join(base_path, "RS67", prev_subpath)):
        print("\nProcessing previous_xsec_results...")
        run_suite(
            base_path=base_path,
            subpath=prev_subpath,
            out_dir="ratio_plots_previous",
            label_suffix="_previous",
        )


if __name__ == "__main__":
    main()