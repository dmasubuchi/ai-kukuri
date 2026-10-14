# KUKURI Kit installer for Windows (PowerShell). Run from a checkout:
#   .\install.ps1 C:\Users\you\kukuri-workspace
#   .\install.ps1 -Repair C:\Users\you\kukuri-workspace
param(
  [Parameter(Mandatory = $true, Position = 0)][string]$Target,
  [switch]$Repair,
  [ValidateSet('en', 'ja')][string]$Lang = 'en'
)
$ErrorActionPreference = 'Stop'
$python = $null
foreach ($candidate in 'python3', 'python', 'py') {
  if (Get-Command $candidate -ErrorAction SilentlyContinue) { $python = $candidate; break }
}
if (-not $python) { Write-Error 'kukuri-kit: Python 3.9 or later is required'; exit 2 }
& $python -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)'
if ($LASTEXITCODE -ne 0) { Write-Error 'kukuri-kit: Python 3.9 or later is required'; exit 2 }
$script = Join-Path $PSScriptRoot 'scripts\init_workspace.py'
$arguments = @('-B', $script, '--lang', $Lang)
if ($Repair) { $arguments += '--repair' }
$arguments += $Target
& $python @arguments
exit $LASTEXITCODE
