"""Validate 2DSOIL_PHREEQCRM_MODEL CASE_1 (conservative) vs Ogata-Banks analytical,
   and cross-check vs the original CB1 simulated profile in the benchmark xlsx."""
import math, os

# --- Ogata-Banks params (from ANALYTICAL_AT_SIMULATED_DEPTHS_CASE_1.py) ---
U_DARCY=25.648; THETA=0.2817; U_PORE=U_DARCY/THETA
ALPHA=75.0; D=ALPHA*U_PORE; C0=1.0; L=750.0; SHIFT=749.99

def ogata(y,t):
    if t==0: return 0.0
    ye = SHIFT if abs(y-L)<1e-9 else y
    xl = L-ye
    if xl<=0: return float('nan')
    eps=U_PORE*t/xl; eta=D/(U_PORE*xl); s=math.sqrt(eps*eta)
    return 0.5*C0*(math.erfc((1-eps)/(2*s))+math.exp(1.0/eta)*math.erfc((1+eps)/(2*s)))

# --- parse 5_ FERTIGATION_OUTPUT.txt: date -> [(y, conc), ...] (x=0 column) ---
FO=r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION\2DSOIL_PHREEQCRM_MODEL\RUN_INPUTS\1_BENCHMARK\FERTIGATION_OUTPUT.txt"
prof={}
with open(FO) as f:
    next(f)
    for ln in f:
        p=[x.strip() for x in ln.split(',')]
        if len(p)<7 or not p[1] or not p[1][0].isdigit(): continue
        prof.setdefault(p[2],[]).append((float(p[5]),float(p[6])))

C0_BC=1000.0
DAYMAP={1:'01/07/2024',2:'01/08/2024',3:'01/09/2024'}   # injection starts 01/06 -> DAY k = 01/(6+k)
print("="*64)
print("5_GENERIC CASE_1 (conservative)  vs  Ogata-Banks analytical")
print("U_pore=%.3f cm/day  D=%.1f cm2/day  alpha=%.0f cm"%(U_PORE,D,ALPHA))
print("="*64)
for t,date in DAYMAP.items():
    if date not in prof: print("DAY %d (%s): MISSING"%(t,date)); continue
    rows=sorted(prof[date],key=lambda r:-r[0])
    samp=[(y,c/C0_BC,ogata(y,t)) for y,c in rows if not math.isnan(ogata(y,t))]
    se=[(s-a)**2 for _,s,a in samp]; ae=[abs(s-a) for _,s,a in samp]
    rmse=math.sqrt(sum(se)/len(se)); mae=sum(ae)/len(ae); mx=max(ae)
    print("\nDAY %d (%s): N=%d  RMSE=%.4f  MAE=%.4f  MaxAbsErr=%.4f  (C/C0)"%(t,date,len(samp),rmse,mae,mx))
    step=max(1,len(samp)//9)
    print("   %8s %9s %9s %8s"%("y(cm)","sim","analytic","diff"))
    for y,s,a in samp[::step]:
        print("   %8.1f %9.4f %9.4f %+8.4f"%(y,s,a,s-a))

# --- optional cross-check vs original CB1 simulated profile in the xlsx ---
try:
    import pandas as pd
    xl=r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION\OLD_VERSIONS\1_BENCHMARKING_STUDY\ANALYSIS_AND_FIGURES\RESULTS_BENCHMARKING_ANALYTICAL_SOLUTION_750CM.xlsx"
    df=pd.read_excel(xl,sheet_name="CASE_1")
    cols=list(df.columns)
    print("\n"+"="*64)
    print("CB1 reference xlsx CASE_1 columns:", cols)
    print("="*64)
    for t,date in DAYMAP.items():
        sub=df[df["DAY"]==t].sort_values("Y")
        if sub.empty: print("xlsx DAY %d: none"%t); continue
        ys=sub["Y"].to_numpy(); simc=sub["CONC_RATIO_SIMULATED"].to_numpy()
        # build 5_ lookup by nearest Y
        m={round(y,1):c/C0_BC for y,c in prof.get(date,[])}
        diffs=[]
        for y,cb1 in zip(ys,simc):
            g=m.get(round(y,1))
            if g is not None: diffs.append(abs(g-cb1))
        if diffs:
            print("DAY %d: |5_generic - CB1_original| over %d matched depths: MAE=%.4f  Max=%.4f"
                  %(t,len(diffs),sum(diffs)/len(diffs),max(diffs)))
except Exception as e:
    print("\n(xlsx cross-check skipped: %s)"%e)
