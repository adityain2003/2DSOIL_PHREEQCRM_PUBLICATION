!=====================================================================
!  PhreeqcRM.FOR  -  GENERIC 2DSOIL <-> PhreeqcRM coupling (2DSOIL_PHREEQCRM_MODEL)
!
!  A SINGLE, branch-free reactive-transport driver. The problem is defined
!  ENTIRELY by input files -- no PQ_MODE, no per-problem code:
!     run.dat            : 2DSOIL transport / grid / time / number of solutes
!     .pqi               : ALL PhreeqcRM chemistry (solutions, exchange, kinetics)
!     PHREEQC_OPTIONS.txt : coupling map + modes (read by Read_Phreeqc_Options
!                           into /PQ_OPT/, /PQ_OPT_C/ -- see phreeqc_options.ins)
!
!  Pattern = the USGS Advect_f90 component round-trip:
!     INIT : RunFile -> FindComponents -> GetComponents/GetGfw -> resolve MAP
!            -> InitialPhreeqc2Module (auto-detected reactant types) -> RunCells
!     STEP : set physical state (SAT_MODE) -> push mobile Conc + driver tracers
!            -> SetConcentrations -> RunCells -> pull mobile components into Conc
!
!  No species API, no hardcoded species names, no hardcoded molecular weights
!  (units come from RM_GetGfw + the units mode). One code path for all problems.
!=====================================================================
      SUBROUTINE PHREEQC_RM
      USE PhreeqcRM
      INCLUDE 'public.ins'
      INCLUDE 'nitvar.ins'
      INCLUDE 'phreeqc_options.ins'

!     thR (residual water content) is read from /WaterM/. dt,dtOld,tOld MUST be
!     DOUBLE PRECISION (exactly as in Watmov.for) -- without that, dt/dtOld/tOld
!     are implicit REAL*4 here, the thR/hSat offsets shift, and thR is read as
!     garbage. Total porosity is thSat(M) from /Materials/ (public.ins); GasMov.For
!     sets ThTot(i)=thSat(i). We deliberately DO NOT declare /GasM/ -- a truncated
!     'Common /GasM/ ThTot(NMatD)' would positionally alias ThTot onto /GasM/'s
!     leading ThOld (wrong porosity).
      DOUBLE PRECISION dt, dtOld, tOld
      Common /WaterM/ ThOld(NumNPD),hTemp(NumNPD),hOld(NumNPD),
     !          ConAxx(NumElD),ConAzz(NumElD),ConAxz(NumElD),
     !          MaxIt,TolTh,TolH,dt,dtOld,tOld,
     !          thR(NMatD),hSat(NMatD),
     !          isat(NumBPD),FreeD

      INTEGER :: I, K, M, STATUS, kk, idx
      INTEGER, SAVE :: ID, NCOMPS
      DOUBLE PRECISION, ALLOCATABLE, SAVE :: c(:,:)
      CHARACTER(LEN=:), ALLOCATABLE, SAVE :: comp_names(:)
      DOUBLE PRECISION, ALLOCATABLE, SAVE :: gfw(:)
      INTEGER, ALLOCATABLE :: ic1(:,:)
      DOUBLE PRECISION, ALLOCATABLE :: sat(:), por(:), repv(:)
      DOUBLE PRECISION, ALLOCATABLE :: temp(:), dens(:), pres(:)
      DOUBLE PRECISION, SAVE :: TIME_PHREEQ
      DOUBLE PRECISION :: TSTEP, thr_m
      LOGICAL, SAVE :: opened_out = .FALSE.
!     ---- generic kinetic-reaction / component-delta report state ----
      INTEGER, SAVE :: NSEL_COL = 0, NDK = 0
      INTEGER, ALLOCATABLE, SAVE :: DK_COL(:)
      CHARACTER(LEN=40), ALLOCATABLE, SAVE :: DK_NAME(:)
      DOUBLE PRECISION, ALLOCATABLE, SAVE :: SELOUT(:,:), c_in(:,:)
      CHARACTER(LEN=:), DIMENSION(:), ALLOCATABLE :: sel_head
      CHARACTER(LEN=80) :: htmp
      LOGICAL, SAVE :: rxn_opened = .FALSE.
      INTEGER :: lp, jj, ndkc
