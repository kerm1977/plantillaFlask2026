#!/data/data/com.termux/files/usr/bin/sh
# MONITOR DE FAILOVER: CELULAR COMO RESPALDO DE PC
# Este script detecta si la PC está caída y levanta el servidor en el celular

# CONFIGURACIÓN
# Reemplaza IP_PC con la IP local de tu computadora
IP_PC="192.168.100.187"
INTERVALO_PING=30  # segundos entre pings
PROYECTO_DIR="$HOME/plantillaFlask2026"

echo "============================================================"
echo "MONITOR DE FAILOVER - LA TRIBU"
echo "============================================================"
echo "IP de la PC a monitorear: $IP_PC"
echo "Intervalo de verificación: $INTERVALO_PING segundos"
echo "============================================================"

# Función para verificar si el servidor está corriendo
check_server_running() {
    if tmux has-session -t latribu 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Función para levantar el servidor
start_server() {
    echo "[!] PC no responde. Levantando servidor en el celular..."
    cd "$PROYECTO_DIR" || exit 1
    
    # Detener sesión anterior si existe
    tmux kill-session -t latribu 2>/dev/null
    
    # Crear nueva sesión con el servidor
    tmux new -d -s latribu "cd $PROYECTO_DIR && python app.py"
    
    echo "[OK] Servidor levantado en el celular"
    echo "[INFO] Para ver el servidor: tmux attach -t latribu"
}

# Bucle principal de monitoreo
while true; do
    # Hacer ping a la PC
    if ping -c 1 -W 3 "$IP_PC" > /dev/null 2>&1; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] PC responde - OK"
        
        # Si el servidor está corriendo en el celular, detenerlo (la PC está activa)
        if check_server_running; then
            echo "[!] PC activa, deteniendo servidor en el celular..."
            tmux kill-session -t latribu 2>/dev/null
            echo "[OK] Servidor detenido en el celular"
        fi
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] PC NO responde - ERROR"
        
        # Si el servidor NO está corriendo, levantarlo
        if ! check_server_running; then
            start_server
        else
            echo "[INFO] Servidor ya corriendo en el celular"
        fi
    fi
    
    sleep "$INTERVALO_PING"
done
