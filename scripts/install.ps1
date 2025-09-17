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
  [string]$Extras = 'docx',
  [ValidateSet('none','pandoc','epubcheck','all')]
  [string]$WithTools = 'none'
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

function Get-PkgSpec([string]$extras, [string]$basePath) {
  $base = Convert-Path $basePath # Ensure absolute path
  # Return just the base path, extras will be handled separately
  return $base
}

function Download-And-Extract-Latest-Release {
    param (
        [string]$RepoApiUrl = "https://api.github.com/repos/LightWraith8268/Docx2Shelf/releases/latest"
    )

    Write-Host "Fetching latest release information from GitHub..."
    try {
        $releaseInfo = Invoke-WebRequest -Uri $RepoApiUrl -UseBasicParsing | ConvertFrom-Json
        $downloadUrl = $releaseInfo.assets | Where-Object { $_.name -like "*.whl" } | Select-Object -ExpandProperty browser_download_url -First 1

        if (-not $downloadUrl) {
            throw "Could not find a .whl release asset. Please ensure a .whl file is attached to the latest GitHub release."
        }

        $tempDir = New-Item -ItemType Directory -Path ([System.IO.Path]::GetTempPath() + "Docx2ShelfInstaller_" + (Get-Random))
        $whlFilePath = Join-Path $tempDir "package.whl"

        Write-Host "Downloading release from $downloadUrl to $whlFilePath..."
        Invoke-WebRequest -Uri $downloadUrl -OutFile $whlFilePath -UseBasicParsing

        return $whlFilePath
    } catch {
        Write-Error "Failed to download latest release .whl: $($_.Exception.Message)"
        exit 1
    }
}

# --- Main Installation Logic ---

# If running from a downloaded installer, download the .whl
$currentWorkingDir = Get-Location
$installSource = ""
if (-not (Test-Path "pyproject.toml")) {
    $installSource = Download-And-Extract-Latest-Release
} else {
    # If pyproject.toml exists, we are running from the source directory
    $installSource = $currentWorkingDir
}

$pkgSpec = Get-PkgSpec $Extras $installSource # Pass $installSource to Get-PkgSpec
Write-Host "Installing Docx2Shelf using method=$Method extras=$Extras"

switch ($Method) {
  'pipx' {
    Ensure-Pipx
    # Use Python to invoke pipx module to avoid quoting issues
    $py = Get-PythonCmd
    # Force reinstall to handle upgrades or existing envs consistently
    # Pass the base path and extras separately
    $pipxArgs = @("--force", $pkgSpec)
    if ($Extras -ne 'none') {
        $pipxArgs += "--extras"
        # Convert 'all' to 'docx,pandoc' for pipx
        $pipxExtras = if ($Extras -eq 'all') { 'docx,pandoc' } else { $Extras }
        $pipxArgs += $pipxExtras
    }
    & $py -m pipx install @pipxArgs
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
  # Optional tools installation
  switch ($WithTools) {
    'none'      { }
    'pandoc'    { Write-Host 'Installing Pandoc via tools manager...'; & docx2shelf tools install pandoc | Out-Null }
    'epubcheck' { Write-Host 'Installing EPUBCheck via tools manager...'; & docx2shelf tools install epubcheck | Out-Null }
    'all'       { Write-Host 'Installing Pandoc + EPUBCheck via tools manager...'; & docx2shelf tools install pandoc | Out-Null; & docx2shelf tools install epubcheck | Out-Null }
  }
  Write-Host 'Done. Try: docx2shelf --help'
} catch {
  Write-Warning 'docx2shelf not found on PATH yet. Ensure your user Scripts folder is on PATH and restart your terminal:'
  Write-Host '  %USERPROFILE%\AppData\Local\Programs\Python\Python311\Scripts (version may vary)'
}