!     ---- generic per-node pH / pe / Eh (redox) report state ----
      INTEGER, SAVE :: PH_COL = 0, PE_COL = 0
      LOGICAL, SAVE :: redox_opened = .FALSE.

      ALLOCATE(sat(NUMNP), por(NUMNP), repv(NUMNP))
      ALLOCATE(temp(NUMNP), dens(NUMNP), pres(NUMNP))

!     =============== physical state (used at init AND every step) ============
      DO I = 1, NUMNP
          M = MatNumN(I)
          IF (PQ_SAT_MODE == 1) THEN
              thr_m  = thR(M)
              sat(I) = (ThNew(I)-thr_m)/(thSat(M)-thr_m)   ! effective saturation
          ELSE IF (PQ_SAT_MODE == 2) THEN
              sat(I) = ThNew(I)                            ! theta directly
          ELSE
              sat(I) = 1.0d0                               ! unity (batch)
          END IF
          IF (PQ_POR_MODE == 1) THEN
              por(I) = thSat(M)                           ! true porosity
          ELSE
              por(I) = 1.0d0                              ! unity (batch)
          END IF
          IF (PQ_REPVOL_MODE == 1) THEN
              repv(I) = (nodeArea(I)*PQ_SLAB_WIDTH)*0.001d0   ! cm^2*cm -> L
          ELSE
              repv(I) = 1.0d0
          END IF
          temp(I) = Tmpr(I)
          dens(I) = 1.0d0
          pres(I) = (hNew(I)*0.01d0*dens(I)*9.81d0)/101325.0d0  ! cm->m, ->atm
      END DO

!     ====================== INITIALIZATION (lInput==1) =======================
      IF (lInput == 1) THEN
          ID = RM_Create(NUMNP, 1)
          STATUS = RM_SetErrorOn(ID, 1)
          STATUS = RM_SetErrorHandlerMode(ID, 1)
          STATUS = RM_SetComponentH2O(ID, PQ_COMP_H2O)
          STATUS = RM_SetRebalanceFraction(ID, 0.5d0)
          STATUS = RM_SetRebalanceByCell(ID, 1)
          STATUS = RM_UseSolutionDensityVolume(ID, 0)
          STATUS = RM_SetPartitionUZSolids(ID, PQ_PART_UZ)
          STATUS = RM_SetUnitsSolution(ID, PQ_UNITS_SOLN)
          STATUS = RM_SetUnitsPPassemblage(ID, PQ_UNITS_PPA)
          STATUS = RM_SetUnitsExchange(ID, PQ_UNITS_EXCH)
          STATUS = RM_SetUnitsSurface(ID, PQ_UNITS_SURF)
          STATUS = RM_SetUnitsGasPhase(ID, PQ_UNITS_GAS)
          STATUS = RM_SetUnitsSSassemblage(ID, PQ_UNITS_SS)
          STATUS = RM_SetUnitsKinetics(ID, PQ_UNITS_KIN)
          STATUS = RM_SetFilePrefix(ID, "PHREEQCRM_2DSOIL")
          STATUS = RM_OpenFiles(ID)
          STATUS = RM_SetPrintChemistryOn(ID, 0, 1, 0)
          STATUS = RM_SetSpeciesSaveOn(ID, 0)
          IF (PQ_REPORT_KIN == 1 .OR. PQ_REPORT_REDOX == 1)
     -        STATUS = RM_SetSelectedOutputOn(ID,1)
          STATUS = RM_LoadDatabase(ID, TRIM(PQ_DATABASE))
          STATUS = RM_SetSaturationUser(ID, sat)
          STATUS = RM_SetPorosity(ID, por)
          STATUS = RM_SetRepresentativeVolume(ID, repv)
          STATUS = RM_SetTemperature(ID, temp)
          STATUS = RM_SetDensityUser(ID, dens)
          STATUS = RM_SetPressure(ID, pres)
!         ---- chemistry definition comes ENTIRELY from the .pqi ----
          STATUS = RM_RunFile(ID, 1, 1, 1, TRIM(PQ_PQI_FILE))
          STATUS = RM_RunString(ID, 1, 0, 1, "DELETE; -all")
          NCOMPS = RM_FindComponents(ID)
          WRITE(*,*) 'GENERIC PhreeqcRM driver: NCOMPS = ', NCOMPS
          STATUS = RM_GetComponents(ID, comp_names)
          STATUS = RM_GetGfw(ID, gfw)
          DO I = 1, NCOMPS
              WRITE(*,*) '   component ', I, ' = ', TRIM(comp_names(I)),
     -                   '  gfw=', gfw(I)
          END DO
