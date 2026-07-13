"""One-shot porter: copy the original benchmarking analysis/figure scripts from
1_BENCHMARKING_STUDY/ANALYSIS_AND_FIGURES into this folder, re-pointed at the
GENERIC engine's results workbook and the central FIGURES/1_BENCHMARK output dir,
and made batch-safe (Agg backend, no blocking plt.show()).

The figure LAYOUT is preserved verbatim — only data source + output paths change.
Re-runnable; overwrites the ported copies.
"""
import os, re

SRC = r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION\OLD_VERSIONS\1_BENCHMARKING_STUDY\ANALYSIS_AND_FIGURES"
DST = r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION\2DSOIL_PHREEQCRM_MODEL\POST_PROCESSING\ANALYSIS\1_BENCHMARK"
FIGDIR = r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION\2DSOIL_PHREEQCRM_MODEL\POST_PROCESSING\FIGURES\1_BENCHMARK"

OLD_XLSX = "RESULTS_BENCHMARKING_ANALYTICAL_SOLUTION_750CM.xlsx"
NEW_XLSX = "RESULTS_BENCHMARKING_GENERIC_750CM.xlsx"

FILES = [
    "ANALYTICAL_AT_SIMULATED_DEPTHS_CASE_1.py",
    "ANALYTICAL_AT_SIMULATED_DEPTHS_CASE_2.py",
    "ANALYTICAL_AT_SIMULATED_DEPTHS_CASE_3.py",
    "ERROR_CALCULATION.py",
    "PHREEQC_BENCHMARKING_CASE_PROGRESSION_FIGURE.py",
    "PHREEQC_BENCHMARKING_COMBINED_FIGURE.py",
    "PHREEQC_BENCHMARKING_DECOMPOSITION_FIGURE.py",
]

for fn in FILES:
    t = open(os.path.join(SRC, fn), encoding="utf-8").read()
    # 1) data source: original CB1 workbook -> generic-engine workbook
    t = t.replace(OLD_XLSX, NEW_XLSX)
    if "matplotlib.pyplot" in t:
        # 2) headless backend (must precede pyplot import)
        t = t.replace("import matplotlib.pyplot as plt",
                      'import matplotlib\nmatplotlib.use("Agg")\nimport matplotlib.pyplot as plt', 1)
        # 3) no blocking window
        t = re.sub(r'(?m)^(\s*)plt\.show\(\)', r'\1pass  # plt.show() disabled (batch render)', t)
        # 4) write figures to the central FIGURES/1_BENCHMARK, not next to the script
        t = t.replace('os.path.join(here, "FIGURES")', repr(FIGDIR))
    open(os.path.join(DST, fn), "w", encoding="utf-8").write(t)
    print("ported:", fn)

print("done.")
