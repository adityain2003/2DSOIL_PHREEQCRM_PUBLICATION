"""RMSE of the GENERIC engine's cumulative NO3-N leached vs observed, at the manuscript's
3 drainage-cycle checkpoints (days 8.80 / 22.60 / 32.00 -- reverse-engineered to reproduce
the previous-code COMPARISON_OF_RESULTS columns to ~0.04 kg/ha).

Observed checkpoint values (user-specified) = [20.6, 25.7, 35.7]
(sheet provenance: COMPARISON_OF_RESULTS 'OBSERVED' col = [20.59, 25.7, 35.74]).

Two RMSE definitions reported:
  manuscript : sqrt(sum(err^2)) / 3        (the sheet's non-standard definition; reproduces its RMSE row)
  standard   : sqrt(mean(err^2)) = sqrt(sum/3)
"""
import os, math, numpy as np, pandas as pd
ROOT = r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION"
GENR = os.path.join(ROOT, "2DSOIL_PHREEQCRM_MODEL", "POST_PROCESSING", "ANALYSIS", "_data", "VARIANT_RUNS")
MUR  = os.path.join(ROOT, "OLD_VERSIONS", "3_NITRATE_LEACHING", "2DSOIL-PHREEQCRM_MURPHY_SAND_LF")
VARS = ["NR","ZK","ZK_ND","FK","FK_ND","CK"]
DAYS = [2.0, 10.0, 24.0]   # end of day 2 / 10 / 24 (one day after each water application drains)
OBS  = [20.6, 25.7, 35.7]

def prof(g05):
    df = pd.read_csv(g05); df.columns=[c.strip() for c in df.columns]
    t = np.asarray(df["Date_time"].values,float); t=t-t[0]
    return t, (-df["N_Leach"]).cumsum().values+0.0

def rmse_manu(model): return math.sqrt(sum((m-o)**2 for m,o in zip(model,OBS)))/3
def rmse_std(model):  return math.sqrt(np.mean([(m-o)**2 for m,o in zip(model,OBS)]))

rows=[]
for v in VARS:
    tg,cg = prof(os.path.join(GENR,v,"DELHI_MURPHY.G05"))
    gen = [float(np.interp(d,tg,cg)) for d in DAYS]
    tp,cp = prof(os.path.join(MUR,v,"DELHI_MURPHY.G05"))     # previous code, SAME days
    prev = [float(np.interp(d,tp,cp)) for d in DAYS]
    rows.append({"variant":v,
        "gen_d2":gen[0],"gen_d10":gen[1],"gen_d24":gen[2],"gen_RMSE_manu":rmse_manu(gen),
        "prev_d2":prev[0],"prev_d10":prev[1],"prev_d24":prev[2],"prev_RMSE_manu":rmse_manu(prev),
        "gen_RMSE_std":rmse_std(gen),"prev_RMSE_std":rmse_std(prev)})
res=pd.DataFrame(rows)
res.to_csv(os.path.join(GENR,"_RMSE_VS_OBSERVED.csv"), index=False)

print("="*100)
print("RMSE vs OBSERVED [%.1f, %.1f, %.1f] kg N/ha  @ end of day [%g, %g, %g]"
      % (OBS[0],OBS[1],OBS[2],DAYS[0],DAYS[1],DAYS[2]))
print("="*100)
print(f"{'var':6s} | {'gen_d2':>6s} {'gen_d10':>7s} {'gen_d24':>7s} {'RMSE':>7s} | "
      f"{'prv_d2':>6s} {'prv_d10':>7s} {'prv_d24':>7s} {'RMSE':>7s}   (RMSE = manuscript sqrt(Sumerr^2)/3)")
print("-"*100)
for r in rows:
    print(f"{r['variant']:6s} | {r['gen_d2']:6.2f} {r['gen_d10']:7.2f} {r['gen_d24']:7.2f} {r['gen_RMSE_manu']:7.3f} | "
          f"{r['prev_d2']:6.2f} {r['prev_d10']:7.2f} {r['prev_d24']:7.2f} {r['prev_RMSE_manu']:7.3f}")
print("\nStandard RMSE = manuscript x sqrt(3).  Both engines sampled at the SAME days for fair comparison.")
print("Saved: _RMSE_VS_OBSERVED.csv")
