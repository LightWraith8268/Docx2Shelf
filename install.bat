@echo off
setlocal enabledelayedexpansion

:: Docx2Shelf Installer for Windows
:: This script installs Python (if needed) and Docx2Shelf, ensuring both are available globally on PATH
:: Features:
:: - Automatic Python 3.11+ installation if not found
:: - Multiple installation fallback methods
:: - Automatic PATH configuration
:: - Optional custom installation location
:: - User-friendly error handling and diagnostics
::
:: Usage:
::   install.bat                    - Standard installation
::   install.bat --path "C:\Tools"  - Install to custom location

:: Parse command line arguments
set "CUSTOM_INSTALL_PATH="
set "SHOW_HELP="

:parse_args
if "%~1"=="" goto :args_done
if /i "%~1"=="--help" set "SHOW_HELP=1"
if /i "%~1"=="-h" set "SHOW_HELP=1"
if /i "%~1"=="--path" (
    set "CUSTOM_INSTALL_PATH=%~2"
    shift
)
shift
goto :parse_args

:args_done

:: Show help if requested
if defined SHOW_HELP (
    echo Docx2Shelf Windows Installer
    echo.
    echo Usage:
    echo   install.bat                     - Standard installation
    echo   install.bat --path "C:\Tools"   - Install to custom location
    echo   install.bat --help              - Show this help
    echo.
    echo Standard installation uses system-appropriate locations:
    echo   - Python: User profile %%LocalAppData%%\Programs\Python
    echo   - Docx2Shelf: pipx managed location or Python Scripts
    echo.
    echo Custom installation allows you to specify a target directory.
    pause
    exit /b 0
)

echo ========================================
echo    Docx2Shelf Windows Installer
echo ========================================
echo.

if defined CUSTOM_INSTALL_PATH (
    echo Custom installation path: %CUSTOM_INSTALL_PATH%
    echo.
)

:: Check for Python
echo Checking for Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    py --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo Python not found on this system.
        echo.
        echo Docx2Shelf requires Python 3.11 or higher to function.
        echo.
        set /p "AUTO_INSTALL=Would you like to install Python automatically? (Y/n): "
        if /i "!AUTO_INSTALL!"=="n" (
            echo Installation cancelled by user.
            echo Please install Python 3.11+ manually from https://python.org
            echo Make sure to check "Add Python to PATH" during installation.
            pause
            exit /b 1
        )

        echo Installing Python automatically...
        call :install_python
        if %errorlevel% neq 0 (
            echo ERROR: Failed to install Python automatically
            echo Please install Python 3.11+ manually from https://python.org
            echo Make sure to check "Add Python to PATH" during installation.
            pause
            exit /b 1
        )

        :: Re-check after installation
        python --version >nul 2>&1
        if %errorlevel% neq 0 (
            py --version >nul 2>&1
            if %errorlevel% neq 0 (
                echo ERROR: Python installation failed or PATH not updated
                echo Please restart your Command Prompt and run this installer again
                echo Or install Python manually from https://python.org
                pause
                exit /b 1
            )
            set "PYTHON_CMD=py"
        ) else (
            set "PYTHON_CMD=python"
        )
    ) else (
        set "PYTHON_CMD=py"
    )
) else (
    set "PYTHON_CMD=python"
)

echo Python found: %PYTHON_CMD%

:: Check Python version compatibility
echo Checking Python version compatibility...

:: Get Python version using simple approach
%PYTHON_CMD% --version 2>&1 | findstr "Python" > nul
if %errorlevel% equ 0 (
    echo Python installation verified.

    :: Check if version is 3.11 or higher
    echo Checking if Python meets minimum requirement (3.11+)...
    %PYTHON_CMD% -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" 2>nul
    set "VERSION_COMPATIBLE=%errorlevel%"
    echo Version check result: !VERSION_COMPATIBLE! (0=compatible, 1=incompatible)
    if !VERSION_COMPATIBLE! neq 0 (
        echo.
        echo WARNING: Your Python version is older than required. Docx2Shelf requires Python 3.11+
        echo.
        set /p "UPGRADE_PYTHON=Would you like to upgrade Python automatically? (Y/n): "
        if /i "!UPGRADE_PYTHON!"=="n" (
            echo Continuing with current Python version...
            echo Note: Some features may not work correctly with your current Python version
        ) else (
            echo Upgrading Python to 3.11+...
            call :install_python
            if %errorlevel% neq 0 (
                echo Failed to upgrade Python, continuing with current version
            ) else (
                :: Re-detect Python command after upgrade
                python --version >nul 2>&1
                if %errorlevel% equ 0 (
                    set "PYTHON_CMD=python"
                ) else (
                    set "PYTHON_CMD=py"
                )
            )
        )
    ) else (
        echo ✓ Python version is compatible
    )
) else (
    echo Warning: Could not determine Python version
)

