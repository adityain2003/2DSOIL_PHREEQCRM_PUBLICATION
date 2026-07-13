"""Find the 3 checkpoint days that best reproduce the previous-code COMPARISON_OF_RESULTS
model columns, by sampling each previous-code variant's G05 cumsum at candidate days and
scoring total |model_sampled - table_value| across all 7 variants."""
import os, numpy as np, pandas as pd
ROOT = r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION"
MUR  = os.path.join(ROOT, "OLD_VERSIONS", "3_NITRATE_LEACHING", "2DSOIL-PHREEQCRM_MURPHY_SAND_LF")
cmp  = pd.read_excel(os.path.join(MUR,"COMPARISON_OF_RESULTS.xlsx"), sheet_name="RMSE").set_index("WA")
VARS = ["NR","ZK","ZK_ND","FK","FK_ND","CK"]

def prof(g05):
    df = pd.read_csv(g05); df.columns=[c.strip() for c in df.columns]
    t = np.asarray(df["Date_time"].values,float); t=t-t[0]
    return t, (-df["N_Leach"]).cumsum().values+0.0

prevs = {v: prof(os.path.join(MUR,v,"DELHI_MURPHY.G05")) for v in VARS}
tbl = {v:[float(cmp.loc[i,v]) for i in (1,2,3)] for v in VARS}

def score(d1,d2,d3):
    s=0.0; rows={}
    for v in VARS:
        t,c=prevs[v]; samp=[float(np.interp(d,t,c)) for d in (d1,d2,d3)]
        rows[v]=samp; s+=sum(abs(samp[i]-tbl[v][i]) for i in range(3))
    return s,rows

# coarse grid search for WA1, WA2; WA3 fixed at end (32)
best=None
for d1 in np.arange(7.0,10.01,0.05):
    for d2 in np.arange(20.0,24.01,0.05):
        s,_=score(d1,d2,32.0)
        if best is None or s<best[0]: best=(s,d1,d2)
s,d1,d2=best
print(f"best day-set: WA1={d1:.2f}  WA2={d2:.2f}  WA3=32.00   total|err|={s:.3f}")
_,rows=score(d1,d2,32.0)
print("\n  reproduce previous-code COMPARISON columns at these days:")
print("  var   | sampled (d1,d2,d3)            | table (WA1,WA2,WA3)")
for v in VARS:
    sm=rows[v]; tb=tbl[v]
    print(f"  {v:5s} | {sm[0]:6.2f} {sm[1]:6.2f} {sm[2]:6.2f}        | {tb[0]:6.2f} {tb[1]:6.2f} {tb[2]:6.2f}")
