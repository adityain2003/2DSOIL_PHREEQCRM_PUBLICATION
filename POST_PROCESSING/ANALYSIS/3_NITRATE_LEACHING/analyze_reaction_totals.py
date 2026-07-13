"""Post-process the generic engine's per-step reaction report (REACTION_TOTALS.txt)
produced when PHREEQC_OPTIONS has REPORT_KINETICS 1.

Each row = one time step; columns = TIME_S, dk_<reaction> (moles reacted that step,
domain total) ..., d[<component>] (net reaction change that step, domain total) ...

For each variant under POST_PROCESSING/ANALYSIS/_data/VARIANT_RUNS/<VAR>/ it:
  1. sums dk_ columns by reaction FAMILY (text before _LAYER) -> cumulative moles
     of mineralization / nitrification / denitrification (etc.);
  2. reports cumulative component net changes d[...];
  3. CONSERVATION CHECK: parses the variant's .pqi -formula stoichiometry and
     verifies, for every component, that  cum d[comp] == sum_reactions(coef*cum_dk)
     to a relative tolerance -- a generic, name-agnostic mass-balance test.

Outputs _REACTION_SUMMARY.csv and prints the conservation report. Runs harmlessly
before any rerun (skips variants with no REACTION_TOTALS.txt yet).
"""
import os, re, glob
import pandas as pd

ROOT = r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION"
VR   = os.path.join(ROOT, "2DSOIL_PHREEQCRM_MODEL", "POST_PROCESSING", "ANALYSIS", "_data", "VARIANT_RUNS")
VARS = ["NR", "ZK", "ZK_ND", "FK", "FK_ND", "CK"]
TOL  = 1e-3   # relative tolerance for the conservation identity
ABSTOL = 1e-6 # mol: components below this (H2O/O/THETA_VMC noise) are treated as zero


def parse_pqi_formulas(pqi_path):
    """reaction_name -> {component: stoichiometric coef} from KINETICS -formula lines."""
    coef = {}
    if not pqi_path or not os.path.exists(pqi_path):
        return coef
    name = None
    for raw in open(pqi_path, "r", errors="ignore"):
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        m = re.match(r"-formula\s+(.*)$", s, re.IGNORECASE)
        if m and name:
            toks = m.group(1).split()
            d = {}
            i = 0
            while i < len(toks):
                t = toks[i]
                if t.startswith("#"):
                    break
                if t.startswith("[") and i + 1 < len(toks):
                    try:
                        d[t] = float(toks[i + 1]); i += 2; continue
                    except ValueError:
                        pass
                i += 1
            coef[name] = d
            name = None
        elif re.match(r"^[A-Za-z]\w*$", s):
            name = s            # a bare token line = a kinetic reaction name
    return coef


def family(dk_heading):
    """dk_DENITRIFICATION_LAYER_3 -> DENITRIFICATION ; dk_FOO -> FOO."""
    nm = dk_heading[3:] if dk_heading.lower().startswith("dk_") else dk_heading
    return re.split(r"_LAYER", nm, flags=re.IGNORECASE)[0]


def main():
    rows = []
    for v in VARS:
        f = os.path.join(VR, v, "REACTION_TOTALS.txt")
        if not os.path.exists(f):
            print(f"  [{v}] no REACTION_TOTALS.txt yet (rebuild engine + rerun sweep)")
            continue
        df = pd.read_csv(f)
        df.columns = [c.strip() for c in df.columns]
        dk_cols = [c for c in df.columns if c.lower().startswith("dk_")]
        dcomp   = [c for c in df.columns if c.startswith("d[")]
        cum = df.sum(numeric_only=True)          # per-step totals -> cumulative end-of-run

        # PHREEQC dk_<rxn> = change in the reactant pool = -(reaction extent)
        fam = {}
        for c in dk_cols:
            fam[family(c)] = fam.get(family(c), 0.0) - float(cum[c])
        comp = {c[2:-1]: float(cum[c]) for c in dcomp}    # 'd[NITRATE]' -> 'NITRATE'

        print("=" * 78)
        print(f"[{v}]  cumulative reaction extents (mol, domain total):")
        for k in sorted(fam):
            print(f"    {k:18s} {fam[k]:14.6e}")
        print("   component net change d[...] (mol):")
        for k in sorted(comp):
            print(f"    {k:18s} {comp[k]:14.6e}")

        # ---- conservation check via .pqi -formula ----
        pqi = None
        cands = glob.glob(os.path.join(VR, v, "PHREEQCRM_RUNFILE_*.pqi"))
        if cands:
            pqi = cands[0]
        coef = parse_pqi_formulas(pqi)
        cum_dk = {c[3:]: -float(cum[c]) for c in dk_cols}  # reaction extent = -(dk reactant change)
        print(f"   conservation check  d[comp] == sum(coef*dk)   [tol {TOL:.0e}]:")
        allok = True
        for cname, cval in comp.items():
            key = cname            # cname already includes brackets, e.g. [ORGANIC_N]
            pred = sum(d[key] * cum_dk.get(rxn, 0.0)
                       for rxn, d in coef.items() if key in d)
            denom = max(abs(cval), abs(pred), 1e-30)
            rel = abs(cval - pred) / denom
            ok = rel < TOL or denom < ABSTOL
            allok = allok and ok
            print(f"    d[{cname:14s}] obs={cval:13.6e} pred={pred:13.6e} "
                  f"rel={rel:8.1e} {'ok' if ok else '** FAIL'}")
        print(f"   ==> {'PASS' if allok else 'FAIL'}")

        row = {"variant": v}
        row.update({f"cum_{k}": fam[k] for k in fam})
        row.update({f"d_{k}": comp[k] for k in comp})
        row["conservation"] = "PASS" if allok else "FAIL"
        rows.append(row)

    if rows:
        pd.DataFrame(rows).to_csv(os.path.join(VR, "_REACTION_SUMMARY.csv"), index=False)
        print("\nSaved: _REACTION_SUMMARY.csv")
    else:
        print("\nNo REACTION_TOTALS.txt files found yet. Build the engine in VS2022, "
              "rerun _sweep_nitrate_variants.ps1, then run this script.")


if __name__ == "__main__":
    main()