!         ---- resolve the component<->solute map + conversion factors ----
          CALL PQ_RESOLVE_MAP(comp_names, NCOMPS, gfw)
!         ---- initial conditions: cell i <- reactant i; reactant types
!              are auto-detected from the .pqi (no per-problem code) ----
          ALLOCATE(ic1(NUMNP,7))
          ic1 = -1
          DO I = 1, NUMNP
              ic1(I,1) = I                                   ! SOLUTION
          END DO
          IF (RM_GetEquilibriumPhasesCount(ID) > 0) THEN
              DO I = 1, NUMNP; ic1(I,2) = I; END DO          ! EQUILIBRIUM_PHASES
          END IF
          IF (RM_GetExchangeSpeciesCount(ID) > 0) THEN
              DO I = 1, NUMNP; ic1(I,3) = I; END DO          ! EXCHANGE
          END IF
          IF (RM_GetSurfaceSpeciesCount(ID) > 0) THEN
              DO I = 1, NUMNP; ic1(I,4) = I; END DO          ! SURFACE
          END IF
          IF (RM_GetGasComponentsCount(ID) > 0) THEN
              DO I = 1, NUMNP; ic1(I,5) = I; END DO          ! GAS_PHASE
          END IF
          IF (RM_GetSolidSolutionComponentsCount(ID) > 0) THEN
              DO I = 1, NUMNP; ic1(I,6) = I; END DO          ! SOLID_SOLUTIONS
          END IF
          IF (RM_GetKineticReactionsCount(ID) > 0) THEN
              DO I = 1, NUMNP; ic1(I,7) = I; END DO          ! KINETICS
          END IF
          STATUS = RM_InitialPhreeqc2Module(ID, ic1)
          DEALLOCATE(ic1)
          TIME_PHREEQ = 0.0d0
          STATUS = RM_SetTime(ID, TIME_PHREEQ)
          STATUS = RM_SetTimeStep(ID, 0.0d0)
          STATUS = RM_RunCells(ID)
          ALLOCATE(c(NUMNP, NCOMPS))
          STATUS = RM_GetConcentrations(ID, c)
!         ---- generic selected-output report: locate dk_* / pH / pe cols ----
          IF (PQ_REPORT_KIN == 1 .OR. PQ_REPORT_REDOX == 1) THEN
              NSEL_COL = RM_GetSelectedOutputColumnCount(ID)
              lp = LEN_TRIM(PQ_KIN_PREFIX)
              NDK = 0
              PH_COL = 0
              PE_COL = 0
              IF (NSEL_COL > 0) THEN
                  STATUS = RM_GetSelectedOutputHeadings(ID, sel_head)
                  DO jj = 1, NSEL_COL
                      htmp = ADJUSTL(sel_head(jj))
                      IF (PQ_REPORT_KIN == 1 .AND. lp >= 1) THEN
                          IF (htmp(1:lp) == PQ_KIN_PREFIX(1:lp))
     -                        NDK = NDK + 1
                      END IF
                      IF (PQ_REPORT_REDOX == 1) THEN
                          IF (TRIM(htmp) == 'pH') PH_COL = jj
                          IF (TRIM(htmp) == 'pe') PE_COL = jj
                      END IF
                  END DO
              END IF
              ALLOCATE(DK_COL(MAX(NDK,1)), DK_NAME(MAX(NDK,1)))
              ALLOCATE(SELOUT(NUMNP, MAX(NSEL_COL,1)))
              ALLOCATE(c_in(NUMNP, NCOMPS))
              ndkc = 0
              IF (PQ_REPORT_KIN == 1 .AND. NSEL_COL > 0 .AND.
     -            lp >= 1) THEN
                  DO jj = 1, NSEL_COL
                      htmp = ADJUSTL(sel_head(jj))
                      IF (htmp(1:lp) == PQ_KIN_PREFIX(1:lp)) THEN
                          ndkc = ndkc + 1
                          DK_COL(ndkc)  = jj
                          DK_NAME(ndkc) = htmp
                      END IF
                  END DO
              END IF
              IF (PQ_REPORT_KIN == 1) WRITE(*,*)
     -            'REACTION REPORT: ', NDK, ' dk_ cols -> ',
     -            TRIM(PQ_KIN_FILE)
              IF (PQ_REPORT_REDOX == 1) WRITE(*,*)
     -            'REDOX REPORT: pH col=', PH_COL, ' pe col=', PE_COL,
     -            ' -> PHREEQC_REDOX_OUT.txt'
          END IF
