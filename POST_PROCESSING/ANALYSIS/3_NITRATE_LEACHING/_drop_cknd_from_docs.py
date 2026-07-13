"""One-shot: remove the CK_ND variant from the nitrate result docs (mechanical part only) --
drop its table rows and fix the variant count (seven -> six). Prose reframing (CK headline) is
applied separately. Operates on the .md sources AND the native docx builders."""
import os, re

ROOT = r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION\2DSOIL_PHREEQCRM_MODEL"
ND   = os.path.join(ROOT, "POST_PROCESSING", "ANALYSIS", "3_NITRATE_LEACHING")
MD   = [os.path.join(ROOT, "COMPARATIVE_RESULTS.md"), os.path.join(ROOT, "MASS_BALANCE.md")]
PY   = [os.path.join(ND, "_build_comparative_results_docx.py"),
        os.path.join(ND, "_build_mass_balance_docx.py")]


def count(t): return t.count("CK_ND")


def fix_seven(t):
    return (t.replace("seven kinetic variants", "six kinetic variants")
             .replace("seven variants", "six variants")
             .replace("seven independent", "six independent")
             .replace("Seven independent", "Six independent")
             .replace("Seven\nindependent", "Six\nindependent"))


for p in MD:
    t = open(p, encoding="utf-8").read(); n0 = count(t)
    # drop markdown table rows whose first cell is CK_ND (with or without ** bold)
    t = "\n".join(ln for ln in t.split("\n") if not re.match(r'^\s*\|\s*\*{0,2}CK_ND\b', ln))
    t = fix_seven(t)
    open(p, "w", encoding="utf-8").write(t)
    print(f"  {os.path.basename(p):28s} CK_ND {n0} -> {count(t)}")

for p in PY:
    t = open(p, encoding="utf-8").read(); n0 = count(t)
    # drop CK_ND list elements: preceding-comma form (own-line-last / packed-end) then trailing-comma form (first-in-list)
    t = re.sub(r',\s*\["CK_ND"[^\]]*\]', '', t)
    t = re.sub(r'\["CK_ND"[^\]]*\],\s*', '', t)
    t = fix_seven(t)
    open(p, "w", encoding="utf-8").write(t)
    print(f"  {os.path.basename(p):28s} CK_ND {n0} -> {count(t)}")

print("done. (remaining CK_ND, if any, are in prose to be reframed)")
