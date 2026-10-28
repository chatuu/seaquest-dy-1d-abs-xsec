import os
import sys
import math
import ROOT
import numpy as np

# ==========================================
# Configuration
# ==========================================
LATEST_FILE_PATH = os.path.expanduser("~/github/seaquest-dy-1d-abs-xsec/src/xsec_pT/RS57/All_XSec_Objects.root")
EXISTING_FILE_PATH = os.path.expanduser("/root/github/e906-development/src/xsec_pT/RS57/All_XSec_Objects.root")
OUTPUT_DIR = "Comparison_Plots"

TARGETS = ["LH2", "LD2", "Flask"]
EFF_HISTOGRAMS = [
    "E_total_reco",
    "E_mix_reco",
    "E_total_final",
    "E_mix_final",
    "E_final_signal"
]

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetEndErrorSize(5)

# ==========================================
# Helper: Correlated Error Propagation
# ==========================================
def get_ratio_and_error(y_new, err_new, y_old, err_old, rho=1.0):
    """
    Calculates the ratio and propagates errors assuming the two measurements 
    are highly correlated (rho = 1.0 for same data, slightly different corrections).
    """
    if y_old <= 0 or y_new <= 0:
        return 0.0, 0.0
    
    ratio = y_new / y_old
    rel_new = err_new / y_new
    rel_old = err_old / y_old
    
    # Error propagation formula with correlation
    radicand = rel_new**2 + rel_old**2 - 2 * rho * rel_new * rel_old
    if radicand < 0: 
        radicand = 0.0
        
    err_ratio = ratio * math.sqrt(radicand)
    return ratio, err_ratio

# ==========================================
# Plotting Functions
# ==========================================
def create_ratio_pad(canvas_name):
    """Sets up the top and bottom pads for the overlay and ratio plots."""
    c = ROOT.TCanvas(canvas_name, "Comparison", 800, 800)
    
    # Top Pad (Overlay)
    pad1 = ROOT.TPad("pad1", "pad1", 0, 0.35, 1, 1.0)
    pad1.SetBottomMargin(0.02)  # Join with bottom pad
    pad1.SetLeftMargin(0.15)
    pad1.SetRightMargin(0.05)
    pad1.SetTopMargin(0.08)
    pad1.SetTickx(1); pad1.SetTicky(1)
    pad1.Draw()
    
    # Bottom Pad (Ratio)
    c.cd()
    pad2 = ROOT.TPad("pad2", "pad2", 0, 0.0, 1, 0.35)
    pad2.SetTopMargin(0.02)
    pad2.SetBottomMargin(0.35)  # Make room for x-axis labels
    pad2.SetLeftMargin(0.15)
    pad2.SetRightMargin(0.05)
    pad2.SetTickx(1); pad2.SetTicky(1)
    pad2.Draw()
    
    return c, pad1, pad2

