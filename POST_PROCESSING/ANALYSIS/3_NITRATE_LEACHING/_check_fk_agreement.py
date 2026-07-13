"""Cross-check the two reporting paths on the FK bundle run:
  dk_ selected-output (per-reaction extents)  vs  component-delta budget.
PHREEQC dk_<rxn> = change in the reactant pool = -(reaction extent), so extent = -sum(dk).
"""
import pandas as pd
f = r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION\2DSOIL_PHREEQCRM_MODEL\RUN_INPUTS\3_NITRATE_LEACHING\REACTION_TOTALS.txt"
df = pd.read_csv(f); df.columns = [c.strip() for c in df.columns]
cum = df.sum(numeric_only=True)
dk = [c for c in df.columns if c.lower().startswith("dk_")]
def ext(pred):                                   # extent = -sum(dk) over matching cols
    return -sum(float(cum[c]) for c in dk if pred(c.upper()))
mn = ext(lambda u: "MINERAL" in u)
nt = ext(lambda u: "NITRIF" in u and "DENITRIF" not in u)
dn = ext(lambda u: "DENITRIF" in u)
dON, dNH4, dNO3, dN2O = (float(cum["d[%s]" % s]) for s in ["[ORGANIC_N]","[AMMONIUM]","[NITRATE]","[NITROUS_GAS]"])
K = 280200.0
print("FK cross-check (kg N/ha):     dk_ path   |  component-delta  | agree?")
for nm, a, b in [("mineralization", mn, -dON),
                 ("nitrification ", nt, -dON-dNH4),
                 ("denitrification", dn, 2*dN2O)]:
    rel = abs(a-b)/max(abs(a),abs(b),1e-30)
    print("  %-16s %8.2f   |   %8.2f       | rel=%.1e %s"
          % (nm, a*K, b*K, rel, "OK" if rel<2e-3 else "**"))
print("\nconservation (component delta == sum coef*extent):")
for nm, obs, pred in [("d[ORGANIC_N]", dON, -mn), ("d[AMMONIUM]", dNH4, mn-nt),
                      ("d[NITRATE]", dNO3, nt-dn), ("d[NITROUS_GAS]", dN2O, 0.5*dn)]:
    rel = abs(obs-pred)/max(abs(obs),abs(pred),1e-30)
    print("  %-15s obs=%11.4e pred=%11.4e rel=%.1e %s"
          % (nm, obs, pred, rel, "OK" if rel<2e-3 else "**"))
