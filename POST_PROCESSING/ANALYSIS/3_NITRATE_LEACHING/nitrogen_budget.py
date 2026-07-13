"""Nitrogen transformation budget for all variants, from the component-delta block
of REACTION_TOTALS.txt (works whether or not dk_ columns are present).

Cascade (from the .pqi -formula):
  ORGANIC_N --min--> AMMONIUM --nit--> NITRATE --denit--> 0.5 NITROUS_GAS
Each transfers exactly 1 N atom per mole of reaction extent, so (moles):
  mineralization xi_min   = -d[ORGANIC_N]
  nitrification  xi_nit   = -d[ORGANIC_N] - d[AMMONIUM]   (= xi_min - d[AMMONIUM])
  denitrification xi_den  =  2 * d[NITROUS_GAS]
Self-consistency: d[NITRATE] should equal xi_nit - xi_den, and the N-weighted sum
  d[ORGANIC_N] + d[AMMONIUM] + d[NITRATE] + 2 d[NITROUS_GAS] = 0 (N conserved by reaction).

kg N/ha = xi[mol] * 14.01[g/mol] / 1000[g/kg] / footprint_ha,
  footprint = x_width * SLAB_WIDTH (here 5 cm x 1 cm = 5 cm^2 = 5e-8 ha).
Leached NO3-N (kg/ha) is read from DELHI_MURPHY.G05 (publication cumsum) for context.
"""
import os, numpy as np, pandas as pd

ROOT = r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION"
VR   = os.path.join(ROOT, "2DSOIL_PHREEQCRM_MODEL", "POST_PROCESSING", "ANALYSIS", "_data", "VARIANT_RUNS")
VARS = ["NR", "ZK", "ZK_ND", "FK", "FK_ND", "CK"]
GFW_N = 14.01            # g N / mol
SLAB  = 1.0              # cm (SLAB_WIDTH)

# footprint from the grid x-extent (read once from FK species output) x SLAB
sp = pd.read_csv(os.path.join(VR, "FK", "PHREEQC_SPECIES_OUT.txt"))
sp.columns = [c.strip() for c in sp.columns]
d0 = sp[sp["TIME"] == sp["TIME"].iloc[0]]
x_width = float(d0["X"].max() - d0["X"].min())        # 5 cm
FOOT_CM2 = x_width * SLAB                              # 5 cm^2
FOOT_HA  = FOOT_CM2 * 1e-8                             # cm^2 -> ha
K = GFW_N / 1000.0 / FOOT_HA                           # mol -> kg N/ha
print(f"footprint = {x_width:.2f} cm x {SLAB:.2f} cm = {FOOT_CM2:.2f} cm^2 ;  kg N/ha = mol * {K:.1f}\n")


def cum_leached_kgha(g05):
    df = pd.read_csv(g05); df.columns = [c.strip() for c in df.columns]
    return float((-df["N_Leach"]).cumsum().values[-1])


rows = []
for v in VARS:
    f = os.path.join(VR, v, "REACTION_TOTALS.txt")
    if not os.path.exists(f):
        continue
    df = pd.read_csv(f); df.columns = [c.strip() for c in df.columns]
    cum = df.sum(numeric_only=True)
    g = lambda name: float(cum.get(f"d[{name}]", 0.0))
    dON, dNH4, dNO3, dN2O = g("[ORGANIC_N]"), g("[AMMONIUM]"), g("[NITRATE]"), g("[NITROUS_GAS]")

    xi_min = -dON
    xi_nit = -dON - dNH4
    xi_den = 2.0 * dN2O
    n_resid = dON + dNH4 + dNO3 + 2.0 * dN2O          # should be ~0
    no3_check = (xi_nit - xi_den) - dNO3              # should be ~0
    leached = cum_leached_kgha(os.path.join(VR, v, "DELHI_MURPHY.G05"))

    rows.append(dict(variant=v,
                     min_mol=xi_min, nit_mol=xi_nit, den_mol=xi_den,
                     min_kgha=xi_min*K, nit_kgha=xi_nit*K, den_kgha=xi_den*K,
                     leached_kgha=leached, Nresid_mol=n_resid))

res = pd.DataFrame(rows)
res.to_csv(os.path.join(VR, "_NITROGEN_BUDGET.csv"), index=False)

print("="*100)
print("NITROGEN TRANSFORMATION BUDGET (cumulative, end of run)   [denit = NO3-N consumed]")
print("="*100)
print("%-6s | %22s | %26s | %9s | %10s" %
      ("var", "moles (min/nit/den)", "kg N/ha (min/nit/den)", "leached", "N_resid"))
print("-"*100)
for r in rows:
    print("%-6s | %6.3e %6.3e %6.3e | %8.2f %8.2f %8.2f | %9.2f | %9.1e" %
          (r["variant"], r["min_mol"], r["nit_mol"], r["den_mol"],
           r["min_kgha"], r["nit_kgha"], r["den_kgha"],
           r["leached_kgha"], r["Nresid_mol"]))
print("-"*100)
print("kg N/ha columns are min / nit / den ; leached = cumulative NO3-N leached (G05).")
print("N_resid = N-weighted sum of component deltas (should be ~0 => reactions conserve N).")
print("\nSaved: _NITROGEN_BUDGET.csv")
