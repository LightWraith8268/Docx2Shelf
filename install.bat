@echo off
setlocal enabledelayedexpansion

:: Docx2Shelf Simple Installer for Windows
echo ========================================
echo    Docx2Shelf Windows Installer
echo ========================================
echo.

:: Find Python
echo Looking for Python...
set "PYTHON_CMD=python"

:: Test if python works
python --version >nul 2>&1
if errorlevel 1 (
    echo Python not found. Please install Python 3.11+ and try again.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Found Python:
python --version

:: Check for Git
echo.
echo Checking for Git...
git --version >nul 2>&1
if errorlevel 1 (
    echo Git not found. This is required for installation.
    echo Please install Git from: https://git-scm.com/download/windows
    echo.
    pause
    exit /b 1
)
echo Git is available.

:: Check current installation
echo.
echo Checking for existing Docx2Shelf installation...
docx2shelf --version >nul 2>&1
if not errorlevel 1 (
    echo Current installation found:
    docx2shelf --version
    echo.
    set /p "UPGRADE=Upgrade to latest version? (Y/n): "
    if /i "!UPGRADE!"=="n" (
        echo Installation cancelled.
        pause
        exit /b 0
    )
    echo Upgrading to latest version...
) else (
    echo No current installation detected.
    echo Installing latest version...
)

:: Install Docx2Shelf
echo.
python -m pip install --user --upgrade git+https://github.com/LightWraith8268/Docx2Shelf.git

if errorlevel 1 (
    echo Installation failed. Please check the error messages above.
    pause
    exit /b 1
)

:: Verify installation
echo.
echo Verifying installation...
docx2shelf --version >nul 2>&1
if errorlevel 1 (
    echo Installation verification failed. You may need to restart your command prompt.
    echo Try running: docx2shelf --version
    echo.
    echo If the command is not found, you may need to:
    echo 1. Restart your command prompt
    echo 2. Add Python Scripts to your PATH
) else (
    echo.
    echo ========================================
    echo    Installation Successful!
    echo ========================================
    echo.
    echo Installed version:
    docx2shelf --version
    echo.
    echo Docx2Shelf is now installed and ready to use.
    echo Try: docx2shelf build --help
)

echo.
echo Installation complete.
pause