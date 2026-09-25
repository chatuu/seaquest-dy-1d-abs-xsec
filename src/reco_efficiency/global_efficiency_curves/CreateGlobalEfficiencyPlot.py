import ROOT
import uproot
import numpy as np
import array

# ==========================================
# CONFIGURATION
# ==========================================
filename = "merged_RS67_3089LH2_recoeff.root"
output_filename = "D1_Distributions_Top10.root"

# Bin Definitions
xf_bins = np.round(np.arange(0.0, 0.9, 0.05), 2).astype(float)
mass_bins = np.array([4.2, 4.5, 4.8, 5.1, 5.4, 5.7, 6.0, 6.3, 6.6, 6.9, 7.5, 8.8], dtype=float)
d1_bins = np.linspace(0, 400, 51)  # 50 bins from 0 to 400

# Branches needed (Unweighted)
branches = [
    "dx", "dy", "dz", "dpx", "dpy", "dpz", "mass", "xF", "xT", 
    "costh", "trackSeparation", "chisq_dimuon", "D1",
    "nHits1", "nHits2", "nHits1St1", "nHits2St1",
    "chisq1_target", "chisq1_upstream", "chisq1_dump", "chisq1",
    "chisq2_target", "chisq2_upstream", "chisq2_dump", "chisq2",
    "x1_t", "y1_t", "x1_d", "y1_d", "z1_v",
    "x2_t", "y2_t", "x2_d", "y2_d", "z2_v",
    "pz1_st1", "y1_st1", "y1_st3", "px1_st1", "px1_st3", "py1_st1", "py1_st3", "pz1_st3",
    "pz2_st1", "y2_st1", "y2_st3", "px2_st1", "px2_st3", "py2_st1", "py2_st3", "pz2_st3",
    "x1_st1", "x2_st1", "D2", "D3"
]

# ==========================================
# HELPER: CUTS FUNCTION
# ==========================================
def apply_cuts(batch):
    beam_offset = 1.6
    
    # Dimuon Cuts
    mask = (np.abs(batch["dx"]) < 0.25)
    mask &= (np.abs(batch["dy"] - beam_offset) < 0.22)
    mask &= (batch["dz"] < -5.0) & (batch["dz"] > -280.0)
    mask &= (np.abs(batch["dpx"]) < 1.8)
    mask &= (np.abs(batch["dpy"]) < 2.0)
    mask &= ((batch["dpx"]**2 + batch["dpy"]**2) < 5.0)
    mask &= (batch["dpz"] < 116.0) & (batch["dpz"] > 38.0)
    mask &= (batch["mass"] > 4.2) & (batch["mass"] < 8.8)
    mask &= ((batch["dx"]**2 + (batch["dy"] - beam_offset)**2) < 0.06)
    mask &= (batch["xF"] < 0.95) & (batch["xF"] > -0.1)
    mask &= (batch["xT"] > 0.05) & (batch["xT"] <= 0.58)
    mask &= (np.abs(batch["costh"]) < 0.5)
    mask &= (np.abs(batch["trackSeparation"]) < 270.0)
    mask &= (batch["chisq_dimuon"] < 18)

    # Track 1 Cuts
    mask &= (batch["chisq1_target"] < 15.)
    mask &= (batch["pz1_st1"] > 9.) & (batch["pz1_st1"] < 75.)
    mask &= (batch["nHits1"] > 13)
    mask &= (batch["x1_t"]**2 + (batch["y1_t"] - beam_offset)**2 < 320.)
    mask &= (batch["x1_d"]**2 + (batch["y1_d"] - beam_offset)**2 < 1100.)
    mask &= (batch["x1_d"]**2 + (batch["y1_d"] - beam_offset)**2 > 16.)
    mask &= (batch["chisq1_target"] < 1.5 * batch["chisq1_upstream"])
    mask &= (batch["chisq1_target"] < 1.5 * batch["chisq1_dump"])
    mask &= (batch["z1_v"] < -5.) & (batch["z1_v"] > -320.)
    mask &= (batch["chisq1"] / (batch["nHits1"] - 5) < 12)
    mask &= ((batch["y1_st1"] / batch["y1_st3"]) < 1.)
    mask &= (np.abs(np.abs(batch["px1_st1"] - batch["px1_st3"]) - 0.416) < 0.008)
    mask &= (np.abs(batch["py1_st1"] - batch["py1_st3"]) < 0.008)
    mask &= (np.abs(batch["pz1_st1"] - batch["pz1_st3"]) < 0.08)
    mask &= ((batch["y1_st1"] * batch["y1_st3"]) > 0.)
    mask &= (np.abs(batch["py1_st1"]) > 0.02)

    # Track 2 Cuts
    mask &= (batch["chisq2_target"] < 15.)
    mask &= (batch["pz2_st1"] > 9.) & (batch["pz2_st1"] < 75.)
    mask &= (batch["nHits2"] > 13)
    mask &= (batch["x2_t"]**2 + (batch["y2_t"] - beam_offset)**2 < 320.)
    mask &= (batch["x2_d"]**2 + (batch["y2_d"] - beam_offset)**2 < 1100.)
    mask &= (batch["x2_d"]**2 + (batch["y2_d"] - beam_offset)**2 > 16.)
    mask &= (batch["chisq2_target"] < 1.5 * batch["chisq2_upstream"])
    mask &= (batch["chisq2_target"] < 1.5 * batch["chisq2_dump"])
    mask &= (batch["z2_v"] < -5.) & (batch["z2_v"] > -320.)
    mask &= (batch["chisq2"] / (batch["nHits2"] - 5) < 12)
    mask &= ((batch["y2_st1"] / batch["y2_st3"]) < 1.)
    mask &= (np.abs(np.abs(batch["px2_st1"] - batch["px2_st3"]) - 0.416) < 0.008)
    mask &= (np.abs(batch["py2_st1"] - batch["py2_st3"]) < 0.008)
    mask &= (np.abs(batch["pz2_st1"] - batch["pz2_st3"]) < 0.08)
    mask &= ((batch["y2_st1"] * batch["y2_st3"]) > 0.)
    mask &= (np.abs(batch["py2_st1"]) > 0.02)

    # Combined & Occupancy
    mask &= (np.abs(batch["chisq1_target"] + batch["chisq2_target"] - batch["chisq_dimuon"]) < 2.)
    mask &= ((batch["y1_st3"] * batch["y2_st3"]) < 0.)
    mask &= ((batch["nHits1"] + batch["nHits2"]) > 29)
    mask &= ((batch["nHits1St1"] + batch["nHits2St1"]) > 8)
    mask &= (np.abs(batch["x1_st1"] + batch["x2_st1"]) < 42)
    mask &= (batch["D1"] < 400) & (batch["D2"] < 400) & (batch["D3"] < 400)
    mask &= ((batch["D1"] + batch["D2"] + batch["D3"]) < 1000)

    return mask

