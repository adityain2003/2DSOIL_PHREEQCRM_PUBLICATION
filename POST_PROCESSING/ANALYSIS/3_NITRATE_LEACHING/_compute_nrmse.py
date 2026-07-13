"""NRMSE for the generic engine, repo convention: NRMSE_% = RMSE / (observed range) * 100.
Mode 2 (3 checkpoints): standard RMSE, range = 35.7-20.6 = 15.1.
Mode 3 (full series): RMSE over N=37, range = max(obs)-min(obs)."""
import os, math, numpy as np, pandas as pd
ROOT = r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION"
GENR = os.path.join(ROOT, "2DSOIL_PHREEQCRM_MODEL", "POST_PROCESSING", "ANALYSIS", "_data", "VARIANT_RUNS")
MUR  = os.path.join(ROOT, "OLD_VERSIONS", "3_NITRATE_LEACHING", "2DSOIL-PHREEQCRM_MURPHY_SAND_LF")
VARS = ["NR","ZK","ZK_ND","FK","FK_ND","CK"]
OBS3 = [20.6, 25.7, 35.7]; D_CYC=[8.80,22.60,32.00]; D_FIX=[2.0,10.0,24.0]
RANGE3 = max(OBS3) - min(OBS3)   # 15.1

obs = pd.read_excel(os.path.join(MUR,"OBSERVED_DATA.xlsx"), sheet_name="OBSERVED_N_LEACHED_DATA")
ot = np.asarray(obs["TIME_DAYS"].values,float); ov = np.asarray(obs["NITRATE_LEACHED"].values,float)
RANGE_D = float(ov.max()-ov.min()); MEAN_D = float(ov.mean())

def prof(g):
    df=pd.read_csv(g); df.columns=[c.strip() for c in df.columns]
    t=np.asarray(df["Date_time"].values,float); t=t-t[0]
    return t,(-df["N_Leach"]).cumsum().values+0.0
def samp(t,c,days): return [float(np.interp(d,t,c)) for d in days]
def std_rmse(model,obs): return math.sqrt(np.mean([(a-b)**2 for a,b in zip(model,obs)]))

print("Observed daily series: range=%.3f  mean=%.3f  (3-checkpoint range=%.1f)" % (RANGE_D,MEAN_D,RANGE3))
print("\n%-6s | %-26s | %-26s | %-22s" % ("var","Mode2 end-cycle 8.8/22.6/32","Mode2 days 2/10/24","Mode3 daily (N=37)"))
print("%-6s | %9s %9s | %9s %9s | %9s %9s" % ("","stdRMSE","NRMSE%","stdRMSE","NRMSE%","RMSE","NRMSE%"))
print("-"*94)
rows=[]
for v in VARS:
    t,c=prof(os.path.join(GENR,v,"DELHI_MURPHY.G05"))
    r_cyc=std_rmse(samp(t,c,D_CYC),OBS3); r_fix=std_rmse(samp(t,c,D_FIX),OBS3)
    m=np.interp(ot,t,c); r_day=math.sqrt(np.mean((m-ov)**2))
    n_cyc=r_cyc/RANGE3*100; n_fix=r_fix/RANGE3*100; n_day=r_day/RANGE_D*100
    rows.append((v,r_cyc,n_cyc,r_fix,n_fix,r_day,n_day))
    print("%-6s | %9.3f %8.1f%% | %9.3f %8.1f%% | %9.3f %8.1f%%" % (v,r_cyc,n_cyc,r_fix,n_fix,r_day,n_day))
pd.DataFrame(rows,columns=["variant","m2cyc_RMSE","m2cyc_NRMSE%","m2fix_RMSE","m2fix_NRMSE%","daily_RMSE","daily_NRMSE%"]
    ).to_csv(os.path.join(GENR,"_NRMSE.csv"),index=False)
print("\nSaved: _NRMSE.csv   (NRMSE_% = RMSE / observed range * 100, repo convention)")
