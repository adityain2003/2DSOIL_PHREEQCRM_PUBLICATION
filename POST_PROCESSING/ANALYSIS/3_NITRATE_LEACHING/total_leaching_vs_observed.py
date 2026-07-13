"""Total NO3-N leached (end-of-run cumulative) per variant vs the observed total.
A single observed value -> 'RMSE' reduces to the absolute deviation."""
import os, numpy as np, pandas as pd
ROOT = r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION"
GENR = os.path.join(ROOT, "2DSOIL_PHREEQCRM_MODEL", "POST_PROCESSING", "ANALYSIS", "_data", "VARIANT_RUNS")
MUR  = os.path.join(ROOT, "OLD_VERSIONS", "3_NITRATE_LEACHING", "2DSOIL-PHREEQCRM_MURPHY_SAND_LF")
VARS = ["NR","ZK","ZK_ND","FK","FK_ND","CK"]
OBS  = 35.7   # observed total (user); OBSERVED_DATA.xlsx final = 35.74

def total(g):
    df = pd.read_csv(g); df.columns = [c.strip() for c in df.columns]
    return float((-df["N_Leach"]).cumsum().values[-1])

print("=" * 80)
print("TOTAL NO3-N leached (end of run, kg N/ha)   vs OBSERVED total = %.1f" % OBS)
print("=" * 80)
print("%-6s | %9s %8s %7s %7s | %10s %8s %7s" %
      ("var","gen_tot","err","|err|","%err","prev_tot","err","|err|"))
print("-" * 80)
rows=[]
for v in VARS:
    g = total(os.path.join(GENR, v, "DELHI_MURPHY.G05"))
    p = total(os.path.join(MUR,  v, "DELHI_MURPHY.G05"))
    rows.append((v,g,p))
    print("%-6s | %9.2f %+8.2f %7.2f %+6.1f%% | %10.2f %+8.2f %7.2f" %
          (v, g, g-OBS, abs(g-OBS), 100*(g-OBS)/OBS, p, p-OBS, abs(p-OBS)))
print("-" * 80)
ranked = sorted(rows, key=lambda r: abs(r[1]-OBS))
print("generic ranked by closeness of TOTAL to observed:")
for v,g,p in ranked:
    print("   %-6s |err|=%5.2f" % (v, abs(g-OBS)))
pd.DataFrame(rows, columns=["variant","gen_total","prev_total"]).assign(
    observed=OBS, gen_abs_err=lambda d:(d.gen_total-OBS).abs(),
    prev_abs_err=lambda d:(d.prev_total-OBS).abs()
).to_csv(os.path.join(GENR,"_TOTAL_LEACHING_VS_OBSERVED.csv"), index=False)
print("\nSaved: _TOTAL_LEACHING_VS_OBSERVED.csv")
