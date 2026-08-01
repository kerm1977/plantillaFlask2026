#!/data/data/com.termux/files/usr/bin/sh
# CONFIGURACIÓN AUTOMÁTICA DE FAILOVER
# Este script configura el monitoreo automático en el celular

echo "============================================================"
echo "CONFIGURACIÓN DE FAILOVER - LA TRIBU"
echo "============================================================"

# Instalar tmux si no está instalado
if ! command -v tmux &> /dev/null; then
    echo "[!] Instalando tmux..."
    pkg install -y tmux
fi

# Instalar termux-boot si no está instalado
if ! command -v termux-boot &> /dev/null; then
    echo "[!] Instalando termux-boot..."
    pkg install -y termux-boot
fi

# Crear directorio de boot
mkdir -p ~/.termux/boot

# Pedir IP de la PC
echo ""
echo "Por favor, ingresa la IP local de tu computadora:"
echo "(Ejemplo: 192.168.100.187)"
read -p "IP de la PC: " PC_IP

# Actualizar el script de monitoreo con la IP correcta
sed -i "s/IP_PC=\"192.168.100.187\"/IP_PC=\"$PC_IP\"/" ~/plantillaFlask2026/failover_monitor.sh

# Dar permisos de ejecución
chmod +x ~/plantillaFlask2026/failover_monitor.sh

# Crear script de arranque automático para el monitoreo
cat > ~/.termux/boot/start_failover.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/sh
termux-wake-lock
sleep 15
cd ~/plantillaFlask2026
./failover_monitor.sh
EOF

chmod +x ~/.termux/boot/start_failover.sh

echo ""
echo "============================================================"
echo "CONFIGURACIÓN COMPLETADA"
echo "============================================================"
echo "IP de la PC configurada: $PC_IP"
echo ""
echo "El monitoreo se iniciará automáticamente al:"
echo "  - Reiniciar el celular"
echo "  - O manualmente con: cd ~/plantillaFlask2026 && ./failover_monitor.sh"
echo ""
echo "Para ver el estado del monitoreo:"
echo "  - Usa otra sesión de tmux: tmux new -s monitor"
echo "  - O detén el monitoreo con Ctrl+C"
echo ""
echo "Para ver el servidor cuando esté activo:"
echo "  - tmux attach -t latribu"
echo "============================================================"