:: Check if pipx is available
echo Checking for pipx...
pipx --version >nul 2>&1
if %errorlevel% neq 0 (
    echo pipx not found. Installing pipx...
    %PYTHON_CMD% -m pip install --user pipx
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install pipx
        pause
        exit /b 1
    )

    :: Ensure pipx is on PATH
    %PYTHON_CMD% -m pipx ensurepath

    :: Add pipx to current session PATH
    for /f "delims=" %%i in ('%PYTHON_CMD% -c "import os, sys; print(os.path.join(os.path.expanduser('~'), '.local', 'bin'))"') do set "PIPX_BIN=%%i"
    if exist "!PIPX_BIN!" (
        set "PATH=!PATH!;!PIPX_BIN!"
        echo Added !PIPX_BIN! to current session PATH
    )

    :: Also try Windows-specific path
    for /f "delims=" %%i in ('%PYTHON_CMD% -c "import sys; print(sys.exec_prefix + '\\Scripts')"') do set "PYTHON_SCRIPTS=%%i"
    if exist "!PYTHON_SCRIPTS!" (
        set "PATH=!PATH!;!PYTHON_SCRIPTS!"
        echo Added !PYTHON_SCRIPTS! to current session PATH
    )
)

echo pipx is available

:: Check for Git availability
echo Checking for Git installation...
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  Git not found in PATH. GitHub installation will not work.
    echo Git is required to install from GitHub repository.
    echo.
    echo Please install Git from: https://git-scm.com/download/windows
    echo Or use an alternative installation method.
    echo.
    set "GIT_AVAILABLE=0"
) else (
    echo ✓ Git is available
    set "GIT_AVAILABLE=1"
)

:: Install Docx2Shelf with enhanced error handling
echo Installing Docx2Shelf...

if "%GIT_AVAILABLE%"=="1" (
    :: Method 1: Try from GitHub (primary source)
    echo Method 1: Installing from GitHub repository...
    if defined CUSTOM_INSTALL_PATH (
        echo Installing to custom path: %CUSTOM_INSTALL_PATH%
        if not exist "%CUSTOM_INSTALL_PATH%" mkdir "%CUSTOM_INSTALL_PATH%"
        %PYTHON_CMD% -m pip install --target "%CUSTOM_INSTALL_PATH%" git+https://github.com/LightWraith8268/Docx2Shelf.git
        if %errorlevel% equ 0 (
            echo ✓ Installation successful to custom path
            set "CUSTOM_INSTALL_SUCCESS=1"
            goto :verify_install
        )
    ) else (
        echo Installing docx2shelf with pip...
        %PYTHON_CMD% -m pip install --user git+https://github.com/LightWraith8268/Docx2Shelf.git > "%TEMP%\docx2shelf_install.log" 2>&1
        set "INSTALL_RESULT=%errorlevel%"

        :: Check if installation actually succeeded by looking for error patterns
        findstr /C:"ERROR:" "%TEMP%\docx2shelf_install.log" >nul
        if !errorlevel! equ 0 (
            echo ❌ Installation failed - Python version incompatibility detected
            echo See error log: %TEMP%\docx2shelf_install.log
            type "%TEMP%\docx2shelf_install.log"
        ) else if !INSTALL_RESULT! equ 0 (
            echo ✓ Installation successful from GitHub
            goto :verify_install
        ) else (
            echo ❌ Installation failed (exit code: !INSTALL_RESULT!)
            type "%TEMP%\docx2shelf_install.log"
        )
    )

    echo ❌ GitHub installation failed. Trying alternative methods...
) else (
    echo Method 1: Skipping GitHub installation (Git not available)
    echo Trying alternative installation methods...
)

:: Method 2: Try with pipx from GitHub (if Git available)
if "%GIT_AVAILABLE%"=="1" (
    echo Method 2: Installing with pipx from GitHub...
    pipx install git+https://github.com/LightWraith8268/Docx2Shelf.git --force
    if %errorlevel% equ 0 (
        echo ✓ Installation successful with pipx
        goto :verify_install
    )
) else (
    echo Method 2: Skipping pipx GitHub install (Git not available)
)