!         ---- seed the initial condition in the chosen direction ----
          IF (PQ_IC_SOURCE == 2) THEN
!             PQI owns IC -> copy .pqi-defined totals into 2DSOIL Conc
              DO kk = 1, PQ_NMAP
                  IF (PQ_MAP_ROLE(kk) /= 1) CYCLE
                  idx = PQ_MAP_CIDX(kk)
                  K   = PQ_MAP_SOLUTE(kk)
                  IF (idx <= 0 .OR. K <= 0) CYCLE
                  DO I = 1, NUMNP                       ! mirror the step pull's CONC_BASIS convention
                      IF (PQ_CONC_BASIS == 2) THEN
                          IF (ThNew(I) > 1.0d-12) THEN
                              Conc(I,K) =
     -                            c(I,idx)/(ThNew(I)*PQ_MAP_CONV(kk))
                          END IF
                      ELSE
                          Conc(I,K) = c(I,idx)/PQ_MAP_CONV(kk)
                      END IF
                  END DO
              END DO
          ELSE
!             NOD owns IC -> push 2DSOIL Conc into PhreeqcRM, re-equilibrate
              CALL PQ_PUSH(c, NCOMPS)
              STATUS = RM_SetConcentrations(ID, c)
              STATUS = RM_RunCells(ID)
              STATUS = RM_GetConcentrations(ID, c)
          END IF

!     ========================= TIME STEP (lInput==0) =========================
      ELSE IF (lInput == 0) THEN
          TSTEP = Step * PQ_STEP_SECS                 ! 2DSOIL day-step -> seconds
          TIME_PHREEQ = TIME_PHREEQ + TSTEP
          STATUS = RM_SetTime(ID, TIME_PHREEQ)
          STATUS = RM_SetTimeStep(ID, TSTEP)
          STATUS = RM_SetSaturationUser(ID, sat)
          STATUS = RM_SetPorosity(ID, por)
          STATUS = RM_SetRepresentativeVolume(ID, repv)
          STATUS = RM_SetTemperature(ID, temp)
          STATUS = RM_SetDensityUser(ID, dens)
          STATUS = RM_SetPressure(ID, pres)
!         refresh c so immobile columns stay current, then overwrite mobile+driver
          STATUS = RM_GetConcentrations(ID, c)
          CALL PQ_PUSH(c, NCOMPS)
          STATUS = RM_SetConcentrations(ID, c)
          IF (PQ_REPORT_KIN == 1 .AND. ALLOCATED(c_in)) c_in = c
          STATUS = RM_RunCells(ID)
          STATUS = RM_GetConcentrations(ID, c)
!         generic per-step diagnostics (reporting only): pull the selected
!         output once if either the kinetic or the redox report needs it
          IF ((PQ_REPORT_KIN == 1 .OR. PQ_REPORT_REDOX == 1) .AND.
     -        ALLOCATED(SELOUT)) THEN
              IF (NDK > 0 .OR. PH_COL > 0 .OR. PE_COL > 0)
     -            STATUS = RM_GetSelectedOutput(ID, SELOUT)
          END IF
          IF (PQ_REPORT_KIN == 1 .AND. ALLOCATED(c_in)) THEN
              CALL PQ_REACTION_REPORT(c, c_in, NCOMPS, comp_names,
     -            SELOUT, MAX(NSEL_COL,1), DK_COL, DK_NAME, NDK,
     -            TIME_PHREEQ, PQ_KIN_FILE, rxn_opened)
          END IF
          IF (PQ_REPORT_REDOX == 1 .AND. ALLOCATED(SELOUT)) THEN
              CALL PQ_REDOX_REPORT(SELOUT, MAX(NSEL_COL,1), PH_COL,
     -            PE_COL, temp, TIME_PHREEQ, redox_opened)
          END IF