# ==========================================
# PROCESSING & PLOTTING
# ==========================================
def process_tree(tree_name):
    print(f"Processing tree: {tree_name}...")
    
    # Dimensions
    n_mass = len(mass_bins) - 1
    n_xf = len(xf_bins) - 1
    n_d1 = len(d1_bins) - 1
    
    # 3D Accumulator (Mass, xF, D1)
    h_acc_3d = np.zeros((n_mass, n_xf, n_d1))
    
    # 1. Fill 3D Numpy Array
    with uproot.open(filename) as file:
        if tree_name not in file:
            print(f"Skipping {tree_name}")
            return None, None

        tree = file[tree_name]
        
        for batch in tree.iterate(branches, library="np", step_size=100000):
            mask = apply_cuts(batch)
            
            v_mass = batch["mass"][mask]
            v_xf   = batch["xF"][mask]
            v_d1   = batch["D1"][mask]
            
            if len(v_mass) == 0: continue

            # Accumulate (Unweighted)
            H, _ = np.histogramdd(
                (v_mass, v_xf, v_d1), 
                bins=(mass_bins, xf_bins, d1_bins)
            )
            h_acc_3d += H
            
    # 2. Identify Top 10 Bins
    print(f"  - Identifying Top 10 Kinematic Bins...")
    
    # Sum over D1 axis to get total counts per kinematic bin (Mass, xF)
    kinematic_counts = np.sum(h_acc_3d, axis=2)
    
    # Flatten and sort indices by count (descending)
    flat_indices = np.argsort(kinematic_counts.ravel())[::-1] 
    top_10_flat = flat_indices[:10]
    
    # Convert back to (mass_idx, xf_idx)
    top_indices = np.unravel_index(top_10_flat, kinematic_counts.shape)
    top_indices = list(zip(top_indices[0], top_indices[1])) 
    
    # 3. Setup Canvas (5 columns x 2 rows)
    c1 = ROOT.TCanvas(f"c_d1_top10_{tree_name}", f"Top 10 D1 Distributions {tree_name}", 1500, 800)
    c1.Divide(5, 2, 0.001, 0.001)
    
    hist_list = []
    text_list = [] 
    d1_edges = array.array('d', d1_bins)
    
    # 4. Loop over Top 10 Bins
    for pad_idx, (i, j) in enumerate(top_indices):
        
        # Extract 1D array for this specific bin
        counts_1d = h_acc_3d[i, j, :]
        total_counts = kinematic_counts[i, j]
        
        # Bin Ranges for Title
        m_low, m_high = mass_bins[i], mass_bins[i+1]
        xf_low, xf_high = xf_bins[j], xf_bins[j+1]
        
        hist_name = f"h_d1_{tree_name}_rank{pad_idx}_m{i}_xf{j}"
        title = f"Rank {pad_idx+1}: M[{m_low:.1f},{m_high:.1f}] xF[{xf_low:.2f},{xf_high:.2f}] (N={int(total_counts)});D1;Counts"
        
        h_temp = ROOT.TH1D(hist_name, title, n_d1, d1_edges)
        
        for k in range(n_d1):
            content = counts_1d[k]
            h_temp.SetBinContent(k + 1, content)
            h_temp.SetBinError(k + 1, np.sqrt(content))
        
        hist_list.append(h_temp)
        
        # Go to Pad (1-based index)
        c1.cd(pad_idx + 1)
        
        # --- STYLING: THIN LINES ---
        h_temp.SetStats(0)
        h_temp.SetLineColor(ROOT.kBlue + 1)
        h_temp.SetFillColor(ROOT.kAzure - 9)
        
        h_temp.SetLineWidth(1)
        h_temp.GetXaxis().SetLabelSize(0.05)
        h_temp.GetYaxis().SetLabelSize(0.05)
        h_temp.SetTitleSize(0.06)
        h_temp.GetXaxis().SetAxisColor(1)
        h_temp.GetYaxis().SetAxisColor(1)
        
        h_temp.Draw("HIST E")
        
        # --- LABELS (Peak and Mean) ---
        if h_temp.GetEntries() > 0:
            # 1. Peak
            max_bin_idx = h_temp.GetMaximumBin()
            max_d1_val = h_temp.GetXaxis().GetBinCenter(max_bin_idx)
            
            # 2. Mean
            mean_d1_val = h_temp.GetMean()
            
            lbl = ROOT.TLatex()
            lbl.SetNDC()
            lbl.SetTextSize(0.06) 
            lbl.SetTextAlign(32)  # Right-aligned, Vertically Centered
            lbl.SetTextColor(ROOT.kRed)
            lbl.SetLineWidth(1) 
            
            # Draw Peak
            lbl.DrawLatex(0.88, 0.85, f"Peak D1: {max_d1_val:.1f}")
            
            # Draw Mean (slightly below)
            lbl.DrawLatex(0.88, 0.78, f"Mean D1: {mean_d1_val:.1f}")
            
            text_list.append(lbl)

    c1.Update()
    return c1, hist_list, text_list

