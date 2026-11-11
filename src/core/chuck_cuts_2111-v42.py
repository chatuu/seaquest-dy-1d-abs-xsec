import os
import numpy as np
import uproot
import matplotlib.pyplot as plt


def check_road_matching(df, rs):
    """Checks if positive and negative track road IDs match valid L1 trigger road combinations."""
    if rs in ["RS67", "RS70"]:
        pos_prefix = "minus"
        neg_prefix = "plus"
    else:
        pos_prefix = "plus"
        neg_prefix = "minus"

    path = f"/root/github/seaquest-dy-1d-abs-xsec/src/core/L1_triggered_roads/{rs}"
    if not os.path.exists(path):
        path = os.path.expanduser(f"~/github/seaquest-dy-1d-abs-xsec/src/core/L1_triggered_roads/{rs}")

    list_road_pos_top = set(np.loadtxt(f"{path}/roads_{pos_prefix}_top.txt", usecols=0, dtype=int, ndmin=1))
    list_road_pos_bot = set(np.loadtxt(f"{path}/roads_{pos_prefix}_bottom.txt", usecols=0, dtype=int, ndmin=1))

    list_road_neg_top = set(np.loadtxt(f"{path}/roads_{neg_prefix}_top.txt", usecols=0, dtype=int, ndmin=1))
    list_road_neg_bot = set(np.loadtxt(f"{path}/roads_{neg_prefix}_bottom.txt", usecols=0, dtype=int, ndmin=1))

    pos_trk_roads = df["trk1_road_ids"]
    neg_trk_roads = df["trk2_road_ids"]

    matching_status = np.zeros(len(pos_trk_roads), dtype=int)

    for i, (event_pos_trk_roads, event_neg_trk_roads) in enumerate(zip(pos_trk_roads, neg_trk_roads)):
        # Positive track
        pt = any(road in list_road_pos_top for road in event_pos_trk_roads)
        pb = any(road in list_road_pos_bot for road in event_pos_trk_roads)

        # Negative track
        nt = any(road in list_road_neg_top for road in event_neg_trk_roads)
        nb = any(road in list_road_neg_bot for road in event_neg_trk_roads)

        # Opposite top-bottom combinations
        tb = pt and nb
        bt = pb and nt

        matching_status[i] = int(tb or bt)

    return matching_status == 1


