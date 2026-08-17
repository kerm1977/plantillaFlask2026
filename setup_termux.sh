#!/data/data/com.termux/files/usr/bin/sh
# setup_termux.sh - Instalacion completa de La Tribu en Termux
# Uso: ./setup_termux.sh

echo "============================================================"
echo "  INSTALADOR AUTOMATICO DE LA TRIBU PARA TERMUX"
echo "============================================================"

# Evitar que Android duerma Termux
command -v termux-wake-lock >/dev/null && termux-wake-lock

echo "[*] Actualizando repositorios..."
pkg update -y

echo "[*] Instalando herramientas basicas..."
pkg install -y python git procps tmux wget

echo "[*] Instalando librerias para Pillow..."
pkg install -y libjpeg-turbo libtiff libwebp libpng freetype

echo "[*] Instalando repositorio TUR y cloudflared..."
pkg install -y tur-repo
pkg update -y
pkg install -y cloudflared

echo "[*] Verificando repositorio de La Tribu..."
cd ~
if [ ! -d "plantillaFlask2026" ]; then
    echo "[*] Clonando plantillaFlask2026..."
    git clone https://github.com/kerm1977/plantillaFlask2026.git
else
    echo "[*] Actualizando plantillaFlask2026..."
fi

cd plantillaFlask2026
git config core.fileMode false
git pull || true

echo "[*] Instalando dependencias Python..."
pip install -r requirements_termux.txt

echo "[*] Verificando token de Cloudflare..."
if [ -f cloudflared_token.txt ]; then
    echo "[*] Usando token del proyecto (cloudflared_token.txt)"
elif [ ! -f ~/.cloudflared_token ]; then
    echo "[*] No se encontro token de Cloudflare; el tunel no arrancara hasta que lo agregues"
fi

echo "[*] Iniciando La Tribu..."
chmod +x reiniciar_tribu.sh
./reiniciar_tribu.sh

echo ""
echo "[OK] Proceso completado. Prueba en el navegador:"
echo "    http://localhost:5050"
echo "    https://latribu.top (si tenes token de Cloudflare)"
echo ""
echo "Para ver sesiones: tmux ls"
