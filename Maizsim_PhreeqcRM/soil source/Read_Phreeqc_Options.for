!   Read_Phreeqc_Options.for  (2DSOIL_PHREEQCRM_MODEL : generic 2DSOIL<->PhreeqcRM coupling)
!
!   Reads PHREEQC_OPTIONS.txt from the working directory ONCE at startup (called
!   from 2DMAIZSIM.FOR after Initialize()) and fills the shared option common
!   blocks /PQ_OPT/ and /PQ_OPT_C/ declared in phreeqc_options.ins.
!
!   Format: free key/value lines; blank lines and lines beginning with '#' are
!   ignored; unknown keys are skipped with a warning. Recognized keys:
!     PQI_FILE <name>            DATABASE <name>
!     UNITS_SOLUTION <i>         UNITS_PPASSEMBLAGE/EXCHANGE/SURFACE/GASPHASE/
!                                SSASSEMBLAGE/KINETICS <i>
!     COMPONENT_H2O <0|1>        PARTITION_UZ_SOLIDS <0|1>
!     SATURATION_MODE <1|2|3>    REP_VOL_MODE <1|2>      POROSITY_MODE <1|2>
!     CONC_BASIS <1|2>
!     CONC_UNIT_FACTOR <r>       SLAB_WIDTH <r>          STEP_SECONDS <r>
!     IC_SOURCE <NOD|PQI>
!     USE_MANAGEMENT/USE_PONDED/USE_TILLAGE/USE_FERTIGATION/USE_NMASSBALANCE <0|1>
!     REPORT_KINETICS <0|1>   KINETIC_PREFIX <str>   KINETIC_FILE <name>
!         (REPORT_KINETICS 1 -> per-step domain totals, in moles, of every
!          selected-output column starting with KINETIC_PREFIX [default dk_]
!          plus the net change of every component, written to KINETIC_FILE)
!     REPORT_REDOX <0|1>
!         (REPORT_REDOX 1 -> per-node pH, pe and Eh written each day to
!          PHREEQC_REDOX_OUT.txt; reads the pH/pe columns from the .pqi
!          SELECTED_OUTPUT [needs -pH true / -pe true] and converts pe to
!          Eh [mV] via Eh = pe*2.303*R*T/F. Reporting only; intensive ->
!          per node, never summed. Turns selected output on by itself.)
!     MAP <solute_index> <component_name> <role>
!         role = mobile | immobile | driver:ThNew    (solute_index = 0 if not mobile)
!
!   If PHREEQC_OPTIONS.txt is absent, safe defaults are used (mol/L, effective
!   saturation, no component map -> no solutes are coupled to 2DSOIL). A MAP
!   line whose component name is not in the .pqi aborts in PQ_RESOLVE_MAP,
!   listing the available component names.
!
      SUBROUTINE Read_Phreeqc_Options()
      INCLUDE 'phreeqc_options.ins'
      INTEGER :: iu, ios, ios2, n
      CHARACTER(LEN=200) :: line
      CHARACTER(LEN=40)  :: key, role, ics
      LOGICAL :: exst