def apply_cuts(tree,
               rs,
               is_mc=False,
               lower_mass_cut=2.0,
               upper_mass_cut=10.0,
               upper_pT2_cut=7.0
               ):
    """Applies standard physics cuts and L1 road-matching cuts to the given TTree arrays in numpy."""
    # Read all branches into a dictionary of numpy arrays
    events = tree.arrays(library="np")

    class EventNamespace:
        def __init__(self, data):
            self.__dict__.update(data)

    e = EventNamespace(events)

    if is_mc:
        bo = 1.6
    else:
        bo = np.where(e.runID >= 11000, 1.6, 0.4)

    dimuon_cut = (
        (np.abs(e.dx) < 0.25) & (np.abs(e.dy - bo) < 0.22) &
        (e.dz < -5.) & (e.dz > -280.) & (np.abs(e.dpx) < 1.8) & (np.abs(e.dpy) < 2.0) &
        (e.dpx * e.dpx + e.dpy * e.dpy < upper_pT2_cut) & (e.dpz < 116.) & (e.dpz > 38.) &
        (e.mass > lower_mass_cut) & (e.mass < upper_mass_cut) &
        (e.dx * e.dx + (e.dy - bo) * (e.dy - bo) < 0.06) &
        (e.xF < 0.95) & (e.xF > -0.1) & (e.xT > 0.05) & (e.xT <= 0.58) &
        (np.abs(e.costh) < 0.5) & (np.abs(e.trackSeparation) < 270.) &
        (e.chisq_dimuon < 18)
    )

    track1_cut = (
        (e.chisq1_target < 15.) & (e.pz1_st1 > 9.) & (e.pz1_st1 < 75.) & (e.nHits1 > 13) &
        (e.x1_t * e.x1_t + (e.y1_t - bo) * (e.y1_t - bo) < 320.) &
        (e.x1_d * e.x1_d + (e.y1_d - bo) * (e.y1_d - bo) < 1100.) &
        (e.x1_d * e.x1_d + (e.y1_d - bo) * (e.y1_d - bo) > 16.) &
        (e.chisq1_target < 1.5 * e.chisq1_upstream) & (e.chisq1_target < 1.5 * e.chisq1_dump) &
        (e.z1_v < -5.) & (e.z1_v > -320.) & (e.chisq1 / (e.nHits1 - 5) < 12) &
        ((e.y1_st1) / (e.y1_st3) < 1.) & (np.abs(np.abs(e.px1_st1 - e.px1_st3) - 0.416) < 0.008) &
        (np.abs(e.py1_st1 - e.py1_st3) < 0.008) & (np.abs(e.pz1_st1 - e.pz1_st3) < 0.08) &
        ((e.y1_st1) * (e.y1_st3) > 0.) & (np.abs(e.py1_st1) > 0.02)
    )

    track2_cut = (
        (e.chisq2_target < 15.) & (e.pz2_st1 > 9.) & (e.pz2_st1 < 75.) & (e.nHits2 > 13) &
        (e.x2_t * e.x2_t + (e.y2_t - bo) * (e.y2_t - bo) < 320.) &
        (e.x2_d * e.x2_d + (e.y2_d - bo) * (e.y2_d - bo) < 1100.) &
        (e.x2_d * e.x2_d + (e.y2_d - bo) * (e.y2_d - bo) > 16.) &
        (e.chisq2_target < 1.5 * e.chisq2_upstream) & (e.chisq2_target < 1.5 * e.chisq2_dump) &
        (e.z2_v < -5.) & (e.z2_v > -320.) & (e.chisq2 / (e.nHits2 - 5) < 12) &
        ((e.y2_st1) / (e.y2_st3) < 1.) & (np.abs(np.abs(e.px2_st1 - e.px2_st3) - 0.416) < 0.008) &
        (np.abs(e.py2_st1 - e.py2_st3) < 0.008) & (np.abs(e.pz2_st1 - e.pz2_st3) < 0.08) &
        ((e.y2_st1) * (e.y2_st3) > 0.) & (np.abs(e.py2_st1) > 0.02)
    )

    tracks_cut = (
        (np.abs(e.chisq1_target + e.chisq2_target - e.chisq_dimuon) < 2.) &
        ((e.y1_st3) * (e.y2_st3) < 0.) & (e.nHits1 + e.nHits2 > 29) &
        (e.nHits1St1 + e.nHits2St1 > 8) & (np.abs(e.x1_st1 + e.x2_st1) < 42)
    )

    occ_cut = (
        (e.D1 < 400) & (e.D2 < 400) & (e.D3 < 400) & (e.D1 + e.D2 + e.D3 < 1000)
    )

    road_matching_cut = check_road_matching(events, rs)

    total_cut_mask = (track1_cut & track2_cut & tracks_cut & dimuon_cut & occ_cut & road_matching_cut)
    filtered_events = {}

    for key, val in events.items():
        filtered_events[key] = val[total_cut_mask]

    filtered_events["pT"] = np.sqrt(filtered_events["dpx"]**2 + filtered_events["dpy"]**2)

    return filtered_events