def plot_histogram_comparison(f_latest, f_old, target, hist_base_name):
    """Plots standard TH1D efficiency comparisons."""
    hist_name = f"{hist_base_name}_{target}"
    dir_path = f"Kinematics/{target}"
    
    h_latest = f_latest.Get(f"{dir_path}/{hist_name}")
    h_old = f_old.Get(f"{dir_path}/{hist_name}")
    
    if not h_latest or not h_old:
        print(f"  [Skip] {hist_name} not found in one or both files.")
        return

    c, pad1, pad2 = create_ratio_pad(f"c_{hist_name}")
    
    # --- Top Pad ---
    pad1.cd()
    h_latest.SetLineColor(ROOT.kRed)
    h_latest.SetMarkerColor(ROOT.kRed)
    h_latest.SetMarkerStyle(20)
    h_latest.SetLineWidth(2)
    
    h_old.SetLineColor(ROOT.kBlue)
    h_old.SetMarkerColor(ROOT.kBlue)
    h_old.SetMarkerStyle(24) # Open circle to easily see overlap
    h_old.SetLineWidth(2)
    
    # Dynamically find Y-axis bounds for Top Pad
    min_y, max_y = 1e9, -1e9
    for i in range(1, h_latest.GetNbinsX() + 1):
        vl, el = h_latest.GetBinContent(i), h_latest.GetBinError(i)
        vo, eo = h_old.GetBinContent(i), h_old.GetBinError(i)
        if vl > 0:
            min_y = min(min_y, vl - el)
            max_y = max(max_y, vl + el)
        if vo > 0:
            min_y = min(min_y, vo - eo)
            max_y = max(max_y, vo + eo)
            
    if min_y > max_y: min_y, max_y = 0.0, 1.0
    y_range = max_y - min_y
    if y_range == 0: y_range = 0.1
    
    h_latest.SetMaximum(max_y + y_range * 0.35) # 35% headroom for legend
    h_latest.SetMinimum(max(0.0, min_y - y_range * 0.1))
    
    # Strip X-axis labels on top pad and center titles
    h_latest.GetXaxis().SetLabelSize(0)
    h_latest.GetXaxis().SetTitleSize(0)
    h_latest.GetXaxis().CenterTitle()
    
    h_latest.GetYaxis().SetTitleSize(0.05)
    h_latest.GetYaxis().SetTitleOffset(1.2)
    h_latest.GetYaxis().CenterTitle()
    
    h_latest.Draw("P E1")
    h_old.Draw("P E1 SAME")
    
    leg = ROOT.TLegend(0.65, 0.70, 0.9, 0.9)
    leg.SetBorderSize(0)
    leg.AddEntry(h_latest, f"Latest {target}", "lep")
    leg.AddEntry(h_old, f"Existing {target}", "lep")
    leg.Draw()
    
    # --- Bottom Pad (Ratio) ---
    pad2.cd()
    h_ratio = h_latest.Clone(f"ratio_{hist_name}")
    h_ratio.Reset()
    
    # Calculate Ratio & Correlated Errors
    for i in range(1, h_latest.GetNbinsX() + 1):
        y_l, e_l = h_latest.GetBinContent(i), h_latest.GetBinError(i)
        y_o, e_o = h_old.GetBinContent(i), h_old.GetBinError(i)
        
        ratio, err_ratio = get_ratio_and_error(y_l, e_l, y_o, e_o, rho=1.0)
        
        h_ratio.SetBinContent(i, ratio)
        h_ratio.SetBinError(i, err_ratio)

    # Polynomial Fit
    xmin = h_ratio.GetXaxis().GetXmin()
    xmax = h_ratio.GetXaxis().GetXmax()
    fit_func = ROOT.TF1("fit_func", "pol0", xmin, xmax)
    h_ratio.Fit(fit_func, "Q0")
    
    fit_val = fit_func.GetParameter(0)
    fit_err = fit_func.GetParError(0)
    
    # Dynamically find Y-axis bounds for Bottom Pad (Ratio)
    min_r, max_r = min(0.99, fit_val - fit_err), max(1.01, fit_val + fit_err) # Ensure 1.0 is always visible
    for i in range(1, h_ratio.GetNbinsX() + 1):
        v, e = h_ratio.GetBinContent(i), h_ratio.GetBinError(i)
        if v > 0:
            min_r = min(min_r, v - e)
            max_r = max(max_r, v + e)
            
    r_range = max_r - min_r
    if r_range == 0: r_range = 0.1
    
    h_ratio.SetMinimum(min_r - r_range * 0.15)
    h_ratio.SetMaximum(max_r + r_range * 0.45) # 45% headroom for TLatex text
    
    h_ratio.SetTitle("")
    h_ratio.GetYaxis().SetTitle("Latest / Existing")
    h_ratio.GetXaxis().SetTitle("p_{T} [GeV]")
    
    # Styling Bottom Axis & Centering
    h_ratio.GetXaxis().SetTitleSize(0.12)
    h_ratio.GetXaxis().SetLabelSize(0.1)
    h_ratio.GetXaxis().SetTitleOffset(1.2)
    h_ratio.GetXaxis().CenterTitle()
    
    h_ratio.GetYaxis().SetTitleSize(0.1)
    h_ratio.GetYaxis().SetLabelSize(0.08)
    h_ratio.GetYaxis().SetTitleOffset(0.6)
    h_ratio.GetYaxis().SetNdivisions(505)
    h_ratio.GetYaxis().CenterTitle()
    
    h_ratio.SetMarkerStyle(20)
    h_ratio.SetMarkerColor(ROOT.kBlack)
    h_ratio.SetLineColor(ROOT.kBlack)
    h_ratio.Draw("P E1")
    
    # Transparent Pink Fit Band
    g_fit_band = ROOT.TGraphErrors()
    g_fit_band.SetPoint(0, xmin, fit_val)
    g_fit_band.SetPointError(0, 0, fit_err)
    g_fit_band.SetPoint(1, xmax, fit_val)
    g_fit_band.SetPointError(1, 0, fit_err)
    g_fit_band.SetFillColorAlpha(ROOT.kPink, 0.4)
    g_fit_band.SetFillStyle(1001)
    
    g_fit_band.Draw("3 SAME")
    
    # Red Fit Line
    fit_func.SetLineColor(ROOT.kRed)
    fit_func.SetLineWidth(2)
    fit_func.Draw("SAME")
    h_ratio.Draw("P E1 SAME") # Redraw points over the band
    
    # Horizontal Line at 1.0
    line = ROOT.TLine(xmin, 1.0, xmax, 1.0)
    line.SetLineStyle(2); line.SetLineColor(ROOT.kGray+2); line.Draw("SAME")
    
    # Fit Label
    latex = ROOT.TLatex()
    latex.SetTextFont(42); latex.SetTextSize(0.08); latex.SetTextColor(ROOT.kRed)
    latex.DrawLatexNDC(0.2, 0.85, f"Best Fit: {fit_val:.4f} #pm {fit_err:.4f}")
    
    c.SaveAs(f"{OUTPUT_DIR}/Comparison_{hist_name}.pdf")
    c.Close()

