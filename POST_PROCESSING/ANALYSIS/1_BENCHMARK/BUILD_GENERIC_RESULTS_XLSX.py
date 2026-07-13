"""Build RESULTS_BENCHMARKING_GENERIC_750CM.xlsx from the GENERIC engine's
benchmark sweep (3 cases). One sheet per case (CASE_1/2/3) with the column
layout the downstream analytical / error / figure scripts expect:

    NODE_NUM, TIME, DATE, HOUR, X, Y, CONC, CONC_RATIO_SIMULATED, Mu, Gamma

CONC_RATIO_SIMULATED = CONC / C0 (C0 = 1000). DAY is days since injection
start (01/06/2024); rows with DAY in 0..5 are kept, matching the original
workbook. Per (DATE, Y) the last-logged value is taken — identical to the
validated validate_case.py mapping (a daily end-of-day snapshot).

The analytical CONC_RATIO_ANALYTICAL_AT_Y_DAY_k columns are NOT added here;
the ANALYTICAL_AT_SIMULATED_DEPTHS_CASE_{1,2,3}.py scripts append them next.
"""
import os
import datetime as dt
import pandas as pd

ROOT = r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION"
RUNS = os.path.join(ROOT, "2DSOIL_PHREEQCRM_MODEL", "POST_PROCESSING", "ANALYSIS", "_data", "BENCHMARK_RUNS")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(HERE, "RESULTS_BENCHMARKING_GENERIC_750CM.xlsx")

C0 = 1000.0
INJ_START = dt.date(2024, 1, 6)          # DAY 0 = first day of solute injection
DAY_MIN, DAY_MAX = 0, 5
# Reaction rates per case (s^-1 / mol L^-1 s^-1), for the Mu/Gamma columns.
RATES = {"CASE_1": (0.0, 0.0), "CASE_2": (3.0e-6, 0.0), "CASE_3": (3.0e-6, 1.0e-6)}


def parse_fertigation(path):
    """Return list of dicts (one per kept node-day), last value per (DATE, Y)."""
    by_key = {}   # (date_str, y) -> row dict   (last logged wins, like validate_case.py)
    with open(path) as f:
        next(f)                                   # header
        for ln in f:
            p = [x.strip() for x in ln.split(",")]
            if len(p) < 7 or not p[1] or not p[1][0].isdigit():
                continue
            node = int(float(p[0])); tim = float(p[1]); date_s = p[2]
            hour = p[3]; x = float(p[4]); y = float(p[5]); conc = float(p[6])
            by_key[(date_s, round(y, 4))] = dict(
                NODE_NUM=node, TIME=tim, DATE=date_s, HOUR=hour, X=x, Y=y, CONC=conc)
    return list(by_key.values())


def to_day(date_s):
    d = dt.datetime.strptime(date_s, "%m/%d/%Y").date()
    return (d - INJ_START).days


def build_case(case):
    fo = os.path.join(RUNS, case, "FERTIGATION_OUTPUT.txt")
    if not os.path.exists(fo):
        raise FileNotFoundError(f"missing sweep output: {fo} (run _sweep_benchmark_cases.ps1)")
    rows = parse_fertigation(fo)
    df = pd.DataFrame(rows)
    df["DAY"] = df["DATE"].map(to_day)
    df = df[(df["DAY"] >= DAY_MIN) & (df["DAY"] <= DAY_MAX)].copy()
    df["CONC_RATIO_SIMULATED"] = df["CONC"] / C0
    mu, ga = RATES[case]
    df["Mu"] = mu; df["Gamma"] = ga
    df = df.sort_values(["DAY", "Y"]).reset_index(drop=True)
    return df[["NODE_NUM", "TIME", "DAY", "DATE", "HOUR", "X", "Y",
               "CONC", "CONC_RATIO_SIMULATED", "Mu", "Gamma"]]


def main():
    with pd.ExcelWriter(OUT, engine="openpyxl") as writer:
        for case in ("CASE_1", "CASE_2", "CASE_3"):
            df = build_case(case)
            df.to_excel(writer, sheet_name=case, index=False)
            ndays = sorted(df["DAY"].unique().tolist())
            npd = df[df["DAY"] == 1].shape[0]
            print(f"{case}: rows={df.shape[0]}  DAYs={ndays}  nodes/day(DAY1)={npd}  "
                  f"CONC_RATIO range {df['CONC_RATIO_SIMULATED'].min():.4f}..{df['CONC_RATIO_SIMULATED'].max():.4f}")
    print("wrote:", OUT)


if __name__ == "__main__":
    main()
