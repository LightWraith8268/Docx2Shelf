@echo off
setlocal enabledelayedexpansion

:: Docx2Shelf Installer for Windows
:: This script installs Python (if needed) and Docx2Shelf, ensuring both are available globally on PATH
:: Features:
:: - Automatic Python 3.11+ installation if not found
:: - Multiple installation fallback methods
:: - Automatic PATH configuration
:: - User-friendly error handling and diagnostics

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
for /f "tokens=2" %%v in ('%PYTHON_CMD% -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2^>nul') do set "PYTHON_VERSION=%%v"

if defined PYTHON_VERSION (
    echo Python version: %PYTHON_VERSION%

    :: Check if version is 3.11 or higher
    %PYTHON_CMD% -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" 2>nul
    if %errorlevel% neq 0 (
        echo.
        echo WARNING: Python %PYTHON_VERSION% is installed but Docx2Shelf requires Python 3.11+
        echo.
        set /p "UPGRADE_PYTHON=Would you like to upgrade Python automatically? (Y/n): "
        if /i "!UPGRADE_PYTHON!"=="n" (
            echo Continuing with current Python version...
            echo Note: Some features may not work correctly with Python %PYTHON_VERSION%
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
    for /f "delims=" %%i in ('%PYTHON_CMD% -c "import sys; print(f'{sys.exec_prefix}\\Scripts')"') do set "PYTHON_SCRIPTS=%%i"
    if exist "!PYTHON_SCRIPTS!" (
        set "PATH=!PATH!;!PYTHON_SCRIPTS!"
        echo Added !PYTHON_SCRIPTS! to current session PATH
    )
)

echo pipx is available

:: Install Docx2Shelf with enhanced error handling
echo Installing Docx2Shelf...

:: Method 1: Try pipx with current package
echo Method 1: Installing with pipx...
pipx install docx2shelf[docx] --force
if %errorlevel% equ 0 (
    echo ✓ Installation successful with pipx
    goto :verify_install
)

echo ❌ pipx installation failed. Trying fallback methods...

:: Method 2: Try with pip and user install
echo Method 2: Installing with pip (user)...
%PYTHON_CMD% -m pip install --user docx2shelf[docx] --upgrade
if %errorlevel% equ 0 (
    echo ✓ Installation successful with pip (user)
    goto :verify_install
)

:: Method 3: Try without extras
echo Method 3: Installing without extras...
%PYTHON_CMD% -m pip install --user docx2shelf --upgrade
if %errorlevel% equ 0 (
    echo ✓ Installation successful without extras
    echo ⚠️  Note: Installing DOCX support separately...
    %PYTHON_CMD% -m pip install --user python-docx
    goto :verify_install
)

:: Method 4: Try installing dependencies individually
echo Method 4: Installing dependencies separately...
echo Installing core dependencies...
%PYTHON_CMD% -m pip install --user ebooklib
%PYTHON_CMD% -m pip install --user python-docx
%PYTHON_CMD% -m pip install --user docx2shelf
if %errorlevel% equ 0 (
    echo ✓ Installation successful with separate dependencies
    goto :verify_install
)

:: Method 5: Try from GitHub (development version)
echo Method 5: Trying development version from GitHub...
%PYTHON_CMD% -m pip install --user git+https://github.com/anthropics/docx2shelf.git
if %errorlevel% equ 0 (
    echo ✓ Installation successful from GitHub
    goto :verify_install
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
docx2shelf --version >nul 2>&1
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
    for /f "delims=" %%i in ('%PYTHON_CMD% -c "import sys; print(f'{sys.exec_prefix}\\Scripts')" 2^>nul') do (
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
        powershell -Command "$env:Path = [Environment]::GetEnvironmentVariable('Path','User'); if ($env:Path -notlike '*!FOUND_PATH!*') { [Environment]::SetEnvironmentVariable('Path', $env:Path + ';!FOUND_PATH!', 'User') }"

        echo PATH updated successfully
    ) else (
        echo WARNING: Could not locate docx2shelf executable
        echo You may need to manually add Python Scripts directory to your PATH
    )
)

:: Final verification
echo.
echo Final verification...
docx2shelf --version
if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo    Installation Successful!
    echo ========================================
    echo.
    echo Docx2Shelf is now installed and available globally.
    echo.
    echo Quick start:
    echo   docx2shelf --help          - Show help
    echo   docx2shelf                 - Interactive mode
    echo   docx2shelf gui             - Launch GUI
    echo   docx2shelf web             - Start web interface
    echo.
    echo If you're using a new terminal window and get "command not found",
    echo restart your terminal or Command Prompt to refresh the PATH.
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
)

echo.
pause
goto :eof

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
        exit /b 1
    )
)

if not exist "%PYTHON_INSTALLER%" (
    echo Python installer download failed
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
        del /f /q "%PYTHON_INSTALLER%" 2>nul
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