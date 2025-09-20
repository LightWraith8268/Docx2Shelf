@echo off
setlocal enabledelayedexpansion

:: Docx2Shelf Simple Installer for Windows
echo ========================================
echo    Docx2Shelf Windows Installer
echo ========================================
echo.

:: Check for Python
echo Checking for Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    py --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo Python not found on this system.
        echo.
        echo Docx2Shelf requires Python 3.11 or higher.
        echo Please install Python from https://python.org
        echo Make sure to check "Add Python to PATH" during installation.
        echo.
        pause
        exit /b 1
    ) else (
        set "PYTHON_CMD=py"
    )
) else (
    set "PYTHON_CMD=python"
)

echo Python found: %PYTHON_CMD%

:: Check Python version compatibility
echo Checking Python version compatibility...
%PYTHON_CMD% -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" 2>nul
if %errorlevel% neq 0 (
    echo.
    echo WARNING: Your Python version is older than required.
    echo Docx2Shelf requires Python 3.11 or higher.
    echo.
    set /p "CONTINUE=Continue anyway? Installation may fail. (y/N): "
    if /i not "!CONTINUE!"=="y" (
        echo Installation cancelled.
        echo Please upgrade Python and run this installer again.
        echo.
        pause
        exit /b 1
    )
    echo Continuing with potentially incompatible Python version...
) else (
    echo Python version is compatible.
)

:: Check for Git
echo Checking for Git installation...
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Git not found. This is required for installation.
    echo Please install Git from: https://git-scm.com/download/windows
    echo.
    pause
    exit /b 1
)

echo Git is available.

:: Install Docx2Shelf
echo.
echo Installing Docx2Shelf...
%PYTHON_CMD% -m pip install --user git+https://github.com/LightWraith8268/Docx2Shelf.git

:: Check if installation succeeded
if %errorlevel% neq 0 (
    echo.
    echo Installation failed. This is likely due to:
    echo 1. Python version incompatibility (requires 3.11+)
    echo 2. Network connectivity issues
    echo 3. Missing dependencies
    echo.
    echo Please check the error messages above.
    echo.
    pause
    exit /b 1
)

:: Verify installation
echo.
echo Verifying installation...
docx2shelf --help >nul 2>&1
if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo    Installation Successful!
    echo ========================================
    echo.
    echo Docx2Shelf is now installed and ready to use.
    echo.
    echo Quick start:
    echo   docx2shelf --help          - Show help
    echo   docx2shelf build           - Build EPUB from DOCX
    echo   docx2shelf wizard          - Interactive wizard
    echo   docx2shelf enterprise      - Enterprise features
    echo.
    echo If you get "command not found" errors, restart your terminal.
    echo.
    echo Installation completed successfully!
    pause
) else (
    echo.
    echo ========================================
    echo    Installation Issues Detected
    echo ========================================
    echo.
    echo Docx2Shelf was installed but may not be on PATH.
    echo.
    echo Solutions:
    echo 1. Restart your Command Prompt/Terminal
    echo 2. Log out and log back in to Windows
    echo.
    echo If issues persist, you may need to manually add Python Scripts
    echo directory to your PATH environment variable.
    echo.
    echo Installation completed with warnings.
    pause
)

exit /b 0