!         pull reacted mobile totals back into 2DSOIL Conc
          DO kk = 1, PQ_NMAP
              IF (PQ_MAP_ROLE(kk) /= 1) CYCLE
              idx = PQ_MAP_CIDX(kk)
              K   = PQ_MAP_SOLUTE(kk)
              IF (idx <= 0 .OR. K <= 0) CYCLE
              DO I = 1, NUMNP
                  IF (PQ_CONC_BASIS == 2) THEN
                      IF (ThNew(I) > 1.0d-12) THEN
                          Conc(I,K) = c(I,idx)/(ThNew(I)*PQ_MAP_CONV(kk))
                      END IF
                  ELSE
                      Conc(I,K) = c(I,idx)/PQ_MAP_CONV(kk)
                  END IF
              END DO
          END DO
          CALL PQ_OUTPUT(c, NCOMPS, comp_names, TIME_PHREEQ, opened_out)
      END IF

      DEALLOCATE(sat, por, repv, temp, dens, pres)
      RETURN
      END SUBROUTINE PHREEQC_RM


!=====================================================================
!  PQ_RESOLVE_MAP : match each PHREEQC_OPTIONS MAP name to a PhreeqcRM
!  component index and compute its unit-conversion factor from the GFW
!  and the solution-units mode. Aborts (listing the available names) on a
!  name mismatch -- the user's safety net for .pqi / options typos.
!=====================================================================
      SUBROUTINE PQ_RESOLVE_MAP(comp_names, ncomps, gfw)
      INCLUDE 'phreeqc_options.ins'
      INTEGER, INTENT(IN) :: ncomps
      CHARACTER(LEN=*), INTENT(IN) :: comp_names(ncomps)
      DOUBLE PRECISION, INTENT(IN) :: gfw(ncomps)
      INTEGER :: kk, j
      DO kk = 1, PQ_NMAP
          PQ_MAP_CIDX(kk) = 0
          DO j = 1, ncomps
              IF (TRIM(ADJUSTL(comp_names(j))) ==
     -            TRIM(ADJUSTL(PQ_MAP_NAME(kk)))) THEN
                  PQ_MAP_CIDX(kk) = j
                  EXIT
              END IF
          END DO
          IF (PQ_MAP_CIDX(kk) == 0) THEN
              WRITE(*,*) 'PHREEQC MAP ERROR: component not found: ',
     -                   TRIM(PQ_MAP_NAME(kk))
              WRITE(*,*) 'Available PhreeqcRM components are:'
              DO j = 1, ncomps
                  WRITE(*,*) '   ', TRIM(comp_names(j))
              END DO
              STOP 'PHREEQC_OPTIONS MAP: component name mismatch'
          END IF
          IF (PQ_UNITS_SOLN == 2) THEN
              PQ_MAP_CONV(kk) =
     -            1.0d0/(gfw(PQ_MAP_CIDX(kk))*PQ_CONC_FACTOR)
          ELSE
              PQ_MAP_CONV(kk) = 1.0d0/PQ_CONC_FACTOR
          END IF
      END DO
      RETURN
      END SUBROUTINE PQ_RESOLVE_MAP


!=====================================================================
!  PQ_PUSH : overwrite the mobile + driver columns of the component
!  array c from 2DSOIL state. Immobile columns are left untouched
!  (they carry whatever RM_GetConcentrations returned).
!=====================================================================
      SUBROUTINE PQ_PUSH(c, ncomps)
      INCLUDE 'public.ins'
      INCLUDE 'phreeqc_options.ins'
      INTEGER, INTENT(IN) :: ncomps
      DOUBLE PRECISION, INTENT(INOUT) :: c(NUMNP, ncomps)
      INTEGER :: kk, I, K, idx
      DO kk = 1, PQ_NMAP
          idx = PQ_MAP_CIDX(kk)
          IF (idx <= 0) CYCLE
          IF (PQ_MAP_ROLE(kk) == 1) THEN              ! mobile
              K = PQ_MAP_SOLUTE(kk)
              IF (K <= 0) CYCLE
              DO I = 1, NUMNP
                  IF (PQ_CONC_BASIS == 2) THEN
                      c(I,idx) = ThNew(I)*Conc(I,K)*PQ_MAP_CONV(kk)
                  ELSE
                      c(I,idx) = Conc(I,K)*PQ_MAP_CONV(kk)
                  END IF
              END DO
          ELSE IF (PQ_MAP_ROLE(kk) == 2) THEN         ! driver tracer
              IF (PQ_MAP_DRIVER(kk) == 1) THEN         ! 1 = ThNew
                  DO I = 1, NUMNP
                      c(I,idx) = ThNew(I)
                  END DO
              END IF
          END IF
      END DO
      RETURN
      END SUBROUTINE PQ_PUSH


