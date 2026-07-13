"""Layer-wise NH4 and NO3 in mg/kg (initial and final), generic engine, nitrate-leaching.

INITIAL = the .nod file itself (the IC); it stores NH4/NO3 in mg/kg (soil, ion basis).
          2DSOIL reads it as  mol/L = mg/kg * BD / (MW*1000), MW = ion GFW.
          (The species-output's first record is NOT the IC - it is already post-leaching.)
FINAL   = PHREEQC_SPECIES_OUT.txt last time record. PhreeqcRM concentrations are mol/L of
          the 1-L batch cell (= mol per bulk litre; SOLN_VOL=1, CONC_BASIS=2), so
                mg(ion)/kg = c[mol/L] * MW * 1000 / BD ;  mg(N)/kg = mg(ion)/kg * 14.01/MW
          per-layer value = volume-weighted mean over the layer's 50 nodes.
Cross-checks: column totals (kg N/ha = mol(N)*280200) vs the documented budget; and NR's
          final NH4 must equal the initial NH4 (immobile, no reaction).
"""
import os, numpy as np, pandas as pd

ROOT   = r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION"
BUNDLE = os.path.join(ROOT, r"2DSOIL_PHREEQCRM_MODEL\RUN_INPUTS\3_NITRATE_LEACHING")
VR     = os.path.join(ROOT, r"2DSOIL_PHREEQCRM_MODEL\POST_PROCESSING\ANALYSIS\_data\VARIANT_RUNS")
NODF   = os.path.join(BUNDLE, "PHREEQC_NITRATE_LEACHING_EXERCISE", "DELHI_MURPHY.nod")
VARS   = ["NR","ZK","ZK_ND","FK","FK_ND","CK"]

MW   = {"[AMMONIUM]":18.04, "[NITRATE]":62.01}
MWN  = 14.01
BD_L = {1:1.58,2:1.58,3:1.58,4:1.58,5:1.58,6:1.58,7:1.65,8:1.65}   # per layer (validated vs .pqi)
DEPTH= {L:"%d-%d cm"%((L-1)*10,L*10) for L in range(1,9)}          # nominal 10-cm soil layers
SLAB = 1.0

def layer_of(node):  return (int(node)-1)//50 + 1                  # node 1..400 -> layer 1..8

def control_widths(vals):
    u=np.sort(np.unique(np.round(vals,5))); w=np.zeros_like(u)
    for i in range(len(u)):
        lo=u[i-1] if i>0 else u[0]; hi=u[i+1] if i<len(u)-1 else u[-1]; w[i]=(hi-lo)/2.0
    return dict(zip(u,w))

def node_vol(df):                                                  # bulk litres per node
    wx=control_widths(df["X"].values); wy=control_widths(df["Y"].values)
    xr=np.round(df["X"].values,5); yr=np.round(df["Y"].values,5)
    return np.array([wx[a]*wy[b] for a,b in zip(xr,yr)])*SLAB*0.001

def col_kgha(rec, comp):                                           # vol-weighted column total
    return float(np.sum(rec[comp].values*node_vol(rec)))*280200.0

def final_layers(rec):                                            # vol-wt layer-mean -> mg/kg
    rec=rec.copy(); rec["layer"]=rec["NODE"].apply(layer_of); rec["V"]=node_vol(rec)
    rows=[]
    for L,g in rec.groupby("layer"):
        bd=BD_L[L]; V=g["V"].values; r={"layer":L,"depth":DEPTH[L],"BD":bd}
        for comp in ("[AMMONIUM]","[NITRATE]"):
            c=np.sum(g[comp].values*V)/np.sum(V)
            ion=c*MW[comp]*1000.0/bd
            r[comp+"_ion"]=ion; r[comp+"_N"]=ion*MWN/MW[comp]
        rows.append(r)
    return pd.DataFrame(rows)

# ---------- .nod = initial condition ----------
nod=pd.read_csv(NODF, skiprows=1, sep=r"\s+", engine="python"); nod.columns=[c.strip() for c in nod.columns]
nod["layer"]=nod["Node"].apply(layer_of)
nod_lyr=nod.groupby("layer").agg(NH4=("NH4","mean"), NO3=("NO3","mean"))

# node geometry (time-invariant) from FK
fk=pd.read_csv(os.path.join(VR,"FK","PHREEQC_SPECIES_OUT.txt")); fk.columns=[c.strip() for c in fk.columns]
geo=fk[fk.TIME==fk.TIME.min()][["NODE","X","Y"]].reset_index(drop=True)
print("grid: Y(node1)=%.1f  Y(node400)=%.1f -> node1 = %s ; depth = %.0f-%.0f cm"
      %(geo[geo.NODE==1].Y.iloc[0],geo[geo.NODE==400].Y.iloc[0],
        "SURFACE" if geo[geo.NODE==1].Y.iloc[0]>geo[geo.NODE==400].Y.iloc[0] else "BOTTOM",
        geo.Y.max()-geo.Y.max(), geo.Y.max()-geo.Y.min()))

