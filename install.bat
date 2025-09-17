@echo off
setlocal

echo Searching for a compatible Python version (3.11+)...

:: Check for Python 3.12
py -3.12 -c "import sys; sys.exit(0)" 2>nul
if %errorlevel% == 0 (
    set "PYTHON_CMD=py -3.12"
    echo Found Python 3.12.
    goto :found_python
)

:: Check for Python 3.11
py -3.11 -c "import sys; sys.exit(0)" 2>nul
if %errorlevel% == 0 (
    set "PYTHON_CMD=py -3.11"
    echo Found Python 3.11.
    goto :found_python
)

echo Error: Python 3.11 or 3.12 not found.
echo Please install Python 3.11 or newer from python.org and ensure it's added to your PATH.
echo Make sure to check the box "Install launcher for all users (recommended)" during installation.
goto :eof

:found_python
echo.
echo Upgrading pip and installing pipx...
%PYTHON_CMD% -m pip install --upgrade pip
%PYTHON_CMD% -m pip install --user -U pipx
echo.

echo Ensuring pipx is in your PATH...
%PYTHON_CMD% -m pipx ensurepath
echo.
echo IMPORTANT: You may need to restart your terminal for the PATH changes to take effect.
echo.

echo Installing docx2shelf with all extras (docx, pandoc, dev)...
:: The [all] extra is interpreted from the install scripts, combining all optional dependencies.
pipx install --python %PYTHON_CMD% .[docx,pandoc,dev] --force
if %errorlevel% neq 0 (
    echo.
    echo Error: Failed to install docx2shelf.
    goto :eof
)
echo.

echo Installing optional tools (Pandoc and EPUBCheck)...
docx2shelf tools install pandoc
docx2shelf tools install epubcheck
echo.

echo Installation complete!
echo You can now use the 'docx2shelf' command from any directory.
echo If the command is not found, please restart your terminal.

endlocal
