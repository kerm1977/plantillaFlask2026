#!/data/data/com.termux/files/usr/bin/sh
# reiniciar_tribu.sh - Reinicia La Tribu en Termux con Cloudflare Tunnel
# Uso: ./reiniciar_tribu.sh

cd ~/plantillaFlask2026 || { echo "[!] No se encontro ~/plantillaFlask2026"; exit 1; }

# Ignorar cambios de permisos para evitar conflictos con git
command -v git >/dev/null 2>&1 && git config core.fileMode false

# Evitar que Android duerma Termux mientras corre
command -v termux-wake-lock >/dev/null && termux-wake-lock

# Asegurar que este script siga ejecutable
test -f "$0" && chmod +x "$0"

# Instalar herramientas basicas si faltan
for pkg in python git procps tmux wget; do
    if ! command -v $pkg >/dev/null 2>&1; then
        echo "[*] Instalando $pkg..."
        pkg install -y $pkg
    fi
done

echo "[*] Cerrando procesos anteriores..."
pkill -f "python app.py" 2>/dev/null || true
pkill -f "cloudflared" 2>/dev/null || true
sleep 2

echo "[*] Limpiando cache compilada..."
rm -rf __pycache__
rm -rf routes/__pycache__

echo "[*] Actualizando desde GitHub..."
git pull

echo "[*] Instalando dependencias Python..."
pip install -r requirements.txt

echo "[*] Iniciando Flask en segundo plano..."
tmux kill-session -t tribu_app 2>/dev/null || true
tmux new -d -s tribu_app "cd ~/plantillaFlask2026 && python app.py"

echo "[*] Verificando cloudflared..."
if ! command -v cloudflared >/dev/null 2>&1; then
    echo "[*] Instalando repositorio TUR y cloudflared..."
    pkg install -y tur-repo
    pkg install -y cloudflared
fi

echo "[*] Iniciando Cloudflare Tunnel..."
if [ -f ~/.cloudflared_token ]; then
    TOKEN=$(cat ~/.cloudflared_token | tr -d '\r\n')
    tmux kill-session -t tribu_cloud 2>/dev/null || true
    tmux new -d -s tribu_cloud "cloudflared tunnel run --token '$TOKEN'"
    echo "[OK] La Tribu y Cloudflare reiniciados."
    echo "    Flask local: https://localhost:5050"
    echo "    Dominio: https://latribu.top"
    echo "    Para ver: tmux attach -t tribu_app"
    echo "    Para tunel: tmux attach -t tribu_cloud"
else
    echo "[OK] Flask reiniciado, pero no se encontro ~/.cloudflared_token"
    echo "    Solo local: https://localhost:5050"
    echo "    Para ver: tmux attach -t tribu_app"
fi

echo "[*] Listo. Para detener todo: tmux kill-session -t tribu_app; tmux kill-session -t tribu_cloud"
