:: ejecutar_tribu.bat
@echo off
:: ===================================================
:: CORRECCION DE RUTA (Obliga a la consola a quedarse aqui)
:: ===================================================
cd /d "%~dp0"

:: ===================================================
:: ENRUTADOR DE PROCESOS - LA TRIBU (Puerto 5050)
:: ===================================================
if "%~1"=="TRIBU_WATCHER" goto tribu_watcher
if "%~1"=="TAIL_WATCHER" goto tail_watcher
if "%~1"=="CLOUD_WATCHER" goto cloud_watcher

:: ===================================================
:: MENU PRINCIPAL INTERACTIVO
:: ===================================================
title Lanzador Maestro (La Tribu)
color 0B

echo =======================================================
echo     SISTEMA DE ENRUTAMIENTO: CAMINATAS LA TRIBU
echo =======================================================
echo.
echo Seleccione el modo de conexion que desea iniciar hoy:
echo.
echo   [1] Modo Cloudflare (Solo Dominio)
echo       - Expone tu app en latribu.top
echo       - Abre una ventana visible del tunel.
echo.
echo   [2] Modo Tailscale Funnel (Solo Subdominio .ts.net)
echo       - Expone tu app usando el tunel publico de Tailscale.
echo.
echo   [3] Modo Hibrido Total (Ambos)
echo       - Activa latribu.top Y tu dominio de Tailscale a la vez.
echo.
echo   [4] LIMPIEZA: Desinstalar servicio invisible (Solo usar 1 vez)
echo       - Borra el servicio de fondo que daba el error 1033.
echo.
set /p opcion="Elija una opcion (1, 2, 3 o 4): "

if "%opcion%"=="4" goto limpiar_cloudflare

echo.
echo [*] Preparando el entorno...
echo [*] Liberando puerto local 5050 para evitar choques...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5050 ^| findstr LISTENING') do taskkill /F /PID %%a > nul 2>&1

echo [*] Iniciando App de La Tribu (Servidor Flask)...
start "TRIBU_WATCHER" cmd /c "%~f0" TRIBU_WATCHER

if "%opcion%"=="1" goto iniciar_cloudflare
if "%opcion%"=="2" goto iniciar_tailscale
if "%opcion%"=="3" goto iniciar_ambos

:iniciar_cloudflare
echo [*] Iniciando Tunel de Cloudflare (latribu.top)...
start "CLOUD_WATCHER" cmd /c "%~f0" CLOUD_WATCHER
goto fin

:iniciar_tailscale
echo [*] Iniciando Enrutador Tailscale Funnel...
start "TAIL_WATCHER" cmd /c "%~f0" TAIL_WATCHER
goto fin

:iniciar_ambos
echo [*] Iniciando Tunel de Cloudflare (latribu.top)...
start "CLOUD_WATCHER" cmd /c "%~f0" CLOUD_WATCHER
echo [*] Iniciando Enrutador Tailscale Funnel...
start "TAIL_WATCHER" cmd /c "%~f0" TAIL_WATCHER
goto fin

:limpiar_cloudflare
echo.
echo =======================================================
echo   LIMPIANDO EL SERVICIO INVISIBLE DE CLOUDFLARE
echo =======================================================
echo ATENCION: Debiste abrir este archivo como Administrador.
echo.
cloudflared.exe service uninstall
echo.
echo [OK] Limpieza terminada. 
echo Cierra esta ventana y vuelve a abrir el archivo normalmente (Opcion 1).
pause
exit

:fin
echo.
echo =======================================================
echo   TODO LISTO. Puede minimizar o cerrar esta ventana.
echo   Veras nuevas ventanas con los servidores corriendo.
echo =======================================================
pause
exit

:: ===================================================
:: SUB-PROCESO: FLASK APP
:: ===================================================
:tribu_watcher
cd /d "%~dp0"
title TRIBU_APP (Local: 5050)
color 0A
set PY_CMD=python
if exist "env\Scripts\python.exe" set PY_CMD=env\Scripts\python.exe

:tribu_loop
echo [!] Corriendo La Tribu con: %PY_CMD%
set PORT=5050
%PY_CMD% app.py
echo [X] Caida en La Tribu. Reiniciando en 3 segundos...
timeout /t 3 > nul
goto tribu_loop

:: ===================================================
:: SUB-PROCESO: TAILSCALE FUNNEL
:: ===================================================
:tail_watcher
cd /d "%~dp0"
title TAILSCALE_MANAGER_TRIBU
color 0D
echo ===================================================
echo [!] CONFIGURANDO ENRUTAMIENTO TAILSCALE
echo ===================================================
echo.
echo [*] Creando ruta publica para LA TRIBU (Puerto 8443)...
tailscale funnel --bg --https=8443 http://127.0.0.1:5050
timeout /t 3 > nul
echo.
echo [OK] Tunnel de Tailscale creado correctamente.
exit

:: ===================================================
:: SUB-PROCESO: CLOUDFLARE TUNNEL
:: ===================================================
:cloud_watcher
cd /d "%~dp0"
title CLOUDFLARE_TUNNEL_TRIBU
color 0E
echo ===================================================
echo [!] CONECTANDO CON CLOUDFLARE (latribu.top)
echo ===================================================
echo.
cloudflared.exe tunnel run --token eyJhIjoiZmZhMDJmYjFkYjUwMzBhMGYzMjBlYjAxMTIxYzJjZmEiLCJ0IjoiZTY3YjVhYWQtMTVjZi00N2M4LTk3YzctZjQzNTlhMDIwNzExIiwicyI6Ik56WmlNRFpqWW1NdFkyWTRZaTAwTVdNMExXRXpPRE10WVdFeVltVTNZbUpoTkRjdyJ9
echo.
echo [X] El tunel se cerro inesperadamente.
pause
exit