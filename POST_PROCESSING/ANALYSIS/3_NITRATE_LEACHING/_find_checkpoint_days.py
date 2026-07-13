"""Reverse-engineer the manuscript's 3 checkpoint DAYS from the previous-code
COMPARISON_OF_RESULTS.xlsx model columns, by finding the simulation day at which
each previous-code variant's cumulative leached (G05 cumsum) equals the table value.
WA3 already confirmed = end-of-run. We solve for WA1, WA2 days per variant."""
import os, numpy as np, pandas as pd
ROOT = r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION"
MUR  = os.path.join(ROOT, "OLD_VERSIONS", "3_NITRATE_LEACHING", "2DSOIL-PHREEQCRM_MURPHY_SAND_LF")
CMP  = os.path.join(MUR, "COMPARISON_OF_RESULTS.xlsx")
VARS = ["NR","ZK","ZK_ND","FK","FK_ND","CK"]

cmp = pd.read_excel(CMP, sheet_name="RMSE")
cmp = cmp.set_index("WA")  # rows 1,2,3 + 'RMSE'

def prof(g05):
    df = pd.read_csv(g05); df.columns=[c.strip() for c in df.columns]
    t = np.asarray(df["Date_time"].values,float); t=t-t[0]
    return t, (-df["N_Leach"]).cumsum().values+0.0

def day_for(t, cum, target):
    # first day where cumulative crosses target (monotone non-decreasing)
    idx = np.searchsorted(cum, target)
    if idx<=0: return float(t[0])
    if idx>=len(cum): return float(t[-1])
    # linear interp in cum
    c0,c1=cum[idx-1],cum[idx]; t0,t1=t[idx-1],t[idx]
    if c1==c0: return float(t0)
    return float(t0 + (target-c0)*(t1-t0)/(c1-c0))

print("variant |  WA1_val  day | WA2_val  day | WA3_val  day(=end?) | prev_end")
for v in VARS:
    t,cum = prof(os.path.join(MUR,v,"DELHI_MURPHY.G05"))
    w1,w2,w3 = float(cmp.loc[1,v]), float(cmp.loc[2,v]), float(cmp.loc[3,v])
    d1,d2,d3 = day_for(t,cum,w1), day_for(t,cum,w2), day_for(t,cum,w3)
    print(f"{v:7s} | {w1:7.3f} {d1:5.2f} | {w2:7.3f} {d2:5.2f} | {w3:7.3f} {d3:6.2f}        | {cum[-1]:7.3f}")
print("\nOBSERVED column in sheet:", [float(cmp.loc[i,'OBSERVED']) for i in (1,2,3)])
