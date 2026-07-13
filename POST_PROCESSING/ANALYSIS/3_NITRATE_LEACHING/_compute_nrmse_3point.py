"""NRMSE based on the three critical values at the three critical times.
obs3 = [20.6, 25.7, 35.7]; standard RMSE = sqrt(mean of 3 squared errors).
Two normalizations: by observed range (max-min = 15.1) and by observed mean (27.333)."""
import os, math, numpy as np, pandas as pd
ROOT = r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION"
GENR = os.path.join(ROOT, "2DSOIL_PHREEQCRM_MODEL", "POST_PROCESSING", "ANALYSIS", "_data", "VARIANT_RUNS")
VARS = ["NR","ZK","ZK_ND","FK","FK_ND","CK"]
OBS3 = [20.6, 25.7, 35.7]
RNG = max(OBS3)-min(OBS3); MEAN = sum(OBS3)/3.0
DAYSETS = {"one day before 0/8/22":[0.0,8.0,22.0], "one day after 2/10/24":[2.0,10.0,24.0],
           "end-of-cycle 8.80/22.60/32.00":[8.80,22.60,32.00]}

def prof(g):
    df=pd.read_csv(g); df.columns=[c.strip() for c in df.columns]
    t=np.asarray(df["Date_time"].values,float); t=t-t[0]
    return t,(-df["N_Leach"]).cumsum().values+0.0

print("3 critical values =", OBS3, " range=%.1f  mean=%.3f" % (RNG, MEAN))
for label, days in DAYSETS.items():
    print("\n=== critical times: %s ===" % label)
    print("%-6s | %-22s | %8s | %10s | %10s" % ("var","sim(t1/t2/t3)","RMSE","NRMSE%range","NRMSE%mean"))
    print("-"*74)
    rows=[]
    for v in VARS:
        t,c=prof(os.path.join(GENR,v,"DELHI_MURPHY.G05"))
        s=[float(np.interp(d,t,c)) for d in days]
        rmse=math.sqrt(np.mean([(a-b)**2 for a,b in zip(s,OBS3)]))
        nr_rng=rmse/RNG*100; nr_mean=rmse/MEAN*100
        rows.append((v,s,rmse,nr_rng,nr_mean))
        print("%-6s | %5.2f / %5.2f / %5.2f | %8.3f | %9.1f%% | %9.1f%%"
              % (v,s[0],s[1],s[2],rmse,nr_rng,nr_mean))
    if "one day after" in label:
        pd.DataFrame([(v,s[0],s[1],s[2],r,a,b) for v,s,r,a,b in rows],
            columns=["variant","sim_t1","sim_t2","sim_t3","RMSE_3pt","NRMSE_range_%","NRMSE_mean_%"]
        ).to_csv(os.path.join(GENR,"_NRMSE_3POINT.csv"), index=False)
print("\nSaved: _NRMSE_3POINT.csv (one-day-after set, mean-normalized in NRMSE_mean_%)")
