"""One-shot: drop the CK_ND variant from the nitrate analysis scripts' variant lists
(VARS = [...]) and the sweep's variant map, so the whole nitrate pipeline runs 6 variants.
Excludes the figure-port files (already CK_ND-free) and the docx builders (handled separately
because CK_ND appears in their hardcoded tables AND analysis prose)."""
import os, re, glob

D = os.path.dirname(os.path.abspath(__file__))
EXCLUDE = {"BUILD_NITRATE_MASS_BALANCE.py", "_port_nitrate_viz.py",
           "_build_comparative_results_docx.py", "_build_mass_balance_docx.py",
           "_drop_cknd_from_scripts.py"}

for f in sorted(glob.glob(os.path.join(D, "*.py"))):
    if os.path.basename(f) in EXCLUDE:
        continue
    t = open(f, encoding="utf-8").read(); o = t
    # drop CK_ND as a list element (last or mid), spaced or unspaced, double- or single-quoted
    t = t.replace(', "CK_ND"]', ']').replace(", 'CK_ND']", "']")
    t = t.replace(',"CK_ND"]', ']').replace(",'CK_ND']", "']")
    t = t.replace(', "CK_ND",', ',').replace(", 'CK_ND',", ",")
    t = t.replace(',"CK_ND",', ',').replace(",'CK_ND',", ",")
    # docstring/prose set lists like "(NR, ZK_ND, FK_ND, CK_ND)"
    t = t.replace(", CK_ND)", ")")
    if t != o:
        open(f, "w", encoding="utf-8").write(t)
        print(f"  edited {os.path.basename(f):32s} remaining CK_ND refs: {t.count('CK_ND')}")

# sweep: remove the CK_ND ordered-dict entry line
ps = os.path.join(D, "_sweep_nitrate_variants.ps1")
t = open(ps, encoding="utf-8").read()
t = re.sub(r'(?m)^[ \t]*"CK_ND"\s*=\s*"[^"]*"\s*\r?\n', '', t)
open(ps, "w", encoding="utf-8").write(t)
print(f"  edited _sweep_nitrate_variants.ps1            remaining CK_ND refs: {t.count('CK_ND')}")
print("done.")
