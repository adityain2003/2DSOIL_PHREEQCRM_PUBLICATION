# _sweep_nitrate_variants.ps1
# Run the GENERIC 2DSOIL<->PhreeqcRM engine for all 6 nitrate-leaching kinetic
# variants, sequentially (shared bundle working dir + output files => cannot parallelize).
# Each variant: copy its .pqi into the bundle, set PQI_FILE, run the exe (CWD=bundle),
# then collect outputs into POST_PROCESSING/ANALYSIS/_data/VARIANT_RUNS/<VAR>/.
$ErrorActionPreference = "Stop"

$ROOT   = "C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION"
$GEN    = Join-Path $ROOT "2DSOIL_PHREEQCRM_MODEL"
$BUND   = Join-Path $GEN  "RUN_INPUTS\3_NITRATE_LEACHING"
$EXED   = Join-Path $GEN  "Maizsim_PhreeqcRM\soil source\x64\Debug\2dMAIZSIM.exe"
$SRCPQI = Join-Path $ROOT "OLD_VERSIONS\3_NITRATE_LEACHING\Maizsim_PhreeqcRM\soil source\x64\Debug"
$EXDIR  = Join-Path $BUND "PHREEQC_NITRATE_LEACHING_EXERCISE"
$OPT    = Join-Path $BUND "PHREEQC_OPTIONS.txt"
$OUTROOT= Join-Path $GEN  "POST_PROCESSING\ANALYSIS\_data\VARIANT_RUNS"
$SUMMARY= Join-Path $OUTROOT "_SWEEP_SUMMARY.txt"
$CSV    = Join-Path $OUTROOT "_SWEEP_SUMMARY.csv"

# variant code -> .pqi filename  (run order)
$variants = [ordered]@{
  "NR"    = "PHREEQCRM_RUNFILE_NITRATE_LEACHING_NO_REACTION.pqi"
  "ZK"    = "PHREEQCRM_RUNFILE_NITRATE_LEACHING_ZERO_ORDER.pqi"
  "ZK_ND" = "PHREEQCRM_RUNFILE_NITRATE_LEACHING_ZERO_ORDER_NO_DENIT.pqi"
  "FK"    = "PHREEQCRM_RUNFILE_NITRATE_LEACHING_FIRST_ORDER.pqi"
  "FK_ND" = "PHREEQCRM_RUNFILE_NITRATE_LEACHING_FIRST_ORDER_NO_DENIT.pqi"
  "CK"    = "PHREEQCRM_RUNFILE_NITRATE_LEACHING_CONDITIONAL_KINETICS.pqi"
}

# files to collect from the exercise subfolder and the bundle root (small, leaching-relevant only)
$exFiles  = @("DELHI_MURPHY.G05","DELHI_MURPHY.G06","DELHI_MURPHY.G04")
$rootFiles= @("PHREEQCRM_2DSOIL.chem.txt","PHREEQC_SPECIES_OUT.txt","PHREEQCRM_2DSOIL.log.txt","REACTION_TOTALS.txt")

New-Item -ItemType Directory -Force -Path $OUTROOT | Out-Null
Remove-Item -Force -ErrorAction SilentlyContinue (Join-Path $OUTROOT "_SWEEP_DONE.txt")
"# Nitrate-leaching variant sweep (generic engine)  started $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Set-Content $SUMMARY
"variant,pqi,exit_code,elapsed_s,g05_md5,g05_lastwrite,status" | Set-Content $CSV

foreach ($var in $variants.Keys) {
  $pqi = $variants[$var]
  $vdir = Join-Path $OUTROOT $var
  New-Item -ItemType Directory -Force -Path $vdir | Out-Null

  # 1. copy variant .pqi into the bundle (engine reads it from CWD)
  Copy-Item (Join-Path $SRCPQI $pqi) (Join-Path $BUND $pqi) -Force

  # 2. set PQI_FILE in the bundle's PHREEQC_OPTIONS.txt (only this line changes)
  $raw = Get-Content $OPT -Raw
  $new = [regex]::Replace($raw, '(?m)^(PQI_FILE\s+)\S+.*$', ('${1}' + $pqi))
  [System.IO.File]::WriteAllText($OPT, $new)

  # 3. run the engine, CWD = bundle
  $g05 = Join-Path $EXDIR "DELHI_MURPHY.G05"
  $stdout = Join-Path $vdir "run_stdout.txt"
  $stderr = Join-Path $vdir "run_stderr.txt"
  $t0 = Get-Date
  $status = "OK"; $exit = -999
  try {
    $p = Start-Process -FilePath $EXED -WorkingDirectory $BUND -NoNewWindow -Wait `
         -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
    $exit = $p.ExitCode
  } catch {
    $status = "LAUNCH_FAIL: $($_.Exception.Message)"
  }
  $elapsed = ((Get-Date) - $t0).TotalSeconds

  # 4. verify G05 freshly written
  if (-not (Test-Path $g05)) { $status = "NO_G05" }
  elseif ((Get-Item $g05).LastWriteTime -lt $t0) { $status = "STALE_G05" }
  if ($exit -ne 0 -and $status -eq "OK") { $status = "NONZERO_EXIT" }

  $md5 = if (Test-Path $g05) { (Get-FileHash $g05 -Algorithm MD5).Hash } else { "NA" }
  $lw  = if (Test-Path $g05) { (Get-Item $g05).LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss') } else { "NA" }

  # 5. collect outputs into the variant folder
  Copy-Item (Join-Path $BUND $pqi) (Join-Path $vdir $pqi) -Force
  Copy-Item $OPT (Join-Path $vdir "PHREEQC_OPTIONS.txt") -Force
  foreach ($f in $exFiles)   { $s = Join-Path $EXDIR $f; if (Test-Path $s) { Copy-Item $s (Join-Path $vdir $f) -Force } }
  foreach ($f in $rootFiles) { $s = Join-Path $BUND  $f; if (Test-Path $s) { Copy-Item $s (Join-Path $vdir $f) -Force } }

  $line = "{0,-6} {1,-58} exit={2} {3,7:N1}s  {4}  md5={5}" -f $var,$pqi,$exit,$elapsed,$status,$md5
  Add-Content $SUMMARY $line
  Add-Content $CSV ("{0},{1},{2},{3:N1},{4},{5},{6}" -f $var,$pqi,$exit,$elapsed,$md5,$lw,$status)
}

# restore bundle to committed state (FK active)
$raw = Get-Content $OPT -Raw
$new = [regex]::Replace($raw, '(?m)^(PQI_FILE\s+)\S+.*$', ('${1}' + "PHREEQCRM_RUNFILE_NITRATE_LEACHING_FIRST_ORDER.pqi"))
[System.IO.File]::WriteAllText($OPT, $new)

"# finished $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'); bundle PQI_FILE restored to FK" | Add-Content $SUMMARY
"DONE $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Set-Content (Join-Path $OUTROOT "_SWEEP_DONE.txt")
