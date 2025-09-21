@echo off
setlocal enabledelayedexpansion

echo ========================================
echo       docx2shelf Universal Uninstaller
echo ========================================
echo.
echo This script will remove docx2shelf from your system.
echo It will attempt to uninstall from all possible installation methods.
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running with administrator privileges.
) else (
    echo Note: Some system-wide installations may require administrator privileges.
    echo If uninstall fails, try running as administrator.
)
echo.

echo [INFO] Starting uninstall process...
echo.

REM Method 1: Try pip uninstall
echo [STEP 1] Attempting pip uninstall...
pip uninstall docx2shelf -y >nul 2>&1
if %errorlevel% == 0 (
    echo [SUCCESS] Removed via pip
) else (
    echo [SKIP] Not installed via pip or pip not available
)

REM Method 2: Try pipx uninstall
echo [STEP 2] Attempting pipx uninstall...
pipx uninstall docx2shelf >nul 2>&1
if %errorlevel% == 0 (
    echo [SUCCESS] Removed via pipx
) else (
    echo [SKIP] Not installed via pipx or pipx not available
)

REM Method 3: Try conda uninstall
echo [STEP 3] Attempting conda uninstall...
conda uninstall docx2shelf -y >nul 2>&1
if %errorlevel% == 0 (
    echo [SUCCESS] Removed via conda
) else (
    echo [SKIP] Not installed via conda or conda not available
)

REM Method 4: Try winget uninstall (if available)
echo [STEP 4] Attempting winget uninstall...
winget uninstall docx2shelf >nul 2>&1
if %errorlevel% == 0 (
    echo [SUCCESS] Removed via winget
) else (
    echo [SKIP] Not installed via winget or winget not available
)

REM Method 5: Try scoop uninstall (if available)
echo [STEP 5] Attempting scoop uninstall...
scoop uninstall docx2shelf >nul 2>&1
if %errorlevel% == 0 (
    echo [SUCCESS] Removed via scoop
) else (
    echo [SKIP] Not installed via scoop or scoop not available
)

REM Method 6: Try chocolatey uninstall (if available)
echo [STEP 6] Attempting chocolatey uninstall...
choco uninstall docx2shelf -y >nul 2>&1
if %errorlevel% == 0 (
    echo [SUCCESS] Removed via chocolatey
) else (
    echo [SKIP] Not installed via chocolatey or chocolatey not available
)

echo.
echo [INFO] Checking for remaining installations...

REM Check if docx2shelf command is still available
docx2shelf --version >nul 2>&1
if %errorlevel% == 0 (
    echo [WARNING] docx2shelf command is still available in PATH
    echo [INFO] This may indicate:
    echo   - Installation in a virtual environment that's currently active
    echo   - Manual installation that requires manual removal
    echo   - Installation via a method not covered by this script
    echo.
    echo [INFO] To find the installation location, run:
    echo   where docx2shelf
    echo   python -c "import docx2shelf; print(docx2shelf.__file__)"
) else (
    echo [SUCCESS] docx2shelf command is no longer available
)

echo.
echo [INFO] Cleaning up user data directories...

REM Remove user data directories
set "APPDATA_DIR=%APPDATA%\docx2shelf"
set "LOCALAPPDATA_DIR=%LOCALAPPDATA%\docx2shelf"
set "USERPROFILE_DIR=%USERPROFILE%\.docx2shelf"

if exist "%APPDATA_DIR%" (
    rmdir /s /q "%APPDATA_DIR%" >nul 2>&1
    if %errorlevel% == 0 (
        echo [SUCCESS] Removed user data from %%APPDATA%%
    ) else (
        echo [WARNING] Could not remove user data from %%APPDATA%%
    )
)

if exist "%LOCALAPPDATA_DIR%" (
    rmdir /s /q "%LOCALAPPDATA_DIR%" >nul 2>&1
    if %errorlevel% == 0 (
        echo [SUCCESS] Removed user data from %%LOCALAPPDATA%%
    ) else (
        echo [WARNING] Could not remove user data from %%LOCALAPPDATA%%
    )
)

if exist "%USERPROFILE_DIR%" (
    rmdir /s /q "%USERPROFILE_DIR%" >nul 2>&1
    if %errorlevel% == 0 (
        echo [SUCCESS] Removed user data from user profile
    ) else (
        echo [WARNING] Could not remove user data from user profile
    )
)

echo.
echo [INFO] Checking for tools installed by docx2shelf...

REM Check for tools that may have been installed by docx2shelf
set "TOOLS_DIR=%LOCALAPPDATA%\docx2shelf-tools"
if exist "%TOOLS_DIR%" (
    rmdir /s /q "%TOOLS_DIR%" >nul 2>&1
    if %errorlevel% == 0 (
        echo [SUCCESS] Removed docx2shelf tools directory
    ) else (
        echo [WARNING] Could not remove tools directory
    )
)

echo.
echo ========================================
echo           Uninstall Complete
echo ========================================
echo.
echo Summary:
echo - Attempted removal via all common package managers
echo - Cleaned user data directories
echo - Removed associated tools
echo.
echo If docx2shelf is still available, you may need to:
echo 1. Deactivate any virtual environments
echo 2. Manually remove from custom installation locations
echo 3. Run this script as administrator for system-wide installations
echo.
echo Thank you for using docx2shelf!
echo.
pause