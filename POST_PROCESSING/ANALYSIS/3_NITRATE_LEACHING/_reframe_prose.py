# -*- coding: utf-8 -*-
"""One-shot: reframe the COMPARATIVE_RESULTS prose to headline CK (conditional kinetics) and
remove the residual CK_ND mentions; fix the remaining 'seven kinetic' count; trim the CK/CK_ND
twin comparison in MASS_BALANCE. Reports any replacement that does not match exactly."""
import os
ROOT = r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION\2DSOIL_PHREEQCRM_MODEL"
ND   = os.path.join(ROOT, "POST_PROCESSING", "ANALYSIS", "3_NITRATE_LEACHING")

CMP_MD = os.path.join(ROOT, "COMPARATIVE_RESULTS.md")
MB_MD  = os.path.join(ROOT, "MASS_BALANCE.md")
CMP_PY = os.path.join(ND, "_build_comparative_results_docx.py")
MB_PY  = os.path.join(ND, "_build_mass_balance_docx.py")

EDITS = {
 CMP_MD: [
  ("- **FK and CK are the best-fitting denitrifying variants; ZK is the worst — drop it.** The ranking\n  is stable across the final, three-time, and daily evaluations.",
   "- **CK (conditional kinetics) is the best-fitting variant overall** — closest to the observed final\n  total (−2.31 kg N/ha, −6.5 %) and lowest RMSE at the three critical times (1.59, NRMSE 10.1 %, \"good\").\n  **FK is a close second** (lowest daily RMSE, 3.61). **ZK is the worst — drop it.** The ranking is\n  stable across the final, three-time, and daily evaluations."),
  ("- The **denitrifying variants** (ZK, FK, CK) under-predict leaching (they remove NO₃ as N₂O); the\n  **no-denit variants over-predict**, except **CK_ND**, which reproduces the observed final total\n  almost exactly (35.69 vs 35.7) and is \"excellent\" at the three critical times (NRMSE 9.4 %) — but\n  it over-leaches mid-series, so the denitrifying CK remains the better physical fit.",
   "- The **denitrifying variants** (ZK, FK, CK) under-predict leaching (they remove NO₃ as N₂O); the\n  **no-denit variants** (ZK_ND, FK_ND) **over-predict** (too much retained NO₃)."),
  ("**Denitrification-active set:** ZK, FK, CK. **No-denitrification set:** NR, ZK_ND, FK_ND, CK_ND.",
   "**Denitrification-active set:** ZK, FK, CK. **No-denitrification set:** NR, ZK_ND, FK_ND."),
  ("| **FK**  | 3.97 | 2.173 | 13.8 | **3.609** | **10.1** |\n| **CK**  | 2.31 | **1.591** | **10.1** | 3.919 | 11.0 |",
   "| **CK**  | 2.31 | **1.591** | **10.1** | 3.919 | 11.0 |\n| **FK**  | 3.97 | 2.173 | 13.8 | **3.609** | **10.1** |"),
  ("→ **CK_ND nails the observed total** (−0.01). Denitrifying variants under-leach (they remove N as\nN₂O); the no-denit variants except CK_ND over-leach (too much retained NO₃).",
   "→ **CK is closest to the observed total** (−2.31, −6.5 %), FK next (−3.97). Denitrifying variants\nunder-leach (they remove N as N₂O); the no-denit variants over-leach (too much retained NO₃)."),
  ("→ At days 2/10/24, **CK (NRMSE 10.1 %, \"good\") is the best denitrifying variant**; FK is \"good\"\n(13.8 %); CK_ND (no denit) is \"excellent\" (9.4 %). ZK and the no-denit FK_ND/ZK_ND are \"poor.\" The",
   "→ At days 2/10/24, **CK (NRMSE 10.1 %, \"good\") is the best-fitting variant**; FK is \"good\"\n(13.8 %). ZK and the no-denit FK_ND/ZK_ND are \"poor.\" The"),
 ],
 CMP_PY: [
  ("bullet(\"FK and CK are the best-fitting denitrifying variants; ZK is the worst — drop it. The ranking is stable across the final, three-time, and daily evaluations.\")",
   "bullet(\"CK (conditional kinetics) is the best-fitting variant overall — closest to the observed final total (−2.31 kg N/ha, −6.5%) and lowest RMSE at the three critical times (1.59, NRMSE 10.1%, “good”). FK is a close second (lowest daily RMSE, 3.61). ZK is the worst — drop it. The ranking is stable across the final, three-time, and daily evaluations.\")"),
  ("bullet(\"The denitrifying variants (ZK, FK, CK) under-predict leaching (they remove NO3 as N2O); the no-denit variants over-predict, except CK_ND, which reproduces the observed final total almost exactly (35.69 vs 35.7) and is “excellent” at the three critical times (NRMSE 9.4%) — but it over-leaches mid-series, so the denitrifying CK remains the better physical fit.\")",
   "bullet(\"The denitrifying variants (ZK, FK, CK) under-predict leaching (they remove NO3 as N2O); the no-denit variants (ZK_ND, FK_ND) over-predict (too much retained NO3).\")"),
  ("tnote=\"Denitrification-active set: ZK, FK, CK.   No-denitrification set: NR, ZK_ND, FK_ND, CK_ND.\")",
   "tnote=\"Denitrification-active set: ZK, FK, CK.   No-denitrification set: NR, ZK_ND, FK_ND.\")"),
  ("[\"FK\",\"3.97\",\"2.173\",\"13.8\",\"3.609\",\"10.1\"],[\"CK\",\"2.31\",\"1.591\",\"10.1\",\"3.919\",\"11.0\"],",
   "[\"CK\",\"2.31\",\"1.591\",\"10.1\",\"3.919\",\"11.0\"],[\"FK\",\"3.97\",\"2.173\",\"13.8\",\"3.609\",\"10.1\"],"),
  ("tnote=\"CK_ND nails the observed total (−0.01). Denitrifying variants under-leach; no-denit variants except CK_ND over-leach.\")",
   "tnote=\"CK is closest to the observed total (−2.31, −6.5%), FK next. Denitrifying variants under-leach; no-denit variants over-leach.\")"),
  ("is the best denitrifying variant; FK “good” (13.8%); \"\n          \"CK_ND “excellent” (9.4%). The before/after",
   "is the best-fitting variant; FK “good” (13.8%). \"\n          \"The before/after"),
 ],
 MB_MD: [
  ("reconstructed for all seven kinetic", "reconstructed for all six kinetic"),
  ("least (21.6); CK denitrifies little (2.5) so it leaches close to its no-denit twin (33.4 vs 35.7).",
   "least (21.6); CK denitrifies little (2.5) so it leaches most of its nitrate (33.4)."),
 ],
 MB_PY: [
  ("reconstructed for all seven kinetic", "reconstructed for all six kinetic"),
 ],
}

for path, reps in EDITS.items():
    t = open(path, encoding="utf-8").read()
    print(os.path.basename(path) + ":")
    for i, (old, new) in enumerate(reps, 1):
        if old in t:
            t = t.replace(old, new, 1); print(f"   ok   rep {i}")
        else:
            print(f"   !!! NOT FOUND rep {i}")
    open(path, "w", encoding="utf-8").write(t)
print("done.")
