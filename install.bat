@echo off
setlocal enabledelayedexpansion
color 0A
mode con: cols=90 lines=30
cls

echo ==========================================================================================
echo  [SYSTEM_INIT] INITIALIZING THE CABINET AUTOMATED INSTALLER...
echo ==========================================================================================
echo.

:: --------------------------------------------------------------------------------------------
:: PHASE 1: HARDWARE & ENVIRONMENT VERIFICATION
:: --------------------------------------------------------------------------------------------
echo  [PHASE 1] VERIFYING PYTHON KERNEL ENVIRONMENT...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [!_WARN] PYTHON NOT DETECTED. INITIALIZING WINGET OVERRIDE...
    echo  [WINGET] FETCHING LATEST PYTHON CORE EXEC...
    winget install --id Python.Python.3.14 --silent --accept-package-agreements --accept-source-agreements >nul 2>&1
    
    :: Re-check environment path variable state after package insertion
    refreshenv >nul 2>&1
    python --version >nul 2>&1
    if !errorlevel! neq 0 (
        echo  [FATAL] PYTHON CORE DEPLOYMENT FAILED. PLEASE INSTALL MANUALLY.
        pause
        exit /b
    )
) else (
    echo  [SYSTEM] PYTHON RUNTIME DETECTION: OK()
)

:: --------------------------------------------------------------------------------------------
:: PHASE 2: PATHWAY RESOLUTION (Local Desktop vs OneDrive Desktop)
:: --------------------------------------------------------------------------------------------
echo.
echo  [PHASE 2] SCANNING STORAGE TARGET BOUNDARIES...

:: Query the Windows Registry directly to find the explicit active Desktop matrix location
set "DESKTOP_PATH="
for /f "tokens=2*" %%A in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders" /v "Desktop" 2^>nul') do set "DESKTOP_PATH=%%B"

:: Fallback matrices if the registry parsing pipeline encounters turbulence
if not defined DESKTOP_PATH set "DESKTOP_PATH=%USERPROFILE%\OneDrive\Desktop"
if not exist "!DESKTOP_PATH!" set "DESKTOP_PATH=%USERPROFILE%\Desktop"
if not exist "!DESKTOP_PATH!" set "DESKTOP_PATH=%USERPROFILE%\OneDrive\Desktop"

:: Strip explicit environment literal string prefixes if present
set "DESKTOP_PATH=!DESKTOP_PATH:%%USERPROFILE%%=%USERPROFILE%!"

echo  [SYSTEM] TARGET DESKTOP RECOGNIZED: !DESKTOP_PATH!
set "TARGET_DIR=!DESKTOP_PATH!\CABINET"
set "ZIP_FILE=%TEMP%\cabinet_source.zip"

:: --------------------------------------------------------------------------------------------
:: PHASE 3: SOURCE FETCH & DECOMPRESSION PIPELINE
:: --------------------------------------------------------------------------------------------
echo.
echo  [PHASE 3] FETCHING ARSENAL FROM GITHUB CORE REPOSITORY...

if exist "!TARGET_DIR!" (
    echo  [UPGRADE] RESTRUCTURING EXISTENT SOURCE BLOCKS...
    rmdir /s /q "!TARGET_DIR!"
)

echo  [NET] STREAMS ESTABLISHED. DOWNLOADING STACK MATRIX...
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://github.com/andomatthew1234/CABINET/archive/refs/heads/main.zip' -OutFile '%ZIP_FILE%'"

echo  [ZIP] EXTRACTING SOURCE STRUCTS TO DESTINATION DIRECTORY...
powershell -Command "Expand-Archive -Path '%ZIP_FILE%' -DestinationPath '%TEMP%\cabinet_temp' -Force"

:: GitHub wraps zip files in a root directory name project-branch. We resolve that wrapper.
for /d %%I in ("%TEMP%\cabinet_temp\*") do move "%%I" "!TARGET_DIR!" >nul
del /f /q "%ZIP_FILE%" >nul
rmdir /s /q "%TEMP%\cabinet_temp" >nul

echo  [SYSTEM] MOUNTING CORE MODULES... OK()

:: --------------------------------------------------------------------------------------------
:: PHASE 4: DEPENDENCY INSTALLATION
:: --------------------------------------------------------------------------------------------
echo.
echo  [PHASE 4] RESOLVING SOFTWARE DEPENDENCIES...
cd /d "!TARGET_DIR!"
echo  [PIP] COMPILING AND INJECTING PYGAME ASSETS...
python -m pip install --upgrade pip --quiet
python -m pip install pygame-ce --quiet

:: --------------------------------------------------------------------------------------------
:: PHASE 5: SHORTCUT COMPILATION & SYSTEM LAUNCH
:: --------------------------------------------------------------------------------------------
echo.
echo  [PHASE 5] COMPILING WINDOWS SYSTEM SHORTCUT DEPLOYMENT...
set "SCRIPT_PATH=!TARGET_DIR!\other\welcome.py"
set "SHORTCUT_PATH=!DESKTOP_PATH!\THE CABINET.lnk"

powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT_PATH%'); $Shortcut.TargetPath = 'python.exe'; $Shortcut.Arguments = '\"%SCRIPT_PATH%\"'; $Shortcut.WorkingDirectory = '!TARGET_DIR!'; $Shortcut.IconLocation = 'shell32.dll,24'; $Shortcut.Save()"

echo  [SYSTEM] THE CABINET DEPLOYMENT SUCCESSFUL.
echo  ==========================================================================================
echo   INITIALIZATION COMPLETE. TRANSFERRING CONTROL MATRIX TO OTHER/WELCOME.PY...
echo  ==========================================================================================
echo.
timeout /t 3 >nul

:: Boot up the beast
python "!SCRIPT_PATH!"
exit