!     ---- defaults ----
      PQ_PQI_FILE    = 'PHREEQCRM_RUNFILE.pqi'
      PQ_DATABASE    = 'Amm_2DSOIL.dat'
      PQ_UNITS_SOLN  = 2
      PQ_UNITS_PPA   = 1
      PQ_UNITS_EXCH  = 1
      PQ_UNITS_SURF  = 1
      PQ_UNITS_GAS   = 1
      PQ_UNITS_SS    = 1
      PQ_UNITS_KIN   = 1
      PQ_COMP_H2O    = 1
      PQ_PART_UZ     = 1
      PQ_SAT_MODE    = 1
      PQ_REPVOL_MODE = 1
      PQ_POR_MODE    = 1
      PQ_CONC_BASIS  = 1
      PQ_IC_SOURCE   = 1
      PQ_CONC_FACTOR = 1000.0d0
      PQ_SLAB_WIDTH  = 1.0d0
      PQ_STEP_SECS   = 86400.0d0
      PQ_USE_MGMT    = 0
      PQ_USE_PONDED  = 1
      PQ_USE_TILL    = 1
      PQ_USE_FERT    = 1
      PQ_USE_NMB     = 0
      PQ_NMAP        = 0
      PQ_REPORT_KIN  = 0
      PQ_REPORT_REDOX = 0
      PQ_KIN_PREFIX  = 'dk_'
      PQ_KIN_FILE    = 'REACTION_TOTALS.txt'

      iu = 1013
      INQUIRE(FILE='PHREEQC_OPTIONS.txt', EXIST=exst)
      IF (.NOT. exst) THEN
          WRITE(*,*) 'Read_Phreeqc_Options: PHREEQC_OPTIONS.txt not ',
     -               'found; using defaults.'
          RETURN
      END IF

      OPEN(UNIT=iu, FILE='PHREEQC_OPTIONS.txt', STATUS='OLD',
     -     IOSTAT=ios)
      IF (ios /= 0) RETURN

   10 CONTINUE
      READ(iu,'(A)',IOSTAT=ios) line
      IF (ios /= 0) GO TO 90
      line = ADJUSTL(line)
      IF (LEN_TRIM(line) == 0) GO TO 10
      IF (line(1:1) == '#')    GO TO 10
      READ(line,*,IOSTAT=ios2) key
      IF (ios2 /= 0) GO TO 10

      SELECT CASE (TRIM(key))
        CASE ('PQI_FILE')
          READ(line,*,IOSTAT=ios2) key, PQ_PQI_FILE
        CASE ('DATABASE')
          READ(line,*,IOSTAT=ios2) key, PQ_DATABASE
        CASE ('UNITS_SOLUTION')
          READ(line,*,IOSTAT=ios2) key, PQ_UNITS_SOLN
        CASE ('UNITS_PPASSEMBLAGE')
          READ(line,*,IOSTAT=ios2) key, PQ_UNITS_PPA
        CASE ('UNITS_EXCHANGE')
          READ(line,*,IOSTAT=ios2) key, PQ_UNITS_EXCH
        CASE ('UNITS_SURFACE')
          READ(line,*,IOSTAT=ios2) key, PQ_UNITS_SURF
        CASE ('UNITS_GASPHASE')
          READ(line,*,IOSTAT=ios2) key, PQ_UNITS_GAS
        CASE ('UNITS_SSASSEMBLAGE')
          READ(line,*,IOSTAT=ios2) key, PQ_UNITS_SS
        CASE ('UNITS_KINETICS')
          READ(line,*,IOSTAT=ios2) key, PQ_UNITS_KIN
        CASE ('COMPONENT_H2O')
          READ(line,*,IOSTAT=ios2) key, PQ_COMP_H2O
        CASE ('PARTITION_UZ_SOLIDS')
          READ(line,*,IOSTAT=ios2) key, PQ_PART_UZ
        CASE ('SATURATION_MODE')
          READ(line,*,IOSTAT=ios2) key, PQ_SAT_MODE
        CASE ('REP_VOL_MODE')
          READ(line,*,IOSTAT=ios2) key, PQ_REPVOL_MODE
        CASE ('POROSITY_MODE')
          READ(line,*,IOSTAT=ios2) key, PQ_POR_MODE
        CASE ('CONC_BASIS')
          READ(line,*,IOSTAT=ios2) key, PQ_CONC_BASIS
        CASE ('CONC_UNIT_FACTOR')
          READ(line,*,IOSTAT=ios2) key, PQ_CONC_FACTOR
        CASE ('SLAB_WIDTH')
          READ(line,*,IOSTAT=ios2) key, PQ_SLAB_WIDTH
        CASE ('STEP_SECONDS')
          READ(line,*,IOSTAT=ios2) key, PQ_STEP_SECS
        CASE ('IC_SOURCE')
          READ(line,*,IOSTAT=ios2) key, ics
          IF (TRIM(ics) == 'PQI' .OR. TRIM(ics) == 'pqi') THEN
              PQ_IC_SOURCE = 2
          ELSE
              PQ_IC_SOURCE = 1
          END IF
        CASE ('MAP')
          IF (PQ_NMAP < PQ_MAXMAP) THEN
              n = PQ_NMAP + 1
              role = ' '
              PQ_MAP_DRIVER(n) = 0
              READ(line,*,IOSTAT=ios2) key, PQ_MAP_SOLUTE(n),
     -             PQ_MAP_NAME(n), role
              IF (ios2 == 0) THEN
                  role = ADJUSTL(role)
                  IF (role(1:6) == 'driver') THEN
                      PQ_MAP_ROLE(n) = 2
                      IF (INDEX(role,'ThNew') > 0 .OR.
     -                    INDEX(role,'THETA') > 0) PQ_MAP_DRIVER(n) = 1
                  ELSE IF (role(1:8) == 'immobile') THEN
                      PQ_MAP_ROLE(n) = 3
                  ELSE
                      PQ_MAP_ROLE(n) = 1
                  END IF
                  PQ_NMAP = n
              END IF
          END IF
        CASE ('USE_MANAGEMENT')
          READ(line,*,IOSTAT=ios2) key, PQ_USE_MGMT
        CASE ('USE_PONDED')
          READ(line,*,IOSTAT=ios2) key, PQ_USE_PONDED
        CASE ('USE_TILLAGE')
          READ(line,*,IOSTAT=ios2) key, PQ_USE_TILL
        CASE ('USE_FERTIGATION')
          READ(line,*,IOSTAT=ios2) key, PQ_USE_FERT
        CASE ('USE_NMASSBALANCE')
          READ(line,*,IOSTAT=ios2) key, PQ_USE_NMB
        CASE ('REPORT_KINETICS')
          READ(line,*,IOSTAT=ios2) key, PQ_REPORT_KIN
        CASE ('REPORT_REDOX')
          READ(line,*,IOSTAT=ios2) key, PQ_REPORT_REDOX
        CASE ('KINETIC_PREFIX')
          READ(line,*,IOSTAT=ios2) key, PQ_KIN_PREFIX
        CASE ('KINETIC_FILE')
          READ(line,*,IOSTAT=ios2) key, PQ_KIN_FILE
        CASE DEFAULT
          WRITE(*,*) 'Read_Phreeqc_Options: ignoring unknown key: ',
     -               TRIM(key)
      END SELECT
      GO TO 10

   90 CONTINUE
      CLOSE(iu)

      WRITE(*,*) '================ PHREEQC_OPTIONS ================'
      WRITE(*,*) ' PQI_FILE = ', TRIM(PQ_PQI_FILE)
      WRITE(*,*) ' DATABASE = ', TRIM(PQ_DATABASE)
      WRITE(*,*) ' UNITS_SOLUTION=', PQ_UNITS_SOLN,
     -           '  SAT_MODE=', PQ_SAT_MODE,
     -           '  CONC_BASIS=', PQ_CONC_BASIS,
     -           '  PARTITION_UZ=', PQ_PART_UZ
      WRITE(*,*) ' REPVOL_MODE=', PQ_REPVOL_MODE,
     -           '  POR_MODE=', PQ_POR_MODE
      WRITE(*,*) ' REPORT_KINETICS=', PQ_REPORT_KIN,
     -           '  KINETIC_PREFIX=', TRIM(PQ_KIN_PREFIX),
     -           '  KINETIC_FILE=', TRIM(PQ_KIN_FILE)
      WRITE(*,*) ' REPORT_REDOX=', PQ_REPORT_REDOX,
     -           '  (-> PHREEQC_REDOX_OUT.txt: pH, pe, Eh per node)'
      WRITE(*,*) ' mapped components (', PQ_NMAP, '):'
      DO n = 1, PQ_NMAP
          WRITE(*,*) '   solute', PQ_MAP_SOLUTE(n), ' <- ',
     -               TRIM(PQ_MAP_NAME(n)), '  role', PQ_MAP_ROLE(n),
     -               '  driver', PQ_MAP_DRIVER(n)
      END DO
      WRITE(*,*) '================================================='
      RETURN
      END SUBROUTINE Read_Phreeqc_Options
