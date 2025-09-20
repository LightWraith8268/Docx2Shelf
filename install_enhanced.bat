@echo off
setlocal enabledelayedexpansion

:: Enhanced Docx2Shelf Installer for Windows
:: This script provides robust installation with multiple fallback mechanisms

echo ========================================
echo    Docx2Shelf Enhanced Windows Installer
echo ========================================
echo.

:: Configuration
set "INSTALL_METHOD="
set "PACKAGE_NAME=docx2shelf"
set "PACKAGE_EXTRAS=[docx]"
set "MIN_PYTHON_VERSION=3.11"
set "GITHUB_REPO=https://github.com/anthropics/docx2shelf"
set "LOCAL_WHEEL_PATH="

:: Parse command line arguments
:parse_args
if "%~1"=="" goto :args_done
if "%~1"=="--local" (
    set "INSTALL_METHOD=local"
    shift
    goto :parse_args
)
if "%~1"=="--wheel" (
    set "LOCAL_WHEEL_PATH=%~2"
    set "INSTALL_METHOD=wheel"
    shift
    shift
    goto :parse_args
)
if "%~1"=="--dev" (
    set "INSTALL_METHOD=dev"
    shift
    goto :parse_args
)
if "%~1"=="--help" (
    goto :show_help
)
shift
goto :parse_args

:args_done

:: Function to check Python version
:check_python_version
echo Checking Python version compatibility...
for /f "tokens=2 delims= " %%a in ('%PYTHON_CMD% --version 2^>^&1') do set "PYTHON_VERSION=%%a"
echo Found Python version: %PYTHON_VERSION%

:: Basic version check (simplified - checks if it starts with 3.1)
echo %PYTHON_VERSION% | findstr "^3\.1" >nul
if %errorlevel% equ 0 (
    echo ✓ Python version is compatible
    goto :python_ok
)

echo ❌ Python version %PYTHON_VERSION% may not be compatible
echo Docx2Shelf requires Python %MIN_PYTHON_VERSION% or higher
echo.
echo Options:
echo 1. Continue anyway (may fail)
echo 2. Exit and upgrade Python
echo.
set /p "choice=Enter choice (1 or 2): "
if "%choice%"=="2" (
    echo Visit https://python.org to download Python %MIN_PYTHON_VERSION%+
    pause
    exit /b 1
)
echo Continuing with potentially incompatible Python version...

:python_ok

:: Check for Python installation
echo Checking for Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    py --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo ❌ ERROR: Python not found
        echo.
        echo Please install Python %MIN_PYTHON_VERSION%+ from https://python.org
        echo Make sure to check "Add Python to PATH" during installation.
        echo.
        echo After installing Python, run this installer again.
        pause
        exit /b 1
    )
    set "PYTHON_CMD=py"
) else (
    set "PYTHON_CMD=python"
)

echo ✓ Python found: %PYTHON_CMD%
call :check_python_version

:: Determine installation method if not specified
if not defined INSTALL_METHOD (
    echo.
    echo Determining best installation method...

    :: Check if we're in a development environment
    if exist "pyproject.toml" (
        if exist "src\docx2shelf" (
            echo ✓ Development environment detected
            set "INSTALL_METHOD=dev"
            goto :install_method_determined
        )
    )

    :: Check for local wheel file
    for %%f in (dist\*.whl) do (
        if exist "%%f" (
            echo ✓ Local wheel file found: %%f
            set "LOCAL_WHEEL_PATH=%%f"
            set "INSTALL_METHOD=wheel"
            goto :install_method_determined
        )
    )

    :: Default to PyPI
    set "INSTALL_METHOD=pypi"
)

:install_method_determined
echo ✓ Installation method: %INSTALL_METHOD%

:: Install or verify pipx for non-dev installations
if not "%INSTALL_METHOD%"=="dev" (
    call :setup_pipx
)

:: Perform installation based on method
echo.
echo ========================================
echo    Installing Docx2Shelf
echo ========================================
echo.

if "%INSTALL_METHOD%"=="dev" (
    call :install_dev
) else if "%INSTALL_METHOD%"=="wheel" (
    call :install_wheel
) else if "%INSTALL_METHOD%"=="local" (
    call :install_local
) else (
    call :install_pypi
)

if %errorlevel% neq 0 (
    echo.
    echo ❌ Primary installation method failed
    echo Attempting fallback installation methods...
    call :try_fallback_installation
)

:: Verify installation
call :verify_installation

goto :end

:: Functions

