# _sweep_benchmark_cases.ps1
# Run the GENERIC 2DSOIL<->PhreeqcRM engine for the 3 benchmarking cases
# (1 = no reaction / Ogata-Banks, 2 = decay, 3 = decay + production), sequentially.
# Each case: set PQI_FILE in the bundle's PHREEQC_OPTIONS.txt, run the exe (CWD = bundle),
# then collect FERTIGATION_OUTPUT.txt into _data/BENCHMARK_RUNS/<CASE>/.
# The bundle's original PQI_FILE is restored at the end.
$ErrorActionPreference = "Stop"

$ROOT    = "C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION"
$GEN     = Join-Path $ROOT "2DSOIL_PHREEQCRM_MODEL"
$BUND    = Join-Path $GEN  "RUN_INPUTS\1_BENCHMARK"
$EXED    = Join-Path $GEN  "Maizsim_PhreeqcRM\soil source\x64\Debug\2dMAIZSIM.exe"
$OPT     = Join-Path $BUND "PHREEQC_OPTIONS.txt"
$OUTROOT = Join-Path $GEN  "POST_PROCESSING\ANALYSIS\_data\BENCHMARK_RUNS"
$SUMMARY = Join-Path $OUTROOT "_SWEEP_SUMMARY.txt"

$cases = [ordered]@{
  "CASE_1" = "PHREEQCRM_RUNFILE_BENCHMARKING_CASE_1.pqi"
  "CASE_2" = "PHREEQCRM_RUNFILE_BENCHMARKING_CASE_2.pqi"
  "CASE_3" = "PHREEQCRM_RUNFILE_BENCHMARKING_CASE_3.pqi"
}

# remember the bundle's current PQI_FILE so we can restore it
$origPqi = ([regex]::Match((Get-Content $OPT -Raw), '(?m)^PQI_FILE\s+(\S+)')).Groups[1].Value

New-Item -ItemType Directory -Force -Path $OUTROOT | Out-Null
Remove-Item -Force -ErrorAction SilentlyContinue (Join-Path $OUTROOT "_SWEEP_DONE.txt")
"# Benchmark case sweep (generic engine)  started $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Set-Content $SUMMARY

foreach ($c in $cases.Keys) {
  $pqi  = $cases[$c]
  $vdir = Join-Path $OUTROOT $c
  New-Item -ItemType Directory -Force -Path $vdir | Out-Null

  # set PQI_FILE (only this line changes)
  $raw = Get-Content $OPT -Raw
  $new = [regex]::Replace($raw, '(?m)^(PQI_FILE\s+)\S+.*$', ('${1}' + $pqi))
  [System.IO.File]::WriteAllText($OPT, $new)

  $fo = Join-Path $BUND "FERTIGATION_OUTPUT.txt"
  $t0 = Get-Date
  $status = "OK"; $exit = -999
  try {
    $p = Start-Process -FilePath $EXED -WorkingDirectory $BUND -NoNewWindow -Wait `
         -RedirectStandardOutput (Join-Path $vdir "run_stdout.txt") `
         -RedirectStandardError (Join-Path $vdir "run_stderr.txt") -PassThru
    $exit = $p.ExitCode
  } catch { $status = "LAUNCH_FAIL: $($_.Exception.Message)" }
  $elapsed = ((Get-Date) - $t0).TotalSeconds

  if (-not (Test-Path $fo)) { $status = "NO_FERTIGATION_OUTPUT" }
  elseif ((Get-Item $fo).LastWriteTime -lt $t0) { $status = "STALE_OUTPUT" }
  if ($exit -ne 0 -and $status -eq "OK") { $status = "NONZERO_EXIT" }

  if (Test-Path $fo) { Copy-Item $fo (Join-Path $vdir "FERTIGATION_OUTPUT.txt") -Force }
  Copy-Item $OPT (Join-Path $vdir "PHREEQC_OPTIONS.txt") -Force

  ("{0,-7} {1,-46} exit={2} {3,7:N1}s  {4}" -f $c,$pqi,$exit,$elapsed,$status) | Add-Content $SUMMARY
}

# restore bundle PQI_FILE
$raw = Get-Content $OPT -Raw
$new = [regex]::Replace($raw, '(?m)^(PQI_FILE\s+)\S+.*$', ('${1}' + $origPqi))
[System.IO.File]::WriteAllText($OPT, $new)

"# finished $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'); bundle PQI_FILE restored to $origPqi" | Add-Content $SUMMARY
"DONE" | Set-Content (Join-Path $OUTROOT "_SWEEP_DONE.txt")
Get-Content $SUMMARY
