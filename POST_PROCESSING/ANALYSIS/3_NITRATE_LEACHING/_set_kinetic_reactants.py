"""Set SELECTED_OUTPUT -kinetic_reactants to the FULL explicit list of every kinetic
reaction defined in each variant's .pqi, so PHREEQC emits a dk_<reaction> column for
each. Edits both the source Debug copies (what the sweep copies from) and the bundle.
NR (no kinetics) is left bare. Reaction names parsed from the .pqi KINETICS -formula blocks."""
import os, re, glob, sys
sys.path.insert(0, r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION\2DSOIL_PHREEQCRM_MODEL\POST_PROCESSING\ANALYSIS\3_NITRATE_LEACHING")
from analyze_reaction_totals import parse_pqi_formulas

DIRS = [
    r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION\OLD_VERSIONS\3_NITRATE_LEACHING\Maizsim_PhreeqcRM\soil source\x64\Debug",
    r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION\2DSOIL_PHREEQCRM_MODEL\RUN_INPUTS\3_NITRATE_LEACHING",
]
rx = re.compile(r"(?m)^(\s*)-kinetic_reactants\b.*$")

for d in DIRS:
    for pqi in sorted(glob.glob(os.path.join(d, "PHREEQCRM_RUNFILE_NITRATE_LEACHING_*.pqi"))):
        names = list(parse_pqi_formulas(pqi).keys())
        t = open(pqi, "r", errors="ignore").read()
        if not rx.search(t):
            print("NO -kinetic_reactants line:", os.path.basename(pqi)); continue
        repl = (lambda m: m.group(1) + "-kinetic_reactants"
                + ((" " + " ".join(names)) if names else ""))
        new = rx.sub(repl, t)
        with open(pqi, "w") as f:
            f.write(new)
        tag = os.path.basename(pqi).replace("PHREEQCRM_RUNFILE_NITRATE_LEACHING_", "").replace(".pqi", "")
        print(f"  {tag:28s} {len(names):2d} reactions  [{d.split(chr(92))[-3] if 'soil source' in d else '5_GENERIC bundle'}]")
print("done")
