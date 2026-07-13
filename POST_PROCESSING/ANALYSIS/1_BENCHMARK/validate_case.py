"""Generalized benchmark validator for the GENERIC engine (2DSOIL_PHREEQCRM_MODEL).
Auto-detects the active CASE from PHREEQC_OPTIONS.txt, parses the engine's
FERTIGATION_OUTPUT.txt, and compares the simulated [A] depth profile against
(a) the Ogata-Banks/van Genuchten ANALYTICAL solution and (b) the original CB1
simulated profile - both read tab-wise from RESULTS_BENCHMARKING_ANALYTICAL_SOLUTION_750CM.xlsx.
Usage:  python validate_case.py [case_number]   (case auto-detected if omitted)
"""
import math, os, sys, re
import pandas as pd

ROOT = r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION"
BUND = os.path.join(ROOT, "2DSOIL_PHREEQCRM_MODEL", "RUN_INPUTS", "1_BENCHMARK")
XLSX = os.path.join(ROOT, "OLD_VERSIONS", "1_BENCHMARKING_STUDY", "ANALYSIS_AND_FIGURES",
                    "RESULTS_BENCHMARKING_ANALYTICAL_SOLUTION_750CM.xlsx")
C0 = 1000.0
DAYMAP = {1: "01/07/2024", 2: "01/08/2024", 3: "01/09/2024"}  # injection starts 01/06

opt = open(os.path.join(BUND, "PHREEQC_OPTIONS.txt")).read()
m = re.search(r"CASE_(\d)", opt)
case = int(sys.argv[1]) if len(sys.argv) > 1 else (int(m.group(1)) if m else 1)

# parse engine output: date -> {y: ratio}
prof = {}
with open(os.path.join(BUND, "FERTIGATION_OUTPUT.txt")) as f:
    next(f)
    for ln in f:
        p = [x.strip() for x in ln.split(",")]
        if len(p) < 7 or not p[1] or not p[1][0].isdigit():
            continue
        prof.setdefault(p[2], {})[round(float(p[5]), 1)] = float(p[6]) / C0

df = pd.read_excel(XLSX, sheet_name="CASE_%d" % case)
base = df[df["DAY"] == 1]                       # one full set of Y + analytical columns
mu = df["Mu"].dropna().unique()[:1]
ga = df["Gamma"].dropna().unique()[:1]
print("=" * 72)
print("VALIDATION  CASE_%d   (Mu=%s  Gamma=%s)" % (case, mu, ga))
print("  5_GENERIC engine  vs  ANALYTICAL  and  vs  original CB1 simulated")
print("=" * 72)
print("%-6s | %-26s | %-26s" % ("Day", "vs ANALYTICAL", "vs CB1 original"))
print("%-6s | %-26s | %-26s" % ("", "RMSE     MAE     MaxErr", "RMSE     MAE     MaxErr"))
print("-" * 72)
for t, date in DAYMAP.items():
    if date not in prof:
        print("%-6d | (engine output for this day missing)" % t)
        continue
    g = prof[date]
    acol = "CONC_RATIO_ANALYTICAL_AT_Y_DAY_%d" % t
    om = {round(float(y), 1): float(c)
          for y, c in zip(df[df["DAY"] == t]["Y"], df[df["DAY"] == t]["CONC_RATIO_SIMULATED"])}
    ea, eo = [], []
    for _, r in base.iterrows():
        y = round(float(r["Y"]), 1)
        ana = float(r[acol])
        if y in g and not math.isnan(ana):
            ea.append(abs(g[y] - ana))
        if y in g and y in om:
            eo.append(abs(g[y] - om[y]))
    def stats(e):
        if not e: return (float("nan"),) * 3
        return (math.sqrt(sum(x * x for x in e) / len(e)), sum(e) / len(e), max(e))
    ra = stats(ea); ro = stats(eo)
    print("%-6d | %7.4f %7.4f %7.4f   | %7.4f %7.4f %7.4f"
          % (t, ra[0], ra[1], ra[2], ro[0], ro[1], ro[2]))
print("-" * 72)
print("(errors are in C/C0 ratio units, 0..1)")
