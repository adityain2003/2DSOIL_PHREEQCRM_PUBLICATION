"""Validate the GENERIC engine's nitrate-leaching run vs the PREVIOUS code,
auto-detecting the kinetic variant (CK/FK/ZK/NR/..._ND) from PHREEQC_OPTIONS.txt
and comparing against the matching original-CB3 run folder under MURPHY_SAND_LF.
Leached N = G05 (-N_Leach).cumsum() [kg N/ha], the publication method
(PYTHON_MURPHY_SAND_LF_VISUALIZATION_V3.py:120). WA checkpoints = days 1,9,23.
"""
import os, math, re
import numpy as np, pandas as pd

ROOT = r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION"
BUND = os.path.join(ROOT, "2DSOIL_PHREEQCRM_MODEL", "RUN_INPUTS", "3_NITRATE_LEACHING")
GEN  = os.path.join(BUND, "PHREEQC_NITRATE_LEACHING_EXERCISE", "DELHI_MURPHY.G05")
MUR  = os.path.join(ROOT, "OLD_VERSIONS", "3_NITRATE_LEACHING", "2DSOIL-PHREEQCRM_MURPHY_SAND_LF")

# --- detect the variant from the active PQI_FILE ---
pqi = ""
m = re.search(r"PQI_FILE\s+(\S+)", open(os.path.join(BUND, "PHREEQC_OPTIONS.txt")).read())
if m: pqi = m.group(1).upper()
if   "NO_REACTION" in pqi:                    VAR = "NR"
elif "CONDITIONAL_KINETICS_NO_DENIT" in pqi:  VAR = "CK_ND"
elif "CONDITIONAL_KINETICS" in pqi:           VAR = "CK"
elif "FIRST_ORDER_NO_DENIT" in pqi:           VAR = "FK_ND"
elif "FIRST_ORDER" in pqi:                    VAR = "FK"
elif "ZERO_ORDER_NO_DENIT" in pqi:            VAR = "ZK_ND"
elif "ZERO_ORDER" in pqi:                     VAR = "ZK"
else:                                         VAR = "CK"
REF = os.path.join(MUR, VAR, "DELHI_MURPHY.G05")

def cumleach(p):
    df = pd.read_csv(p); df.columns = [c.strip() for c in df.columns]
    t = np.asarray(df["Date_time"].values, float); t = t - t[0]
    return t, (-df["N_Leach"]).cumsum().values + 0.0

tg, cg = cumleach(GEN)
to, co = cumleach(REF)
print("=" * 72)
print("NITRATE LEACHING  variant=%s   5_GENERIC  vs  previous code" % VAR)
print("=" * 72)
print("5_GENERIC : end cumulative leached = %.4f kg N/ha" % cg[-1])
print("prev code : end cumulative leached = %.4f kg N/ha" % co[-1])
co_at = np.interp(tg, to, co); err = cg - co_at
print("\n5_GENERIC vs previous code (%s):  RMSE=%.4f  MAE=%.4f  MaxAbsErr=%.4f kg N/ha  (N=%d)"
      % (VAR, math.sqrt(np.mean(err**2)), np.mean(np.abs(err)), np.max(np.abs(err)), len(tg)))
print("\n  WA checkpoint | 5_GENERIC | prev code |  diff")
for d in (1, 9, 23, 32):
    g = np.interp(d, tg, cg); o = np.interp(d, to, co)
    tag = "  day %2d" % d + ("  WA#%d" % {1:1,9:2,23:3}[d] if d in (1,9,23) else "      ")
    print("  %-12s | %9.3f | %9.3f | %+.3f" % (tag, g, o, g-o))

# --- checkpoint RMSE vs observed (manuscript style: WA#1/2/3 = days 1,9,23) ---
obs = pd.read_excel(os.path.join(MUR, "OBSERVED_DATA.xlsx"), sheet_name="OBSERVED_N_LEACHED_DATA")
ot = np.asarray(obs["TIME_DAYS"].values, float); ov = np.asarray(obs["NITRATE_LEACHED"].values, float)
WA = [1, 9, 23]
gen = [np.interp(d, tg, cg) for d in WA]
ref = [np.interp(d, to, co) for d in WA]
obv = [ov[int(np.argmin(np.abs(ot - d)))] for d in WA]
rmse = lambda a, b: math.sqrt(np.mean((np.array(a) - np.array(b))**2))
print("\nCheckpoint RMSE (WA#1/2/3):  gen vs prev=%.3f | gen vs obs=%.3f | prev vs obs=%.3f kg N/ha"
      % (rmse(gen, ref), rmse(gen, obv), rmse(ref, obv)))
