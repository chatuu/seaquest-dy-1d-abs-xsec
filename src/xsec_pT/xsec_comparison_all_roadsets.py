#!/usr/bin/env python3
import os
import re
import ROOT

# Run in batch mode so canvases do not pop up on screen
ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetOptTitle(1)
ROOT.gStyle.SetEndErrorSize(4)

ROADSETS = ["RS57", "RS59", "RS62", "RS67", "RS70"]
BASE_DIR = "."

# Color and marker styling per roadset
ROADSET_STYLES = {
    "RS57": {"color": ROOT.kBlue + 1,    "marker": 20},
    "RS59": {"color": ROOT.kRed + 1,     "marker": 21},
    "RS62": {"color": ROOT.kGreen + 2,   "marker": 22},
    "RS67": {"color": ROOT.kMagenta + 1, "marker": 23},
    "RS70": {"color": ROOT.kOrange + 7,  "marker": 33},
}

# Known paths and object names inside All_XSec_Objects.root
CANDIDATE_PATHS = {
    "LH2": {
        "stat": [
            "CrossSections_LH2/g_xsec_LH2_geom",
            "CrossSections_LH2/h_xsec_LH2_geom",
            "CrossSections_LH2/h_xsec_LH2",
            "g_xsec_LH2_geom",
            "h_xsec_LH2_geom",
            "h_xsec_LH2",
        ],
        "sys": [
            "CrossSections_LH2/g_sys_LH2_geom",
            "CrossSections_LH2/h_sys_LH2_geom",
            "CrossSections_LH2/h_xsec_LH2_sys",
            "g_sys_LH2_geom",
            "h_sys_LH2_geom",
            "h_xsec_LH2_sys",
        ],
    },
    "LD2": {
        "stat": [
            "CrossSections_LD2/g_xsec_LD2_geom",
            "CrossSections_LD2/h_xsec_LD2_geom",
            "CrossSections_LD2/h_xsec_LD2",
            "g_xsec_LD2_geom",
            "h_xsec_LD2_geom",
            "h_xsec_LD2",
        ],
        "sys": [
            "CrossSections_LD2/g_sys_LD2_geom",
            "CrossSections_LD2/h_sys_LD2_geom",
            "CrossSections_LD2/h_xsec_LD2_sys",
            "g_sys_LD2_geom",
            "h_sys_LD2_geom",
            "h_xsec_LD2_sys",
        ],
    },
}


def is_plottable(obj):
    """Returns True only if obj is a valid TH1 or TGraph (and not a TDirectory)."""
    if not obj:
        return False
    if obj.InheritsFrom("TDirectory"):
        return False
    return bool(obj.InheritsFrom("TH1") or obj.InheritsFrom("TGraph"))


def collect_plottables(directory, path_prefix=""):
    """
    Recursively traverses TDirectory/TDirectoryFile to collect TH1 and TGraph objects
    without deserializing TCanvas objects (which would alter ROOT.gPad).
    """
    items = []
    if not directory or not hasattr(directory, "GetListOfKeys"):
        return items

    for key in directory.GetListOfKeys():
        kname = key.GetName()
        class_name = key.GetClassName()
        full_path = f"{path_prefix}/{kname}" if path_prefix else kname

        # Skip saved TCanvas/TPad objects so they never hijack ROOT.gPad
        if class_name.startswith("TCanvas") or class_name.startswith("TPad"):
            continue

        obj = directory.Get(kname)
        if not obj:
            continue

        if obj.InheritsFrom("TDirectory"):
            items.extend(collect_plottables(obj, full_path))
        elif is_plottable(obj):
            cloned = obj.Clone(f"{kname}_clone_{len(items)}")
            if hasattr(cloned, "SetDirectory"):
                cloned.SetDirectory(0)
            items.append((full_path, kname, cloned.GetTitle(), cloned))

    return items


