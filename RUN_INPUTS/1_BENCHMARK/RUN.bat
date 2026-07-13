@echo off
REM ============================================================
REM  Run the generic 2DSOIL-PhreeqcRM engine for THIS exercise.
REM  The chemistry is chosen by PHREEQC_OPTIONS.txt in this
REM  folder (the PQI_FILE option) -- there is no PQ_MODE.
REM
REM  IMPORTANT: build the solution in Visual Studio FIRST -
REM  the shipped 2dMAIZSIM.exe is stale (the sources changed).
REM
REM  Double-click this file, or run it from a terminal. It sets
REM  the working directory to this folder so run.dat, the .pqi,
REM  databases and the grid folder are all found here.
REM ============================================================
cd /d "%~dp0"
set "EXE=%~dp0..\..\Maizsim_PhreeqcRM\soil source\x64\Debug\2dMAIZSIM.exe"
if not exist "%EXE%" (
  echo ERROR: 2dMAIZSIM.exe not found - build the solution in Visual Studio first.
  echo   Expected at: "%EXE%"
  pause
  exit /b 1
)
echo Working directory : %CD%
echo Executable        : "%EXE%"
echo.
"%EXE%"
echo.
echo === Run finished. Output files are in this folder. ===
pause
