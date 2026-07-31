#!/data/data/com.termux/files/usr/bin/sh
# termux_boot.sh - Arranque automatico de La Tribu en Android
# Copiar a: ~/.termux/boot/start_latribu.sh

termux-wake-lock
sleep 15
cd ~/plantillaFlask2026
./reiniciar_tribu.sh