def find_xsec_objects(tfile, target):
    """
    Retrieves (stat_obj, sys_obj, stat_path, sys_path) for 'LH2' or 'LD2'.
    First checks direct paths in CANDIDATE_PATHS, then falls back to directory traversal.
    """
    stat_obj, sys_obj = None, None
    stat_path, sys_path = None, None

    # 1. Try direct path lookup first
    for path in CANDIDATE_PATHS[target]["stat"]:
        obj = tfile.Get(path)
        if is_plottable(obj):
            stat_obj = obj.Clone(f"raw_stat_{target}")
            if hasattr(stat_obj, "SetDirectory"):
                stat_obj.SetDirectory(0)
            stat_path = path
            break

    for path in CANDIDATE_PATHS[target]["sys"]:
        obj = tfile.Get(path)
        if is_plottable(obj):
            sys_obj = obj.Clone(f"raw_sys_{target}")
            if hasattr(sys_obj, "SetDirectory"):
                sys_obj.SetDirectory(0)
            sys_path = path
            break

    if stat_obj and sys_obj:
        return stat_obj, sys_obj, stat_path, sys_path

    # 2. Fallback: scan plottable TH1/TGraph objects recursively
    plottables = collect_plottables(tfile)
    target_pos = r"lh2|pp" if target == "LH2" else r"ld2|pd"
    target_neg = r"ld2|pd" if target == "LH2" else r"lh2|pp"
    exclude_pat = r"ratio|pd_2pp|flask|yield|y_total|y_mix|y_corr|eff|e_total|e_mix|e_final|reco|hodo"

    for full_path, kname, title, obj in plottables:
        meta = f"{full_path} {title}".lower()
        low_path = full_path.lower()
        low_name = kname.lower()

        if re.search(exclude_pat, low_path):
            continue
        if not re.search(target_pos, meta) or re.search(target_neg, low_path):
            continue
        if not re.search(r"xsec|cross|sigma|stat|sys", meta):
            continue

        is_sys = bool(re.search(r"sys|band|err_sys", low_path) or re.search(r"sys", low_name))
        if is_sys and sys_obj is None:
            sys_obj, sys_path = obj, full_path
        elif not is_sys and stat_obj is None:
            stat_obj, stat_path = obj, full_path

    return stat_obj, sys_obj, stat_path, sys_path


def build_sys_band(stat_obj, sys_obj, unique_tag):
    """
    Ensures the systematic uncertainty object is properly formatted for error-band drawing
    for both TGraphErrors/TGraphAsymmErrors and TH1 objects.
    """
    if not is_plottable(sys_obj):
        return None

    sys_clone = sys_obj.Clone(f"sys_{unique_tag}")
    if hasattr(sys_clone, "SetDirectory"):
        sys_clone.SetDirectory(0)

    # Case 1: TGraph / TGraphErrors / TGraphAsymmErrors
    if sys_clone.InheritsFrom("TGraph") and stat_obj.InheritsFrom("TGraph"):
        n_pts = min(stat_obj.GetN(), sys_clone.GetN())
        stat_x = stat_obj.GetX()
        stat_y = stat_obj.GetY()
        sys_y = sys_clone.GetY()

        has_ey = any(sys_clone.GetErrorY(i) > 0 for i in range(n_pts))

        for i in range(n_pts):
            # If sys_clone stored systematic errors in Y with EY=0, center on stat_y
            if not has_ey:
                err_y = sys_y[i]
                sys_clone.SetPoint(i, stat_x[i], stat_y[i])
                if sys_clone.InheritsFrom("TGraphAsymmErrors"):
                    sys_clone.SetPointEYlow(i, err_y)
                    sys_clone.SetPointEYhigh(i, err_y)
                elif hasattr(sys_clone, "SetPointError"):
                    ex = sys_clone.GetErrorX(i)
                    sys_clone.SetPointError(i, ex, err_y)

            # Ensure horizontal box half-width (EX) is non-zero so "2" error bands are visible
            ex_low = sys_clone.GetErrorXlow(i) if hasattr(sys_clone, "GetErrorXlow") else sys_clone.GetErrorX(i)
            ex_high = sys_clone.GetErrorXhigh(i) if hasattr(sys_clone, "GetErrorXhigh") else sys_clone.GetErrorX(i)
            if ex_low <= 0 and ex_high <= 0:
                default_ex = 0.04
                if sys_clone.InheritsFrom("TGraphAsymmErrors"):
                    sys_clone.SetPointEXlow(i, default_ex)
                    sys_clone.SetPointEXhigh(i, default_ex)
                elif hasattr(sys_clone, "SetPointError"):
                    sys_clone.SetPointError(i, default_ex, sys_clone.GetErrorY(i))

    # Case 2: TH1
    elif sys_clone.InheritsFrom("TH1") and stat_obj.InheritsFrom("TH1"):
        nbins = stat_obj.GetNbinsX()
        has_bin_errors = any(sys_clone.GetBinError(b) > 0 for b in range(1, nbins + 1))
        same_central = all(
            abs(sys_clone.GetBinContent(b) - stat_obj.GetBinContent(b))
            <= 1e-4 * max(abs(stat_obj.GetBinContent(b)), 1e-12)
            for b in range(1, nbins + 1)
            if stat_obj.GetBinContent(b) > 0
        )

        if not (has_bin_errors and same_central):
            max_sys_val = max([sys_clone.GetBinContent(b) for b in range(1, nbins + 1)] + [0.0])
            max_stat_val = max([stat_obj.GetBinContent(b) for b in range(1, nbins + 1)] + [0.0])

            for b in range(1, nbins + 1):
                y_val = stat_obj.GetBinContent(b)
                s_val = sys_clone.GetBinContent(b)
                err_sys = y_val * s_val if (max_stat_val > 5.0 and max_sys_val < 1.0) else s_val
                sys_clone.SetBinContent(b, y_val)
                sys_clone.SetBinError(b, err_sys)

    return sys_clone


