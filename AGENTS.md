# ============================================================
#   REGLAS SAGRADAS — LA TRIBU DE LOS LIBRES
# ============================================================

## REGLA #1 — BLINDADO

**NUNCA modificar, sobrescribir ni borrar ningún archivo de este proyecto sin
permiso explícito del dueño.** Antes de cualquier edición hay que explicar:

1. QUÉ archivo se va a tocar.
2. POR QUÉ es necesario el cambio.
3. QUÉ efecto tiene sobre el contenido existente.

…y esperar la aprobación del usuario. El contenido, el formato, la media y el
posicionamiento existentes son **sagrados**: este sitio está en producción y
su alteración puede tener consecuencias legales para el dueño.

Los archivos llevan la marca `BLINDADO` en su cabecera. La marca refuerza la
regla, pero aplica a **todo** el proyecto — marcado o no.

## Excepción acordada

El usuario sí autoriza cambios cuando los solicita explícitamente (una
función nueva, una corrección pedida). Aun así: tocar lo mínimo necesario,
preservar todo lo demás, verificar antes de subir.

## Verificación rápida

- Servidor local: `python app.py` (venv: `env\Scripts\python.exe`), puerto 5050.
- Reinicio oficial: `reiniciar_tribu.bat` / `ejecutar.bat` (usa el venv).
- Sintaxis Python: `py_compile` por archivo.
- Sintaxis JS: `node --check archivo.js`.
- Público: `curl https://www.latribu.top/` debe dar 200.

## Deploy

- Cloudflare tunnel (`ejecutar.bat`, watcher CLOUD_WATCHER, protocolo http2).
- GitHub: `https://github.com/kerm1977/plantillaFlask2026.git` → rama `main`.