:setup_pipx
echo Checking for pipx...
pipx --version >nul 2>&1
if %errorlevel% neq 0 (
    echo pipx not found. Installing pipx...
    %PYTHON_CMD% -m pip install --user pipx
    if %errorlevel% neq 0 (
        echo ❌ Failed to install pipx
        echo Falling back to pip installation method...
        set "INSTALL_METHOD=pip_fallback"
        goto :eof
    )

    :: Ensure pipx is available
    %PYTHON_CMD% -m pipx ensurepath

    :: Add pipx to current session PATH
    call :add_pipx_to_path
)
echo ✓ pipx is available
goto :eof

:add_pipx_to_path
for /f "delims=" %%i in ('%PYTHON_CMD% -c "import os; print(os.path.join(os.path.expanduser('~'), '.local', 'bin'))"') do set "PIPX_BIN=%%i"
if exist "!PIPX_BIN!" (
    set "PATH=!PATH!;!PIPX_BIN!"
    echo ✓ Added !PIPX_BIN! to current session PATH
)

:: Also try Windows-specific path
for /f "delims=" %%i in ('%PYTHON_CMD% -c "import sys, os; print(os.path.join(sys.exec_prefix, 'Scripts'))"') do set "PYTHON_SCRIPTS=%%i"
if exist "!PYTHON_SCRIPTS!" (
    set "PATH=!PATH!;!PYTHON_SCRIPTS!"
    echo ✓ Added !PYTHON_SCRIPTS! to current session PATH
)
goto :eof

:install_dev
echo Installing from development source...
if not exist "pyproject.toml" (
    echo ❌ ERROR: Not in a development directory
    echo pyproject.toml not found
    exit /b 1
)

%PYTHON_CMD% -m pip install -e .[dev]
if %errorlevel% neq 0 (
    echo ❌ Development installation failed
    exit /b 1
)
echo ✓ Development installation completed
goto :eof

:install_wheel
echo Installing from local wheel: %LOCAL_WHEEL_PATH%
if not exist "%LOCAL_WHEEL_PATH%" (
    echo ❌ ERROR: Wheel file not found: %LOCAL_WHEEL_PATH%
    exit /b 1
)

if "%INSTALL_METHOD%"=="pip_fallback" (
    %PYTHON_CMD% -m pip install --user "%LOCAL_WHEEL_PATH%"
) else (
    pipx install "%LOCAL_WHEEL_PATH%" --force
)

if %errorlevel% neq 0 (
    echo ❌ Wheel installation failed
    exit /b 1
)
echo ✓ Wheel installation completed
goto :eof

:install_local
echo Installing from current directory...
if "%INSTALL_METHOD%"=="pip_fallback" (
    %PYTHON_CMD% -m pip install --user .
) else (
    pipx install . --force
)

if %errorlevel% neq 0 (
    echo ❌ Local installation failed
    exit /b 1
)
echo ✓ Local installation completed
goto :eof

:install_pypi
echo Installing from PyPI...
echo Attempting to install: %PACKAGE_NAME%%PACKAGE_EXTRAS%

if "%INSTALL_METHOD%"=="pip_fallback" (
    %PYTHON_CMD% -m pip install --user %PACKAGE_NAME%%PACKAGE_EXTRAS%
) else (
    pipx install %PACKAGE_NAME%%PACKAGE_EXTRAS% --force
)

if %errorlevel% neq 0 (
    echo ❌ PyPI installation failed
    exit /b 1
)
echo ✓ PyPI installation completed
goto :eof

:try_fallback_installation
echo.
echo Trying fallback installation methods...

:: Try pip instead of pipx
echo Fallback 1: Using pip instead of pipx...
%PYTHON_CMD% -m pip install --user %PACKAGE_NAME%%PACKAGE_EXTRAS%
if %errorlevel% equ 0 (
    echo ✓ Fallback pip installation succeeded
    goto :eof
)

:: Try without extras
echo Fallback 2: Installing without extras...
%PYTHON_CMD% -m pip install --user %PACKAGE_NAME%
if %errorlevel% equ 0 (
    echo ✓ Fallback installation without extras succeeded
    echo ⚠️  Note: Some features may not be available without extras
    goto :eof
)

:: Try installing dependencies separately
echo Fallback 3: Installing dependencies separately...
%PYTHON_CMD% -m pip install --user ebooklib
%PYTHON_CMD% -m pip install --user python-docx
%PYTHON_CMD% -m pip install --user %PACKAGE_NAME%
if %errorlevel% equ 0 (
    echo ✓ Fallback installation with separate dependencies succeeded
    goto :eof
)

echo ❌ All fallback installation methods failed
echo.
echo Please try:
echo 1. Check your internet connection
echo 2. Upgrade pip: %PYTHON_CMD% -m pip install --upgrade pip
echo 3. Try manual installation: %PYTHON_CMD% -m pip install --user %PACKAGE_NAME%
echo 4. Contact support with the error details above
exit /b 1

:verify_installation
echo.
echo ========================================
echo    Verifying Installation
echo ========================================
echo.

