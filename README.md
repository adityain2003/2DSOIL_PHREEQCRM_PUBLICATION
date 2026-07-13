# 2DSOIL ↔ PhreeqcRM — a generic, configuration-driven reactive-transport coupling

This work integrates **PhreeqcRM** with **2DSOIL** to model reactive chemical transport in soil.
PhreeqcRM (the reaction module of the USGS model **PHREEQC**) handles the geochemistry; **2DSOIL**
(a finite-element soil-process model) handles water flow and solute transport. Each problem
is defined entirely by input files.

> Methods, the coupling scheme, validation, and results are described in the accompanying manuscript.

---

## 1. Overview

This code runs PHREEQC-based chemistry with 2DSOIL water and solute transport, selected entirely
through input files. It is validated on three exercises — a transport benchmark, cation exchange,
and nitrate leaching.

## 2. Model components

| Component | Role | Origin |
|---|---|---|
| **2DSOIL** | 2-D finite-element solver for water flow, heat, solute transport, and gas — the transport engine (`soil source/`) | USDA-ARS |
| **PhreeqcRM** | Reaction module of PHREEQC v3; does all aqueous/solid-phase geochemistry | USGS (public domain / CC0) |

The coupling lives on the 2DSOIL side. Each timestep, 2DSOIL advects the mobile solutes; PhreeqcRM
then reacts every node's water in a batch step; the reacted totals are written back for the next
transport step.

## 3. Repository layout

```
2DSOIL_PHREEQCRM_MODEL/
├── README.md                     ← this file
│
├── Maizsim_PhreeqcRM/            ← the coupled model source (Visual Studio solution)
│   ├── maizsim07_PHREEQCRM.sln    ← top-level VS solution (crop + soil)
│   ├── soil source/               ← 2DSOIL + the coupling driver (Intel Fortran)
│   │   ├── PhreeqcRM.FOR           ← generic driver: PQ_RESOLVE_MAP / PQ_PUSH / round-trip / PQ_OUTPUT
│   │   ├── Read_Phreeqc_Options.for← PHREEQC_OPTIONS.txt parser
│   │   ├── phreeqc_options.ins     ← option COMMON blocks
│   │   ├── FERTIGATION.FOR         ← multi-solute surface boundary condition
│   │   ├── 2DMAIZSIM.FOR           ← orchestrator / gated timestep loop
│   │   ├── solmov.for              ← FEM advection–dispersion solute mover
│   │   ├── RM_interface.F90        ← PhreeqcRM Fortran bindings (the RM_* API)
│   │   └── …                       ← the rest of 2DSOIL
│   ├── crop source/               ← MAIZSIM crop model (C++; bundled, not invoked)
│   └── PHREEQCRM/                  ← vendored PhreeqcRM (CC0)
│
├── RUN_INPUTS/                   ← self-contained run bundles (one per exercise)
│   ├── 1_BENCHMARK/               ← inert / decay / decay+production transport
│   ├── 2_CATION_EXCHANGE/         ← Na/K/Ca exchange chromatography
│   └── 3_NITRATE_LEACHING/        ← Murphy-sand kinetic N cascade (6 variants)
│
└── POST_PROCESSING/
    ├── ANALYSIS/                  ← validators, budget scripts, error metrics
    │   ├── 1_BENCHMARK/  2_CATION_EXCHANGE/  3_NITRATE_LEACHING/
    │   └── _data/                 ← the committed simulation outputs the metrics are computed from
    └── FIGURES/                   ← publication figures (PNG / PDF / EPS / SVG)
```
