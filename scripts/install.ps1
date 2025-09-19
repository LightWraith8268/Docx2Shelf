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
  [string]$WithTools = 'none',
  [ValidateSet('none','publishing','workflow','accessibility','cloud','premium')]
  [string]$WithPlugins = 'none'
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

  # Run pipx ensurepath to add to permanent PATH
  Write-Host 'Ensuring pipx is on PATH...'
  & $py -m pipx ensurepath --force

  # Add pipx script directory to current session PATH
  $pythonVersion = & $py -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
  $pipxScriptPath = "$env:USERPROFILE\AppData\Local\Programs\Python\Python${pythonVersion}\Scripts"

  # Also check the roaming path
  $pipxScriptPathRoaming = "$env:USERPROFILE\.local\bin"

  # Add both potential paths to current session
  $pathsToAdd = @($pipxScriptPath, $pipxScriptPathRoaming)
  foreach ($pathToAdd in $pathsToAdd) {
      if (Test-Path $pathToAdd) {
          if ($env:Path -notlike "*$pathToAdd*") {
              $env:Path = "$env:Path;$pathToAdd"
              Write-Host "Added to current session PATH: $pathToAdd"
          }
      }
  }

  # Test if pipx is now available
  if (-not (Get-Command pipx -ErrorAction SilentlyContinue)) {
      Write-Host 'pipx still not found. You may need to restart your terminal.'
  }
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
    # Build package spec with extras in bracket notation for older pipx compatibility
    $packageWithExtras = $pkgSpec
    if ($Extras -ne 'none') {
        # Convert 'all' to 'docx,pandoc' for extras
        $pipxExtras = if ($Extras -eq 'all') { 'docx,pandoc' } else { $Extras }
        $packageWithExtras = "${pkgSpec}[${pipxExtras}]"
    }
    # Force reinstall to handle upgrades or existing envs consistently
    & $py -m pipx install --force $packageWithExtras
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

# Add common pipx installation paths to current session
$py = Get-PythonCmd
$pythonVersion = & $py -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
$commonPaths = @(
    "$env:USERPROFILE\.local\bin",
    "$env:USERPROFILE\AppData\Roaming\Python\Python${pythonVersion}\Scripts",
    "$env:APPDATA\Python\Python${pythonVersion}\Scripts"
)

foreach ($path in $commonPaths) {
    if ((Test-Path $path) -and ($env:Path -notlike "*$path*")) {
        $env:Path = "$env:Path;$path"
        Write-Host "Added potential docx2shelf path to session: $path"
    }
}

try {
  $docx2shelfCmd = Get-Command docx2shelf -ErrorAction Stop
  Write-Host "✓ Found docx2shelf at: $($docx2shelfCmd.Source)"
  & docx2shelf --help | Out-Null
  Write-Host "✓ docx2shelf is working correctly"

  # Optional tools installation
  switch ($WithTools) {
    'none'      { }
    'pandoc'    { Write-Host 'Installing Pandoc via tools manager...'; & docx2shelf tools install pandoc }
    'epubcheck' { Write-Host 'Installing EPUBCheck via tools manager...'; & docx2shelf tools install epubcheck }
    'all'       {
        Write-Host 'Installing Pandoc + EPUBCheck via tools manager...'
        & docx2shelf tools install pandoc
        & docx2shelf tools install epubcheck
    }
  }

  # Optional plugin bundles installation
  switch ($WithPlugins) {
    'none'         { }
    'publishing'   {
        Write-Host 'Installing Publishing Bundle (Store Profiles, ONIX Export, Kindle Previewer)...'
        & docx2shelf plugins bundles install publishing
    }
    'workflow'     {
        Write-Host 'Installing Workflow Bundle (Anthology Builder, Series Builder, Web Interface)...'
        & docx2shelf plugins bundles install workflow
    }
    'accessibility' {
        Write-Host 'Installing Accessibility Bundle (Media Overlays, Dyslexic Themes)...'
        & docx2shelf plugins bundles install accessibility
    }
    'cloud'        {
        Write-Host 'Installing Cloud Integration Bundle (Google Docs, OneDrive)...'
        & docx2shelf plugins bundles install cloud
    }
    'premium'      {
        Write-Host 'Installing Premium Bundle (All marketplace plugins)...'
        & docx2shelf plugins bundles install premium
    }
  }
  Write-Host ''
  Write-Host '🎉 Installation successful! You can now use docx2shelf.'
  Write-Host 'Try: docx2shelf --help'
  Write-Host 'Or just: docx2shelf (for interactive mode)'
} catch {
  Write-Warning 'docx2shelf not found on PATH. This can happen after installation.'
  Write-Host ''
  Write-Host 'Solutions:'
  Write-Host '1. Restart your terminal/PowerShell and try: docx2shelf --help'
  Write-Host '2. If that fails, manually add this directory to your PATH:'

  foreach ($path in $commonPaths) {
      if (Test-Path $path) {
          if (Test-Path "$path\docx2shelf.exe") {
              Write-Host "   $path (docx2shelf.exe found here)"
              break
          } else {
              Write-Host "   $path (check for docx2shelf.exe)"
          }
      }
  }

  Write-Host '3. Or run the installer again in a new terminal'
}
