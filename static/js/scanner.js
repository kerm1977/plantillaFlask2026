// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
// scanner.js - Lector de cámara QR/barras con html5-qrcode (superusuario)
(function () {
    'use strict';
    var qr = null;
    var active = false;

    async function start(elementId, onCode) {
        if (typeof Html5Qrcode === 'undefined') {
            if (onCode) onCode(null, new Error('Librería de escaneo no cargada'));
            return;
        }
        if (!qr) qr = new Html5Qrcode(elementId);
        if (active) return;
        active = true;
        try {
            await qr.start(
                { facingMode: 'environment' },
                { fps: 10, qrbox: { width: 220, height: 220 } },
                function (decoded) {
                    var payload = null;
                    var ev = decoded.match(/\/puntos-(scan|evento)\/(\d+)/);
                    var per = decoded.match(/\/tarjeta\/([^/\s?]+)\//);
                    if (ev) {
                        payload = {
                            kind: ev[1] === 'evento' ? 'evento' : 'caminata',
                            id: parseInt(ev[2], 10)
                        };
                    } else if (per) {
                        payload = { kind: 'persona', cedula: per[1].replace(/\D/g, '') || per[1] };
                    }
                    if (payload && onCode) {
                        stop().then(function () { onCode(payload); });
                    }
                },
                function () { /* errores de lectura por frame: ignorar */ }
            );
        } catch (e) {
            active = false;
            if (onCode) onCode(null, e);
        }
    }

    async function stop() {
        if (qr && active) {
            active = false;
            try { await qr.stop(); } catch (e) { /* ya detenida */ }
        }
    }

    window.ScanCam = { start: start, stop: stop };
})();
