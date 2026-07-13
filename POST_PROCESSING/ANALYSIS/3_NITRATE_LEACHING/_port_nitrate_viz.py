"""One-shot porter: copy the V3 nitrate-leaching visualization from
3_NITRATE_LEACHING/2DSOIL-PHREEQCRM_MURPHY_SAND_LF into this folder, re-pointed at the
GENERIC engine's data and the central FIGURES/3_NITRATE_LEACHING output dir, batch-safe.

Re-points (the original uses CWD-relative paths):
  MASS_BALANCE_PHREEQC_<VAR>.txt  -> this folder (built by BUILD_NITRATE_MASS_BALANCE.py)
  <VAR>/DELHI_MURPHY.G05          -> _data/VARIANT_RUNS/<VAR>/
  OBSERVED_DATA.xlsx              -> the reference workbook in the legacy folder (field data)
  COMPARISON_OF_RESULTS.xlsx      -> COMPARISON_OF_RESULTS_GENERIC.xlsx (generic RMSE, this folder)
  Figure_*.png                    -> FIGURES/3_NITRATE_LEACHING/
Figure layout preserved verbatim; only data source + output paths change.
"""
import os, re

ROOT = r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION"
SRC = os.path.join(ROOT, "OLD_VERSIONS", "3_NITRATE_LEACHING", "2DSOIL-PHREEQCRM_MURPHY_SAND_LF")
DST = os.path.join(ROOT, "2DSOIL_PHREEQCRM_MODEL", "POST_PROCESSING", "ANALYSIS", "3_NITRATE_LEACHING")
FIGDIR = os.path.join(ROOT, "2DSOIL_PHREEQCRM_MODEL", "POST_PROCESSING", "FIGURES", "3_NITRATE_LEACHING")
VRDIR = os.path.join(ROOT, "2DSOIL_PHREEQCRM_MODEL", "POST_PROCESSING", "ANALYSIS", "_data", "VARIANT_RUNS")
OBS = os.path.join(SRC, "OBSERVED_DATA.xlsx")
SRC_FILE = "PYTHON_MURPHY_SAND_LF_VISUALIZATION_V3.py"

t = open(os.path.join(SRC, SRC_FILE), encoding="utf-8").read()

# headless backend
t = t.replace("import matplotlib.pyplot as PLT",
              'import matplotlib\nmatplotlib.use("Agg")\nimport matplotlib.pyplot as PLT', 1)

# inject generic-data path constants right after 'import os'
const = (
    "import os\n"
    "MBDIR   = r'%s' + os.sep\n"
    "VRDIR   = r'%s' + os.sep\n"
    "FIGDIR  = r'%s' + os.sep\n"
    "OBSPATH = r'%s'\n"
    "CMPPATH = MBDIR + 'COMPARISON_OF_RESULTS_GENERIC.xlsx'\n"
    "os.makedirs(FIGDIR, exist_ok=True)\n"
) % (DST, VRDIR, FIGDIR, OBS)
t = t.replace("import os\n", const, 1)

# re-point data reads
t = t.replace("PD.read_csv('MASS_BALANCE_PHREEQC_", "PD.read_csv(MBDIR + 'MASS_BALANCE_PHREEQC_")
t = re.sub(r"PD\.read_csv\('(\w+)/DELHI_MURPHY\.G05'\)",
           r"PD.read_csv(VRDIR + '\1/DELHI_MURPHY.G05')", t)
t = t.replace("PD.read_excel('OBSERVED_DATA.xlsx'", "PD.read_excel(OBSPATH")
t = t.replace("PD.read_excel('COMPARISON_OF_RESULTS.xlsx'", "PD.read_excel(CMPPATH")
# Figure 3 RMSE now lives in the PER_WATER_APPLICATION sheet (RMSE is the last row)
t = t.replace("sheet_name='RMSE'", "sheet_name='PER_WATER_APPLICATION'")

# re-point figure saves to the central FIGURES dir
t = t.replace(".savefig('Figure", ".savefig(FIGDIR + 'Figure")

# batch-safe
t = t.replace("os.system('cls')", "pass  # os.system('cls') disabled (batch)")
t = re.sub(r"(?m)^(\s*)PLT\.show\(\)", r"\1pass  # PLT.show() disabled (batch render)", t)

# --- drop the CK_ND variant (not in the manuscript; figures use 6 variants) ---
# Remove standalone CK_ND load/process/plot/print lines and the per-line value-list elements,
# but keep the inline rmse_values list (edited below).
keep = [ln for ln in t.split("\n")
        if not ("CK_ND" in ln and not ln.lstrip().startswith("rmse_values"))]
t = "\n".join(keep)
t = t.replace(", CK_ND_RMSE", "")                 # rmse_values inline list element
t = t.replace(", 'CK-ND'", "")                    # scenario_labels + rmse_scenario_labels labels
t = t.replace("rmse_colors = ['#0072B2', '#E69F00', '#009E73', '#800000', '#E69F00', '#009E73', '#800000']",
              "rmse_colors = ['#0072B2', '#E69F00', '#009E73', '#800000', '#E69F00', '#009E73']")
t = t.replace("[1.0, 1.0, 1.0, 1.0, 0.7, 0.7, 0.7]", "[1.0, 1.0, 1.0, 1.0, 0.7, 0.7]")

open(os.path.join(DST, SRC_FILE), "w", encoding="utf-8").write(t)
print("ported:", SRC_FILE)
