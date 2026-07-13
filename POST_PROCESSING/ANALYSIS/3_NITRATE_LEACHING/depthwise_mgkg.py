"""NH4 and NO3 at discrete depths 0,10,20,...,80 cm (initial and final), generic engine.

Grid is uniform 1 cm; nodes sit exactly at every target depth (depth = Ymax - Y).
A node at depth = 10*k cm is the BOTTOM row of layer k, so the step-function IC gives
the same value at 0 and 10 cm (both layer 1). Lateral (5 x-nodes) are identical -> mean.

INITIAL = .nod (mg/kg, ion basis).  FINAL = species-out last record, mol/L ->
          mg(ion)/kg = c*MW*1000/BD ;  mg(N)/kg = ion*14.01/MW.
"""
import os, numpy as np, pandas as pd

ROOT   = r"C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION"
BUNDLE = os.path.join(ROOT, r"2DSOIL_PHREEQCRM_MODEL\RUN_INPUTS\3_NITRATE_LEACHING")
VR     = os.path.join(ROOT, r"2DSOIL_PHREEQCRM_MODEL\POST_PROCESSING\ANALYSIS\_data\VARIANT_RUNS")
NODF   = os.path.join(BUNDLE, "PHREEQC_NITRATE_LEACHING_EXERCISE", "DELHI_MURPHY.nod")
VARS   = ["NR","ZK","ZK_ND","FK","FK_ND","CK"]
DEPTHS = [0,10,20,30,40,50,60,70,80]

MW  = {"[AMMONIUM]":18.04, "[NITRATE]":62.01}; MWN=14.01
BD_L= {1:1.58,2:1.58,3:1.58,4:1.58,5:1.58,6:1.58,7:1.65,8:1.65}
def layer_of(n): return (int(n)-1)//50 + 1

# geometry: map each target depth -> the node row (5 nodes) at that depth
fk=pd.read_csv(os.path.join(VR,"FK","PHREEQC_SPECIES_OUT.txt")); fk.columns=[c.strip() for c in fk.columns]
geo=fk[fk.TIME==fk.TIME.min()][["NODE","Y"]].reset_index(drop=True)
Ymax=geo.Y.max(); geo["depth"]=Ymax-geo.Y
depth_nodes={}
for t in DEPTHS:
    yr=geo.iloc[(geo.depth-t).abs().argsort()[:1]].Y.values[0]   # nearest existing Y
    nodes=sorted(geo[np.isclose(geo.Y,yr)].NODE.values)
    depth_nodes[t]=(nodes, layer_of(nodes[0]), Ymax-yr)
print("target -> nodes (layer, actual depth):")
for t in DEPTHS:
    nn,L,ad=depth_nodes[t]; print("  %2d cm -> nodes %d-%d  (L%d, %.0f cm, BD %.2f)"%(t,min(nn),max(nn),L,ad,BD_L[L]))

# initial from .nod
nod=pd.read_csv(NODF, skiprows=1, sep=r"\s+", engine="python"); nod.columns=[c.strip() for c in nod.columns]
nod=nod.set_index("Node")

def row(depthmap_vals):  # helper to format
    return depthmap_vals

ini=[]
for t in DEPTHS:
    nn,L,ad=depth_nodes[t]; bd=BD_L[L]
    nh4=nod.loc[nn,"NH4"].mean(); no3=nod.loc[nn,"NO3"].mean()
    ini.append(dict(depth=t,layer=L,BD=bd,NH4ion=nh4,NO3ion=no3,
                    NH4N=nh4*MWN/MW["[AMMONIUM]"],NO3N=no3*MWN/MW["[NITRATE]"]))
ini=pd.DataFrame(ini)

print("\n=============== INITIAL  at depth (mg/kg) ===============")
print("depth layer |  NH4-N   NO3-N  |  NH4_ion  NO3_ion")
for _,r in ini.iterrows():
    print(" %2dcm  L%d  | %6.3f  %6.3f | %7.3f  %7.3f"%(r.depth,r.layer,r.NH4N,r.NO3N,r.NH4ion,r.NO3ion))

# finals
finrows=[]
for v in VARS:
    f=os.path.join(VR,v,"PHREEQC_SPECIES_OUT.txt")
    if not os.path.exists(f): continue
    sp=pd.read_csv(f); sp.columns=[c.strip() for c in sp.columns]
    rec=sp[sp.TIME==sp.TIME.max()].set_index("NODE")
    for t in DEPTHS:
        nn,L,ad=depth_nodes[t]; bd=BD_L[L]
        for comp,tag in (("[AMMONIUM]","NH4"),("[NITRATE]","NO3")):
            c=rec.loc[nn,comp].mean(); ion=c*MW[comp]*1000.0/bd
            finrows.append(dict(variant=v,depth=t,layer=L,species=tag,
                                mgkg_N=ion*MWN/MW[comp], mgkg_ion=ion))
fin=pd.DataFrame(finrows)

# tidy wide CSVs (as N)
iout=ini.rename(columns={"NH4N":"NH4N_mgkg","NO3N":"NO3N_mgkg","NH4ion":"NH4ion_mgkg","NO3ion":"NO3ion_mgkg"})
iout.insert(0,"state","initial"); iout.insert(1,"variant","-")
iout.to_csv(os.path.join(VR,"_DEPTHWISE_INITIAL_MGKG.csv"),index=False)
fw=fin.pivot_table(index=["variant","depth","layer"],columns="species",values=["mgkg_N","mgkg_ion"]).reset_index()
fw.columns=["%s_%s"%(a,b) if b else a for a,b in fw.columns]
fw.to_csv(os.path.join(VR,"_DEPTHWISE_FINAL_MGKG.csv"),index=False)

for v in ["FK","CK"]:
    print("\n=============== FINAL  %s  at depth (mg/kg) ==============="%v)
    print("depth layer |  NH4-N   NO3-N  |  NH4_ion  NO3_ion")
    for t in DEPTHS:
        nn,L,ad=depth_nodes[t]
        a=fin[(fin.variant==v)&(fin.depth==t)&(fin.species=="NH4")].iloc[0]
        n=fin[(fin.variant==v)&(fin.depth==t)&(fin.species=="NO3")].iloc[0]
        print(" %2dcm  L%d  | %6.3f  %6.3f | %7.3f  %7.3f"%(t,L,a.mgkg_N,n.mgkg_N,a.mgkg_ion,n.mgkg_ion))

# compact NO3-N profile across all 7 variants
print("\n=============== FINAL NO3-N (mg N/kg) by depth x variant ===============")
print("depth | "+" ".join("%6s"%v for v in VARS))
for t in DEPTHS:
    vals=[fin[(fin.variant==v)&(fin.depth==t)&(fin.species=="NO3")].iloc[0].mgkg_N for v in VARS]
    print(" %2dcm | "%t+" ".join("%6.3f"%x for x in vals))
print("\nSaved _DEPTHWISE_INITIAL_MGKG.csv , _DEPTHWISE_FINAL_MGKG.csv")