# ==========================================
# MAIN
# ==========================================
def main():
    # --- GLOBAL STYLE SETTINGS FOR THIN LINES ---
    ROOT.gStyle.SetOptStat(0)
    ROOT.gStyle.SetFrameLineWidth(1) 
    ROOT.gStyle.SetLineWidth(1)      
    ROOT.gStyle.SetHistLineWidth(1)  
    ROOT.gStyle.SetFuncWidth(1)      
    ROOT.gStyle.SetGridWidth(1)      
    
    outfile = ROOT.TFile(output_filename, "RECREATE")
    
    # Process Result
    c_res, h_res_list, t_res = process_tree("result")
    if c_res:
        c_res.Write()
        # --- SAVE PDF FOR RESULT ---
        print("Saving PDF: D1_Distributions_Top10_Result.pdf...")
        c_res.SaveAs("D1_Distributions_Top10_Result.pdf")
        
        dirname = outfile.mkdir("result_histograms")
        dirname.cd()
        for h in h_res_list:
            h.Write()
            
    # Process Result Mix
    c_mix, h_mix_list, t_mix = process_tree("result_mix")
    if c_mix:
        outfile.cd()
        c_mix.Write()
        # --- SAVE PDF FOR RESULT MIX ---
        print("Saving PDF: D1_Distributions_Top10_ResultMix.pdf...")
        c_mix.SaveAs("D1_Distributions_Top10_ResultMix.pdf")
        
        dirname = outfile.mkdir("result_mix_histograms")
        dirname.cd()
        for h in h_mix_list:
            h.Write()
            
    outfile.Close()
    print(f"\nSaved to {output_filename}")

if __name__ == "__main__":
    main()