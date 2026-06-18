@echo off
setlocal enabledelayedexpansion
title THE CABINET - CORE INITIALIZATION SYSTEM
mode con: cols=90 lines=30
color 0A

:: --- RETRO TERMINAL HEADER ---
echo ==========================================================================
echo   __  __  _   _   ___     ___    _    ___    _  _   _____  _____ 
echo  ^|  \/  ^| ^| ^| ^| ^| ^| _ \   / __^|  /_\  ^| _ )  ^| ^|^| ^| ^|  ___^|^|_   _^|
echo  ^| ^|\/^| ^| ^| ^|_^| ^| ^|   /  ^| (__  / _ \ ^| _ \  ^| __ ^| ^|  __^|   ^| ^|  
echo  ^|_^|  ^|_^|  \___/  ^|_^|_\   \___^|/_/ \_\^|___/  ^|_^|^|_^| ^|_____^|  ^|_^|  
echo                                                                      
echo ==========================================================================
echo [SYSTEM]: CORE INITIALIZATION MODULE V3.14
echo [SYSTEM]: SECURITY LIMITERS BYPASSED. OVERCLOCK STACK READY.
echo --------------------------------------------------------------------------
timeout /t 2 >nul

:: --- STEP 1: DETECT DESKTOP ENVIRONMENT ---
echo [STATUS]: SCANNING DISK PATH MATRIX...
set "DESKTOP_DIR="

:: Check Local Desktop
if exist "%USERPROFILE%\Desktop" (
    set "DESKTOP_DIR=%USERPROFILE%\Desktop"
    echo [OK]: LOCAL DESKTOP NODE DETECTED.
)

:: Check OneDrive Desktop Overrides
if exist "%USERPROFILE%\OneDrive\Desktop" (
    set "DESKTOP_DIR=%USERPROFILE%\OneDrive\Desktop"
    echo [OK]: ONEDRIVE DESKTOP OVERRIDE ATTAINED.
)

:: Fallback Vector
if "%DESKTOP_DIR%"=="" (
    set "DESKTOP_DIR=%USERPROFILE%\OneDrive"
    echo [WARN]: DESKTOP NOT FOUND. FALLING BACK TO ROOT VECTOR.
)
set "TARGET_FOLDER=%DESKTOP_DIR%\CABINET"
timeout /t 1 >nul

:: --- STEP 2: DEPENDENCY INJECTION ---
echo --------------------------------------------------------------------------
echo [STATUS]: PIPING PYTHON EXTENSION PACKAGES...
python -m pip install --upgrade pip --quiet
echo [STATUS]: FETCHING PYGAME ENGINE MATRIX...
python -m pip install pygame-ce --quiet
if %errorlevel% neq 0 (
    python -m pip install pygame --quiet
)
echo [OK]: PYTHON ARCHITECTURE PRIMED.
timeout /t 1 >nul

:: --- STEP 3: REPOSITORY EXTRACTION ---
echo --------------------------------------------------------------------------
echo [STATUS]: OPENING DOWNLINK STREAM TO GITHUB REPOSITORY...
set "REPO_URL=https://github.com/andomatthew1234/CABINET/archive/refs/heads/main.zip"
set "ZIP_FILE=%TEMP%\cabinet_source.zip"
set "EXTRACT_TEMP=%TEMP%\cabinet_extract"

:: PowerShell Payload: Download & Silent Extract
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%REPO_URL%' -OutFile '%ZIP_FILE%'"
echo [OK]: INBOUND PAYLOAD CACHED. EXTRACTING SPATIAL FILE TREE...

if exist "%EXTRACT_TEMP%" rmdir /s /q "%EXTRACT_TEMP%"
powershell -Command "Expand-Archive -Path '%ZIP_FILE%' -DestinationPath '%EXTRACT_TEMP%' -Force"

:: Secure directory deployment
if exist "%TARGET_FOLDER%" rmdir /s /q "%TARGET_FOLDER%"
xcopy "%EXTRACT_TEMP%\CABINET-main\*" "%TARGET_FOLDER%\" /E /I /Y /Q >nul

:: Cleanup caches
del "%ZIP_FILE%"
rmdir /s /q "%EXTRACT_TEMP%"
echo [OK]: FILE MATRIX SPLICED TO %TARGET_FOLDER%
timeout /t 1 >nul

:: --- STEP 4: SHORTCUT CREATION ---
echo --------------------------------------------------------------------------
echo [STATUS]: C
set "SCRIPT_PATH=%TARGET_FOLDER%\other\welcome.py"
set "SHORTCUT_PATH=%DESKTOP_DIR%\THE CABINET.lnk"

powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT_PATH%'); $Shortcut.TargetPath = 'python.exe'; $Shortcut.Arguments = '\"%SCRIPT_PATH%\"'; $Shortcut.WorkingDirectory = '%TARGET_FOLDER%'; $Shortcut.Description = 'Ignite The Cabinet'; $Shortcut.Save()"
echo [OK]: ICON INTERACTIVE LINK EXTRACTED TO DESKTOP node.
timeout /t 1 >nul

:: --- STEP 5: SYSTEM WAKE (FIXED LAUNCH PIPELINE) ---
echo --------------------------------------------------------------------------
echo [SYSTEM]: MANDATORY PROTOCOLS COMPLETE.
echo [SYSTEM]: IGNITING THE ENGINE...
timeout /t 2 >nul

:: Launch using absolute paths inside a detached window instance to prevent crash
start /d "%TARGET_FOLDER%" python "%TARGET_FOLDER%\other\welcome.py"
exit