def style_objects(stat_obj, sys_obj, color, marker_style):
    """Applies marker, line, and shaded error-band styling."""
    stat_obj.SetLineColor(color)
    stat_obj.SetMarkerColor(color)
    stat_obj.SetMarkerStyle(marker_style)
    stat_obj.SetMarkerSize(1.2)
    stat_obj.SetLineWidth(2)
    stat_obj.SetFillColorAlpha(color, 0.28)
    stat_obj.SetFillStyle(1001)

    if sys_obj:
        sys_obj.SetLineColor(color)
        sys_obj.SetMarkerColor(color)
        sys_obj.SetMarkerSize(0)
        sys_obj.SetFillColorAlpha(color, 0.28)
        sys_obj.SetFillStyle(1001)


def update_axis_limits(obj, x_min, x_max, y_min, y_max, first_obj):
    """Computes (x_min, x_max, y_min, y_max) across TH1 or TGraph objects."""
    if obj.InheritsFrom("TH1"):
        ax_min = obj.GetXaxis().GetXmin()
        ax_max = obj.GetXaxis().GetXmax()
        x_min = ax_min if first_obj else min(x_min, ax_min)
        x_max = ax_max if first_obj else max(x_max, ax_max)
        for b in range(1, obj.GetNbinsX() + 1):
            val = obj.GetBinContent(b)
            err = obj.GetBinError(b)
            if val > 0:
                y_min = min(y_min, val - err if val - err > 0 else val)
                y_max = max(y_max, val + err)
    elif obj.InheritsFrom("TGraph"):
        n_pts = obj.GetN()
        if n_pts > 0:
            x_buf = obj.GetX()
            y_buf = obj.GetY()
            for i in range(n_pts):
                xv = x_buf[i]
                yv = y_buf[i]
                ex = obj.GetErrorX(i) if hasattr(obj, "GetErrorX") else 0.0
                ey = obj.GetErrorY(i) if hasattr(obj, "GetErrorY") else 0.0
                if first_obj and i == 0:
                    x_min = 0.0
                    x_max = xv + ex + 0.15
                else:
                    x_min = min(x_min, 0.0, xv - ex)
                    x_max = max(x_max, xv + ex + 0.15)
                if yv > 0:
                    y_min = min(y_min, yv - ey if yv - ey > 0 else yv)
                    y_max = max(y_max, yv + ey)

    return x_min, x_max, y_min, y_max


