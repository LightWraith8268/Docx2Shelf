<#
.SYNOPSIS
  Docx2Shelf installer for Windows (PowerShell)

.PARAMETER Method
  pipx | pip-user | pip-system (default: pipx)

.PARAMETER Extras
  none | docx | pandoc | all (default: docx)
#>

[CmdletBinding()]
param(
  [ValidateSet('pipx','pip-user','pip-system')]
  [string]$Method = 'pipx',
  [ValidateSet('none','docx','pandoc','all')]
  [string]$Extras = 'docx'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-PythonCmd {
  if (Get-Command py -ErrorAction SilentlyContinue) { return 'py' }
  if (Get-Command python -ErrorAction SilentlyContinue) { return 'python' }
  throw 'Python not found. Install Python 3.11+ and re-run.'
}

function Ensure-Pipx {
  if (Get-Command pipx -ErrorAction SilentlyContinue) { return }
  Write-Host 'pipx not found; installing to user site...'
  $py = Get-PythonCmd
  & $py -m pip install --user pipx
  & $py -m pipx ensurepath | Out-Null
  Write-Host 'If pipx is not found, open a new terminal to refresh PATH.'
}

function Get-PkgSpec([string]$extras) {
  switch ($extras) {
    'none'   { return '.'' }
    'docx'   { return '.[docx]' }
    'pandoc' { return '.[pandoc]' }
    'all'    { return '.[docx,pandoc]' }
  }
}

$pkgSpec = Get-PkgSpec $Extras
Write-Host "Installing Docx2Shelf using method=$Method extras=$Extras"

switch ($Method) {
  'pipx' {
    Ensure-Pipx
    # Prefer pipx executable; fallback to module call
    $pipxCmd = $(if (Get-Command pipx -ErrorAction SilentlyContinue) { 'pipx' } else { (Get-PythonCmd) + ' -m pipx' })
    # Install or upgrade
    try {
      & $pipxCmd install $pkgSpec
    } catch {
      Write-Host 'Attempting pipx upgrade instead...'
      & $pipxCmd upgrade $pkgSpec
    }
  }
  'pip-user' {
    $py = Get-PythonCmd
    & $py -m pip install --user $pkgSpec
  }
  'pip-system' {
    $py = Get-PythonCmd
    & $py -m pip install $pkgSpec
  }
}

Write-Host 'Verifying CLI on PATH...'
try {
  $null = Get-Command docx2shelf -ErrorAction Stop
  & docx2shelf --help | Out-Null
  Write-Host 'Done. Try: docx2shelf --help'
} catch {
  Write-Warning 'docx2shelf not found on PATH yet. Ensure your user Scripts folder is on PATH and restart your terminal:'
  Write-Host '  %USERPROFILE%\AppData\Local\Programs\Python\Python311\Scripts (version may vary)'
}

