:: ==============================================================
::   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
::   Explicar antes de editar. Contenido sagrado protegido.
:: ==============================================================
@echo off
:: reiniciar_tribu.bat - Reinicia el servidor de La Tribu

cd /d "%~dp0"

echo [*] Cerrando ventanas y procesos anteriores...
:: Si alguien hizo clic dentro de una consola, Windows la deja en modo
:: "Seleccionar ..." (congela el proceso). Se cierran ambas variantes.
taskkill /F /T /FI "WINDOWTITLE eq Lanzador Maestro (La Tribu)*" >nul 2>&1
taskkill /F /T /FI "WINDOWTITLE eq TRIBU_APP*" >nul 2>&1
taskkill /F /T /FI "WINDOWTITLE eq CLOUDFLARE_TUNNEL_TRIBU*" >nul 2>&1
taskkill /F /T /FI "WINDOWTITLE eq TAILSCALE_MANAGER_TRIBU*" >nul 2>&1
taskkill /F /T /FI "WINDOWTITLE eq Seleccionar Lanzador Maestro*" >nul 2>&1
taskkill /F /T /FI "WINDOWTITLE eq Seleccionar TRIBU_APP*" >nul 2>&1
taskkill /F /T /FI "WINDOWTITLE eq Seleccionar CLOUDFLARE_TUNNEL_TRIBU*" >nul 2>&1
taskkill /F /T /FI "WINDOWTITLE eq Seleccionar TAILSCALE_MANAGER_TRIBU*" >nul 2>&1
taskkill /F /IM cloudflared.exe >nul 2>&1

echo [*] Cerrando procesos en el puerto 5050...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5050 ^| findstr LISTENING') do taskkill /F /PID %%a > nul 2>&1

echo [*] Eliminando cache compilada...
if exist "__pycache__" rmdir /S /Q "__pycache__"
if exist "routes\__pycache__" rmdir /S /Q "routes\__pycache__"

echo [*] Iniciando La Tribu (modo directo, sin menu)...
start "TRIBU_WATCHER" cmd /c "ejecutar.bat" TRIBU_WATCHER
start "CLOUD_WATCHER" cmd /c "ejecutar.bat" CLOUD_WATCHER

echo [OK] Proceso de reinicio iniciado.
timeout /t 5
