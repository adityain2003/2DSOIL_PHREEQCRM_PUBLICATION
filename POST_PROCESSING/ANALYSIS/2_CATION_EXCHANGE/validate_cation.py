"""Validate the GENERIC engine's cation-exchange run vs the IPhreeqc reference,
using the SAME methodology as the original ERROR_CALCULATION_CATION_EXCHANGE.py
(interpolate IPhreeqc onto the simulated Y grid; mask <0.01 mmol/L; days 1-3).
Reports 5_GENERIC vs IPhreeqc side-by-side with the original CB2 vs IPhreeqc baseline.
"""
import os, math
import numpy as np, pandas as pd

ROOT = r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION"
XLSX = os.path.join(ROOT, "OLD_VERSIONS", "2_CATION_EXCHANGE_PROBLEM", "ANALYSIS_AND_FIGURES",
                    "RESULTS_100cm_1cm_ALL_NODES.xlsx")
FO   = os.path.join(ROOT, "2DSOIL_PHREEQCRM_MODEL", "RUN_INPUTS", "2_CATION_EXCHANGE",
                    "FERTIGATION_OUTPUT.txt")
GFW  = [40.08, 35.453, 22.9898, 39.102, 14.0067]          # Ca Cl Na K N  (mg/L -> mmol/L)
SPEC = [("Ca2+",0,"Ca2+ IPhreeqc","Ca2+ 2DSoil-PhreeqcRM"),
        ("Cl-", 1,"Cl- IPhreeqc", "Cl- 2DSoil-PhreeqcRM"),
        ("Na+", 2,"Na+ IPhreeqc", "Na+ 2DSoil-PhreeqcRM"),
        ("K+",  3,"K+ IPhreeqc",  "K+ 2DSoil-PhreeqcRM"),
        ("NO3-",4,"NO3- IPhreeqc","NO3- 2DSoil-PhreeqcRM")]
DAYS = {1:86400, 2:172800, 3:259200}
DATEDAY = {"01/02/2024":1, "01/03/2024":2, "01/04/2024":3}   # 01/01 = t0
MASK = 0.01

def metrics(sim, ref):
    sim = np.asarray(sim,float); ref = np.asarray(ref,float); err = sim-ref
    rmse = math.sqrt(np.mean(err**2)); mae = np.mean(np.abs(err)); mx = np.max(np.abs(err))
    if np.var(ref) > 0 and np.std(sim) > 0:
        r2 = np.corrcoef(sim,ref)[0,1]**2
        nse = 1 - np.sum(err**2)/np.sum((ref-ref.mean())**2)
    else:
        r2 = nse = float("nan")
    return len(sim), rmse, mae, mx, r2, nse

# ---- parse generic-engine output -> {day: {Y_abs: [mmol/L x5]}} ----
mine = {}
for ln in open(FO).read().splitlines()[1:]:
    p = [x.strip() for x in ln.split(",")]
    if len(p) < 11: continue
    try: date=p[2]; y=float(p[5]); v=[float(p[i]) for i in range(6,11)]
    except: continue
    if date not in DATEDAY: continue
    mine.setdefault(DATEDAY[date], {})[round(y-1.0,3)] = [v[i]/GFW[i] for i in range(5)]

df = pd.read_excel(XLSX, sheet_name="100cm_1_cm_ALL_NODES_IPHR_1cm")
print("="*86)
print("CATION EXCHANGE validation  -  vs IPhreeqc reference (mmol/L, days 1-3)")
print("="*86)
print("%-5s %-3s | %-26s | %-26s" % ("sp","day","5_GENERIC vs IPhreeqc","orig CB2 vs IPhreeqc"))
print("%-5s %-3s | %7s %7s %6s | %7s %7s %6s" % ("","","RMSE","MAE","R2","RMSE","MAE","R2"))
print("-"*86)
agg = {"my":[], "cb":[]}
for label, idx, refcol, cb2col in SPEC:
    for day, tsec in DAYS.items():
        rdf = df[df["time Iphreeqc"]==tsec][["Y Iphreeqc",refcol]].dropna().sort_values("Y Iphreeqc")
        ry, rv = rdf["Y Iphreeqc"].to_numpy(), rdf[refcol].to_numpy()
        cdf = df[df["Time ABS 2DSoil-PhreeqcRM"]==tsec][["Y_ABS 2DSoil_PhreeqcRM",cb2col]].dropna().sort_values("Y_ABS 2DSoil_PhreeqcRM")
        cy, cv = cdf["Y_ABS 2DSoil_PhreeqcRM"].to_numpy(), cdf[cb2col].to_numpy()
        md = mine.get(day,{}); my_y = np.array(sorted(md)); my_v = np.array([md[y][idx] for y in my_y])
        if len(ry) < 2 or len(my_y) < 2: continue
        ra = np.interp(my_y, ry, rv); m1 = (my_v>MASK)&(ra>MASK)
        rc = np.interp(cy, ry, rv);   m2 = (cv>MASK)&(rc>MASK)
        rm = metrics(my_v[m1], ra[m1]) if m1.sum()>=5 else None
        rb = metrics(cv[m2],   rc[m2]) if m2.sum()>=5 else None
        if rm: agg["my"].append(rm[1])
        if rb: agg["cb"].append(rb[1])
        f = lambda r: ("%7.4f %7.4f %6.3f"%(r[1],r[2],r[4])) if r else " "*22
        print("%-5s %-3d | %s | %s" % (label, day, f(rm), f(rb)))
    print()
print("-"*86)
print("mean RMSE (all species, days 1-3):   5_GENERIC=%.4f   CB2=%.4f   mmol/L"
      % (np.mean(agg["my"]), np.mean(agg["cb"])))
