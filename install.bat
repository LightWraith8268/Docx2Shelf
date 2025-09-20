@echo off
setlocal enabledelayedexpansion

:: Docx2Shelf Simple Installer for Windows
echo ========================================
echo    Docx2Shelf Windows Installer
echo ========================================
echo.

:: Check for Python with intelligent version detection
echo Checking for Python installation...
call :detect_best_python

echo Python found: !PYTHON_CMD!
echo Version details:
!PYTHON_CMD! --version

:: Check Python version compatibility
echo Checking Python version compatibility...
!PYTHON_CMD! -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" 2>nul
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
                echo [SUCCESS] Python upgrade successful and compatible.

                :: Upgrade pip to latest version and clear cache
                echo Upgrading pip to latest version...
                !PYTHON_CMD! -m pip install --upgrade pip
                echo Clearing pip cache...
                !PYTHON_CMD! -m pip cache purge >nul 2>&1
                echo [SUCCESS] Pip upgraded and cache cleared.
            )
        )
    )
) else (
    echo Python version is compatible.

    :: Check and upgrade pip even for compatible Python versions
    echo Checking pip version...
    !PYTHON_CMD! -m pip install --upgrade pip >nul 2>&1
    if !errorlevel! equ 0 (
        echo [SUCCESS] Pip is up to date.
    )
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
!PYTHON_CMD! -m pip install --user git+https://github.com/LightWraith8268/Docx2Shelf.git

if !errorlevel! equ 0 (
    echo.
    echo [SUCCESS] Installation successful!
    echo.
) else (
    echo.
    echo [ERROR] Installation failed. This is likely due to:
    echo 1. Python version incompatibility (requires 3.11+)
    echo 2. Network connectivity issues
    echo 3. Missing dependencies
    echo.
    echo Please check the error messages above.
    echo.
    pause
    exit /b 1
)

:: Add Python Scripts directory to PATH if needed
echo.
echo Configuring PATH for docx2shelf command...
call :add_scripts_to_path

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
    echo Installation completed successfully!
    pause
) else (
    echo.
    echo ========================================
    echo    Installation Issues Detected
    echo ========================================
    echo.
    echo Docx2Shelf was installed but the command is not accessible.
    echo.
    echo This is usually due to PATH configuration. Solutions:
    echo.
    echo 1. RESTART this Command Prompt and try again
    echo 2. Log out and log back in to Windows
    echo 3. Open a new Command Prompt window
    echo.
    echo Alternative: Use the full path to run docx2shelf:
    if exist "!SCRIPTS_DIR!\docx2shelf.exe" (
        echo   "!SCRIPTS_DIR!\docx2shelf.exe" --help
    ) else (
        echo   Check your Python Scripts directory for docx2shelf.exe
    )
    echo.
    echo The installation was successful, but requires a terminal restart.
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

:detect_best_python
:: Detect the best available Python installation, preferring newer versions
echo Scanning for Python installations...

:: Method 1: Try specific Python 3.11+ installations first
set "PYTHON311_USER=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
set "PYTHON311_SYSTEM=%PROGRAMFILES%\Python311\python.exe"
set "PYTHON312_USER=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
set "PYTHON312_SYSTEM=%PROGRAMFILES%\Python312\python.exe"

:: Check for Python 3.12 first (newest)
if exist "!PYTHON312_USER!" (
    "!PYTHON312_USER!" -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_CMD=!PYTHON312_USER!"
        echo Found Python 3.12 in user directory
        exit /b 0
    )
)

if exist "!PYTHON312_SYSTEM!" (
    "!PYTHON312_SYSTEM!" -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_CMD=!PYTHON312_SYSTEM!"
        echo Found Python 3.12 in system directory
        exit /b 0
    )
)

:: Check for Python 3.11
if exist "!PYTHON311_USER!" (
    "!PYTHON311_USER!" -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_CMD=!PYTHON311_USER!"
        echo Found Python 3.11 in user directory
        exit /b 0
    )
)

if exist "!PYTHON311_SYSTEM!" (
    "!PYTHON311_SYSTEM!" -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_CMD=!PYTHON311_SYSTEM!"
        echo Found Python 3.11 in system directory
        exit /b 0
    )
)

