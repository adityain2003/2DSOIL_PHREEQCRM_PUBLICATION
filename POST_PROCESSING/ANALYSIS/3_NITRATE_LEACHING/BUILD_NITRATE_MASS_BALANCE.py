"""Adapter: build MASS_BALANCE_PHREEQC_<VAR>.txt (the columns the V3 nitrate viz expects)
from the GENERIC engine's per-step REACTION_TOTALS.txt + DELHI_MURPHY.G05, for all 7 variants.

The generic engine reports component-deltas (moles, net reaction change per RunCells step) in
REACTION_TOTALS.txt; the old per-problem code wrote MINERAL_N / DELTA_NITRIFIED_N /
DELTA_DENITRIFIED_N directly. Conversion (CLAUDE.md):
    nitrified  (mol) = -d[ORGANIC_N] - d[AMMONIUM]
    denitrified(mol) =  2 * d[NITROUS_GAS]          (FULL denitrified NO3, mass-correct)
    d[NITRATE] (mol) =  reaction change to soil nitrate ( = nitrified - denitrified )
    kg N/ha          =  mol * K,   K = 14.01/1000 / (x_width*SLAB*1e-8) = 280200
Soil nitrate timeline (transport included via the G05 leaching term):
    MINERAL_N(t) = NO3_initial + 280200*cumsum(d[NITRATE])(t) - cum_leached(t)

REACTION_TOTALS is on a fine adaptive step grid (~2986 steps); G05 is coarser (~769). The
cumulative reaction extents are interpolated onto the G05 time axis so MASS_BALANCE rows align
1:1 with G05 (TIME_2DSOIL = G05 Date_time), making the viz's TIME_COMMON join exact.

NOTE: the generic denitrification (full NO3 removal) is LARGER than the old code's (half); this
is the documented mass-correct behavior, so the regenerated Figure 2 denit bars differ from the
old published figure by design.

Also writes COMPARISON_OF_RESULTS_GENERIC.xlsx (sheet RMSE) from the generic _RMSE_VS_OBSERVED.csv
so the viz's Figure 3 shows the generic engine's RMSE vs observed.
"""
import os
import numpy as np
import pandas as pd

ROOT = r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION"
VR   = os.path.join(ROOT, "2DSOIL_PHREEQCRM_MODEL", "POST_PROCESSING", "ANALYSIS", "_data", "VARIANT_RUNS")
HERE = os.path.dirname(os.path.abspath(__file__))
VARS = ["NR", "ZK", "ZK_ND", "FK", "FK_ND", "CK"]   # CK_ND excluded (not in the manuscript)
SLAB = 1.0
GFW_N = 14.01


def control_widths(vals):
    u = np.sort(np.unique(np.round(vals, 5)))
    w = np.zeros_like(u)
    for i in range(len(u)):
        lo = u[i-1] if i > 0 else u[0]
        hi = u[i+1] if i < len(u)-1 else u[-1]
        w[i] = (hi - lo) / 2.0
    return dict(zip(u, w))


def node_area_map(df0):
    wx = control_widths(df0["X"].values); wy = control_widths(df0["Y"].values)
    xr = np.round(df0["X"].values, 5); yr = np.round(df0["Y"].values, 5)
    return np.array([wx[a]*wy[b] for a, b in zip(xr, yr)])


# geometry + K (from FK species output), and initial soil-NO3 pool (shared IC)
sp = pd.read_csv(os.path.join(VR, "FK", "PHREEQC_SPECIES_OUT.txt")); sp.columns = [c.strip() for c in sp.columns]
d0 = sp[sp["TIME"] == sp["TIME"].iloc[0]]
x_width = float(d0["X"].max() - d0["X"].min())
FOOT_HA = x_width * SLAB * 1e-8
K = GFW_N / 1000.0 / FOOT_HA
area0 = node_area_map(d0)
NO3_INIT = float(np.sum(d0["[NITRATE]"].values * area0 * SLAB * 0.001)) * K   # kg N/ha
print(f"K = {K:.1f} kg N/ha per mol ; NO3_initial = {NO3_INIT:.3f} kg N/ha\n")