!=====================================================================
!  PQ_OUTPUT : generic diagnostic dump of ALL component concentrations
!  at every node, written at hour 0 of each day to PHREEQC_SPECIES_OUT.txt
!  (CSV, header from the component names). Reporting only -- never read
!  back into state.
!=====================================================================
      SUBROUTINE PQ_OUTPUT(c, ncomps, comp_names, tphreeq, opened)
      INCLUDE 'public.ins'
      INTEGER, INTENT(IN) :: ncomps
      DOUBLE PRECISION, INTENT(IN) :: c(NUMNP, ncomps)
      CHARACTER(LEN=*), INTENT(IN) :: comp_names(ncomps)
      DOUBLE PRECISION, INTENT(IN) :: tphreeq
      LOGICAL, INTENT(INOUT) :: opened
      INTEGER :: I, J
      IF (.NOT. opened) THEN
          OPEN(UNIT=1001, FILE='PHREEQC_SPECIES_OUT.txt',
     -         STATUS='UNKNOWN')
          WRITE(1001,'(A)',ADVANCE='NO') 'NODE,TIME,X,Y'
          DO J = 1, ncomps
              WRITE(1001,'(A,A)',ADVANCE='NO') ',', TRIM(comp_names(J))
          END DO
          WRITE(1001,'(A)') ''
          opened = .TRUE.
      END IF
      IF (MOD(INT(tphreeq),86400) == 0) THEN
          DO I = 1, NUMNP
              WRITE(1001,'(I6,A,E15.7,A,F10.3,A,F10.3)',ADVANCE='NO')
     -            I, ',', tphreeq, ',', x(I), ',', y(I)
              DO J = 1, ncomps
                  WRITE(1001,'(A,E15.7)',ADVANCE='NO') ',', c(I,J)
              END DO
              WRITE(1001,'(A)') ''
          END DO
      END IF
      RETURN
      END SUBROUTINE PQ_OUTPUT


!=====================================================================
!  PQ_REACTION_REPORT : generic per-step mass-balance diagnostics.
!  Writes ONE row per time step (domain totals, in MOLES):
!    - for every selected-output column whose heading starts with the
!      configured prefix (default 'dk_'): moles of that kinetic reaction
!      reacted this step, summed over all nodes;
!    - for every PhreeqcRM component: the net change produced by the
!      reaction step (c_out - c_in), summed over all nodes (d[<name>]).
!  Domain weight W_i = nodeArea(i)*SLAB_WIDTH*0.001 (bulk cell volume, L).
!  W_i has no theta; theta enters c via the theta-weighted push (CONC_BASIS=2),
!  so these totals are mass-consistent with the leached/transported solute. NOTE
!  PHREEQC dk_<rxn> = change in the reactant pool = -(reaction extent), so the
!  reconciliation identity is  d[X] == -sum over reactions of (formula_coef * dk).
!  Reporting only -- never read back into 2DSOIL state.
!=====================================================================
      SUBROUTINE PQ_REACTION_REPORT(c_out, c_in, ncomps, comp_names,
     -    selout, nsel, dk_col, dk_name, ndk, tphreeq, fname, opened)
      INCLUDE 'public.ins'
      INCLUDE 'phreeqc_options.ins'
      INTEGER, INTENT(IN) :: ncomps, nsel, ndk
      DOUBLE PRECISION, INTENT(IN) :: c_out(NUMNP,ncomps)
      DOUBLE PRECISION, INTENT(IN) :: c_in(NUMNP,ncomps)
      DOUBLE PRECISION, INTENT(IN) :: selout(NUMNP,nsel)
      INTEGER, INTENT(IN) :: dk_col(*)
      CHARACTER(LEN=*), INTENT(IN) :: comp_names(ncomps), dk_name(*)
      DOUBLE PRECISION, INTENT(IN) :: tphreeq
      CHARACTER(LEN=*), INTENT(IN) :: fname
      LOGICAL, INTENT(INOUT) :: opened
      INTEGER :: I, J, M
      DOUBLE PRECISION :: W, tot
      IF (.NOT. opened) THEN
          OPEN(UNIT=1051, FILE=TRIM(fname), STATUS='UNKNOWN')
          WRITE(1051,'(A)',ADVANCE='NO') 'TIME_S'
          DO M = 1, ndk
              WRITE(1051,'(A,A)',ADVANCE='NO') ',', TRIM(dk_name(M))
          END DO
          DO J = 1, ncomps
              WRITE(1051,'(A,A,A)',ADVANCE='NO')
     -            ',d[', TRIM(comp_names(J)), ']'
          END DO
          WRITE(1051,'(A)') ''
          opened = .TRUE.
      END IF
      WRITE(1051,'(E16.8)',ADVANCE='NO') tphreeq
      DO M = 1, ndk
          tot = 0.0d0
          DO I = 1, NUMNP
              W = nodeArea(I)*PQ_SLAB_WIDTH*0.001d0
              tot = tot + selout(I,dk_col(M))*W
          END DO
          WRITE(1051,'(A,E16.8)',ADVANCE='NO') ',', tot
      END DO
      DO J = 1, ncomps
          tot = 0.0d0
          DO I = 1, NUMNP
              W = nodeArea(I)*PQ_SLAB_WIDTH*0.001d0
              tot = tot + (c_out(I,J)-c_in(I,J))*W
          END DO
          WRITE(1051,'(A,E16.8)',ADVANCE='NO') ',', tot
      END DO
      WRITE(1051,'(A)') ''
      RETURN
      END SUBROUTINE PQ_REACTION_REPORT


