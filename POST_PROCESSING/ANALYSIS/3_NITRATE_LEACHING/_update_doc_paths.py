# -*- coding: utf-8 -*-
"""Task #5: update stale `_VALIDATION/` path references to the POST_PROCESSING layout
(scripts -> POST_PROCESSING/ANALYSIS/<study>/, data -> POST_PROCESSING/ANALYSIS/_data/VARIANT_RUNS).
Reports any replacement that does not match."""
import os
RT = r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION"
GEN = os.path.join(RT, "2DSOIL_PHREEQCRM_MODEL")
ND = os.path.join(GEN, "POST_PROCESSING", "ANALYSIS", "3_NITRATE_LEACHING")

VR_OLD = "_VALIDATION/VARIANT_RUNS"
VR_NEW = "POST_PROCESSING/ANALYSIS/_data/VARIANT_RUNS"

# files where the only change is the uniform VARIANT_RUNS data path
A = [os.path.join(GEN, "COMPARATIVE_RESULTS.md"), os.path.join(GEN, "MASS_BALANCE.md"),
     os.path.join(ND, "_build_comparative_results_docx.py"), os.path.join(ND, "_sweep_nitrate_variants.ps1"),
     os.path.join(ND, "analyze_reaction_totals.py"), os.path.join(ND, "extract_leaching_profiles.py")]

# context-specific scripts-dir replacements
B = {
 os.path.join(GEN, "COMPARATIVE_RESULTS.md"): [
   ("Scripts — `2DSOIL_PHREEQCRM_MODEL/_VALIDATION/`:", "Scripts — `2DSOIL_PHREEQCRM_MODEL/POST_PROCESSING/ANALYSIS/3_NITRATE_LEACHING/`:")],
 os.path.join(GEN, "MASS_BALANCE.md"): [
   ("Scripts — `_VALIDATION/`:", "Scripts — `POST_PROCESSING/ANALYSIS/3_NITRATE_LEACHING/`:")],
 os.path.join(ND, "_build_comparative_results_docx.py"): [
   ('table(["script (_VALIDATION/)","role"]', 'table(["script (ANALYSIS/3_NITRATE_LEACHING/)","role"]')],
 os.path.join(ND, "_build_mass_balance_docx.py"): [
   ('table(["script (_VALIDATION/)","role"]', 'table(["script (ANALYSIS/3_NITRATE_LEACHING/)","role"]')],
 os.path.join(GEN, "VALIDATION.md"): [
   ("`_VALIDATION/validate_case.py`", "`POST_PROCESSING/ANALYSIS/1_BENCHMARK/validate_case.py`"),
   ("`_VALIDATION/validate_cation.py`", "`POST_PROCESSING/ANALYSIS/2_CATION_EXCHANGE/validate_cation.py`"),
   ("| `_VALIDATION/` | comparison scripts |", "| `POST_PROCESSING/ANALYSIS/<study>/` | comparison scripts |")],
 os.path.join(RT, "CLAUDE.md"): [
   ("## Analysis pipeline (`2DSOIL_PHREEQCRM_MODEL/_VALIDATION/`)", "## Analysis pipeline (`2DSOIL_PHREEQCRM_MODEL/POST_PROCESSING/ANALYSIS/`)"),
   ("is built by `_VALIDATION/_md_to_docx.py`", "is built by `POST_PROCESSING/ANALYSIS/_common/_md_to_docx.py`")],
 os.path.join(RT, "CURRENT_TASK.md"): [
   ("2DSOIL_PHREEQCRM_MODEL/_VALIDATION/validate_nitrate.py", "2DSOIL_PHREEQCRM_MODEL/POST_PROCESSING/ANALYSIS/3_NITRATE_LEACHING/validate_nitrate.py")],
}

touched = set(A) | set(B)
for f in touched:
    t = open(f, encoding="utf-8").read(); n0 = t.count("_VALIDATION")
    if f in A:
        t = t.replace(VR_OLD, VR_NEW)
    for old, new in B.get(f, []):
        if old in t: t = t.replace(old, new)
        else: print("   !!! NOT FOUND in", os.path.basename(f), ":", old[:50])
    open(f, "w", encoding="utf-8").write(t)
    print(f"  {os.path.basename(f):34s} _VALIDATION {n0} -> {t.count('_VALIDATION')}")
print("done.")
