"""Do the two independent reporting paths give the SAME total N transformations?
  PATH 1 (selected output): extent = -sum(dk_<reaction>)   [PHREEQC dk = reactant change]
  PATH 2 (pre/post RunCells, component deltas):
          mineralization = -d[ORGANIC_N]
          nitrification  = -d[ORGANIC_N] - d[AMMONIUM]
          denitrification= 2 * d[NITROUS_GAS]
Reported per variant in kg N/ha (mol x 280200) with the relative difference.
"""
import os, pandas as pd
VR = r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION\2DSOIL_PHREEQCRM_MODEL\POST_PROCESSING\ANALYSIS\_data\VARIANT_RUNS"
VARS = ["NR","ZK","ZK_ND","FK","FK_ND","CK"]
K = 280200.0   # mol N -> kg N/ha

def dk_sum(cum, cols, want):
    tot = 0.0
    for c in cols:
        u = c.upper()
        hit = ("MINERAL" in u) if want == "min" else \
              ("NITRIF" in u and "DENITRIF" not in u) if want == "nit" else \
              ("DENITRIF" in u)
        if hit:
            tot += float(cum[c])
    return -tot                     # extent = -(dk reactant change)

rows = []
for v in VARS:
    f = os.path.join(VR, v, "REACTION_TOTALS.txt")
    df = pd.read_csv(f); df.columns = [c.strip() for c in df.columns]
    cum = df.sum(numeric_only=True)
    dkc = [c for c in df.columns if c.lower().startswith("dk_")]
    g = lambda s: float(cum.get("d[%s]" % s, 0.0))
    dON, dNH4, dN2O = g("[ORGANIC_N]"), g("[AMMONIUM]"), g("[NITROUS_GAS]")
    paths = {
        "mineralization":  (dk_sum(cum, dkc, "min"), -dON),
        "nitrification":   (dk_sum(cum, dkc, "nit"), -dON - dNH4),
        "denitrification": (dk_sum(cum, dkc, "den"), 2.0 * dN2O),
    }
    for rxn, (a, b) in paths.items():
        rel = 0.0 if max(abs(a), abs(b)) < 1e-9 else abs(a - b) / max(abs(a), abs(b))
        rows.append(dict(variant=v, reaction=rxn,
                         selout_kgha=a*K, delta_kgha=b*K, rel_diff=rel))

res = pd.DataFrame(rows)
res.to_csv(os.path.join(VR, "_DK_VS_DELTA_CHECK.csv"), index=False)
print("="*86)
print("N transformations (kg N/ha):  selected-output dk_   vs   pre/post-RunCells deltas")
print("="*86)
print("%-6s | %-15s | %14s | %14s | %10s" % ("var","reaction","selected-out","component-delta","rel diff"))
print("-"*86)
for r in rows:
    print("%-6s | %-15s | %14.4f | %14.4f | %10.1e" %
          (r["variant"], r["reaction"], r["selout_kgha"], r["delta_kgha"], r["rel_diff"]))
print("-"*86)
print("max relative difference over all variants/reactions: %.2e" % res["rel_diff"].max())
print("Saved: _DK_VS_DELTA_CHECK.csv")
