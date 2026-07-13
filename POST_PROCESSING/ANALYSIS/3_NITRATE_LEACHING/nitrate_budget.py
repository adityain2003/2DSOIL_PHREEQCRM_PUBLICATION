"""Mineral nitrate budget (kg N/ha), ignoring the large organic pool.

Nitrate balance:  initial_NO3 + nitrified - denitrified - leached = residual_NO3
=> recovered initial_NO3 = residual_NO3 + leached + denitrified - nitrified
(should be the SAME for every variant -- they share one initial condition.)

Inputs (already computed):
  _NITROGEN_BUDGET.csv   -> nit_kgha, den_kgha, leached_kgha
  _RESIDUAL_NITROGEN.csv -> res_no3 (final soil NO3), res_nh4 (final soil NH4)
"""
import os, pandas as pd
VR = r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION\2DSOIL_PHREEQCRM_MODEL\POST_PROCESSING\ANALYSIS\_data\VARIANT_RUNS"
nb = pd.read_csv(os.path.join(VR, "_NITROGEN_BUDGET.csv")).set_index("variant")
rn = pd.read_csv(os.path.join(VR, "_RESIDUAL_NITROGEN.csv")).set_index("variant")
VARS = ["NR","ZK","ZK_ND","FK","FK_ND","CK"]

print("="*100)
print("MINERAL NITRATE BUDGET (kg N/ha)   initial_NO3 + nitrified - denitrified - leached = residual_NO3")
print("="*100)
print("%-6s | %9s %9s %9s | %11s | %9s | %12s" %
      ("var","nitrified","denitrif.","leached","residNO3","residNH4","init_NO3*"))
print("-"*100)
rows=[]
for v in VARS:
    nit=nb.loc[v,"nit_kgha"]; den=nb.loc[v,"den_kgha"]; leach=nb.loc[v,"leached_kgha"]
    rno3=rn.loc[v,"res_no3"]; rnh4=rn.loc[v,"res_nh4"]
    init=rno3+leach+den-nit          # recovered initial nitrate
    rows.append((v,nit,den,leach,rno3,rnh4,init))
    print("%-6s | %9.2f %9.2f %9.2f | %11.2f | %9.2f | %12.2f" %
          (v,nit,den,leach,rno3,rnh4,init))
print("-"*100)
vals=[r[6] for r in rows]
print("* init_NO3 = residNO3 + leached + denitrified - nitrified  (should be identical across variants)")
print("  recovered initial nitrate: mean=%.2f  min=%.2f  max=%.2f  spread=%.2f kg N/ha (%.2f%%)"
      % (sum(vals)/len(vals), min(vals), max(vals), max(vals)-min(vals),
         100*(max(vals)-min(vals))/(sum(vals)/len(vals))))
pd.DataFrame(rows,columns=["variant","nitrified","denitrified","leached","resid_NO3","resid_NH4","init_NO3"]
            ).to_csv(os.path.join(VR,"_NITRATE_BUDGET.csv"),index=False)
print("\nSaved: _NITRATE_BUDGET.csv")