:: Method 3: Try installing dependencies separately (Git-free fallback)
echo Method 3: Installing core dependencies separately...
%PYTHON_CMD% -m pip install --user ebooklib python-docx lxml
if %errorlevel% equ 0 (
    echo Dependencies installed successfully
    if "%GIT_AVAILABLE%"=="1" (
        echo Now installing docx2shelf from GitHub...
        %PYTHON_CMD% -m pip install --user git+https://github.com/LightWraith8268/Docx2Shelf.git --no-deps
        if %errorlevel% equ 0 (
            echo ✓ Installation successful with separate dependencies
            goto :verify_install
        )
    ) else (
        echo ℹ️  Dependencies installed, but cannot install docx2shelf without Git
        echo Please install Git and run the installer again, or install docx2shelf manually
    )
)

:: Method 4: Try development/editable install from local directory
echo Method 4: Checking for local source...
if exist "pyproject.toml" (
    echo Found local source, installing in development mode...
    %PYTHON_CMD% -m pip install --user -e .
    if %errorlevel% equ 0 (
        echo ✓ Installation successful from local source
        goto :verify_install
    )
)

:: Method 5: Manual installation guidance
if "%GIT_AVAILABLE%"=="0" (
    echo.
    echo ======================================
    echo    Manual Installation Required
    echo ======================================
    echo.
    echo Git is required to install docx2shelf from GitHub.
    echo.
    echo Options:
    echo 1. Install Git from: https://git-scm.com/download/windows
    echo    Then run this installer again
    echo.
    echo 2. Download the source code manually:
    echo    - Go to: https://github.com/LightWraith8268/Docx2Shelf
    echo    - Click "Code" → "Download ZIP"
    echo    - Extract and run: %PYTHON_CMD% -m pip install --user -e .
    echo.
    echo 3. Use Git Bash (if available):
    echo    - Install Git with Git Bash option
    echo    - Run this installer from Git Bash
    echo.
    echo Press any key to continue...
    pause >nul
    exit /b 1
)

:: All methods failed
echo.
echo ❌ All installation methods failed
echo.
echo Diagnostic information:
echo Python version:
%PYTHON_CMD% --version
echo.
echo Pip version:
%PYTHON_CMD% -m pip --version
echo.
echo Available packages (docx2shelf):
%PYTHON_CMD% -m pip search docx2shelf 2>nul || echo "Search not available"
echo.
echo Possible solutions:
echo 1. Check your internet connection
echo 2. Update pip: %PYTHON_CMD% -m pip install --upgrade pip
echo 3. Clear pip cache: %PYTHON_CMD% -m pip cache purge
echo 4. Try manual installation from source
echo 5. Contact support with the information above
echo.
pause
exit /b 1

:verify_install

:: Verify installation and update PATH if needed
echo Verifying installation...