def plot_target_roadsets(target, output_pdf):
    """
    Loads all roadsets for 'LH2' or 'LD2' first, then creates and activates the TCanvas
    using a linear y-axis scale.
    """
    keep_alive = []
    sys_draw_list = []
    stat_draw_list = []
    legend_entries = []

    y_min, y_max = 1e30, -1e30
    x_min, x_max = 0.0, 2.5

    # 1. Load and clone all objects from TFiles BEFORE creating the TCanvas
    for rs in ROADSETS:
        filepath = os.path.join(BASE_DIR, rs, "All_XSec_Objects.root")
        if not os.path.exists(filepath):
            print(f"[WARNING] Missing file: {filepath}")
            continue

        tfile = ROOT.TFile.Open(filepath, "READ")
        if not tfile or tfile.IsZombie():
            print(f"[WARNING] Could not open: {filepath}")
            continue

        raw_stat, raw_sys, stat_path, sys_path = find_xsec_objects(tfile, target)
        if not is_plottable(raw_stat):
            all_paths = [p[0] for p in collect_plottables(tfile)]
            print(f"[WARNING] Could not find {target} cross-section in {filepath}.")
            print(f"          Available TH1/TGraph paths: {all_paths}")
            tfile.Close()
            continue

        print(f"[INFO] {rs} ({target}) -> stat: '{stat_path}', sys: '{sys_path}'")

        unique_tag = f"{target}_{rs}"
        stat_clone = raw_stat.Clone(f"stat_{unique_tag}")
        if hasattr(stat_clone, "SetDirectory"):
            stat_clone.SetDirectory(0)

        sys_clone = build_sys_band(stat_clone, raw_sys, unique_tag)
        tfile.Close()

        style = ROADSET_STYLES[rs]
        style_objects(stat_clone, sys_clone, style["color"], style["marker"])

        x_min, x_max, y_min, y_max = update_axis_limits(
            stat_clone, x_min, x_max, y_min, y_max, first_obj=(len(stat_draw_list) == 0)
        )
        if sys_clone:
            x_min, x_max, y_min, y_max = update_axis_limits(
                sys_clone, x_min, x_max, y_min, y_max, first_obj=False
            )

        legend_entries.append((stat_clone, f"{rs} (Stat. #pm Sys.)"))
        if sys_clone:
            sys_draw_list.append(sys_clone)
        stat_draw_list.append(stat_clone)
        keep_alive.extend([stat_clone, sys_clone])

    if not stat_draw_list:
        print(f"[ERROR] No valid objects found to plot for {target} ({output_pdf}).")
        return

    # 2. Create TCanvas and make it the current pad with linear y-axis
    canvas = ROOT.TCanvas(f"c_{target}", f"{target} Cross Section", 900, 700)
    canvas.cd()
    canvas.SetLogy(0)
    canvas.SetGrid(1, 1)
    canvas.SetTickx(1)
    canvas.SetTicky(1)
    canvas.SetLeftMargin(0.14)
    canvas.SetRightMargin(0.05)
    canvas.SetBottomMargin(0.12)
    canvas.SetTopMargin(0.08)

    target_latex = "LH_{2} (pp)" if target == "LH2" else "LD_{2} (pd)"
    frame_title = (
        f"{target_latex} Differential Cross Section vs. p_{{T}} (All Roadsets);"
        f"p_{{T}} [GeV/c];"
        f"d#sigma / dp_{{T}} [pb / (GeV/c)]"
    )

    frame = canvas.DrawFrame(
        x_min,
        0.0,
        x_max,
        y_max * 1.35 if y_max > 0 else 1.0,
        frame_title,
    )
    frame.GetXaxis().SetTitleSize(0.045)
    frame.GetYaxis().SetTitleSize(0.045)
    frame.GetXaxis().SetTitleOffset(1.1)
    frame.GetYaxis().SetTitleOffset(1.35)
    keep_alive.append(frame)

    # 3. Draw systematic error bands underneath
    for sys_obj in sys_draw_list:
        if sys_obj.InheritsFrom("TGraph"):
            sys_obj.Draw("2 SAME")
        else:
            sys_obj.Draw("E2 SAME")

    # 4. Draw statistical error bars and markers on top
    for stat_obj in stat_draw_list:
        if stat_obj.InheritsFrom("TGraph"):
            stat_obj.Draw("P E1 Z SAME")
        else:
            stat_obj.Draw("P E1 X0 SAME")

    # 5. Build and draw legend
    legend = ROOT.TLegend(0.58, 0.65, 0.92, 0.89)
    legend.SetBorderSize(1)
    legend.SetFillColor(ROOT.kWhite)
    legend.SetTextSize(0.032)
    for obj, label in legend_entries:
        legend.AddEntry(obj, label, "lepf")
    legend.Draw()
    keep_alive.append(legend)

    canvas.RedrawAxis()
    canvas.Modified()
    canvas.Update()
    canvas.SaveAs(output_pdf)
    print(f"Saved plot: {output_pdf}")


if __name__ == "__main__":
    plot_target_roadsets(
        target="LH2",
        output_pdf="CrossSection_AllRoadsets_LH2_geom_vs_pT.pdf",
    )
    plot_target_roadsets(
        target="LD2",
        output_pdf="CrossSection_AllRoadsets_LD2_geom_vs_pT.pdf",
    )