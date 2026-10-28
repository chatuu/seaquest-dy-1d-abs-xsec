import os
import math
import ROOT


def setup_root():
    """Configures global ROOT visual options matching analyzer.py."""
    ROOT.gROOT.SetBatch(True)
    ROOT.gStyle.SetOptStat(0)
    ROOT.gStyle.SetPalette(ROOT.kBird)
    ROOT.gStyle.SetEndErrorSize(5)
    ROOT.gErrorIgnoreLevel = ROOT.kFatal


def resolve_path(filepath):
    """Resolves paths reliably across container (/root) and host (/home/ckuruppu) environments."""
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


def generate_emix_final_pdfs(f_curr, f_prev):
    """Multiplies E_mix_hodo (latest) and E_mix_reco (previous) and saves formatted 1D PDFs."""
    targets = ["LH2", "LD2", "Flask"]

    for label in targets:
        dir_path = f"Kinematics/{label}"
        hodo_path = f"{dir_path}/E_mix_hodo_{label}"
        reco_path = f"{dir_path}/E_mix_reco_{label}"
        final_name = f"E_mix_final_{label}"

        h_hodo = f_curr.Get(hodo_path)
        h_reco = f_prev.Get(reco_path)

        if not h_hodo:
            raise KeyError(f"Could not find '{hodo_path}' in current ROOT file.")
        if not h_reco:
            raise KeyError(f"Could not find '{reco_path}' in previous ROOT file.")

        nbins = h_hodo.GetNbinsX()
        if nbins != h_reco.GetNbinsX():
            raise ValueError(f"Bin count mismatch for {label}: {nbins} vs {h_reco.GetNbinsX()}")

        hist = h_hodo.Clone(final_name)
        hist.SetDirectory(0)
        hist.Reset()

        title_str = f"<E_{{mix,final}}> = <E_{{mix,reco}}> #times <E_{{mix,hodo}}> ({label});p_{{T}} [GeV];Efficiency"
        hist.SetTitle(title_str)
        if not hist.GetSumw2N():
            hist.Sumw2()
        hist.SetStats(0)
        hist.GetXaxis().CenterTitle()
        hist.GetYaxis().CenterTitle()
        hist.GetXaxis().SetTitleOffset(1.3)
        hist.GetYaxis().SetTitleOffset(1.7)

        for i in range(1, nbins + 1):
            val_hodo = h_hodo.GetBinContent(i)
            err_hodo = h_hodo.GetBinError(i)

            val_reco = h_reco.GetBinContent(i)
            err_reco = h_reco.GetBinError(i)

            val_final = val_hodo * val_reco
            err_final = math.sqrt((val_hodo * err_reco) ** 2 + (val_reco * err_hodo) ** 2)

            hist.SetBinContent(i, val_final)
            hist.SetBinError(i, err_final)

        c = ROOT.TCanvas(f"c_E_mix_final_{label}", "", 1200, 900)
        c.SetRightMargin(0.05)
        c.SetLeftMargin(0.16)
        c.SetBottomMargin(0.14)
        c.SetTickx(1)
        c.SetTicky(1)

        max_y, min_y = -1e9, 1e9
        for i in range(1, hist.GetNbinsX() + 1):
            val = hist.GetBinContent(i)
            err = hist.GetBinError(i)
            if val == 0 and err == 0:
                continue
            if val + err > max_y:
                max_y = val + err
            if val - err < min_y:
                min_y = val - err

        if max_y > -1e8:
            hist.SetMaximum(max_y * 1.5)
            hist.SetMinimum(min_y * 1.2 if min_y < 0 else 0.0)
        else:
            hist.SetMinimum(0.0)
            hist.SetMaximum(1.0)

        hist.SetLineColor(ROOT.kBlue)
        hist.SetLineWidth(2)
        hist.Draw("HIST E1")

        latex_draws = []
        offset = (max_y if max_y > -1e8 else 1.0) * 0.08
        for i in range(1, hist.GetNbinsX() + 1):
            val = hist.GetBinContent(i)
            err = hist.GetBinError(i)
            if val == 0 and err == 0:
                continue
            pt_center = hist.GetBinCenter(i)
            y_pos = val + err + offset
            txt = ROOT.TLatex(pt_center, y_pos, f"#splitline{{{val:.4f}}}{{#pm {err:.4f}}}")
            txt.SetTextSize(0.022)
            txt.SetTextAlign(21)
            txt.SetTextColor(ROOT.kBlack)
            txt.Draw()
            latex_draws.append(txt)

        out_pdf = f"E_mix_final_{label}.pdf"
        c.SaveAs(out_pdf)
        c.Close()
        print(f"Saved: {out_pdf}")


