"""Build RESULTS_100cm_1cm_ALL_NODES_GENERIC.xlsx for the cation-exchange study.

Start from the original workbook sheet (which carries the IPhreeqc REFERENCE columns +
both depth grids), and OVERWRITE only the 5 simulated columns
(`<species> 2DSoil-PhreeqcRM`) with the GENERIC engine's concentrations parsed from
_data/CATION_RUN/FERTIGATION_OUTPUT.txt (CONC1..5 = Ca, Cl, Na, K, N in mg/L -> mmol/L
via GFW). The IPhreeqc reference, grids, and times are kept verbatim, so the downstream
viz + error scripts run unchanged on the generic-engine simulated data.

Simulated and generic rows are aligned by depth RANK within each time snapshot (both have
100 nodes/time on the same 1 cm column grid), which is robust to the node-vs-cell-centered
offset (generic depth = FERTIGATION Y - 1 cm = the sheet's Y_ABS coordinate).
"""
import os
import pandas as pd

ROOT = r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION"
SRC_XLSX = os.path.join(ROOT, "OLD_VERSIONS", "2_CATION_EXCHANGE_PROBLEM", "ANALYSIS_AND_FIGURES",
                        "RESULTS_100cm_1cm_ALL_NODES.xlsx")
SRC_SHEET = "100cm_1_cm_ALL_NODES_IPHR_1cm"
RUN = os.path.join(ROOT, "2DSOIL_PHREEQCRM_MODEL", "POST_PROCESSING", "ANALYSIS", "_data",
                   "CATION_RUN", "FERTIGATION_OUTPUT.txt")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "RESULTS_100cm_1cm_ALL_NODES_GENERIC.xlsx")

# FERTIGATION CONC1..5 order = Ca, Cl, Na, K, N (mg/L). GFW -> mmol/L.
GFW = [40.08, 35.453, 22.9898, 39.102, 14.0067]
SIM_COLS = ["Ca2+ 2DSoil-PhreeqcRM", "Cl- 2DSoil-PhreeqcRM", "Na+ 2DSoil-PhreeqcRM",
            "K+ 2DSoil-PhreeqcRM", "NO3- 2DSoil-PhreeqcRM"]
TIME_COL = "Time ABS 2DSoil-PhreeqcRM"
YABS_COL = "Y_ABS 2DSoil_PhreeqcRM"
# Time-ABS seconds -> generic FERTIGATION DATE
TIME2DATE = {0: "01/01/2024", 86400: "01/02/2024", 172800: "01/03/2024",
             259200: "01/04/2024", 345600: "01/05/2024", 432000: "01/06/2024"}


def parse_generic():
    """date -> list of (genY, [Ca,Cl,Na,K,NO3 mmol/L]) sorted ascending by genY."""
    by_date = {}
    with open(RUN) as f:
        next(f)
        for ln in f:
            p = [x.strip() for x in ln.split(",")]
            if len(p) < 11 or not p[1] or not p[1][0].isdigit():
                continue
            date = p[2]; y = float(p[5])
            conc = [float(p[i]) for i in range(6, 11)]
            mmol = [conc[i] / GFW[i] for i in range(5)]
            by_date.setdefault(date, []).append((y, mmol))
    for d in by_date:
        by_date[d].sort(key=lambda r: r[0])   # ascending genY = ascending depth-from-base
    return by_date


def main():
    df = pd.read_excel(SRC_XLSX, sheet_name=SRC_SHEET)
    gen = parse_generic()

    matched = 0
    for tsec in sorted(df[TIME_COL].dropna().unique()):
        date = TIME2DATE.get(int(round(tsec)))
        if date is None or date not in gen:
            continue
        sidx = df.index[df[TIME_COL] == tsec].tolist()
        sidx = sorted(sidx, key=lambda i: df.at[i, YABS_COL])   # ascending Y_ABS
        grows = gen[date]
        if len(sidx) != len(grows):
            print(f"  WARN tsec={tsec} date={date}: sheet {len(sidx)} rows vs generic {len(grows)} — aligning min length")
        for i, (_, mmol) in zip(sidx, grows):
            for c, val in zip(SIM_COLS, mmol):
                df.at[i, c] = val
            matched += 1

    with pd.ExcelWriter(OUT, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=SRC_SHEET, index=False)

    print(f"rows overwritten with generic sim: {matched}")
    for c in SIM_COLS:
        print(f"  {c:28s} range {df[c].min():.4f} .. {df[c].max():.4f} mmol/L")
    print("wrote:", OUT)


if __name__ == "__main__":
    main()
