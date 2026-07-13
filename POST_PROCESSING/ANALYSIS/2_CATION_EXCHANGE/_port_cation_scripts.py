"""One-shot porter: copy the cation-exchange visualization + error scripts from
2_CATION_EXCHANGE_PROBLEM/ANALYSIS_AND_FIGURES into this folder, re-pointed at the
GENERIC results workbook and the central FIGURES/2_CATION_EXCHANGE output dir, and
made batch-safe (Agg backend, no blocking plt.show()). Figure layout preserved verbatim.
Re-runnable; overwrites the ported copies.
"""
import os, re

SRC = r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION\OLD_VERSIONS\2_CATION_EXCHANGE_PROBLEM\ANALYSIS_AND_FIGURES"
DST = r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION\2DSOIL_PHREEQCRM_MODEL\POST_PROCESSING\ANALYSIS\2_CATION_EXCHANGE"
FIGDIR = r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION\2DSOIL_PHREEQCRM_MODEL\POST_PROCESSING\FIGURES\2_CATION_EXCHANGE"

OLD_XLSX = "RESULTS_100cm_1cm_ALL_NODES.xlsx"
NEW_XLSX = "RESULTS_100cm_1cm_ALL_NODES_GENERIC.xlsx"

FILES = ["CATION_EXCHANGE_VISUALIZATION.py", "ERROR_CALCULATION_CATION_EXCHANGE.py"]

for fn in FILES:
    t = open(os.path.join(SRC, fn), encoding="utf-8").read()
    t = t.replace(OLD_XLSX, NEW_XLSX)
    if "matplotlib.pyplot" in t:
        t = t.replace("import matplotlib.pyplot as plt",
                      'import matplotlib\nmatplotlib.use("Agg")\nimport matplotlib.pyplot as plt', 1)
        t = re.sub(r'(?m)^(\s*)plt\.show\(\)', r'\1pass  # plt.show() disabled (batch render)', t)
        # viz builds its output dir as os.path.join(here, FIGURES_DIR) -> central FIGURES/2_CATION_EXCHANGE
        t = t.replace('os.path.join(here, FIGURES_DIR)', repr(FIGDIR))
    open(os.path.join(DST, fn), "w", encoding="utf-8").write(t)
    print("ported:", fn)

print("done.")
