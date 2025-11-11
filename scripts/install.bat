@echo off
REM Docx2Shelf Installation Script for Windows
REM This script downloads and installs the latest version of Docx2Shelf

setlocal enabledelayedexpansion
color 0A

echo.
echo ========================================
echo   Docx2Shelf Installation Script
echo ========================================
echo.

REM Check for internet connection
timeout /t 1 /nobreak >nul
powershell -Command "try { $null = [System.Net.ServicePointManager]::ServerCertificateValidationCallback; } catch { exit 1 }" >nul 2>&1

REM Create temporary directory
set "TEMP_DIR=%TEMP%\docx2shelf_install_%RANDOM%"
mkdir "!TEMP_DIR!" 2>nul

echo [*] Downloading Docx2Shelf installer...
echo.

REM Download latest installer from GitHub releases
powershell -Command "^
  $ErrorActionPreference = 'Stop'; ^
  $ProgressPreference = 'SilentlyContinue'; ^
  try { ^
    $url = 'https://api.github.com/repos/LightWraith8268/Docx2Shelf/releases/latest'; ^
    $release = Invoke-RestMethod -Uri $url -Headers @{'Accept' = 'application/vnd.github.v3+json'}; ^
    $installer = $release.assets | Where-Object { $_.name -match 'Setup\.exe' } | Select-Object -First 1; ^
    if ($installer) { ^
      $installerUrl = $installer.browser_download_url; ^
      $installerPath = '!TEMP_DIR!\Docx2Shelf-Setup.exe'; ^
      Write-Host '[+] Found installer: ' $installer.name; ^
      Write-Host '[*] Downloading from GitHub...'; ^
      Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath -UseBasicParsing; ^
      Write-Host '[+] Download complete'; ^
    } else { ^
      Write-Host '[!] No installer found in latest release'; ^
      exit 1; ^
    } ^
  } catch { ^
    Write-Host '[!] Download failed: ' $_.Exception.Message; ^
    exit 1; ^
  } ^
"

if %ERRORLEVEL% neq 0 (
    echo [!] Failed to download installer
    echo.
    echo Please download manually from:
    echo https://github.com/LightWraith8268/Docx2Shelf/releases/latest
    echo.
    pause
    exit /b 1
)

echo.
echo [*] Running installer...
echo.

REM Run the installer
"!TEMP_DIR!\Docx2Shelf-Setup.exe"

REM Clean up
echo.
echo [*] Cleaning up temporary files...
timeout /t 2 /nobreak >nul
rmdir /s /q "!TEMP_DIR!" 2>nul

echo.
echo [+] Installation complete!
echo.
pause
