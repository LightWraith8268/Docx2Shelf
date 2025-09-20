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
    set /p "UPGRADE_PYTHON=Would you like to upgrade Python automatically? (Y/n): "
    if /i "!UPGRADE_PYTHON!"=="n" (
        echo.
        set /p "CONTINUE=Continue with current Python version anyway? Installation may fail. (y/N): "
        if /i not "!CONTINUE!"=="y" (
            echo Installation cancelled.
            echo Please upgrade Python manually and run this installer again.
            echo.
            pause
            exit /b 1
        )
        echo Continuing with potentially incompatible Python version...
    ) else (
        echo.
        echo Installing Python 3.11...
        call :install_python
        if !errorlevel! neq 0 (
            echo Python upgrade failed. Continuing with current version...
            echo Note: Installation may fail due to version incompatibility.
        ) else (
            echo Python upgrade completed. Re-checking...
            :: Refresh environment variables to pick up new PATH
            call :refresh_environment

            :: Re-detect Python command after upgrade with comprehensive checks
            call :detect_python_after_upgrade

            :: Verify the new Python version
            echo Verifying new Python installation...
            !PYTHON_CMD! --version
            !PYTHON_CMD! -c "import sys; print('Python ' + str(sys.version_info.major) + '.' + str(sys.version_info.minor) + '.' + str(sys.version_info.micro))"

            :: Final compatibility check
            !PYTHON_CMD! -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" 2>nul
            if !errorlevel! neq 0 (
                echo WARNING: Upgraded Python still shows as incompatible.
                echo This may require a system restart or manual PATH configuration.
                echo Continuing with installation attempt...
            ) else (
                echo ✓ Python upgrade successful and compatible.
            )
        )
    )
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

goto :eof

:install_python
:: Simple Python installation subroutine
echo.
echo ========================================
echo    Installing Python 3.11
echo ========================================
echo.

:: Determine architecture
if "%PROCESSOR_ARCHITECTURE%"=="AMD64" (
    set "ARCH=amd64"
) else if "%PROCESSOR_ARCHITEW6432%"=="AMD64" (
    set "ARCH=amd64"
) else (
    set "ARCH=win32"
)

:: Set Python download URL
set "PYTHON_VERSION=3.11.9"
set "PYTHON_URL=https://www.python.org/ftp/python/!PYTHON_VERSION!/python-!PYTHON_VERSION!-!ARCH!.exe"
set "PYTHON_INSTALLER=%TEMP%\python-installer.exe"

echo Downloading Python !PYTHON_VERSION! for !ARCH!...
powershell -Command "try { (New-Object Net.WebClient).DownloadFile('!PYTHON_URL!', '!PYTHON_INSTALLER!') } catch { exit 1 }"
if !errorlevel! neq 0 (
    echo Failed to download Python installer.
    echo Please install Python manually from https://python.org
    pause
    exit /b 1
)

echo Installing Python !PYTHON_VERSION!...
echo This may take a few minutes...
"!PYTHON_INSTALLER!" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1

if !errorlevel! neq 0 (
    echo Python installation failed.
    echo Please install Python manually from https://python.org
    del /f /q "!PYTHON_INSTALLER!" 2>nul
    pause
    exit /b 1
)

:: Clean up
del /f /q "!PYTHON_INSTALLER!" 2>nul

echo Python installation completed successfully.
timeout /t 3 /nobreak >nul
exit /b 0

:refresh_environment
:: Refresh environment variables without requiring a restart
echo Refreshing environment variables...
for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "USERPATH=%%B"
for /f "tokens=2*" %%A in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH 2^>nul') do set "SYSTEMPATH=%%B"
set "PATH=%SYSTEMPATH%;%USERPATH%"
exit /b 0

:detect_python_after_upgrade
:: Comprehensive Python detection after upgrade
echo Detecting Python installation...

:: Method 1: Try python command directly
python --version >nul 2>&1
if !errorlevel! equ 0 (
    python -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_CMD=python"
        echo Found compatible python command
        exit /b 0
    )
)

:: Method 2: Try py launcher
py --version >nul 2>&1
if !errorlevel! equ 0 (
    py -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_CMD=py"
        echo Found compatible py launcher
        exit /b 0
    )
)

:: Method 3: Try specific Python 3.11 installation paths
set "PYTHON311_USER=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
set "PYTHON311_SYSTEM=%PROGRAMFILES%\Python311\python.exe"

if exist "!PYTHON311_USER!" (
    "!PYTHON311_USER!" --version >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_CMD=!PYTHON311_USER!"
        echo Found Python 3.11 in user directory
        exit /b 0
    )
)

if exist "!PYTHON311_SYSTEM!" (
    "!PYTHON311_SYSTEM!" --version >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_CMD=!PYTHON311_SYSTEM!"
        echo Found Python 3.11 in system directory
        exit /b 0
    )
)

:: Method 4: Try py launcher with specific version
py -3.11 --version >nul 2>&1
if !errorlevel! equ 0 (
    set "PYTHON_CMD=py -3.11"
    echo Found Python 3.11 via py launcher
    exit /b 0
)

:: Fallback: Use whatever we had before
echo Could not detect upgraded Python, using previous command: !PYTHON_CMD!
exit /b 0