if defined CUSTOM_INSTALL_SUCCESS (
    :: For custom installations, add the path and create a launcher script
    echo Setting up custom installation...
    set "DOCX2SHELF_SCRIPT=%CUSTOM_INSTALL_PATH%\docx2shelf.bat"

    :: Create a launcher batch file
    echo @echo off > "%DOCX2SHELF_SCRIPT%"
    echo %PYTHON_CMD% "%CUSTOM_INSTALL_PATH%\docx2shelf\cli.py" %%%%* >> "%DOCX2SHELF_SCRIPT%"

    :: Add custom path to PATH
    set "PATH=%PATH%;%CUSTOM_INSTALL_PATH%"

    :: Add to permanent PATH for current user
    echo Adding !CUSTOM_INSTALL_PATH! to user PATH permanently...
    powershell -Command "$customPath = '!CUSTOM_INSTALL_PATH!'; $userPath = [Environment]::GetEnvironmentVariable('Path','User'); if ($userPath -notlike '*' + $customPath + '*') { [Environment]::SetEnvironmentVariable('Path', $userPath + ';' + $customPath, 'User') }"

    echo ✓ Custom installation configured
) else (
    :: Standard verification
    docx2shelf --help >nul 2>&1
    if %errorlevel% neq 0 (
        echo docx2shelf not found on PATH. Attempting to locate and add to PATH...

    :: Find potential paths where docx2shelf might be installed
    set "FOUND_PATH="

    :: Check pipx path
    for /f "delims=" %%i in ('%PYTHON_CMD% -c "import os; print(os.path.join(os.path.expanduser('~'), '.local', 'bin'))" 2^>nul') do (
        if exist "%%i\docx2shelf.exe" (
            set "FOUND_PATH=%%i"
            goto :found
        )
    )

    :: Check Python Scripts path
    for /f "delims=" %%i in ('%PYTHON_CMD% -c "import sys; print(sys.exec_prefix + '\\Scripts')" 2^>nul') do (
        if exist "%%i\docx2shelf.exe" (
            set "FOUND_PATH=%%i"
            goto :found
        )
    )

    :: Check user site-packages scripts
    for /f "delims=" %%i in ('%PYTHON_CMD% -c "import site, os; print(os.path.join(site.getusersitepackages(), '..', '..', 'Scripts'))" 2^>nul') do (
        if exist "%%i\docx2shelf.exe" (
            set "FOUND_PATH=%%i"
            goto :found
        )
    )

    :found
    if defined FOUND_PATH (
        echo Found docx2shelf at: !FOUND_PATH!

        :: Add to current session
        set "PATH=!PATH!;!FOUND_PATH!"

        :: Add to permanent PATH for current user
        echo Adding !FOUND_PATH! to user PATH permanently...
        powershell -Command "$foundPath = '!FOUND_PATH!'; $userPath = [Environment]::GetEnvironmentVariable('Path','User'); if ($userPath -notlike '*' + $foundPath + '*') { [Environment]::SetEnvironmentVariable('Path', $userPath + ';' + $foundPath, 'User') }"

        echo PATH updated successfully
    ) else (
        echo WARNING: Could not locate docx2shelf executable
        echo You may need to manually add Python Scripts directory to your PATH
    )
)

:: Final verification
echo.
echo Final verification...
docx2shelf --help >nul 2>&1
set "VERIFICATION_RESULT=%errorlevel%"

if %VERIFICATION_RESULT% equ 0 (
    echo ✓ docx2shelf is working correctly
) else (
    echo ⚠️  docx2shelf command verification failed
)

if %VERIFICATION_RESULT% equ 0 (
    echo.
    echo ========================================
    echo    Installation Successful!
    echo ========================================
    echo.
    echo ✅ Docx2Shelf is now installed and available globally.
    if defined CUSTOM_INSTALL_PATH (
        echo 📁 Custom installation location: %CUSTOM_INSTALL_PATH%
    )
    echo 📦 Installation source: GitHub repository
    echo 🎉 Installation completed successfully!
    echo.
    echo Quick start:
    echo   docx2shelf --help          - Show help
    echo   docx2shelf build           - Build EPUB from DOCX
    echo   docx2shelf wizard          - Interactive wizard
    echo   docx2shelf ai --help       - AI-powered features
    echo   docx2shelf enterprise      - Enterprise features (v1.3.4+)
    echo.
    echo If you're using a new terminal window and get "command not found",
    echo restart your terminal or Command Prompt to refresh the PATH.
    echo.
    echo ⚠️  IMPORTANT: Close this window when ready to continue.
    echo.
    echo Installation completed successfully!
    echo Press any key to exit...
    pause >nul
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
    echo 2. Run: refreshenv (if you have Chocolatey)
    echo 3. Log out and log back in to Windows
    echo.
    echo If issues persist, you can run docx2shelf directly:
    if defined FOUND_PATH (
        echo   "!FOUND_PATH!\docx2shelf.exe" --help
    )
    echo.
    echo ⚠️  IMPORTANT: Installation had issues. Please read above for solutions.
    echo.
    echo Press any key to exit...
    pause >nul
)

:: Script end - ensure pause before exit
echo.
echo FAILSAFE: If you see this message, please report it as a bug.
echo Press any key to exit...
pause >nul
exit /b 0

:install_python
:: Automatic Python installation subroutine
echo.
echo ========================================
echo    Installing Python Automatically
echo ========================================
echo.

:: Check Windows architecture
if "%PROCESSOR_ARCHITECTURE%"=="AMD64" (
    set "ARCH=amd64"
) else if "%PROCESSOR_ARCHITEW6432%"=="AMD64" (
    set "ARCH=amd64"
) else (
    set "ARCH=win32"
)

:: Set Python download URL (latest stable version)
:: Using Python 3.11.9 for maximum compatibility
set "PYTHON_VERSION=3.11.9"
set "PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-%ARCH%.exe"

:: Alternative: Use Python 3.12.1 for latest features (uncomment to use)
:: set "PYTHON_VERSION=3.12.1"
:: set "PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-%ARCH%.exe"
set "PYTHON_INSTALLER=%TEMP%\python-installer.exe"

echo Downloading Python %PYTHON_VERSION% for %ARCH%...
echo From: %PYTHON_URL%
echo.

:: Download Python installer
powershell -Command "try { (New-Object Net.WebClient).DownloadFile('%PYTHON_URL%', '%PYTHON_INSTALLER%') } catch { exit 1 }"
if %errorlevel% neq 0 (
    echo Failed to download Python installer
    echo.
    echo Trying alternative download method...
    curl -L -o "%PYTHON_INSTALLER%" "%PYTHON_URL%"
    if %errorlevel% neq 0 (
        echo Failed to download Python with curl
        echo.
        echo Please check your internet connection and try again
        echo Or download Python manually from https://python.org
        echo.
        pause
        exit /b 1
    )
)

if not exist "%PYTHON_INSTALLER%" (
    echo Python installer download failed
    echo Please check your internet connection and try again
    pause
    exit /b 1
)

echo Python installer downloaded successfully

:: Verify file size (basic integrity check)
for %%F in ("%PYTHON_INSTALLER%") do set "FILE_SIZE=%%~zF"
if %FILE_SIZE% LSS 10000000 (
    echo Warning: Downloaded file seems too small (%FILE_SIZE% bytes)
    echo This might indicate a download error
    set /p "CONTINUE_ANYWAY=Continue with installation anyway? (y/N): "
    if /i not "!CONTINUE_ANYWAY!"=="y" (
        echo Installation cancelled
        del /f /q "%PYTHON_INSTALLER%" 2>nul
        pause
        exit /b 1
    )
) else (
    echo Downloaded file size: %FILE_SIZE% bytes - looks good
)
echo.

:: Install Python silently with all options enabled
echo Installing Python %PYTHON_VERSION%...
echo This may take a few minutes...
echo.

:: Install with these options:
:: /quiet - Silent installation
:: InstallAllUsers=0 - Install for current user only (no admin required)
:: PrependPath=1 - Add Python to PATH
:: AssociateFiles=1 - Associate .py files
:: Include_launcher=1 - Install Python launcher
:: Include_test=0 - Skip test suite
:: Include_doc=0 - Skip documentation
:: Include_dev=0 - Skip development headers
:: Include_pip=1 - Include pip
:: Include_tcltk=1 - Include tkinter

"%PYTHON_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 AssociateFiles=1 Include_launcher=1 Include_test=0 Include_doc=0 Include_dev=0 Include_pip=1 Include_tcltk=1

if %errorlevel% neq 0 (
    echo Python installation failed with error code %errorlevel%
    echo.
    echo Trying installation with different options...

    :: Try with minimal options if full install fails
    "%PYTHON_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1

    if %errorlevel% neq 0 (
        echo Python installation failed
        echo.
        echo Please try installing Python manually:
        echo 1. Download from https://python.org
        echo 2. Run the installer as Administrator
        echo 3. Make sure to check "Add Python to PATH"
        echo.
        del /f /q "%PYTHON_INSTALLER%" 2>nul
        pause
        exit /b 1
    )
)

echo Python installation completed
echo.

:: Clean up installer
del /f /q "%PYTHON_INSTALLER%" 2>nul

:: Refresh environment variables for current session
echo Refreshing environment variables...
call :refresh_env

:: Wait a moment for installation to complete
timeout /t 3 /nobreak >nul

echo Python installation process finished
echo.
exit /b 0

:refresh_env
:: Refresh environment variables from registry
for /f "usebackq tokens=2,*" %%A in (`reg query HKCU\Environment /v PATH 2^>nul`) do set "USER_PATH=%%B"
for /f "usebackq tokens=2,*" %%A in (`reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH 2^>nul`) do set "SYSTEM_PATH=%%B"

if defined USER_PATH if defined SYSTEM_PATH (
    set "PATH=%SYSTEM_PATH%;%USER_PATH%"
) else if defined SYSTEM_PATH (
    set "PATH=%SYSTEM_PATH%"
) else if defined USER_PATH (
    set "PATH=%USER_PATH%"
)
exit /b 0

endlocal