# initial table (ion basis from .nod, plus as-N)
ini=pd.DataFrame([dict(layer=L, depth=DEPTH[L], BD=BD_L[L],
        NH4ion=float(nod_lyr.loc[L,"NH4"]), NO3ion=float(nod_lyr.loc[L,"NO3"]),
        NH4N=float(nod_lyr.loc[L,"NH4"])*MWN/MW["[AMMONIUM]"],
        NO3N=float(nod_lyr.loc[L,"NO3"])*MWN/MW["[NITRATE]"]) for L in range(1,9)])

# verify initial column total (merge .nod mg/kg onto node geometry)
chk=geo.copy(); chk["layer"]=chk.NODE.apply(layer_of); chk["bd"]=chk.layer.map(BD_L)
chk=chk.merge(nod[["Node","NH4","NO3"]].rename(columns={"Node":"NODE"}), on="NODE")
Vb=node_vol(chk)
molNO3=np.sum(chk.NO3.values*chk.bd.values*Vb/(MW["[NITRATE]"]*1000.0))
molNH4=np.sum(chk.NH4.values*chk.bd.values*Vb/(MW["[AMMONIUM]"]*1000.0))

print("\n================ INITIAL  (from .nod = the IC)  mg/kg ================")
print("layer depth       BD   |  NH4_ion  NH4-N  |  NO3_ion  NO3-N")
for _,r in ini.iterrows():
    print("  %d   %-9s %.2f | %7.3f  %6.3f | %7.3f  %6.3f"%(r.layer,r.depth,r.BD,r.NH4ion,r.NH4N,r.NO3ion,r.NO3N))
print("  [check] initial column: NO3-N = %.2f , NH4-N = %.2f kg N/ha  (expect ~25.5 / ~3.9)"%(molNO3*280200,molNH4*280200))

# ---------- finals ----------
ini[["state","variant"]]=["initial","-"]
all_fin=[]
print("\n%-6s %8s %8s   (final column totals, kg N/ha)"%("var","NO3-N","NH4-N"))
for v in VARS:
    f=os.path.join(VR,v,"PHREEQC_SPECIES_OUT.txt")
    if not os.path.exists(f): continue
    sp=pd.read_csv(f); sp.columns=[c.strip() for c in sp.columns]
    rec=sp[sp.TIME==sp.TIME.max()]
    fl=final_layers(rec); fl["variant"]=v; all_fin.append(fl)
    print("%-6s %8.2f %8.2f"%(v,col_kgha(rec,"[NITRATE]"),col_kgha(rec,"[AMMONIUM]")))
fin=pd.concat(all_fin, ignore_index=True)

# NR immobile check
nrf=fin[fin.variant=="NR"].set_index("layer")["[AMMONIUM]_ion"]
print("  [check] NR final NH4_ion vs .nod NH4 (immobile):",
      ", ".join("%.2f/%.2f"%(nrf[L],nod_lyr.loc[L,"NH4"]) for L in range(1,9)))

# save tidy CSVs
ini.rename(columns={"NH4N":"NH4N_mgkg","NO3N":"NO3N_mgkg","NH4ion":"NH4ion_mgkg","NO3ion":"NO3ion_mgkg"}
   )[["state","variant","layer","depth","BD","NH4N_mgkg","NO3N_mgkg","NH4ion_mgkg","NO3ion_mgkg"]
   ].to_csv(os.path.join(VR,"_LAYERWISE_INITIAL_MGKG.csv"),index=False)
fo=fin.rename(columns={"[AMMONIUM]_N":"NH4N_mgkg","[NITRATE]_N":"NO3N_mgkg",
                       "[AMMONIUM]_ion":"NH4ion_mgkg","[NITRATE]_ion":"NO3ion_mgkg"})
fo["state"]="final"
fo[["state","variant","layer","depth","BD","NH4N_mgkg","NO3N_mgkg","NH4ion_mgkg","NO3ion_mgkg"]
   ].to_csv(os.path.join(VR,"_LAYERWISE_FINAL_MGKG.csv"),index=False)

for v in VARS:
    sub=fo[fo.variant==v]
    if sub.empty: continue
    print("\n========== FINAL  %-5s  mg/kg ==========="%v)
    print("layer depth       |  NH4-N   NO3-N  |  NH4_ion  NO3_ion")
    for _,r in sub.iterrows():
        print("  %d   %-9s | %6.3f  %6.3f | %7.3f  %7.3f"%(r.layer,r.depth,r.NH4N_mgkg,r.NO3N_mgkg,r.NH4ion_mgkg,r.NO3ion_mgkg))
print("\nSaved _LAYERWISE_INITIAL_MGKG.csv , _LAYERWISE_FINAL_MGKG.csv")
