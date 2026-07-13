"""Extract cumulative NO3-N leaching profiles for all 7 kinetic variants from the
GENERIC engine runs collected under POST_PROCESSING/ANALYSIS/_data/VARIANT_RUNS/<VAR>/DELHI_MURPHY.G05.

Leaching profile (publication method, PYTHON_MURPHY_SAND_LF_VISUALIZATION_V3.py:120):
    cumulative NO3-N leached [kg N/ha] = (-N_Leach).cumsum(),  day = Date_time - Date_time[0]

Outputs (in POST_PROCESSING/ANALYSIS/_data/VARIANT_RUNS/):
  <VAR>/leaching_profile.csv        per-step: step, date_serial, day, N_Leach_step, cum_NO3N_leached_kgNha
  _COMBINED_LEACHING_PROFILES.csv   day + one cumulative column per variant (generic engine)
  _LEACHING_SUMMARY.csv             per-variant end total + checkpoints (days 1/9/23/32), gen vs prev code
Also prints the summary table to stdout.
"""
import os, math
import numpy as np, pandas as pd

ROOT = r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION"
OUT  = os.path.join(ROOT, "2DSOIL_PHREEQCRM_MODEL", "POST_PROCESSING", "ANALYSIS", "_data", "VARIANT_RUNS")
MUR  = os.path.join(ROOT, "OLD_VERSIONS", "3_NITRATE_LEACHING", "2DSOIL-PHREEQCRM_MURPHY_SAND_LF")
VARS = ["NR", "ZK", "ZK_ND", "FK", "FK_ND", "CK"]
CHECK = [1, 9, 23, 32]   # days 1/9/23 = water-application drainage cycles; 32 = end


def profile(g05):
    df = pd.read_csv(g05)
    df.columns = [c.strip() for c in df.columns]
    t = np.asarray(df["Date_time"].values, float); t = t - t[0]
    cum = (-df["N_Leach"]).cumsum().values + 0.0
    return df, t, cum


rows, combined = [], None
for v in VARS:
    g05 = os.path.join(OUT, v, "DELHI_MURPHY.G05")
    if not os.path.exists(g05):
        print(f"  !! MISSING generic G05 for {v}: {g05}")
        continue
    df, t, cum = profile(g05)
    # per-variant leaching profile CSV
    prof = pd.DataFrame({
        "step": np.arange(1, len(t) + 1),
        "date_serial": df["Date_time"].values,
        "day": t,
        "N_Leach_step": df["N_Leach"].values,
        "cum_NO3N_leached_kgNha": cum,
    })
    prof.to_csv(os.path.join(OUT, v, "leaching_profile.csv"), index=False)

    # combined (generic engine) on the FK/first variant's day grid
    if combined is None:
        combined = pd.DataFrame({"day": t})
    combined[v] = np.interp(combined["day"].values, t, cum)

    # previous-code reference (for context only; full comparison is the next step)
    ref = os.path.join(MUR, v, "DELHI_MURPHY.G05")
    if os.path.exists(ref):
        _, tr, cr = profile(ref)
        prev_end = cr[-1]
        prev_chk = [float(np.interp(d, tr, cr)) for d in CHECK]
    else:
        prev_end, prev_chk = float("nan"), [float("nan")] * len(CHECK)

    gen_chk = [float(np.interp(d, t, cum)) for d in CHECK]
    rows.append({
        "variant": v, "n_steps": len(t),
        "gen_end_kgNha": cum[-1],
        **{f"gen_d{d}": gen_chk[i] for i, d in enumerate(CHECK)},
        "prev_end_kgNha": prev_end,
        **{f"prev_d{d}": prev_chk[i] for i, d in enumerate(CHECK)},
        "gen_minus_prev_end": cum[-1] - prev_end,
    })

if combined is not None:
    combined.to_csv(os.path.join(OUT, "_COMBINED_LEACHING_PROFILES.csv"), index=False)
summary = pd.DataFrame(rows)
summary.to_csv(os.path.join(OUT, "_LEACHING_SUMMARY.csv"), index=False)

pd.set_option("display.width", 200); pd.set_option("display.max_columns", 50)
print("=" * 92)
print("GENERIC ENGINE — cumulative NO3-N leached (kg N/ha) per kinetic variant")
print("=" * 92)
disp = summary[["variant", "n_steps", "gen_d1", "gen_d9", "gen_d23", "gen_end_kgNha",
                "prev_end_kgNha", "gen_minus_prev_end"]].copy()
disp.columns = ["var", "steps", "day1", "day9", "day23", "gen_END", "prev_END", "gen-prev"]
print(disp.to_string(index=False, float_format=lambda x: f"{x:8.3f}"))
print("\nPer-variant leaching_profile.csv + _COMBINED_LEACHING_PROFILES.csv + _LEACHING_SUMMARY.csv written to:")
print("  " + OUT)
