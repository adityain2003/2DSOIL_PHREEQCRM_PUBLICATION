# _run_cation_generic.ps1
# Run the GENERIC 2DSOIL<->PhreeqcRM engine ONCE for the cation-exchange problem
# (single configuration, no variants), CWD = bundle, and collect FERTIGATION_OUTPUT.txt
# into _data/CATION_RUN/. The bundle's PHREEQC_OPTIONS already selects the cation .pqi.
$ErrorActionPreference = "Stop"

$ROOT = "C:\Users\adity\Desktop\2DSOIL_PHREEQCRM_INTEGRATION"
$GEN  = Join-Path $ROOT "2DSOIL_PHREEQCRM_MODEL"
$BUND = Join-Path $GEN  "RUN_INPUTS\2_CATION_EXCHANGE"
$EXED = Join-Path $GEN  "Maizsim_PhreeqcRM\soil source\x64\Debug\2dMAIZSIM.exe"
$OUT  = Join-Path $GEN  "POST_PROCESSING\ANALYSIS\_data\CATION_RUN"

New-Item -ItemType Directory -Force -Path $OUT | Out-Null
$fo = Join-Path $BUND "FERTIGATION_OUTPUT.txt"
$t0 = Get-Date
$p = Start-Process -FilePath $EXED -WorkingDirectory $BUND -NoNewWindow -Wait `
     -RedirectStandardOutput (Join-Path $OUT "run_stdout.txt") `
     -RedirectStandardError (Join-Path $OUT "run_stderr.txt") -PassThru
$elapsed = ((Get-Date) - $t0).TotalSeconds

$status = "OK"
if ($p.ExitCode -ne 0) { $status = "NONZERO_EXIT($($p.ExitCode))" }
elseif (-not (Test-Path $fo)) { $status = "NO_FERTIGATION_OUTPUT" }
elseif ((Get-Item $fo).LastWriteTime -lt $t0) { $status = "STALE_OUTPUT" }

if (Test-Path $fo) { Copy-Item $fo (Join-Path $OUT "FERTIGATION_OUTPUT.txt") -Force }
Copy-Item (Join-Path $BUND "PHREEQC_OPTIONS.txt") (Join-Path $OUT "PHREEQC_OPTIONS.txt") -Force

$line = "cation run: exit=$($p.ExitCode)  $('{0:N1}' -f $elapsed)s  $status"
$line | Set-Content (Join-Path $OUT "_RUN_DONE.txt")
$line