:: Try to run docx2shelf
docx2shelf --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ docx2shelf is available on PATH
    docx2shelf --version
    call :installation_success
    goto :eof
)

echo ⚠️  docx2shelf not found on PATH. Searching for installation...
call :find_and_add_to_path

:: Try again
docx2shelf --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ docx2shelf is now available
    docx2shelf --version
    call :installation_success
) else (
    call :installation_partial_success
)
goto :eof

:find_and_add_to_path
echo Searching for docx2shelf installation...
set "FOUND_PATH="

:: Search common installation paths
set "SEARCH_PATHS="
set "SEARCH_PATHS=%SEARCH_PATHS% %USERPROFILE%\.local\bin"
set "SEARCH_PATHS=%SEARCH_PATHS% %PYTHON_PREFIX%\Scripts"
set "SEARCH_PATHS=%SEARCH_PATHS% %LOCALAPPDATA%\Programs\Python\Python*\Scripts"

for %%p in (%SEARCH_PATHS%) do (
    if exist "%%p\docx2shelf.exe" (
        set "FOUND_PATH=%%p"
        goto :found_path
    )
)

:: Advanced search using Python
for /f "delims=" %%i in ('%PYTHON_CMD% -c "import os, sys, site; paths = [os.path.join(site.getusersitepackages(), '..', '..', 'Scripts'), os.path.join(sys.exec_prefix, 'Scripts'), os.path.join(os.path.expanduser('~'), '.local', 'bin')]; [print(p) for p in paths if os.path.exists(os.path.join(p, 'docx2shelf.exe'))]" 2^>nul') do (
    set "FOUND_PATH=%%i"
    goto :found_path
)

:found_path
if defined FOUND_PATH (
    echo ✓ Found docx2shelf at: !FOUND_PATH!

    :: Add to current session
    set "PATH=!PATH!;!FOUND_PATH!"

    :: Add to permanent PATH for current user
    echo Adding !FOUND_PATH! to user PATH permanently...
    powershell -NoProfile -Command "try { $currentPath = [Environment]::GetEnvironmentVariable('Path', 'User'); if ($currentPath -notlike '*!FOUND_PATH!*') { [Environment]::SetEnvironmentVariable('Path', $currentPath + ';!FOUND_PATH!', 'User'); Write-Host 'PATH updated successfully' } else { Write-Host 'Path already contains the directory' } } catch { Write-Host 'Failed to update PATH automatically' }"
) else (
    echo ❌ Could not locate docx2shelf executable
    echo Installation may have failed or executable is in an unexpected location
)
goto :eof

:installation_success
echo.
echo ========================================
echo    Installation Successful! 🎉
echo ========================================
echo.
echo Docx2Shelf is now installed and available globally.
echo.
echo Quick start:
echo   docx2shelf --help                 - Show help
echo   docx2shelf wizard                 - Interactive conversion wizard
echo   docx2shelf theme-editor           - Advanced theme editor
echo   docx2shelf build --input file.docx --title "My Book" --author "Author"
echo.
echo Advanced features:
echo   docx2shelf gui                    - Launch GUI (if available)
echo   docx2shelf web                    - Start web interface (if available)
echo   docx2shelf tools install pandoc   - Install additional tools
echo.
if not "%INSTALL_METHOD%"=="dev" (
    echo If you're using a new terminal window and get "command not found",
    echo restart your terminal or Command Prompt to refresh the PATH.
)
goto :eof

:installation_partial_success
echo.
echo ========================================
echo    Installation Partially Successful
echo ========================================
echo.
echo Docx2Shelf was installed but may not be accessible from PATH.
echo.
echo Troubleshooting:
echo 1. Restart your Command Prompt/Terminal
echo 2. Run: refreshenv (if you have Chocolatey)
echo 3. Log out and log back in to Windows
echo.
if defined FOUND_PATH (
    echo You can run docx2shelf directly using:
    echo   "!FOUND_PATH!\docx2shelf.exe" --help
) else (
    echo Try finding the installation manually:
    echo   where docx2shelf
    echo   %PYTHON_CMD% -m pip show docx2shelf
)
goto :eof

:show_help
echo.
echo Enhanced Docx2Shelf Windows Installer
echo.
echo Usage: install_enhanced.bat [OPTIONS]
echo.
echo Options:
echo   --local      Install from current directory
echo   --wheel PATH Install from specific wheel file
echo   --dev        Install in development mode (requires source)
echo   --help       Show this help message
echo.
echo Examples:
echo   install_enhanced.bat                    # Install from PyPI
echo   install_enhanced.bat --local            # Install from current directory
echo   install_enhanced.bat --wheel dist\*.whl # Install from wheel file
echo   install_enhanced.bat --dev              # Development installation
echo.
exit /b 0

:end
echo.
pause
endlocal
exit /b 0