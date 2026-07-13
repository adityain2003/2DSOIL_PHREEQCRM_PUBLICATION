"""Consolidated, consistently-sampled computation of every metric reported, for all 7
variants and BOTH engines (generic, previous code) sampled at identical days. Prints
authoritative blocks used to build RESULTS.md."""
import os, math, numpy as np, pandas as pd
ROOT = r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION"
GENR = os.path.join(ROOT, "2DSOIL_PHREEQCRM_MODEL", "POST_PROCESSING", "ANALYSIS", "_data", "VARIANT_RUNS")
MUR  = os.path.join(ROOT, "OLD_VERSIONS", "3_NITRATE_LEACHING", "2DSOIL-PHREEQCRM_MURPHY_SAND_LF")
VARS = ["NR","ZK","ZK_ND","FK","FK_ND","CK"]
OBS3 = [20.6, 25.7, 35.7]; OBS_TOT = 35.7
D_CYC = [8.80, 22.60, 32.00]; D_FIX = [2.0, 10.0, 24.0]

def prof(g):
    df = pd.read_csv(g); df.columns=[c.strip() for c in df.columns]
    t = np.asarray(df["Date_time"].values,float); t=t-t[0]
    return t, (-df["N_Leach"]).cumsum().values+0.0
def samp(t,c,days): return [float(np.interp(d,t,c)) for d in days]
def rmse_manu(m): return math.sqrt(sum((a-b)**2 for a,b in zip(m,OBS3)))/3
def rmse_std3(m): return math.sqrt(np.mean([(a-b)**2 for a,b in zip(m,OBS3)]))

obs = pd.read_excel(os.path.join(MUR,"OBSERVED_DATA.xlsx"), sheet_name="OBSERVED_N_LEACHED_DATA")
ot = np.asarray(obs["TIME_DAYS"].values,float); ov = np.asarray(obs["NITRATE_LEACHED"].values,float)

def block(title): print("\n##### "+title)

G = {v: prof(os.path.join(GENR,v,"DELHI_MURPHY.G05")) for v in VARS}
P = {v: prof(os.path.join(MUR, v,"DELHI_MURPHY.G05")) for v in VARS}

block("TOTALS + checkpoints (generic)")
for v in VARS:
    t,c=G[v]; print(v, "d1=%.3f d9=%.3f d23=%.3f END=%.3f | prevEND=%.3f diff=%+.3f"
        % (np.interp(1,t,c),np.interp(9,t,c),np.interp(23,t,c),c[-1],P[v][1][-1],c[-1]-P[v][1][-1]))

block("RMSE @ end-of-cycle [8.80,22.60,32.00] vs OBS3 (manu | std) gen vs prev")
for v in VARS:
    g=samp(*G[v],D_CYC); p=samp(*P[v],D_CYC)
    print(v,"gen[%.2f,%.2f,%.2f] manu=%.3f std=%.3f | prev manu=%.3f std=%.3f"
        %(g[0],g[1],g[2],rmse_manu(g),rmse_std3(g),rmse_manu(p),rmse_std3(p)))

block("RMSE @ [2,10,24] vs OBS3 (manu) gen vs prev")
for v in VARS:
    g=samp(*G[v],D_FIX); p=samp(*P[v],D_FIX)
    print(v,"gen[%.2f,%.2f,%.2f] manu=%.3f | prev[%.2f,%.2f,%.2f] manu=%.3f"
        %(g[0],g[1],g[2],rmse_manu(g),p[0],p[1],p[2],rmse_manu(p)))

block("TOTAL vs observed total 35.7 (gen |err|, prev |err|)")
for v in VARS:
    gt,pt=G[v][1][-1],P[v][1][-1]
    print(v,"gen=%.2f |err|=%.2f (%.1f%%) | prev=%.2f |err|=%.2f"%(gt,abs(gt-OBS_TOT),100*(gt-OBS_TOT)/OBS_TOT,pt,abs(pt-OBS_TOT)))

block("RMSE vs FULL observed series N=%d (gen RMSE/MAE/MaxAE/bias | prev RMSE/bias)"%len(ot))
for v in VARS:
    t,c=G[v]; m=np.interp(ot,t,c); e=m-ov
    tp,cp=P[v]; mp=np.interp(ot,tp,cp); ep=mp-ov
    print(v,"genRMSE=%.3f MAE=%.3f MaxAE=%.3f bias=%+.3f | prevRMSE=%.3f bias=%+.3f"
        %(math.sqrt(np.mean(e**2)),np.mean(abs(e)),np.max(abs(e)),np.mean(e),
          math.sqrt(np.mean(ep**2)),np.mean(ep)))
