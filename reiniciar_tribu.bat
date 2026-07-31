@echo off
:: reiniciar_tribu.bat - Reinicia el servidor de La Tribu

cd /d "%~dp0"

echo [*] Cerrando procesos en el puerto 5050...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5050 ^| findstr LISTENING') do taskkill /F /PID %%a > nul 2>&1

echo [*] Eliminando cache compilada...
if exist "__pycache__" rmdir /S /Q "__pycache__"
if exist "routes\__pycache__" rmdir /S /Q "routes\__pycache__"

echo [*] Iniciando ejecutarR.bat...
start "" "ejecutarR.bat"

echo [OK] Proceso de reinicio iniciado.
timeout /t 5
