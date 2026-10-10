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

## REGLA BLINDADA — Invitación personalizada

Aprobada por el dueño. En `static/js/invitacion.js`:

- **El enlace del mensaje de WhatsApp es INTocable**: `linkEvento()` devuelve
  siempre `https://www.latribu.top/puntos-scan/<id>` — el MISMO enlace del QR
  de cada caminata (route `main.puntos_scan` en `routes/scan.py`, usado por
  `caminata_qr_share.js` con `url_for(_external=True)`). Dominio fijo, nunca
  `location.origin` (localhost rompía el link).
- **Sliders propios, pista inerte**: NO volver a `input[type=range]` — el
  track no responde a toques, solo el thumb arrastra (`bindSliders`).
- **Diseño aprobado**: acordeón, controles en %, blur con raster previo a
  html2canvas, degradado naranja, escala global. No regresar.
- Vista previa DOM (sin parpadeo) + captura `html2canvas` a 1080×1920.
- **Envío WhatsApp**: el PNG se **pre-renderiza** (`precapturar`) cuando hay
  evento+persona — `navigator.share({files,text})` debe salir dentro de la
  activación del toque o el navegador lo rechaza y cae a descargar. Tras
  enviar, `siguiente()` limpia la persona y reabre el buscador para
  encadenar invitaciones. Cancelar el share (AbortError) no abre nada.
