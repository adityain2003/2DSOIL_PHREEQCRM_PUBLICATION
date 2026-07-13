"""Print one variant's Table-1 numbers (total leached + 3-event RMSE) for the
CURRENT VARIANT_RUNS output, compared to the n=2.0 manuscript baseline.
Methodology mirrors total_leaching_vs_observed.py / rmse_vs_observed.py exactly.
Usage: python _one_variant.py <VAR>
"""
import sys, os, math, numpy as np, pandas as pd
ROOT = r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION"
GENR = os.path.join(ROOT, "2DSOIL_PHREEQCRM_MODEL", "POST_PROCESSING", "ANALYSIS", "_data", "VARIANT_RUNS")
OBS3 = [20.6, 25.7, 35.7]; OBS_TOT = 35.7; D = [2.0, 10.0, 24.0]
# n=2.0 baseline (manuscript Table 1): (total_leached, RMSE_std) from the committed
# _TOTAL_LEACHING_VS_OBSERVED.csv and _RMSE_VS_OBSERVED.csv (gen_ columns).
BASE = {"NR":(25.50605,6.243452), "ZK":(21.63695,9.087067), "ZK_ND":(59.19631,12.271981),
        "FK":(31.72883,3.763441), "FK_ND":(49.60062,7.553092), "CK":(33.38669,2.755259)}

def prof(g):
    df = pd.read_csv(g); df.columns = [c.strip() for c in df.columns]
    t = np.asarray(df["Date_time"].values, float); t = t - t[0]
    return t, (-df["N_Leach"]).cumsum().values + 0.0

def rmse(m): return math.sqrt(np.mean([(a-b)**2 for a, b in zip(m, OBS3)]))

v = sys.argv[1]
t, c = prof(os.path.join(GENR, v, "DELHI_MURPHY.G05"))
tot = float(c[-1]); r = rmse([float(np.interp(d, t, c)) for d in D])
bt, br = BASE[v]
print(f"{v:6s} | total  n1.78={tot:7.2f}  n2.0={bt:7.2f}  d={tot-bt:+6.2f}  "
      f"| mismatch n1.78={100*(tot-OBS_TOT)/OBS_TOT:+6.1f}%  n2.0={100*(bt-OBS_TOT)/OBS_TOT:+6.1f}%  "
      f"| RMSE n1.78={r:6.2f}  n2.0={br:6.2f}  d={r-br:+6.2f}")
