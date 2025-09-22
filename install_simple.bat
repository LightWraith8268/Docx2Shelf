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
    echo Git not found. Please install Git and try again.
    echo Download from: https://git-scm.com/download/windows
    pause
    exit /b 1
)

:: Install Docx2Shelf
echo.
echo Installing Docx2Shelf...
python -m pip install --user git+https://github.com/LightWraith8268/Docx2Shelf.git

if errorlevel 1 (
    echo Installation failed. Please check the error messages above.
    pause
    exit /b 1
)

:: Verify installation
echo.
echo Verifying installation...
docx2shelf --help >nul 2>&1
if errorlevel 1 (
    echo Installation verification failed. You may need to restart your command prompt.
    echo Try running: docx2shelf --help
) else (
    echo.
    echo ========================================
    echo    Installation Successful!
    echo ========================================
    echo.
    echo Docx2Shelf is now installed and ready to use.
    echo Try: docx2shelf build --help
)

echo.
echo Installation complete.
pause