"""RMSE of each variant's cumulative NO3-N leached vs the FULL observed series
(OBSERVED_DATA.xlsx, sheet OBSERVED_N_LEACHED_DATA) -- model interpolated onto every
observed time point. Standard RMSE = sqrt(mean(err^2)) over all N observed points."""
import os, math, numpy as np, pandas as pd
ROOT = r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION"
GENR = os.path.join(ROOT, "2DSOIL_PHREEQCRM_MODEL", "POST_PROCESSING", "ANALYSIS", "_data", "VARIANT_RUNS")
MUR  = os.path.join(ROOT, "OLD_VERSIONS", "3_NITRATE_LEACHING", "2DSOIL-PHREEQCRM_MURPHY_SAND_LF")
VARS  = ["NR","ZK","ZK_ND","FK","FK_ND","CK"]
DENIT = ["ZK","FK","CK"]

obs = pd.read_excel(os.path.join(MUR,"OBSERVED_DATA.xlsx"), sheet_name="OBSERVED_N_LEACHED_DATA")
ot  = np.asarray(obs["TIME_DAYS"].values, float)
ov  = np.asarray(obs["NITRATE_LEACHED"].values, float)
N   = len(ot)

def prof(g):
    df = pd.read_csv(g); df.columns=[c.strip() for c in df.columns]
    t = np.asarray(df["Date_time"].values,float); t=t-t[0]
    return t, (-df["N_Leach"]).cumsum().values+0.0

def metrics(g):
    t,c = prof(g); m = np.interp(ot, t, c); e = m - ov
    return dict(rmse=math.sqrt(np.mean(e**2)), mae=np.mean(np.abs(e)),
                maxae=np.max(np.abs(e)), bias=np.mean(e), end=float(c[-1]))

print("="*92)
print("RMSE vs FULL observed series  (N=%d points, days %.2f..%.2f)   sqrt(mean(err^2))" % (N, ot[0], ot[-1]))
print("="*92)
print("%-6s | %8s %7s %7s %7s | %8s %7s %7s %7s" %
      ("var","gRMSE","gMAE","gMaxAE","gBias","pRMSE","pMAE","pMaxAE","pBias"))
print("-"*92)
rows=[]
for v in VARS:
    gm = metrics(os.path.join(GENR,v,"DELHI_MURPHY.G05"))
    pm = metrics(os.path.join(MUR, v,"DELHI_MURPHY.G05"))
    rows.append((v,gm,pm))
    print("%-6s | %8.3f %7.3f %7.3f %+7.3f | %8.3f %7.3f %7.3f %+7.3f" %
          (v, gm["rmse"],gm["mae"],gm["maxae"],gm["bias"],
              pm["rmse"],pm["mae"],pm["maxae"],pm["bias"]))
print("-"*92)
print("DENIT-ACTIVE only, ranked by generic RMSE vs full observed series:")
for v,gm,pm in sorted([r for r in rows if r[0] in DENIT], key=lambda r:r[1]["rmse"]):
    print("   %-5s gen RMSE=%6.3f   prev RMSE=%6.3f" % (v, gm["rmse"], pm["rmse"]))
print("\nALL 7, ranked by generic RMSE:")
for v,gm,pm in sorted(rows, key=lambda r:r[1]["rmse"]):
    print("   %-6s gen RMSE=%6.3f" % (v, gm["rmse"]))
pd.DataFrame([(v,gm["rmse"],gm["mae"],gm["maxae"],gm["bias"],pm["rmse"],pm["mae"],pm["maxae"],pm["bias"])
             for v,gm,pm in rows],
    columns=["variant","gen_RMSE","gen_MAE","gen_MaxAE","gen_bias","prev_RMSE","prev_MAE","prev_MaxAE","prev_bias"]
).to_csv(os.path.join(GENR,"_RMSE_VS_DAILY_OBSERVED.csv"), index=False)
print("\nSaved: _RMSE_VS_DAILY_OBSERVED.csv")
