:: ejecutar_tribu.bat
@echo off
cd /d "%~dp0"

if "%~1"=="TRIBU_WATCHER" goto tribu_watcher
if "%~1"=="TAIL_WATCHER" goto tail_watcher
if "%~1"=="CLOUD_WATCHER" goto cloud_watcher

title Lanzador Maestro (La Tribu)
color 0B

echo =======================================================
echo     SISTEMA DE ENRUTAMIENTO: CAMINATAS LA TRIBU
echo =======================================================
echo.
echo   [1] Modo Cloudflare (Solo Dominio)
echo   [2] Modo Tailscale Funnel (.ts.net)
echo   [3] Modo Hibrido Total (Ambos)
echo   [4] LIMPIEZA: Desinstalar servicio invisible
echo.
echo [!] MODO INMORTAL ACTIVO: El sistema iniciara la Opcion [1]
echo automaticamente en 10 segundos si no tocas nada...
echo.

:: Temporizador de 10 segundos que elige el 1 por defecto
choice /c 1234 /t 10 /d 1 /m "Elija una opcion:"
if errorlevel 4 goto limpiar_cloudflare
if errorlevel 3 goto iniciar_ambos
if errorlevel 2 goto iniciar_tailscale
if errorlevel 1 goto iniciar_cloudflare

:iniciar_cloudflare
echo [*] Liberando puertos...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5050 ^| findstr LISTENING') do taskkill /F /PID %%a > nul 2>&1
start "TRIBU_WATCHER" cmd /c "%~f0" TRIBU_WATCHER
start "CLOUD_WATCHER" cmd /c "%~f0" CLOUD_WATCHER
goto fin

:iniciar_tailscale
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5050 ^| findstr LISTENING') do taskkill /F /PID %%a > nul 2>&1
start "TRIBU_WATCHER" cmd /c "%~f0" TRIBU_WATCHER
start "TAIL_WATCHER" cmd /c "%~f0" TAIL_WATCHER
goto fin

:iniciar_ambos
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5050 ^| findstr LISTENING') do taskkill /F /PID %%a > nul 2>&1
start "TRIBU_WATCHER" cmd /c "%~f0" TRIBU_WATCHER
start "CLOUD_WATCHER" cmd /c "%~f0" CLOUD_WATCHER
start "TAIL_WATCHER" cmd /c "%~f0" TAIL_WATCHER
goto fin

:limpiar_cloudflare
cloudflared.exe service uninstall
pause
exit

:fin
echo.
echo =======================================================
echo   SISTEMA BLINDADO Y CORRIENDO.
echo   Si cierras las ventanas verde o amarilla, 
echo   se volveran a abrir solas a los 3 segundos.
echo =======================================================
pause
exit

:: ===================================================
:: BUCLE INFINITO: FLASK APP
:: ===================================================
:tribu_watcher
cd /d "%~dp0"
title TRIBU_APP (Local: 5050)
color 0A
set PY_CMD=python
if exist "env\Scripts\python.exe" set PY_CMD=env\Scripts\python.exe

:tribu_loop
echo [!] Corriendo La Tribu...
%PY_CMD% app.py
echo [X] SERVIDOR CAIDO O CERRADO. ¡Reviviendo en 3 segundos!
timeout /t 3 > nul
goto tribu_loop

:: ===================================================
:: BUCLE INFINITO: CLOUDFLARE TUNNEL
:: ===================================================
:cloud_watcher
cd /d "%~dp0"
title CLOUDFLARE_TUNNEL_TRIBU
color 0E

:cloud_loop
echo [!] CONECTANDO CON CLOUDFLARE...
cloudflared.exe tunnel run --token eyJhIjoiZmZhMDJmYjFkYjUwMzBhMGYzMjBlYjAxMTIxYzJjZmEiLCJ0IjoiZTY3YjVhYWQtMTVjZi00N2M4LTk3YzctZjQzNTlhMDIwNzExIiwicyI6Ik56WmlNRFpqWW1NdFkyWTRZaTAwTVdNMExXRXpPRE10WVdFeVltVTNZbUpoTkRjdyJ9
echo [X] TUNEL DESCONECTADO O CERRADO. ¡Forzando reconexion en 3 segundos!
timeout /t 3 > nul
goto cloud_loop

:: ===================================================
:: BUCLE INFINITO: TAILSCALE
:: ===================================================
:tail_watcher
cd /d "%~dp0"
title TAILSCALE_MANAGER_TRIBU
color 0D

:tail_loop
echo [!] ENRUTANDO TAILSCALE...
tailscale funnel --bg --https=8443 [http://127.0.0.1:5050](http://127.0.0.1:5050)
echo [X] TAILSCALE CERRADO. Reiniciando...
timeout /t 3 > nul
goto tail_loop
