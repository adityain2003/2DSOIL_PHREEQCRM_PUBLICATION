"""Residual (end-of-run) nitrogen left in the column, and the full N budget.

Absolute pools are computed from the node concentrations in PHREEQC_SPECIES_OUT.txt,
weighted by reconstructed node control-volume areas:
    pool_moles(component) = sum_i  c_i * (nodeArea_i * SLAB * 0.001 L)
nodeArea_i = wx(x_i) * wy(y_i), control volumes from the structured grid (sum -> 5x80 cm^2).
kg N/ha = pool_moles * N_atoms * 14.01/1000 / footprint_ha, footprint = 5 cm * 1 cm = 5e-8 ha.

Residual soil N   = ORGANIC_N + AMMONIUM + NITRATE remaining in the column (end).
N2O-N (gaseous)   = 2 * NITROUS_GAS  (the denitrified N; starts at 0, only accumulates).
Validation        : N2O-N(species, end) should match denitrified from the reaction report.
Closure (if t0 record present): Initial = Residual + N2O-N + Leached.
"""
import os, numpy as np, pandas as pd

ROOT = r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION"
VR   = os.path.join(ROOT, "2DSOIL_PHREEQCRM_MODEL", "POST_PROCESSING", "ANALYSIS", "_data", "VARIANT_RUNS")
VARS = ["NR", "ZK", "ZK_ND", "FK", "FK_ND", "CK"]
SLAB = 1.0
GFW_N = 14.01
NATOM = {"[ORGANIC_N]": 1, "[AMMONIUM]": 1, "[NITRATE]": 1, "[NITROUS_GAS]": 2}


def control_widths(vals):
    """midpoint control-volume width per unique coordinate (sums to max-min)."""
    u = np.sort(np.unique(np.round(vals, 5)))
    w = np.zeros_like(u)
    for i in range(len(u)):
        lo = u[i-1] if i > 0 else u[0]
        hi = u[i+1] if i < len(u)-1 else u[-1]
        w[i] = (hi - lo) / 2.0
    return dict(zip(u, w))


def node_area_map(df0):
    wx = control_widths(df0["X"].values)
    wy = control_widths(df0["Y"].values)
    xr = np.round(df0["X"].values, 5); yr = np.round(df0["Y"].values, 5)
    return np.array([wx[a]*wy[b] for a, b in zip(xr, yr)])


def cum_leached_kgha(g05):
    df = pd.read_csv(g05); df.columns = [c.strip() for c in df.columns]
    return float((-df["N_Leach"]).cumsum().values[-1])


# footprint + K from FK geometry
sp0 = pd.read_csv(os.path.join(VR, "FK", "PHREEQC_SPECIES_OUT.txt"))
sp0.columns = [c.strip() for c in sp0.columns]
d00 = sp0[sp0["TIME"] == sp0["TIME"].iloc[0]]
FOOT_HA = (d00["X"].max()-d00["X"].min()) * SLAB * 1e-8
K = 1.0 / 1000.0 / FOOT_HA * GFW_N        # mol(N) -> kg N/ha
print("footprint=%.2f cm^2  kg N/ha = molN * %.1f" % ((d00["X"].max()-d00["X"].min())*SLAB, K))
print("species-output TIME grid: first=%.1f last=%.1f n_times=%d\n"
      % (sp0["TIME"].min(), sp0["TIME"].max(), sp0["TIME"].nunique()))


def pools_kgha(df_rec, area):
    """kg N/ha for each N component over a single-time node record."""
    out = {}
    for comp, na in NATOM.items():
        if comp in df_rec.columns:
            mol = float(np.sum(df_rec[comp].values * area * SLAB * 0.001))  # component moles
            out[comp] = mol * na * K
    return out


rows = []
for v in VARS:
    f = os.path.join(VR, v, "PHREEQC_SPECIES_OUT.txt")
    if not os.path.exists(f):
        continue
    sp = pd.read_csv(f); sp.columns = [c.strip() for c in sp.columns]
    t_first, t_last = sp["TIME"].min(), sp["TIME"].max()
    rec_last = sp[sp["TIME"] == t_last]
    rec_first = sp[sp["TIME"] == t_first]
    area = node_area_map(rec_last)

    fin = pools_kgha(rec_last, area)
    ini = pools_kgha(rec_first, area)
    residual = fin.get("[ORGANIC_N]",0)+fin.get("[AMMONIUM]",0)+fin.get("[NITRATE]",0)
    n2o      = fin.get("[NITROUS_GAS]", 0.0)                  # already x2 via NATOM
    leached  = cum_leached_kgha(os.path.join(VR, v, "DELHI_MURPHY.G05"))
    init_tot = ini.get("[ORGANIC_N]",0)+ini.get("[AMMONIUM]",0)+ini.get("[NITRATE]",0)+ini.get("[NITROUS_GAS]",0)
    accounted = residual + n2o + leached
    rows.append(dict(variant=v,
        res_org=fin.get("[ORGANIC_N]",0), res_nh4=fin.get("[AMMONIUM]",0),
        res_no3=fin.get("[NITRATE]",0), residual_soilN=residual,
        n2o_N=n2o, leached=leached, accounted=accounted,
        init_tot_at_tfirst=init_tot))

res = pd.DataFrame(rows)
res.to_csv(os.path.join(VR, "_RESIDUAL_NITROGEN.csv"), index=False)

print("="*104)
print("END-OF-RUN NITROGEN (kg N/ha):  residual soil N = ORGANIC + NH4 + NO3 left in column")
print("="*104)
print("%-6s | %7s %7s %7s | %11s | %8s | %8s | %10s" %
      ("var","resORG","resNH4","resNO3","RESIDUAL","N2O-N","leached","res+N2O+leach"))
print("-"*104)
for r in rows:
    print("%-6s | %7.2f %7.2f %7.2f | %11.2f | %8.2f | %8.2f | %10.2f" %
          (r["variant"], r["res_org"], r["res_nh4"], r["res_no3"],
           r["residual_soilN"], r["n2o_N"], r["leached"], r["accounted"]))
print("-"*104)
print("N2O-N is the denitrified N (cross-check vs reaction-report denit). 'res+N2O+leach' should")
print("equal the INITIAL total N. (init at first species record, t=%.0fs, shown in CSV.)" % sp0["TIME"].min())
print("\nSaved: _RESIDUAL_NITROGEN.csv")
