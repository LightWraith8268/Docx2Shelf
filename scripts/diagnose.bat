@echo off
setlocal enabledelayedexpansion

:: Docx2Shelf Diagnostic Script
:: This script helps diagnose installation and configuration issues

echo ========================================
echo    Docx2Shelf Diagnostic Tool
echo ========================================
echo.

:: Create log file with timestamp
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "timestamp=%dt:~0,4%-%dt:~4,2%-%dt:~6,2%_%dt:~8,2%-%dt:~10,2%-%dt:~12,2%"
set "LOGFILE=docx2shelf_diagnostic_%timestamp%.log"

echo Diagnostic started at %timestamp% > "%LOGFILE%"
echo ========================================
echo    System Diagnostic Report
echo ========================================

:: System Information
echo.
echo [SYSTEM INFORMATION]
echo OS: >> "%LOGFILE%"
systeminfo | findstr /C:"OS Name" /C:"OS Version" /C:"System Type" >> "%LOGFILE%"
echo.

:: Python Environment
echo [PYTHON ENVIRONMENT]
echo Checking Python installation...
set "PYTHON_FOUND=0"

:: Check python command
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ python command available
    set "PYTHON_CMD=python"
    set "PYTHON_FOUND=1"
    echo Python via 'python' command: >> "%LOGFILE%"
    python --version >> "%LOGFILE%" 2>&1
    python -c "import sys; print('Executable:', sys.executable)" >> "%LOGFILE%" 2>&1
) else (
    echo ❌ python command not found
    echo python command not found >> "%LOGFILE%"
)

:: Check py launcher
py --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ py launcher available
    if %PYTHON_FOUND% equ 0 (
        set "PYTHON_CMD=py"
        set "PYTHON_FOUND=1"
    )
    echo Python via py launcher: >> "%LOGFILE%"
    py --version >> "%LOGFILE%" 2>&1
    py -c "import sys; print('Executable:', sys.executable)" >> "%LOGFILE%" 2>&1
) else (
    echo ❌ py launcher not found
    echo py launcher not found >> "%LOGFILE%"
)

if %PYTHON_FOUND% equ 0 (
    echo.
    echo ❌ CRITICAL: No Python installation found
    echo Please install Python 3.11+ from https://python.org
    echo No Python installation found >> "%LOGFILE%"
    goto :report_end
)

echo Using Python command: %PYTHON_CMD%
echo.

:: Python Path and Environment
echo [PYTHON ENVIRONMENT DETAILS]
echo Python paths and environment: >> "%LOGFILE%"
%PYTHON_CMD% -c "import sys; print('Python version:', sys.version); print('Executable:', sys.executable); print('Prefix:', sys.prefix); print('Path:', sys.path)" >> "%LOGFILE%" 2>&1

:: Package Management
echo [PACKAGE MANAGEMENT]
echo Checking pip...
%PYTHON_CMD% -m pip --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ pip available
    echo Pip version: >> "%LOGFILE%"
    %PYTHON_CMD% -m pip --version >> "%LOGFILE%" 2>&1
) else (
    echo ❌ pip not available
    echo pip not available >> "%LOGFILE%"
)

echo Checking pipx...
pipx --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ pipx available
    echo Pipx version: >> "%LOGFILE%"
    pipx --version >> "%LOGFILE%" 2>&1
    echo Pipx environment: >> "%LOGFILE%"
    pipx list >> "%LOGFILE%" 2>&1
) else (
    echo ❌ pipx not available
    echo pipx not available >> "%LOGFILE%"
)

:: Docx2Shelf Installation Check
echo.
echo [DOCX2SHELF INSTALLATION]
echo Checking docx2shelf installation...

:: Check if docx2shelf is on PATH
docx2shelf --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ docx2shelf available on PATH
    echo Docx2shelf version: >> "%LOGFILE%"
    docx2shelf --version >> "%LOGFILE%" 2>&1

    echo Docx2shelf location: >> "%LOGFILE%"
    where docx2shelf >> "%LOGFILE%" 2>&1
) else (
    echo ❌ docx2shelf not found on PATH
    echo docx2shelf not found on PATH >> "%LOGFILE%"
)

:: Check if docx2shelf is installed via pip
echo Checking pip installations: >> "%LOGFILE%"
%PYTHON_CMD% -m pip show docx2shelf >> "%LOGFILE%" 2>&1
if %errorlevel% equ 0 (
    echo ✓ docx2shelf installed via pip
) else (
    echo ❌ docx2shelf not installed via pip
)

:: Check pipx installations
echo Checking pipx installations: >> "%LOGFILE%"
pipx list | findstr docx2shelf >> "%LOGFILE%" 2>&1
if %errorlevel% equ 0 (
    echo ✓ docx2shelf installed via pipx
) else (
    echo ❌ docx2shelf not installed via pipx
)

:: PATH Analysis
echo.
echo [PATH ANALYSIS]
echo Current PATH: >> "%LOGFILE%"
echo %PATH% >> "%LOGFILE%"
echo.

