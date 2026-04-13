@echo off
color 0b
title Instalador de CronoGrulla

echo.
echo ==========================================
echo    Instalando CronoGrulla...
echo ==========================================
echo.

set "INSTALL_DIR=%LocalAppData%\CronoGrulla"
set "EXE_NAME=CronoGrulla.exe"

:: Crear la carpeta de instalacion
if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%"
)

:: Copiar el ejecutable
echo Copiando archivos del programa...
copy /y "CronoGrulla.exe" "%INSTALL_DIR%\%EXE_NAME%" >nul

:: Crear acceso directo en el Escritorio usando un script temporal VBS
echo Creando accesos directos...
set "VBS_SCRIPT=%temp%\crear_acceso_CronoGrulla.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%VBS_SCRIPT%"
echo sLinkFile = "%userprofile%\Desktop\CronoGrulla.lnk" >> "%VBS_SCRIPT%"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%VBS_SCRIPT%"
echo oLink.TargetPath = "%INSTALL_DIR%\%EXE_NAME%" >> "%VBS_SCRIPT%"
echo oLink.WorkingDirectory = "%INSTALL_DIR%" >> "%VBS_SCRIPT%"
echo oLink.Description = "CronoGrulla - Ingenieria de Metodos" >> "%VBS_SCRIPT%"
echo oLink.Save >> "%VBS_SCRIPT%"

cscript /nologo "%VBS_SCRIPT%"
del "%VBS_SCRIPT%"

:: Crear acceso directo en el Menu de Inicio
set "START_MENU_DIR=%appdata%\Microsoft\Windows\Start Menu\Programs\CronoGrulla"
if not exist "%START_MENU_DIR%" (
    mkdir "%START_MENU_DIR%"
)
set "VBS_SCRIPT_START=%temp%\crear_acceso_start.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%VBS_SCRIPT_START%"
echo sLinkFile = "%START_MENU_DIR%\CronoGrulla.lnk" >> "%VBS_SCRIPT_START%"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%VBS_SCRIPT_START%"
echo oLink.TargetPath = "%INSTALL_DIR%\%EXE_NAME%" >> "%VBS_SCRIPT_START%"
echo oLink.WorkingDirectory = "%INSTALL_DIR%" >> "%VBS_SCRIPT_START%"
echo oLink.Description = "CronoGrulla - Ingenieria de Metodos" >> "%VBS_SCRIPT_START%"
echo oLink.Save >> "%VBS_SCRIPT_START%"

cscript /nologo "%VBS_SCRIPT_START%"
del "%VBS_SCRIPT_START%"

echo.
echo ==========================================
echo   !Instalacion Completada con Exito!
echo ==========================================
echo Se ha creado un acceso directo en su Escritorio.
echo Puede cerrar esta ventana con total seguridad.
echo.
timeout /t 5 >nul
