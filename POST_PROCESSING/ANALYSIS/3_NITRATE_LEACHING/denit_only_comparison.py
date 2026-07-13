"""Comparison restricted to the denitrification-ACTIVE variants (ZK, FK, CK);
the no-denitrification cases (NR, ZK_ND, FK_ND) are removed.
Three metrics, generic engine and previous code, vs observed [20.6, 25.7, 35.7] / total 35.7:
  RMSE @ end-of-cycle days [8.80, 22.60, 32.00]   (manuscript sqrt(Sum err^2)/3)
  RMSE @ days [2, 10, 24]
  |err| on TOTAL leached (end of run) vs observed total 35.7
"""
import os, math, numpy as np, pandas as pd
ROOT = r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION"
GENR = os.path.join(ROOT, "2DSOIL_PHREEQCRM_MODEL", "POST_PROCESSING", "ANALYSIS", "_data", "VARIANT_RUNS")
MUR  = os.path.join(ROOT, "OLD_VERSIONS", "3_NITRATE_LEACHING", "2DSOIL-PHREEQCRM_MURPHY_SAND_LF")
DENIT = ["ZK","FK","CK"]
OBS   = [20.6, 25.7, 35.7]; OBS_TOT = 35.7
D_CYC = [8.80, 22.60, 32.00]; D_FIX = [2.0, 10.0, 24.0]

def prof(g):
    df = pd.read_csv(g); df.columns=[c.strip() for c in df.columns]
    t = np.asarray(df["Date_time"].values,float); t=t-t[0]
    return t, (-df["N_Leach"]).cumsum().values+0.0
def rmse_manu(model): return math.sqrt(sum((m-o)**2 for m,o in zip(model,OBS)))/3
def samp(g,days):
    t,c=prof(g); return [float(np.interp(d,t,c)) for d in days]

print("="*86)
print("DENITRIFICATION-ACTIVE variants only (ZK, FK, CK)  --  no-denit cases removed")
print("="*86)
print("%-5s | %-21s | %-21s | %-15s" % ("var","RMSE @ days 8.8/22.6/32","RMSE @ days 2/10/24","|err| TOTAL"))
print("%-5s | %9s %9s | %9s %9s | %7s %7s" % ("","generic","prev","generic","prev","generic","prev"))
print("-"*86)
rows=[]
for v in DENIT:
    g=os.path.join(GENR,v,"DELHI_MURPHY.G05"); p=os.path.join(MUR,v,"DELHI_MURPHY.G05")
    r_g_cyc, r_p_cyc = rmse_manu(samp(g,D_CYC)), rmse_manu(samp(p,D_CYC))
    r_g_fix, r_p_fix = rmse_manu(samp(g,D_FIX)), rmse_manu(samp(p,D_FIX))
    gt, pt = prof(g)[1][-1], prof(p)[1][-1]
    rows.append((v,r_g_cyc,r_p_cyc,r_g_fix,r_p_fix,abs(gt-OBS_TOT),abs(pt-OBS_TOT)))
    print("%-5s | %9.3f %9.3f | %9.3f %9.3f | %7.2f %7.2f" %
          (v,r_g_cyc,r_p_cyc,r_g_fix,r_p_fix,abs(gt-OBS_TOT),abs(pt-OBS_TOT)))
print("-"*86)
for label,idx in [("end-of-cycle days",1),("days 2/10/24",3),("TOTAL",5)]:
    best=min(rows,key=lambda r:r[idx])
    print("  best generic by %-18s: %s (%.3f)" % (label,best[0],best[idx]))
