#!/data/data/com.termux/files/usr/bin/sh
# reiniciar_tribu.sh - Reinicia La Tribu en Termux con Cloudflare Tunnel

cd ~/plantillaFlask2026

# Evitar que Android duerma Termux mientras corre
termux-wake-lock

echo "[*] Cerrando procesos anteriores..."
pkill -f "python app.py" 2>/dev/null || true
pkill -f "cloudflared" 2>/dev/null || true
sleep 2

echo "[*] Limpiando cache compilada..."
rm -rf __pycache__
rm -rf routes/__pycache__

echo "[*] Actualizando desde GitHub..."
git pull

echo "[*] Iniciando Flask en segundo plano..."
nohup python app.py > flask.log 2>&1 &

echo "[*] Iniciando Cloudflare Tunnel..."
if [ -f ~/.cloudflared_token ]; then
    TOKEN=$(cat ~/.cloudflared_token)
    nohup ./cloudflared tunnel run --token "$TOKEN" > cloudflared.log 2>&1 &
    echo "[OK] La Tribu y Cloudflare reiniciados."
    echo "    Flask: https://localhost:5050"
    echo "    Dominio: https://latribu.top"
else
    echo "[OK] Flask reiniciado, pero no se encontro ~/.cloudflared_token"
    echo "    Solo local: https://localhost:5050"
fi

echo "[*] Para ver logs: cat flask.log  |  cat cloudflared.log"
