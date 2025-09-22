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
if !errorlevel! neq 0 (
    echo.
    echo WARNING: Your Python version is older than required.
    echo Docx2Shelf requires Python 3.11 or higher (current latest: Python 3.12).
    echo.
    echo Your version:
    !PYTHON_CMD! --version 2>nul
    if !errorlevel! neq 0 echo Unable to determine version
    echo Required: Python 3.11.0 or newer
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
if !errorlevel! neq 0 (
    echo Git not found. This is required for installation.
    echo Please install Git from: https://git-scm.com/download/windows
    echo.
    pause
    exit /b 1
)

echo Git is available.

:: Get latest version information from GitHub
echo.
echo Checking latest version from GitHub...
call :get_latest_version
if not "!LATEST_VERSION!"=="" (
    echo Latest version available: !LATEST_VERSION!
) else (
    echo [Note] Could not determine latest version (continuing anyway)
)

:: Check if docx2shelf is already installed and compare versions
echo Checking current installation...
call :check_current_version
if not "!CURRENT_VERSION!"=="" (
    echo Current version installed: !CURRENT_VERSION!

    if not "!LATEST_VERSION!"=="" (
        call :compare_versions "!CURRENT_VERSION!" "!LATEST_VERSION!"
        if !VERSION_COMPARISON! equ 0 (
            echo.
            echo [INFO] You already have the latest version (!CURRENT_VERSION!) installed.
            set /p "FORCE_REINSTALL=Would you like to reinstall anyway? (y/N): "
            if /i not "!FORCE_REINSTALL!"=="y" (
                echo Installation cancelled - already up to date.
                echo.
                set /p "DELETE_SCRIPT=Delete this installer script? (Y/n): "
                if /i not "!DELETE_SCRIPT!"=="n" (
                    echo Deleting installer script...
                    (goto) 2>nul & del "%~f0"
                )
                pause
                exit /b 0
            )
            echo Proceeding with reinstallation...
        ) else if !VERSION_COMPARISON! equ 1 (
            echo [INFO] Newer version available: !LATEST_VERSION! (currently have !CURRENT_VERSION!)
            echo Proceeding with upgrade...
        ) else (
            echo [INFO] You have a newer version (!CURRENT_VERSION!) than the latest release (!LATEST_VERSION!)
            echo This may be a development version.
            set /p "CONTINUE_ANYWAY=Continue with installation anyway? (y/N): "
            if /i not "!CONTINUE_ANYWAY!"=="y" (
                echo Installation cancelled.
                echo.
                set /p "DELETE_SCRIPT=Delete this installer script? (Y/n): "
                if /i not "!DELETE_SCRIPT!"=="n" (
                    echo Deleting installer script...
                    (goto) 2>nul & del "%~f0"
                )
                pause
                exit /b 0
            )
        )
    )
) else (
    echo No current installation detected.
)

:: Install Docx2Shelf
echo.
echo Installing Docx2Shelf from GitHub (latest version)...
!PYTHON_CMD! -m pip install --user git+https://github.com/LightWraith8268/Docx2Shelf.git

if !errorlevel! equ 0 (
    echo.
    echo [SUCCESS] Docx2Shelf installation successful!
    echo.

    :: Ask about installing optional tools
    echo ========================================
    echo    Optional Tools Installation
    echo ========================================
    echo.
    echo Docx2Shelf works best with these additional tools:
    echo.
    echo 1. PANDOC - High-quality document conversion (RECOMMENDED)
    echo    - Provides superior DOCX to EPUB conversion
    echo    - Handles complex formatting and tables
    echo    - Essential for professional results
    echo.
    echo 2. EPUBCHECK - Industry-standard EPUB validation
    echo    - Validates EPUB files for compliance
    echo    - Required for publishing to most stores
    echo    - Catches formatting and structure issues
    echo.

    set /p "INSTALL_TOOLS=Would you like to install these tools? (Y/n): "
    if /i not "!INSTALL_TOOLS!"=="n" (
        echo.
        echo Installing optional tools...
        call :install_optional_tools
    ) else (
        echo.
        echo Skipping optional tools installation.
        echo You can install them later using: docx2shelf tools install
    )
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
if !errorlevel! equ 0 (
    echo.
    echo ========================================
    echo    Installation Successful!
    echo ========================================
    echo.
    echo Docx2Shelf is now installed and ready to use.

    :: Download uninstall script for future use
    echo.
    echo Downloading uninstall script for future use...
    curl -L -o uninstall.bat "https://github.com/LightWraith8268/Docx2Shelf/releases/latest/download/uninstall.bat" >nul 2>&1
    if !errorlevel! equ 0 (
        echo [SUCCESS] Uninstall script downloaded to: uninstall.bat
        echo To uninstall later, simply run: uninstall.bat
    ) else (
        echo [WARNING] Could not download uninstall script.
        echo You can download it later from: https://github.com/LightWraith8268/Docx2Shelf/releases/latest/download/uninstall.bat
    )

    :: Show installed version
    echo.
    echo Installed version:
    docx2shelf --version 2>nul || echo [Note] Version information not available yet

    echo.
    echo ========================================
    echo    Quick Start Guide
    echo ========================================
    echo.
    echo ** INTERACTIVE MODE (RECOMMENDED) **
    echo   docx2shelf                 - Launch full interactive GUI
    echo   docx2shelf interactive     - Launch interactive menu
    echo   docx2shelf wizard          - Step-by-step conversion wizard
    echo.
    echo ** COMMAND LINE MODE **
    echo   docx2shelf --help          - Show all available commands
    echo   docx2shelf build           - Build EPUB from DOCX
    echo   docx2shelf doctor          - Environment diagnostics
    echo   docx2shelf validate        - Validate EPUB files
    echo   docx2shelf quality         - Quality analysis
    echo   docx2shelf convert         - Format conversion
    echo.
    echo ** NEW USER? Start with: docx2shelf **
    echo.
    echo Installation completed successfully!
    echo.
    set /p "DELETE_SCRIPT=Delete this installer script? (Y/n): "
    if /i not "!DELETE_SCRIPT!"=="n" (
        echo Deleting installer script...
        echo Thank you for using Docx2Shelf!
        (goto) 2>nul & del "%~f0"
    )
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

:get_latest_version
:: Get the latest release version from GitHub API
set "LATEST_VERSION="
echo Querying GitHub API for latest release...

:: Use PowerShell to make HTTP request (works on Windows 7+)
powershell -NoProfile -Command "try { $response = Invoke-RestMethod -Uri 'https://api.github.com/repos/LightWraith8268/Docx2Shelf/releases/latest' -ErrorAction Stop; Write-Output $response.tag_name } catch { Write-Output '' }" > "%TEMP%\docx2shelf_version.tmp" 2>nul

if exist "%TEMP%\docx2shelf_version.tmp" (
    set /p LATEST_VERSION=<"%TEMP%\docx2shelf_version.tmp"
    del "%TEMP%\docx2shelf_version.tmp" >nul 2>&1
)

:: Clean up any whitespace
for /f "tokens=*" %%a in ("!LATEST_VERSION!") do set "LATEST_VERSION=%%a"

if "!LATEST_VERSION!"=="" (
    echo [Note] Could not retrieve version info from GitHub API
) else (
    echo Found latest release: !LATEST_VERSION!
)

exit /b 0

:check_current_version
:: Check if docx2shelf is installed and get its version
set "CURRENT_VERSION="

:: Try to get version with simple approach first
docx2shelf --version >nul 2>&1
if !errorlevel! neq 0 (
    :: Command not found or failed
    exit /b 0
)

:: If we get here, docx2shelf exists, now try to get version safely
:: Use PowerShell for more reliable parsing
powershell -NoProfile -Command "try { $output = & 'docx2shelf' '--version' 2>$null; if ($output -match '(\d+\.\d+\.\d+)') { Write-Output $matches[1] } } catch { }" > "%TEMP%\docx2shelf_ver.txt" 2>nul

if exist "%TEMP%\docx2shelf_ver.txt" (
    for /f %%A in ("%TEMP%\docx2shelf_ver.txt") do (
        set "CURRENT_VERSION=%%A"
    )
    del "%TEMP%\docx2shelf_ver.txt" >nul 2>&1
)

exit /b 0

:compare_versions
:: Compare two version strings (v1 v2)
:: Returns: VERSION_COMPARISON = 0 (equal), 1 (v2 newer), -1 (v1 newer)
set "V1=%~1"
set "V2=%~2"
set "VERSION_COMPARISON=0"

:: Remove 'v' prefix if present
set "V1=!V1:v=!"
set "V2=!V2:v=!"

:: Simple string comparison for versions like "1.4.2" vs "1.4.3"
:: Convert to comparable numbers by replacing dots
set "V1_NUM=!V1:.=!"
set "V2_NUM=!V2:.=!"

:: Pad with zeros to ensure proper numeric comparison
for /l %%i in (1,1,10) do (
    if "!V1_NUM:~%%i,1!"=="" set "V1_NUM=!V1_NUM!0"
    if "!V2_NUM:~%%i,1!"=="" set "V2_NUM=!V2_NUM!0"
)

:: Compare numerically
if !V1_NUM! lss !V2_NUM! (
    set "VERSION_COMPARISON=1"
) else if !V1_NUM! gtr !V2_NUM! (
    set "VERSION_COMPARISON=-1"
) else (
    set "VERSION_COMPARISON=0"
)

exit /b 0

:install_optional_tools
:: Install Pandoc and EPUBCheck using docx2shelf tools command
echo Installing Pandoc...
docx2shelf tools install pandoc
if !errorlevel! equ 0 (
    echo [SUCCESS] Pandoc installed successfully
) else (
    echo [WARNING] Pandoc installation failed - you can try again later with: docx2shelf tools install pandoc
)

echo.
echo Installing EPUBCheck...
docx2shelf tools install epubcheck
if !errorlevel! equ 0 (
    echo [SUCCESS] EPUBCheck installed successfully
) else (
    echo [WARNING] EPUBCheck installation failed - you can try again later with: docx2shelf tools install epubcheck
)

echo.
echo Optional tools installation completed.
exit /b 0