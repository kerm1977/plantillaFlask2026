// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
// caminata_qr_share.js - Long-press en caminata: compartir enlace QR por WhatsApp (superusuario)
(function () {
    'use strict';
    var qrModal = null;
    var lpFired = false;

    function openShare(nombre, scanUrl, posterUrl) {
        var modalEl = document.getElementById('qrShareModal');
        if (!modalEl) return;
        if (!qrModal) qrModal = new bootstrap.Modal(modalEl);
        document.getElementById('qrShareEventName').textContent = nombre;
        document.getElementById('qrShareLink').value = scanUrl;
        document.getElementById('qrShareMsg').value = '';
        var posterImg = document.getElementById('qrSharePoster');
        if (posterImg) {
            if (posterUrl) { posterImg.src = posterUrl; posterImg.style.display = 'block'; }
            else { posterImg.removeAttribute('src'); posterImg.style.display = 'none'; }
        }
        modalEl.dataset.scanUrl = scanUrl;
        modalEl.dataset.posterUrl = posterUrl || '';
        qrModal.show();
    }

    function setupLongPress(el) {
        var timer = null;
        var start = function () {
            timer = setTimeout(function () {
                lpFired = true;
                openShare(el.dataset.nombre || '', el.dataset.scanUrl || '', el.dataset.posterUrl || '');
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

    window.QRShare = { open: openShare };

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
                var modalEl = document.getElementById('qrShareModal');
                var msg = (document.getElementById('qrShareMsg').value || '').trim();
                var link = modalEl.dataset.scanUrl || '';
                var poster = modalEl.dataset.posterUrl || '';
                var full = msg ? (msg + '\n\n' + link) : link;
                var fallback = function () {
                    var text = poster ? (poster + '\n\n' + full) : full;
                    if (navigator.clipboard) {
                        navigator.clipboard.writeText(text).catch(function () {});
                    }
                    window.open('https://wa.me/?text=' + encodeURIComponent(text), '_blank');
                };
                if (poster && navigator.canShare && window.fetch && window.File) {
                    fetch(poster).then(function (r) { return r.blob(); }).then(function (b) {
                        var ext = (poster.split('.').pop() || 'jpg').split('?')[0].toLowerCase();
                        var file = new File([b], 'poster.' + ext, { type: b.type || 'image/jpeg' });
                        if (navigator.canShare({ files: [file] })) {
                            navigator.share({ files: [file], text: full }).catch(function (err) {
                                if (err && err.name === 'AbortError') return;
                                fallback();
                            });
                        } else {
                            fallback();
                        }
                    }).catch(fallback);
                } else {
                    fallback();
                }
            });
        }
    });
})();