!=====================================================================
!  PQ_REDOX_REPORT : generic per-node redox dump (reporting only).
!  Reads the pH and pe columns out of the PhreeqcRM selected-output
!  array (their indices located once at init by exact heading match),
!  converts pe -> Eh via the Nernst relation Eh = pe*(2.303*R*T/F),
!  and writes one row per node at hour 0 of each day to
!  PHREEQC_REDOX_OUT.txt (CSV: NODE,TIME,X,Y,pH,pe,Eh_mV).
!  pH/pe/Eh are INTENSIVE -> reported per node, never summed or
!  area-weighted (unlike the extensive moles in PQ_REACTION_REPORT).
!  T (per cell, Celsius) is the same temperature pushed to PhreeqcRM
!  via RM_SetTemperature. Columns absent from the .pqi SELECTED_OUTPUT
!  (ph_col / pe_col == 0) are written as -999. Never read back to state.
!=====================================================================
      SUBROUTINE PQ_REDOX_REPORT(selout, nsel, ph_col, pe_col, tcel,
     -    tphreeq, opened)
      INCLUDE 'public.ins'
      INTEGER, INTENT(IN) :: nsel, ph_col, pe_col
      DOUBLE PRECISION, INTENT(IN) :: selout(NUMNP, nsel)
      DOUBLE PRECISION, INTENT(IN) :: tcel(NUMNP)
      DOUBLE PRECISION, INTENT(IN) :: tphreeq
      LOGICAL, INTENT(INOUT) :: opened
      INTEGER :: I
      DOUBLE PRECISION :: phv, pev, ehv, tk
      IF (.NOT. opened) THEN
          OPEN(UNIT=1071, FILE='PHREEQC_REDOX_OUT.txt',
     -         STATUS='UNKNOWN')
          WRITE(1071,'(A)') 'NODE,TIME,X,Y,pH,pe,Eh_mV'
          opened = .TRUE.
      END IF
      IF (MOD(INT(tphreeq),86400) == 0) THEN
          DO I = 1, NUMNP
              phv = -999.0d0
              pev = -999.0d0
              ehv = -999.0d0
              IF (ph_col > 0) phv = selout(I, ph_col)
              IF (pe_col > 0) THEN
                  pev = selout(I, pe_col)
                  tk  = tcel(I) + 273.15d0
                  ehv = pev * (1000.0d0*2.303d0*8.3144d0*tk)/96484.0d0
              END IF
              WRITE(1071,'(I6,A,E15.7,A,F10.3,A,F10.3)',ADVANCE='NO')
     -            I, ',', tphreeq, ',', x(I), ',', y(I)
              WRITE(1071,'(A,F10.4,A,F10.4,A,F12.4)')
     -            ',', phv, ',', pev, ',', ehv
          END DO
      END IF
      RETURN
      END SUBROUTINE PQ_REDOX_REPORT