def build_variant(v, res_no3_v):
    rt = pd.read_csv(os.path.join(VR, v, "REACTION_TOTALS.txt")); rt.columns = [c.strip() for c in rt.columns]
    g  = pd.read_csv(os.path.join(VR, v, "DELHI_MURPHY.G05"));     g.columns = [c.strip() for c in g.columns]

    t_rt = rt["TIME_S"].to_numpy() / 86400.0                      # days since start
    dON  = rt["d[[ORGANIC_N]]"].to_numpy(); dNH4 = rt["d[[AMMONIUM]]"].to_numpy()
    dNO3 = rt["d[[NITRATE]]"].to_numpy();   dN2O = rt["d[[NITROUS_GAS]]"].to_numpy()
    nit_step = (-dON - dNH4) * K
    den_step = (2.0 * dN2O) * K
    no3_step = dNO3 * K
    # cumulative reaction extents with a t=0 anchor
    t_c   = np.concatenate(([0.0], t_rt))
    cumN  = np.concatenate(([0.0], np.cumsum(nit_step)))
    cumD  = np.concatenate(([0.0], np.cumsum(den_step)))
    cumR  = np.concatenate(([0.0], np.cumsum(no3_step)))          # cumulative reaction d[NITRATE]

    t_g = (g["Date_time"] - g["Date_time"].iloc[0]).to_numpy()    # days since start
    cum_leached = (-g["N_Leach"]).cumsum().to_numpy()

    TOTAL_NIT = np.interp(t_g, t_c, cumN)
    TOTAL_DEN = np.interp(t_g, t_c, cumD)
    react_NO3 = np.interp(t_g, t_c, cumR)
    # anchor the soil-NO3 timeline on the validated final pool (res_no3) and integrate backward;
    # this is robust to the species-file initial and recovers the true initial as a cross-check.
    MINERAL_N = res_no3_v + (react_NO3 - react_NO3[-1]) - (cum_leached - cum_leached[-1])

    # per-G05-step deltas whose cumsum reproduces TOTAL_* (viz does TOTAL = DELTA.cumsum())
    dNIT = np.diff(TOTAL_NIT, prepend=0.0)
    dDEN = np.diff(TOTAL_DEN, prepend=0.0)

    out = pd.DataFrame({
        "TIME_2DSOIL": g["Date_time"].to_numpy(),
        "TIME_PHREEQCRM": (t_g * 86400.0),
        "DATE": g["Date"].astype(str).str.strip().to_numpy() if "Date" in g.columns else "",
        "MINERAL_N": MINERAL_N,
        "DELTA_NITRIFIED_N": dNIT,
        "DELTA_DENITRIFIED_N": dDEN,
    })
    out.to_csv(os.path.join(HERE, f"MASS_BALANCE_PHREEQC_{v}.txt"), index=False)
    return dict(v=v, mineral_init=MINERAL_N[0], mineral_end=MINERAL_N[-1],
                nit_end=TOTAL_NIT[-1], den_end=TOTAL_DEN[-1], leached_end=cum_leached[-1])


def main():
    rn = pd.read_csv(os.path.join(VR, "_RESIDUAL_NITROGEN.csv")).set_index("variant")
    print("%-6s | %12s | %10s %10s | %10s %10s | %10s" %
          ("var", "implied_init", "MINERAL_end", "res_no3", "cum_NIT", "cum_DEN", "leached"))
    print("   (implied_init should be ~25.5 for ALL variants -> reconstruction is self-consistent)")
    print("-" * 86)
    for v in VARS:
        r = build_variant(v, float(rn.loc[v, "res_no3"]))
        print("%-6s | %12.3f | %10.3f %10.3f | %10.3f %10.3f | %10.3f" %
              (v, r["mineral_init"], r["mineral_end"], rn.loc[v, "res_no3"],
               r["nit_end"], r["den_end"], r["leached_end"]))

    # COMPARISON_OF_RESULTS workbook (two sheets), generic engine vs observed:
    #   CUMULATIVE_ERROR      : end-of-run cumulative NO3-N leached vs observed total + error
    #   PER_WATER_APPLICATION : cumulative leached after each WA (days 2/10/24) + RMSE row
    rm = pd.read_csv(os.path.join(VR, "_RMSE_VS_OBSERVED.csv")).set_index("variant")
    tl = pd.read_csv(os.path.join(VR, "_TOTAL_LEACHING_VS_OBSERVED.csv")).set_index("variant")
    OBS_WA = [20.6, 25.7, 35.7]   # observed cumulative NO3-N leached after WA#1/2/3 (days 2/10/24)
    OBS_TOTAL = 35.7              # observed end-of-run total

    cum_rows = []
    for v in VARS:
        g = float(tl.loc[v, "gen_total"])
        cum_rows.append({"Variant": v, "Cumulative_NO3N_Leached_kgha": round(g, 2),
                         "Observed_kgha": OBS_TOTAL, "Error_kgha": round(g - OBS_TOTAL, 2),
                         "Abs_Error_kgha": round(abs(g - OBS_TOTAL), 2),
                         "Pct_Error": round(100.0 * (g - OBS_TOTAL) / OBS_TOTAL, 1)})
    cum_df = pd.DataFrame(cum_rows)

    def wa_row(label, col, obs):
        r = {"Water_Application": label}
        r.update({v: round(float(rm.loc[v, col]), 3) for v in VARS})
        r["OBSERVED"] = obs
        return r
    wa_df = pd.DataFrame([
        wa_row("WA#1 (day 2)",  "gen_d2",  OBS_WA[0]),
        wa_row("WA#2 (day 10)", "gen_d10", OBS_WA[1]),
        wa_row("WA#3 (day 24)", "gen_d24", OBS_WA[2]),
        wa_row("RMSE",          "gen_RMSE_manu", 0.0),
    ])

    with pd.ExcelWriter(os.path.join(HERE, "COMPARISON_OF_RESULTS_GENERIC.xlsx"), engine="openpyxl") as w:
        cum_df.to_excel(w, sheet_name="CUMULATIVE_ERROR", index=False)
        wa_df.to_excel(w, sheet_name="PER_WATER_APPLICATION", index=False)
    print("\nMINERAL_end should track res_no3; cum_NIT/DEN should match _NITROGEN_BUDGET.")
    print(f"Wrote {len(VARS)} MASS_BALANCE_PHREEQC_<VAR>.txt + COMPARISON_OF_RESULTS_GENERIC.xlsx (2 sheets)")


if __name__ == "__main__":
    main()