echo Python Scripts directories: >> "%LOGFILE%"
%PYTHON_CMD% -c "import sys, os; scripts_dir = os.path.join(sys.exec_prefix, 'Scripts'); print('Global Scripts:', scripts_dir); print('Exists:', os.path.exists(scripts_dir))" >> "%LOGFILE%" 2>&1
%PYTHON_CMD% -c "import site, os; user_scripts = os.path.join(site.getusersitepackages(), '..', '..', 'Scripts'); print('User Scripts:', os.path.abspath(user_scripts)); print('Exists:', os.path.exists(user_scripts))" >> "%LOGFILE%" 2>&1

:: Search for docx2shelf executable
echo.
echo [EXECUTABLE SEARCH]
echo Searching for docx2shelf executable...
set "FOUND_LOCATIONS="

:: Search in common locations
set "SEARCH_PATHS="
set "SEARCH_PATHS=%SEARCH_PATHS% %USERPROFILE%\.local\bin"
set "SEARCH_PATHS=%SEARCH_PATHS% %APPDATA%\Python\Python*\Scripts"
set "SEARCH_PATHS=%SEARCH_PATHS% %LOCALAPPDATA%\Programs\Python\Python*\Scripts"

for %%p in (%SEARCH_PATHS%) do (
    if exist "%%p\docx2shelf.exe" (
        echo ✓ Found: %%p\docx2shelf.exe
        echo Found docx2shelf at: %%p\docx2shelf.exe >> "%LOGFILE%"
        set "FOUND_LOCATIONS=!FOUND_LOCATIONS! %%p"
    )
)

:: Advanced search using Python
for /f "delims=" %%i in ('%PYTHON_CMD% -c "import os, sys, site; paths = [os.path.join(site.getusersitepackages(), '..', '..', 'Scripts'), os.path.join(sys.exec_prefix, 'Scripts'), os.path.join(os.path.expanduser('~'), '.local', 'bin')]; [print(p) for p in paths if os.path.exists(os.path.join(p, 'docx2shelf.exe'))]" 2^>nul') do (
    echo ✓ Found via Python search: %%i\docx2shelf.exe
    echo Found via Python search: %%i\docx2shelf.exe >> "%LOGFILE%"
    set "FOUND_LOCATIONS=!FOUND_LOCATIONS! %%i"
)

:: Dependencies Check
echo.
echo [DEPENDENCIES CHECK]
echo Checking required dependencies...

:: Check ebooklib
%PYTHON_CMD% -c "import ebooklib; print('ebooklib version:', ebooklib.__version__)" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ ebooklib available
    echo Ebooklib: >> "%LOGFILE%"
    %PYTHON_CMD% -c "import ebooklib; print('ebooklib version:', ebooklib.__version__)" >> "%LOGFILE%" 2>&1
) else (
    echo ❌ ebooklib not available
    echo ebooklib not available >> "%LOGFILE%"
)

:: Check python-docx
%PYTHON_CMD% -c "import docx; print('python-docx available')" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ python-docx available
    echo Python-docx: available >> "%LOGFILE%"
) else (
    echo ❌ python-docx not available
    echo python-docx not available >> "%LOGFILE%"
)

:: Network Connectivity
echo.
echo [NETWORK CONNECTIVITY]
echo Checking PyPI connectivity...
%PYTHON_CMD% -c "import urllib.request; urllib.request.urlopen('https://pypi.org', timeout=5); print('PyPI reachable')" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ PyPI reachable
    echo PyPI connectivity: OK >> "%LOGFILE%"
) else (
    echo ❌ PyPI not reachable
    echo PyPI connectivity: FAILED >> "%LOGFILE%"
)

:report_end
echo.
echo ========================================
echo    Diagnostic Summary
echo ========================================
echo.

:: Generate summary
if %PYTHON_FOUND% equ 0 (
    echo ❌ CRITICAL: Python not found
    echo Please install Python 3.11+ from https://python.org
) else (
    echo ✓ Python: Found (%PYTHON_CMD%)
)

docx2shelf --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Docx2Shelf: Working
) else (
    echo ❌ Docx2Shelf: Not working
    if defined FOUND_LOCATIONS (
        echo   Found installations at: !FOUND_LOCATIONS!
        echo   Try adding one of these to PATH or restart terminal
    ) else (
        echo   No installations found - please reinstall
    )
)

echo.
echo Full diagnostic log saved to: %LOGFILE%
echo.
echo Recommended actions:
if %PYTHON_FOUND% equ 0 (
    echo 1. Install Python 3.11+ from https://python.org
)
docx2shelf --version >nul 2>&1
if %errorlevel% neq 0 (
    if defined FOUND_LOCATIONS (
        echo 1. Restart your terminal/command prompt
        echo 2. Or add to PATH: !FOUND_LOCATIONS!
    ) else (
        echo 1. Reinstall docx2shelf using: install.bat
        echo 2. Or try: %PYTHON_CMD% -m pip install --user docx2shelf[docx]
    )
)

echo 3. Run this diagnostic again to verify fixes
echo.
pause
endlocal