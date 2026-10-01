// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
// caminata_qr_share.js - Long-press en caminata: compartir enlace QR por WhatsApp (superusuario)
(function () {
    'use strict';
    var qrModal = null;
    var lpFired = false;

    function openShare(nombre, scanUrl) {
        var modalEl = document.getElementById('qrShareModal');
        if (!modalEl) return;
        if (!qrModal) qrModal = new bootstrap.Modal(modalEl);
        document.getElementById('qrShareEventName').textContent = nombre;
        document.getElementById('qrShareLink').value = scanUrl;
        document.getElementById('qrShareMsg').value = '';
        modalEl.dataset.scanUrl = scanUrl;
        qrModal.show();
    }

    function setupLongPress(el) {
        var timer = null;
        var start = function () {
            timer = setTimeout(function () {
                lpFired = true;
                openShare(el.dataset.nombre || '', el.dataset.scanUrl || '');
            }, 600);
        };
        var cancel = function () { if (timer) { clearTimeout(timer); timer = null; } };
        el.addEventListener('mousedown', start);
        el.addEventListener('touchstart', start, { passive: true });
        el.addEventListener('mouseup', cancel);
        el.addEventListener('mouseleave', cancel);
        el.addEventListener('touchend', cancel);
        el.addEventListener('touchcancel', cancel);
        el.addEventListener('contextmenu', function (e) { e.preventDefault(); });
    }

    document.addEventListener('DOMContentLoaded', function () {
        document.querySelectorAll('.cam-qr-share').forEach(setupLongPress);

        // Tras un long-press, suprime el click para no navegar al detalle (stretched-link)
        document.addEventListener('click', function (e) {
            if (lpFired) {
                lpFired = false;
                e.preventDefault();
                e.stopPropagation();
            }
        }, true);

        var send = document.getElementById('qrShareSend');
        if (send) {
            send.addEventListener('click', function (e) {
                e.preventDefault();
                var msg = (document.getElementById('qrShareMsg').value || '').trim();
                var link = document.getElementById('qrShareModal').dataset.scanUrl || '';
                var full = msg ? (msg + '\n\n' + link) : link;
                if (navigator.clipboard) {
                    navigator.clipboard.writeText(full).catch(function () {});
                }
                window.open('https://wa.me/?text=' + encodeURIComponent(full), '_blank');
            });
        }
    });
})();
