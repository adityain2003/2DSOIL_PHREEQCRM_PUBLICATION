*||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||*
*                                                                      *
*     2DSOIL  - Numerical model of two-dimensional soil environment    *
*                           for field crops                            *
*                                                                      *
*                              Release 3.1.2.0                          *
*||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||*
*                                                                      *
*  GENERIC 2DSOIL_PHREEQCRM_MODEL main program. There is NO PQ_MODE: the       *
*  problem is defined entirely by run.dat, the .pqi, and               *
*  PHREEQC_OPTIONS.txt. Read_Phreeqc_Options() fills the option common  *
*  blocks; the divergent 2DSOIL module calls below are gated by the     *
*  orchestrator flags (PQ_USE_*) read from PHREEQC_OPTIONS.txt.         *
*||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||*

      Include 'public.ins'
      include 'puplant.ins'
      Include 'puweath.ins'
      Include 'nitvar.ins'
      Include 'PuSurface.ins'
      Include 'phreeqc_options.ins'

      character*132 RunDat
      integer len, status
      RunFile="Run.Dat"
      Call get_command_argument(1, RunDat, len, status)
      if (len.gt.0) then
        RunFile=RunDat
        endif

      Call Initialize()
      Call Read_Phreeqc_Options()
      Call Get_Grid_and_Boundary()
1     Call Synchronizer()


C
C SetSurfaceD --  reading daily weather
C SetSurfaceH --  reading hourly weather
      if ((HourlyWeather+DailyWeather.gt.1).or.
     !   ((HourlyWeather+DailyWeather).eq.0))then
              Write (*,*) "error in weather file type"
        Endif
      if (HourlyWeather.eq.1) Call SetSurfaceH()
      if (DailyWeather.eq.1) Call SetSurfaceD()
      Call SetTDB()
      Call AutoIrrigate()
      if (PQ_USE_MGMT   .gt. 0) Call Management()
      Call Irrigation()
      if (PQ_USE_PONDED .gt. 0) Call PondedIrrigationByHead()
      if (PQ_USE_PONDED .gt. 0) Call PondedIrrigationByFlux()
      if (PQ_USE_TILL   .gt. 0) Call TillageProcess

c     Call Drip()

      Starter=1.0D0

!      Call CROP(PCRL,MSW1, NumNP,NumSol,Sink(1),
!     !      NumBP,TNext(1),NumMod,Starter)
!      Call Carbon_Partitioning()
!      Call Rootgrow()
!      call Root_Mover()
!      Call WaterUptake()
!      Call SoluteUptake()
!      Call GasUptake()

c      Call SetBoundary()
cccz here we start to add surface process
cccz surface mulch (physical perspective)
!      Call Surface_Mulch_Process()
cccz surface water
!      Call Surface_Water_Balance_Adjustment()
!      Call SoilNitrogen()
      Call WaterMover()
      Call SoluteMover()
      Call HeatMover()
      Call GasMover()

!      WRITE(*,*) Time

      Call PHREEQC_RM()

      if (PQ_USE_FERT .gt. 0) CALL FERTIGATION()
      if (PQ_USE_NMB  .gt. 0) CALL Nitrogen_Mass_Balance()



C      Call MacroChem()
c      Call Water_Mass_Balance()
      if (outputSoilYes.gt.0) then
         Call Output()
        endif


      Goto 1
      End
