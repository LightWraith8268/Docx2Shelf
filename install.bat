@echo off
setlocal

:: Define the URL for the raw install.ps1 script
set "INSTALL_PS1_URL=https://raw.githubusercontent.com/LightWraith8268/Docx2Shelf/main/scripts/install.ps1"
set "TEMP_PS1_PATH=%TEMP%\install_docx2shelf.ps1"

echo Downloading the latest installer script...

powershell -Command "Invoke-WebRequest -Uri '%INSTALL_PS1_URL%' -OutFile '%TEMP_PS1_PATH%' -UseBasicParsing"
if %errorlevel% neq 0 (
    echo Error: Failed to download install.ps1. Please check your internet connection.
    goto :eof
)

echo Running the installer script...

:: Pass all arguments from install.bat to install.ps1
powershell -ExecutionPolicy Bypass -File "%TEMP_PS1_PATH%" %*
if %errorlevel% neq 0 (
    echo Error: Installation failed. See above for details.
    goto :eof
)

echo Cleaning up temporary files...
del "%TEMP_PS1_PATH%"

echo Installation process completed.

pause

endlocal