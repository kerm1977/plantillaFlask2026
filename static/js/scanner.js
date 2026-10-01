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
                    var m = decoded.match(/\/puntos-scan\/(\d+)/);
                    if (m && onCode) {
                        var id = parseInt(m[1], 10);
                        stop().then(function () { onCode(id); });
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