def build_graphs_from_th1(h_xsec, h_sys, suffix_name):
    """Converts h1_xsec and h1_sys TH1D histograms into TGraphErrors for stat points and sys bands."""
    g_xsec = ROOT.TGraphErrors()
    g_xsec.SetName(f"g_xsec_{suffix_name}")
    g_sys = ROOT.TGraphErrors()
    g_sys.SetName(f"g_sys_{suffix_name}")

    pt_idx = 0
    for b in range(1, h_xsec.GetNbinsX() + 1):
        val = h_xsec.GetBinContent(b)
        if val <= 0:
            continue
        stat_err = h_xsec.GetBinError(b)
        sys_err = h_sys.GetBinError(b)
        pt_center = h_xsec.GetBinCenter(b)
        pt_half_width = h_xsec.GetBinWidth(b) / 2.0

        g_xsec.SetPoint(pt_idx, pt_center, val)
        g_xsec.SetPointError(pt_idx, 0.0, stat_err)

        g_sys.SetPoint(pt_idx, pt_center, val)
        g_sys.SetPointError(pt_idx, pt_half_width, sys_err)
        pt_idx += 1

    return g_xsec, g_sys


def generate_xsec_comparison_pdfs(f_curr, f_prev):
    """Generates split-canvas Latest vs Previous cross-section overlay and ratio plots for LH2 and LD2."""
    targets = ["LH2", "LD2"]

    for target in targets:
        dir_name = f"CrossSections_{target}"
        xsec_name = f"{dir_name}/h1_xsec_{target}_geom"
        sys_name = f"{dir_name}/h1_sys_{target}_geom"

        h_xsec_curr = f_curr.Get(xsec_name)
        h_sys_curr = f_curr.Get(sys_name)
        h_xsec_prev = f_prev.Get(xsec_name)
        h_sys_prev = f_prev.Get(sys_name)

        if not all([h_xsec_curr, h_sys_curr, h_xsec_prev, h_sys_prev]):
            raise KeyError(f"Missing '{xsec_name}' or '{sys_name}' in one of the ROOT files.")

        nbins = h_xsec_curr.GetNbinsX()
        if nbins != h_xsec_prev.GetNbinsX():
            raise ValueError(f"Bin count mismatch in {xsec_name}: {nbins} vs {h_xsec_prev.GetNbinsX()}")

        # Build TGraphErrors for top pad
        g_xsec_curr, g_sys_curr = build_graphs_from_th1(h_xsec_curr, h_sys_curr, f"{target}_latest")
        g_xsec_prev, g_sys_prev = build_graphs_from_th1(h_xsec_prev, h_sys_prev, f"{target}_prev")

        # Build Ratio TGraphErrors (Latest / Previous) for bottom pad
        g_ratio_stat = ROOT.TGraphErrors()
        g_ratio_stat.SetName(f"g_ratio_stat_{target}")
        g_ratio_sys = ROOT.TGraphErrors()
        g_ratio_sys.SetName(f"g_ratio_sys_{target}")

        r_idx = 0
        for b in range(1, nbins + 1):
            y_curr = h_xsec_curr.GetBinContent(b)
            y_prev = h_xsec_prev.GetBinContent(b)
            if y_curr <= 0 or y_prev <= 0:
                continue

            e_stat_curr = h_xsec_curr.GetBinError(b)
            e_sys_curr = h_sys_curr.GetBinError(b)
            e_stat_prev = h_xsec_prev.GetBinError(b)
            e_sys_prev = h_sys_prev.GetBinError(b)

            ratio = y_curr / y_prev

            rel_stat_curr = e_stat_curr / y_curr
            rel_stat_prev = e_stat_prev / y_prev
            err_ratio_stat = ratio * math.sqrt(rel_stat_curr ** 2 + rel_stat_prev ** 2)

            rel_sys_curr = e_sys_curr / y_curr
            rel_sys_prev = e_sys_prev / y_prev
            err_ratio_sys = ratio * math.sqrt(rel_sys_curr ** 2 + rel_sys_prev ** 2)

            pt_center = h_xsec_curr.GetBinCenter(b)
            pt_half_width = h_xsec_curr.GetBinWidth(b) / 2.0

            g_ratio_stat.SetPoint(r_idx, pt_center, ratio)
            g_ratio_stat.SetPointError(r_idx, 0.0, err_ratio_stat)

            g_ratio_sys.SetPoint(r_idx, pt_center, ratio)
            g_ratio_sys.SetPointError(r_idx, pt_half_width, err_ratio_sys)
            r_idx += 1

        canvas = ROOT.TCanvas(f"c_comp_{target}", f"Comparison {target}", 800, 800)

        # --- Pad 1: Cross-Sections Overlay (Top 65%) ---
        pad1 = ROOT.TPad("pad1", "pad1", 0, 0.35, 1, 1.0)
        pad1.SetBottomMargin(0.15)
        pad1.SetLeftMargin(0.16)
        pad1.SetRightMargin(0.05)
        pad1.SetTopMargin(0.08)
        pad1.SetTickx(1)
        pad1.SetTicky(1)
        pad1.Draw()
        pad1.cd()

        mg_top = ROOT.TMultiGraph()

        # Previous Styling (Blue with transparent Azure band)
        g_sys_prev.SetMarkerSize(0)
        g_sys_prev.SetLineColor(ROOT.kBlue)
        g_sys_prev.SetFillColorAlpha(ROOT.kAzure + 1, 0.5)
        g_sys_prev.SetFillStyle(1001)
        g_xsec_prev.SetMarkerStyle(20)
        g_xsec_prev.SetMarkerColor(ROOT.kBlue)
        g_xsec_prev.SetLineColor(ROOT.kBlue)

        # Latest Styling (Red with transparent Pink band)
        g_sys_curr.SetMarkerSize(0)
        g_sys_curr.SetLineColor(ROOT.kRed)
        g_sys_curr.SetFillColorAlpha(ROOT.kPink - 9, 0.5)
        g_sys_curr.SetFillStyle(1001)
        g_xsec_curr.SetMarkerStyle(20)
        g_xsec_curr.SetMarkerColor(ROOT.kRed)
        g_xsec_curr.SetLineColor(ROOT.kRed)

        mg_top.Add(g_sys_prev, "2")
        mg_top.Add(g_sys_curr, "2")
        mg_top.Add(g_xsec_prev, "P")
        mg_top.Add(g_xsec_curr, "P")

        mg_top.Draw("A")
        mg_top.SetTitle("")
        mg_top.GetXaxis().SetLimits(0.0, 2.0)

        mg_top.GetYaxis().SetTitle("d#sigma/dp_{T} [nb/GeV/Nucleus]")
        mg_top.GetYaxis().CenterTitle()
        mg_top.GetYaxis().SetTitleFont(43)
        mg_top.GetYaxis().SetTitleSize(22)
        mg_top.GetYaxis().SetTitleOffset(2.0)
        mg_top.GetYaxis().SetLabelFont(43)
        mg_top.GetYaxis().SetLabelSize(20)

        mg_top.GetXaxis().SetTitle("p_{T} [GeV]")
        mg_top.GetXaxis().CenterTitle()
        mg_top.GetXaxis().SetTitleFont(43)
        mg_top.GetXaxis().SetTitleSize(22)
        mg_top.GetXaxis().SetTitleOffset(1.2)
        mg_top.GetXaxis().SetLabelFont(43)
        mg_top.GetXaxis().SetLabelSize(20)

        y_max = 0.0
        for g_x, g_s in [(g_xsec_curr, g_sys_curr), (g_xsec_prev, g_sys_prev)]:
            for i in range(g_x.GetN()):
                val = g_x.GetY()[i] + max(g_x.GetErrorY(i), g_s.GetErrorY(i))
                if val > y_max:
                    y_max = val
        mg_top.SetMinimum(0.0)
        mg_top.SetMaximum(y_max * 1.4 if y_max > 0 else 1.0)

        leg_top = ROOT.TLegend(0.62, 0.65, 0.88, 0.88)
        leg_top.SetBorderSize(0)
        leg_top.SetFillStyle(0)
        leg_top.SetTextFont(43)
        leg_top.SetTextSize(18)
        leg_top.AddEntry(g_xsec_curr, f"Latest ({target})", "lep")
        leg_top.AddEntry(g_sys_curr, "Latest Sys. Unc.", "f")
        leg_top.AddEntry(g_xsec_prev, f"Previous ({target})", "lep")
        leg_top.AddEntry(g_sys_prev, "Previous Sys. Unc.", "f")
        leg_top.Draw()

        target_prefix = "pp" if target == "LH2" else "pd"
        internal_title = ROOT.TLatex()
        internal_title.SetNDC(True)
        internal_title.SetTextFont(43)
        internal_title.SetTextSize(22)
        internal_title.SetTextAlign(13)
        internal_title.DrawLatex(0.19, 0.86, f"Drell-Yan process in {target_prefix}")

        prelim = ROOT.TLatex()
        prelim.SetNDC(True)
        prelim.SetTextFont(43)
        prelim.SetTextSize(24)
        prelim.SetTextColor(ROOT.kBlue)
        prelim.SetTextAlign(33)
        prelim.DrawLatex(0.85, 0.55, "Preliminary")

        # --- Pad 2: Ratio Latest / Previous (Bottom 35%) ---
        canvas.cd()
        pad2 = ROOT.TPad("pad2", "pad2", 0, 0.0, 1, 0.35)
        pad2.SetTopMargin(0.05)
        pad2.SetBottomMargin(0.35)
        pad2.SetLeftMargin(0.16)
        pad2.SetRightMargin(0.05)
        pad2.SetTickx(1)
        pad2.SetTicky(1)
        pad2.Draw()
        pad2.cd()

        mg_bottom = ROOT.TMultiGraph()

        # Fit horizontal pol0 to systematic errors as in analyzer.py
        fit_func = ROOT.TF1(f"fit_ratio_{target}", "pol0", 0.0, 2.0)
        g_ratio_sys.Fit(fit_func, "Q0")
        fit_val = fit_func.GetParameter(0)
        fit_err = fit_func.GetParError(0)

        g_fit_band = ROOT.TGraphErrors()
        g_fit_band.SetPoint(0, 0.0, fit_val)
        g_fit_band.SetPointError(0, 0.0, fit_err)
        g_fit_band.SetPoint(1, 2.0, fit_val)
        g_fit_band.SetPointError(1, 0.0, fit_err)
        g_fit_band.SetFillColorAlpha(ROOT.kPink, 0.4)
        g_fit_band.SetFillStyle(1001)

        g_ratio_sys.SetMarkerSize(0)
        g_ratio_sys.SetLineColor(ROOT.kGreen + 2)
        g_ratio_sys.SetFillColorAlpha(ROOT.kGreen - 9, 0.5)
        g_ratio_sys.SetFillStyle(1001)

        g_ratio_stat.SetMarkerStyle(20)
        g_ratio_stat.SetMarkerColor(ROOT.kBlack)
        g_ratio_stat.SetLineColor(ROOT.kBlack)

        mg_bottom.Add(g_fit_band, "3")
        mg_bottom.Add(g_ratio_sys, "2")
        mg_bottom.Add(g_ratio_stat, "P")

        mg_bottom.Draw("A")
        mg_bottom.SetTitle("")
        mg_bottom.GetXaxis().SetLimits(0.0, 2.0)

        mg_bottom.GetYaxis().SetTitle("Latest / Previous")
        mg_bottom.GetYaxis().CenterTitle()
        mg_bottom.GetYaxis().SetTitleFont(43)
        mg_bottom.GetYaxis().SetTitleSize(22)
        mg_bottom.GetYaxis().SetTitleOffset(2.0)
        mg_bottom.GetYaxis().SetLabelFont(43)
        mg_bottom.GetYaxis().SetLabelSize(20)
        mg_bottom.GetYaxis().SetNdivisions(505)

        mg_bottom.GetXaxis().SetTitle("p_{T} [GeV]")
        mg_bottom.GetXaxis().CenterTitle()
        mg_bottom.GetXaxis().SetTitleFont(43)
        mg_bottom.GetXaxis().SetTitleSize(22)
        mg_bottom.GetXaxis().SetTitleOffset(1.2)
        mg_bottom.GetXaxis().SetLabelFont(43)
        mg_bottom.GetXaxis().SetLabelSize(20)

        y_max_r, y_min_r = -1e9, 1e9
        if fit_val + fit_err > y_max_r:
            y_max_r = fit_val + fit_err
        if fit_val - fit_err < y_min_r:
            y_min_r = fit_val - fit_err

        for i in range(g_ratio_stat.GetN()):
            y = g_ratio_stat.GetY()[i]
            err = max(g_ratio_stat.GetErrorY(i), g_ratio_sys.GetErrorY(i))
            if y + err > y_max_r:
                y_max_r = y + err
            if y - err < y_min_r:
                y_min_r = y - err

        if y_min_r < y_max_r:
            y_range = max(y_max_r - y_min_r, 0.05)
            mg_bottom.SetMinimum(max(0.0, y_min_r - 0.5 * y_range))
            mg_bottom.SetMaximum(y_max_r + 0.6 * y_range)
        else:
            mg_bottom.SetMinimum(0.5)
            mg_bottom.SetMaximum(1.5)

        line = ROOT.TLine(0.0, 1.0, 2.0, 1.0)
        line.SetLineStyle(2)
        line.SetLineColor(ROOT.kGray + 2)
        line.SetLineWidth(2)
        line.Draw("SAME")

        fit_func.SetLineColor(ROOT.kRed)
        fit_func.SetLineWidth(2)
        fit_func.Draw("SAME")

        latex_fit = ROOT.TLatex()
        latex_fit.SetTextFont(43)
        latex_fit.SetTextSize(20)
        latex_fit.SetTextColor(ROOT.kRed)
        y_text = fit_val + fit_err + ((mg_bottom.GetYaxis().GetXmax() - mg_bottom.GetYaxis().GetXmin()) * 0.05)
        latex_fit.DrawLatex(0.2, y_text, f"Best Fit: {fit_val:.4f} #pm {fit_err:.4f}")

        out_pdf = f"CrossSection_Comparison_{target}_geom_vs_pT.pdf"
        canvas.SaveAs(out_pdf)
        canvas.Close()
        print(f"Saved: {out_pdf}")


def main():
    setup_root()

    prev_file_path = resolve_path(
        "/root/github/seaquest-dy-1d-abs-xsec/src/xsec_pT/RS70/previous_xsec_results/All_XSec_Objects.root"
    )
    curr_file_path = resolve_path(
        "/root/github/seaquest-dy-1d-abs-xsec/src/xsec_pT/RS70/All_XSec_Objects.root"
    )

    f_prev = ROOT.TFile.Open(prev_file_path, "READ")
    f_curr = ROOT.TFile.Open(curr_file_path, "READ")

    if not f_prev or f_prev.IsZombie():
        raise RuntimeError(f"Failed to open {prev_file_path}")
    if not f_curr or f_curr.IsZombie():
        raise RuntimeError(f"Failed to open {curr_file_path}")

    # 1. Generate E_mix_final_{LH2,LD2,Flask}.pdf
    generate_emix_final_pdfs(f_curr, f_prev)

    # 2. Generate CrossSection_Comparison_{LH2,LD2}_geom_vs_pT.pdf
    generate_xsec_comparison_pdfs(f_curr, f_prev)

    f_curr.Close()
    f_prev.Close()


if __name__ == "__main__":
    main()