def plot_xsec_comparison(f_latest, f_old, target):
    """Plots TGraphErrors comparisons for Cross Sections (Data + Systematics)."""
    dir_path = f"CrossSections_{target}"
    
    g_xsec_latest = f_latest.Get(f"{dir_path}/g_xsec_{target}_geom")
    g_sys_latest  = f_latest.Get(f"{dir_path}/g_sys_{target}_geom")
    g_xsec_old    = f_old.Get(f"{dir_path}/g_xsec_{target}_geom")
    g_sys_old     = f_old.Get(f"{dir_path}/g_sys_{target}_geom")
    
    if not all([g_xsec_latest, g_sys_latest, g_xsec_old, g_sys_old]):
        print(f"  [Skip] Cross-section graphs missing for {target}.")
        return
    
    c, pad1, pad2 = create_ratio_pad(f"c_xsec_{target}")
    
    # --- Top Pad ---
    pad1.cd()
    mg = ROOT.TMultiGraph()
    mg.SetTitle(";p_{T} [GeV];d#sigma/dp_{T} [nb/GeV/Nucleus]")
    
    # Styling Old (Existing)
    g_sys_old.SetLineColor(ROOT.kBlue)
    g_sys_old.SetFillColorAlpha(ROOT.kAzure - 4, 0.4)
    g_sys_old.SetMarkerSize(0)
    
    g_xsec_old.SetLineColor(ROOT.kBlue)
    g_xsec_old.SetMarkerColor(ROOT.kBlue)
    g_xsec_old.SetMarkerStyle(24) # Open circle
    
    # Styling Latest
    g_sys_latest.SetLineColor(ROOT.kRed)
    g_sys_latest.SetFillColorAlpha(ROOT.kPink - 9, 0.4)
    g_sys_latest.SetMarkerSize(0)
    
    g_xsec_latest.SetLineColor(ROOT.kRed)
    g_xsec_latest.SetMarkerColor(ROOT.kRed)
    g_xsec_latest.SetMarkerStyle(20) # Solid circle
    
    mg.Add(g_sys_old, "2")
    mg.Add(g_sys_latest, "2")
    mg.Add(g_xsec_old, "P")
    mg.Add(g_xsec_latest, "P")
    
    mg.Draw("A")
    mg.GetXaxis().SetLimits(0.0, 2.0)
    mg.GetXaxis().SetLabelSize(0) # Hide X labels for top pad
    mg.GetXaxis().SetTitleSize(0)
    mg.GetXaxis().CenterTitle()
    
    mg.GetYaxis().SetTitleSize(0.05)
    mg.GetYaxis().SetTitleOffset(1.2)
    mg.GetYaxis().CenterTitle()
    
    # Dynamically find Y max/min for Top Pad
    min_y, max_y = 1e9, -1e9
    for i in range(g_xsec_latest.GetN()):
        yl, el_stat, el_sys = g_xsec_latest.GetY()[i], g_xsec_latest.GetErrorY(i), g_sys_latest.GetErrorY(i)
        el = max(el_stat, el_sys)
        if yl > 0:
            min_y = min(min_y, yl - el)
            max_y = max(max_y, yl + el)
            
        yo, eo_stat, eo_sys = g_xsec_old.GetY()[i], g_xsec_old.GetErrorY(i), g_sys_old.GetErrorY(i)
        eo = max(eo_stat, eo_sys)
        if yo > 0:
            min_y = min(min_y, yo - eo)
            max_y = max(max_y, yo + eo)
            
    if min_y > max_y: min_y, max_y = 0.0, 1.0
    y_range = max_y - min_y
    if y_range == 0: y_range = 0.1

    mg.SetMinimum(max(0.0, min_y - y_range * 0.05))
    mg.SetMaximum(max_y + y_range * 0.35) # 35% headroom
    
    leg = ROOT.TLegend(0.55, 0.65, 0.9, 0.9)
    leg.SetBorderSize(0)
    leg.AddEntry(g_xsec_latest, f"Latest {target} Data", "lep")
    leg.AddEntry(g_sys_latest,  f"Latest {target} Sys.", "f")
    leg.AddEntry(g_xsec_old,    f"Existing {target} Data", "lep")
    leg.AddEntry(g_sys_old,     f"Existing {target} Sys.", "f")
    leg.Draw()
    
    # --- Bottom Pad (Ratio) ---
    pad2.cd()
    
    g_ratio_stat = ROOT.TGraphErrors()
    g_ratio_sys = ROOT.TGraphErrors()
    
    pt_idx = 0
    # Assuming matching binning centers
    for i in range(g_xsec_latest.GetN()):
        x = g_xsec_latest.GetX()[i]
        
        y_l, e_l = g_xsec_latest.GetY()[i], g_xsec_latest.GetErrorY(i)
        y_o, e_o = g_xsec_old.GetY()[i], g_xsec_old.GetErrorY(i)
        e_sys_l = g_sys_latest.GetErrorY(i)
        e_sys_o = g_sys_old.GetErrorY(i)
        x_err = g_sys_latest.GetErrorX(i)
        
        if y_o > 0 and y_l > 0:
            # Ratio
            ratio, err_ratio_stat = get_ratio_and_error(y_l, e_l, y_o, e_o, rho=1.0)
            _, err_ratio_sys = get_ratio_and_error(y_l, e_sys_l, y_o, e_sys_o, rho=1.0)
            
            g_ratio_stat.SetPoint(pt_idx, x, ratio)
            g_ratio_stat.SetPointError(pt_idx, 0.0, err_ratio_stat)
            
            g_ratio_sys.SetPoint(pt_idx, x, ratio)
            g_ratio_sys.SetPointError(pt_idx, x_err, err_ratio_sys)
            pt_idx += 1

    mg_ratio = ROOT.TMultiGraph()
    
    # Fit statistical ratio points
    fit_func = ROOT.TF1("fit_func_xsec", "pol0", 0.0, 2.0)
    g_ratio_stat.Fit(fit_func, "Q0")
    fit_val = fit_func.GetParameter(0)
    fit_err = fit_func.GetParError(0)
    
    # Dynamically find Y-axis bounds for Ratio Pad
    min_r, max_r = min(0.99, fit_val - fit_err), max(1.01, fit_val + fit_err)
    for i in range(g_ratio_stat.GetN()):
        vr = g_ratio_stat.GetY()[i]
        er = max(g_ratio_stat.GetErrorY(i), g_ratio_sys.GetErrorY(i))
        if vr > 0:
            min_r = min(min_r, vr - er)
            max_r = max(max_r, vr + er)
            
    r_range = max_r - min_r
    if r_range == 0: r_range = 0.1
    
    mg_ratio.SetMinimum(min_r - r_range * 0.15)
    mg_ratio.SetMaximum(max_r + r_range * 0.45) # 45% headroom for TLatex text
    
    # Fit Band (Pink Transparent)
    g_fit_band = ROOT.TGraphErrors()
    g_fit_band.SetPoint(0, 0.0, fit_val); g_fit_band.SetPointError(0, 0.0, fit_err)
    g_fit_band.SetPoint(1, 2.0, fit_val); g_fit_band.SetPointError(1, 0.0, fit_err)
    g_fit_band.SetFillColorAlpha(ROOT.kPink, 0.4)
    g_fit_band.SetFillStyle(1001)
    
    # Style Ratio Sys Band
    g_ratio_sys.SetMarkerSize(0)
    g_ratio_sys.SetLineColor(ROOT.kGreen+2)
    g_ratio_sys.SetFillColorAlpha(ROOT.kGreen-9, 0.5)
    
    # Style Ratio Stat Points
    g_ratio_stat.SetMarkerStyle(20)
    g_ratio_stat.SetMarkerColor(ROOT.kBlack)
    g_ratio_stat.SetLineColor(ROOT.kBlack)
    
    mg_ratio.Add(g_fit_band, "3")
    mg_ratio.Add(g_ratio_sys, "2")
    mg_ratio.Add(g_ratio_stat, "P")
    
    mg_ratio.Draw("A")
    mg_ratio.GetXaxis().SetLimits(0.0, 2.0)
    
    mg_ratio.SetTitle("")
    mg_ratio.GetYaxis().SetTitle("Latest / Existing")
    mg_ratio.GetXaxis().SetTitle("p_{T} [GeV]")
    
    # Styling Bottom Axis & Centering
    mg_ratio.GetXaxis().SetTitleSize(0.12); mg_ratio.GetXaxis().SetLabelSize(0.1)
    mg_ratio.GetXaxis().SetTitleOffset(1.2)
    mg_ratio.GetXaxis().CenterTitle()
    
    mg_ratio.GetYaxis().SetTitleSize(0.1); mg_ratio.GetYaxis().SetLabelSize(0.08)
    mg_ratio.GetYaxis().SetTitleOffset(0.6); mg_ratio.GetYaxis().SetNdivisions(505)
    mg_ratio.GetYaxis().CenterTitle()
    
    line = ROOT.TLine(0.0, 1.0, 2.0, 1.0)
    line.SetLineStyle(2); line.SetLineColor(ROOT.kGray+2); line.Draw("SAME")
    
    fit_func.SetLineColor(ROOT.kRed)
    fit_func.SetLineWidth(2)
    fit_func.Draw("SAME")
    
    latex = ROOT.TLatex()
    latex.SetTextFont(42); latex.SetTextSize(0.08); latex.SetTextColor(ROOT.kRed)
    latex.DrawLatexNDC(0.2, 0.85, f"Best Fit: {fit_val:.4f} #pm {fit_err:.4f}")
    
    c.SaveAs(f"{OUTPUT_DIR}/Comparison_CrossSection_{target}_geom_vs_pT.pdf")
    c.Close()

# ==========================================
# Main Execution
# ==========================================
def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    if not os.path.exists(LATEST_FILE_PATH):
        print(f"Error: Latest file not found at {LATEST_FILE_PATH}")
        sys.exit(1)
        
    if not os.path.exists(EXISTING_FILE_PATH):
        print(f"Error: Existing file not found at {EXISTING_FILE_PATH}")
        sys.exit(1)

    print("Opening ROOT files...")
    f_latest = ROOT.TFile.Open(LATEST_FILE_PATH)
    f_old = ROOT.TFile.Open(EXISTING_FILE_PATH)

    print("Generating Efficiency Comparisons...")
    for target in TARGETS:
        for eff in EFF_HISTOGRAMS:
            plot_histogram_comparison(f_latest, f_old, target, eff)

    print("Generating Cross Section Comparisons...")
    for target in ["LH2", "LD2"]:  # Flask has no xsec
        plot_xsec_comparison(f_latest, f_old, target)

    f_latest.Close()
    f_old.Close()
    print(f"\nAll comparison plots generated successfully in '{OUTPUT_DIR}/'.")

if __name__ == "__main__":
    main()