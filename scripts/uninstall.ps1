<#
.SYNOPSIS
  Docx2Shelf uninstaller for Windows (PowerShell)

.PARAMETER Method
  auto | pipx | pip-user | pip-system (default: auto)
#>

[CmdletBinding()]
param(
  [ValidateSet('auto','pipx','pip-user','pip-system')]
  [string]$Method = 'auto',
  [switch]$RemoveTools
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-PythonCmd {
  if (Get-Command py -ErrorAction SilentlyContinue) { return 'py' }
  if (Get-Command python -ErrorAction SilentlyContinue) { return 'python' }
  throw 'Python not found.'
}

Write-Host "Uninstalling Docx2Shelf using method=$Method"

if ($Method -eq 'auto') {
  if (Get-Command pipx -ErrorAction SilentlyContinue) {
    $Method = 'pipx'
  } else {
    $Method = 'pip-user'
  }
}

switch ($Method) {
  'pipx' {
    if (Get-Command pipx -ErrorAction SilentlyContinue) {
      pipx uninstall docx2shelf | Out-Null
    } else {
      Write-Host 'pipx not found; nothing to remove via pipx'
    }
  }
  'pip-user' {
    $py = Get-PythonCmd
    & $py -m pip uninstall -y docx2shelf | Out-Null
  }
  'pip-system' {
    $py = Get-PythonCmd
    & $py -m pip uninstall -y docx2shelf | Out-Null
  }
}

Write-Host "Done. If 'docx2shelf' remains on PATH, restart your terminal or delete it from your Python Scripts directory."

if ($RemoveTools) {
  try {
    if (Get-Command docx2shelf -ErrorAction SilentlyContinue) {
      Write-Host 'Removing managed tools (Pandoc/EPUBCheck) from Docx2Shelf cache...'
      docx2shelf tools uninstall all | Out-Null
    } else {
      $td = Join-Path $env:APPDATA 'Docx2Shelf\bin'
      if (Test-Path $td) { Remove-Item -Recurse -Force $td }
    }
  } catch {
    Write-Warning "Failed to remove tools cache: $_"
  }
}