def apply_cuts_with_fiducial(tree,
                             rs=None,
                             is_mc=False,
                             lower_mass_cut=2.0,
                             upper_mass_cut=10.0,
                             upper_pT2_cut=7.0
                             ):
    """Applies standard physics cuts with fiducial cuts to the given TTree arrays in numpy."""
    # Read all branches into a dictionary of numpy arrays
    events = tree.arrays(library="np")

    class EventNamespace:
        def __init__(self, data):
            self.__dict__.update(data)

    e = EventNamespace(events)

    if is_mc:
        bo = 1.6
    else:
        bo = np.where(e.runID >= 11000, 1.6, 0.4)

    dimuon_cut = (
        (np.abs(e.dx) < 0.25) & (np.abs(e.dy - bo) < 0.22) &
        (e.dz < -5.) & (e.dz > -280.) & (np.abs(e.dpx) < 1.8) & (np.abs(e.dpy) < 2.0) &
        (e.dpx * e.dpx + e.dpy * e.dpy < upper_pT2_cut) & (e.dpz < 116.) & (e.dpz > 38.) &
        (e.mass > lower_mass_cut) & (e.mass < upper_mass_cut) &
        (e.dx * e.dx + (e.dy - bo) * (e.dy - bo) < 0.06) &
        (e.xF < 0.95) & (e.xF > -0.1) & (e.xT > 0.05) & (e.xT <= 0.58) &
        (np.abs(e.costh) < 0.5) & (np.abs(e.trackSeparation) < 270.) &
        (e.chisq_dimuon < 18)
    )

    track1_cut = (
        (e.chisq1_target < 15.) & (e.pz1_st1 > 9.) & (e.pz1_st1 < 75.) & (e.nHits1 > 13) &
        (e.x1_t * e.x1_t + (e.y1_t - bo) * (e.y1_t - bo) < 320.) &
        (e.x1_d * e.x1_d + (e.y1_d - bo) * (e.y1_d - bo) < 1100.) &
        (e.x1_d * e.x1_d + (e.y1_d - bo) * (e.y1_d - bo) > 16.) &
        (e.chisq1_target < 1.5 * e.chisq1_upstream) & (e.chisq1_target < 1.5 * e.chisq1_dump) &
        (e.z1_v < -5.) & (e.z1_v > -320.) & (e.chisq1 / (e.nHits1 - 5) < 12) &
        ((e.y1_st1) / (e.y1_st3) < 1.) & (np.abs(np.abs(e.px1_st1 - e.px1_st3) - 0.416) < 0.008) &
        (np.abs(e.py1_st1 - e.py1_st3) < 0.008) & (np.abs(e.pz1_st1 - e.pz1_st3) < 0.08) &
        ((e.y1_st1) * (e.y1_st3) > 0.) & (np.abs(e.py1_st1) > 0.02)
    )

    track2_cut = (
        (e.chisq2_target < 15.) & (e.pz2_st1 > 9.) & (e.pz2_st1 < 75.) & (e.nHits2 > 13) &
        (e.x2_t * e.x2_t + (e.y2_t - bo) * (e.y2_t - bo) < 320.) &
        (e.x2_d * e.x2_d + (e.y2_d - bo) * (e.y2_d - bo) < 1100.) &
        (e.x2_d * e.x2_d + (e.y2_d - bo) * (e.y2_d - bo) > 16.) &
        (e.chisq2_target < 1.5 * e.chisq2_upstream) & (e.chisq2_target < 1.5 * e.chisq2_dump) &
        (e.z2_v < -5.) & (e.z2_v > -320.) & (e.chisq2 / (e.nHits2 - 5) < 12) &
        ((e.y2_st1) / (e.y2_st3) < 1.) & (np.abs(np.abs(e.px2_st1 - e.px2_st3) - 0.416) < 0.008) &
        (np.abs(e.py2_st1 - e.py2_st3) < 0.008) & (np.abs(e.pz2_st1 - e.pz2_st3) < 0.08) &
        ((e.y2_st1) * (e.y2_st3) > 0.) & (np.abs(e.py2_st1) > 0.02)
    )

    tracks_cut = (
        (np.abs(e.chisq1_target + e.chisq2_target - e.chisq_dimuon) < 2.) &
        ((e.y1_st3) * (e.y2_st3) < 0.) & (e.nHits1 + e.nHits2 > 29) &
        (e.nHits1St1 + e.nHits2St1 > 8) & (np.abs(e.x1_st1 + e.x2_st1) < 42)
    )

    occ_cut = (
        (e.D1 < 400) & (e.D2 < 400) & (e.D3 < 400) & (e.D1 + e.D2 + e.D3 < 1000)
    )

    fiducial_cut = (
        (e.xF < 0.8) & (e.xF > 0.0) &
        (e.mass < 8.8) & (e.mass > 0.0) &
        (np.sqrt(e.dpx * e.dpx + e.dpy * e.dpy) > 0.0) & (np.sqrt(e.dpx * e.dpx + e.dpy * e.dpy) < 1.8)
    )

    total_cut_mask = (track1_cut & track2_cut & tracks_cut & dimuon_cut & occ_cut & fiducial_cut)
    if rs is not None:
        total_cut_mask = total_cut_mask & check_road_matching(events, rs)

    filtered_events = {}

    for key, val in events.items():
        filtered_events[key] = val[total_cut_mask]

    filtered_events["pT"] = np.sqrt(filtered_events["dpx"]**2 + filtered_events["dpy"]**2)

    return filtered_events