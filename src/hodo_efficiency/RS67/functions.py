import numpy as np
import pandas as pd
import os

# Global cache for efficiency map
HODO_EFF_MAP = None
HODO_EFF_FILE = "/home/ckuruppu/github/seaquest-dy-1d-abs-xsec/src/hodo_efficiency/HodoscopeEfficiencyTables/hodoscope_eff_RS57-70_final.tsv"

# ==========================================
# EFFICIENCY CALCULATION
# ==========================================
def decode_hodo_ids(road_id):
    rid = int(road_id)
    abs_rid = abs(rid)
    h1_id = int((abs_rid - 1) / (16**3) + 1)
    h2_id = int(((abs_rid - 1) / (16**2)) % 16 + 1)
    h3_id = int(((abs_rid - 1) / 16) % 16 + 1)
    h4_id = int((abs_rid - 1) % 16 + 1)
    if rid < 0: labels = {"H1": "H1B", "H2": "H2B", "H3": "H3B", "H4": "H4B"}
    else: labels = {"H1": "H1T", "H2": "H2T", "H3": "H3T", "H4": "H4T"}
    ids = {"H1": h1_id, "H2": h2_id, "H3": h3_id, "H4": h4_id}
    return ids, labels

def load_hodo_eff_map():
    global HODO_EFF_MAP
    if HODO_EFF_MAP is not None: return HODO_EFF_MAP
    mapping = {}
    try:
        if os.path.exists(HODO_EFF_FILE):
            df = pd.read_csv(HODO_EFF_FILE, sep=r'\s+', header=None)
            for _, row in df.iterrows():
                mapping[(str(row.iloc[0]).strip(), int(row.iloc[1]))] = (float(row.iloc[2]), float(row.iloc[3]), float(row.iloc[4]))
        else:
            print(f"Warning: {HODO_EFF_FILE} not found. Efficiencies will be 1.0.")
        HODO_EFF_MAP = mapping
    except: HODO_EFF_MAP = {}
    return HODO_EFF_MAP

def calculate_single_pair_eff(pos_id, neg_id):
    """Helper to calculate efficiency for a single road pair."""
    pos_ids, pos_lbls = decode_hodo_ids(pos_id)
    neg_ids, neg_lbls = decode_hodo_ids(neg_id)
    
    eff_map = load_hodo_eff_map()
    eff_prod = 1.0
    sum_sq_relative_errors = 0.0
    
    all_keys = []
    for h in ['H1', 'H2', 'H3', 'H4']:
        all_keys.append((pos_lbls[h], pos_ids[h]))
        all_keys.append((neg_lbls[h], neg_ids[h]))

    for key in all_keys:
        if key in eff_map:
            val = eff_map[key][0]
            err_low = eff_map[key][1]
            err_up = eff_map[key][2]
            avg_err = (abs(err_low) + abs(err_up)) / 2.0
            
            eff_prod *= val
            if val > 0:
                sum_sq_relative_errors += (avg_err / val)**2
        else:
            eff_prod *= 1.0 

    prop_error = eff_prod * np.sqrt(sum_sq_relative_errors)
    return eff_prod, prop_error

def is_vector_type(obj):
    """Robust check if an object is a list/vector."""
    if hasattr(obj, '__len__') and not isinstance(obj, (str, bytes, dict)):
        return True
    if 'ROOT.VecOps.RVec' in str(type(obj)):
        return True
    return False

def calculate_hodo_efficiency_columns(df_in):
    """
    Calculates hodoeff and hodoeff_error and adds them as columns to the DataFrame.
    """
    if df_in.empty:
        return df_in

    print(f"   -> Calculating hodoscope efficiency for {len(df_in)} events...")
    df = df_in.copy()
    eff_vals = []
    eff_errs = []

    for index, row in df.iterrows():
        pos_roads = row['posRoad']
        neg_roads = row['negRoad']
        
        if not is_vector_type(pos_roads): pos_roads = [pos_roads]
        if not is_vector_type(neg_roads): neg_roads = [neg_roads]

        temp_effs = []
        temp_errs = []
        
        n_pairs = min(len(pos_roads), len(neg_roads))
        
        if n_pairs > 0:
            for i in range(n_pairs):
                val, err = calculate_single_pair_eff(int(pos_roads[i]), int(neg_roads[i]))
                temp_effs.append(val)
                temp_errs.append(err)
            
            avg_eff = np.mean(temp_effs)
            sum_sq_err = np.sum(np.array(temp_errs)**2)
            avg_err = (1.0 / n_pairs) * np.sqrt(sum_sq_err)
        else:
            avg_eff = 0.0
            avg_err = 0.0

        eff_vals.append(avg_eff)
        eff_errs.append(avg_err)

    df['hodoeff'] = np.array(eff_vals, dtype=float)
    df['hodoeff_error'] = np.array(eff_errs, dtype=float)
    return df