:: Method 2: Try py launcher with specific versions
py -3.12 --version >nul 2>&1
if !errorlevel! equ 0 (
    py -3.12 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_CMD=py -3.12"
        echo Found Python 3.12 via py launcher
        exit /b 0
    )
)

py -3.11 --version >nul 2>&1
if !errorlevel! equ 0 (
    py -3.11 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_CMD=py -3.11"
        echo Found Python 3.11 via py launcher
        exit /b 0
    )
)

:: Method 3: Try generic py launcher (uses latest installed)
py --version >nul 2>&1
if !errorlevel! equ 0 (
    py -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_CMD=py"
        echo Found compatible Python via py launcher
        exit /b 0
    ) else (
        :: py exists but not compatible version
        set "PYTHON_CMD=py"
        echo Found Python via py launcher (version may be incompatible)
        exit /b 0
    )
)

:: Method 4: Try direct python command
python --version >nul 2>&1
if !errorlevel! equ 0 (
    python -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_CMD=python"
        echo Found compatible Python via python command
        exit /b 0
    ) else (
        :: python exists but not compatible version
        set "PYTHON_CMD=python"
        echo Found Python via python command (version may be incompatible)
        exit /b 0
    )
)

:: No Python found
echo Python not found on this system.
echo.
echo Docx2Shelf requires Python 3.11 or higher.
echo Please install Python from https://python.org
echo Make sure to check "Add Python to PATH" during installation.
echo.
pause
exit /b 1

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

:add_scripts_to_path
:: Add Python Scripts directory to PATH for current session and permanently
echo Checking Python Scripts directory...

:: Detect the Scripts directory based on the Python command being used
set "SCRIPTS_DIR="

if "!PYTHON_CMD!"=="python" (
    for /f "tokens=*" %%A in ('python -c "import sys, os; print(os.path.join(sys.prefix, 'Scripts'))" 2^>nul') do set "SCRIPTS_DIR=%%A"
) else if "!PYTHON_CMD!"=="py" (
    for /f "tokens=*" %%A in ('py -c "import sys, os; print(os.path.join(sys.prefix, 'Scripts'))" 2^>nul') do set "SCRIPTS_DIR=%%A"
) else (
    :: For direct path commands, try to derive Scripts directory
    for /f "tokens=*" %%A in ('!PYTHON_CMD! -c "import sys, os; print(os.path.join(sys.prefix, 'Scripts'))" 2^>nul') do set "SCRIPTS_DIR=%%A"
)

:: Fallback: Check common user Scripts location
if "!SCRIPTS_DIR!"=="" (
    set "SCRIPTS_DIR=%APPDATA%\Python\Python311\Scripts"
)

:: Check if Scripts directory exists and contains docx2shelf
if exist "!SCRIPTS_DIR!\docx2shelf.exe" (
    echo Found docx2shelf.exe in: !SCRIPTS_DIR!

    :: Check if Scripts directory is already in PATH
    echo %PATH% | findstr /i "!SCRIPTS_DIR!" >nul
    if !errorlevel! neq 0 (
        echo Adding Scripts directory to PATH...

        :: Add to current session PATH
        set "PATH=%PATH%;!SCRIPTS_DIR!"

        :: Add to user PATH permanently (registry)
        for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "CURRENT_USER_PATH=%%B"
        if "!CURRENT_USER_PATH!"=="" (
            reg add "HKCU\Environment" /v PATH /t REG_EXPAND_SZ /d "!SCRIPTS_DIR!" /f >nul 2>&1
        ) else (
            echo !CURRENT_USER_PATH! | findstr /i "!SCRIPTS_DIR!" >nul
            if !errorlevel! neq 0 (
                reg add "HKCU\Environment" /v PATH /t REG_EXPAND_SZ /d "!CURRENT_USER_PATH!;!SCRIPTS_DIR!" /f >nul 2>&1
            )
        )

        echo [SUCCESS] Scripts directory added to PATH
    ) else (
        echo [SUCCESS] Scripts directory already in PATH
    )
) else (
    echo Warning: Could not find docx2shelf.exe in expected Scripts directory
    echo Expected location: !SCRIPTS_DIR!
)

exit /b 0