@echo off
setlocal enabledelayedexpansion

:: Docx2Shelf Installer for Windows
:: This script installs Docx2Shelf and ensures it's available globally on PATH

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
        echo ERROR: Python not found. Please install Python 3.11+ from https://python.org
        echo Make sure to check "Add Python to PATH" during installation.
        pause
        exit /b 1
    )
    set "PYTHON_CMD=py"
) else (
    set "PYTHON_CMD=python"
)

echo Python found: %PYTHON_CMD%

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
endlocal