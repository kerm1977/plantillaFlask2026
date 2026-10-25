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
        modalEl._posterBlob = null;
        modalEl._posterPromise = null;
        if (posterUrl && window.fetch) {
            modalEl._posterPromise = fetch(posterUrl)
                .then(function (r) { return r.blob(); })
                .then(function (b) { modalEl._posterBlob = b; return b; })
                .catch(function () { return null; });
        }
        qrModal.show();
    }

    function toastShare(t) {
        var el = document.createElement('div');
        el.textContent = t;
        el.style.cssText = 'position:fixed;left:50%;bottom:90px;transform:translateX(-50%);background:#4527a0;color:#fff;padding:10px 18px;border-radius:999px;font-weight:700;font-size:0.85rem;box-shadow:0 6px 18px rgba(0,0,0,.35);z-index:2000;max-width:90%;text-align:center;';
        document.body.appendChild(el);
        setTimeout(function () { el.remove(); }, 4500);
    }

    function blobToPng(blob) {
        return new Promise(function (resolve, reject) {
            var url = URL.createObjectURL(blob);
            var img = new Image();
            img.onload = function () {
                var c = document.createElement('canvas');
                c.width = img.naturalWidth; c.height = img.naturalHeight;
                c.getContext('2d').drawImage(img, 0, 0);
                URL.revokeObjectURL(url);
                c.toBlob(function (b) { b ? resolve(b) : reject(new Error('toBlob')); }, 'image/png');
            };
            img.onerror = reject;
            img.src = url;
        });
    }

    function downloadBlob(blob, name) {
        var u = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = u; a.download = name;
        document.body.appendChild(a); a.click(); a.remove();
        setTimeout(function () { URL.revokeObjectURL(u); }, 5000);
    }

    function attachForDesktop(blob, ext) {
        var png = (blob.type === 'image/png') ? Promise.resolve(blob) : blobToPng(blob);
        png.then(function (pngBlob) {
            if (!(navigator.clipboard && window.ClipboardItem)) throw new Error('no clipboard img');
            return navigator.clipboard.write([new ClipboardItem({ 'image/png': pngBlob })]);
        }).then(function () {
            toastShare('Imagen copiada: pegala con Ctrl+V en el chat de WhatsApp');
        }).catch(function () {
            downloadBlob(blob, 'poster.' + ext);
            toastShare('Póster descargado: adjuntalo al mensaje de WhatsApp');
        });
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
                var blob = modalEl._posterBlob || null;
                var ext = (poster.split('.').pop() || 'jpg').split('?')[0].toLowerCase();
                var full = msg ? (msg + '\n\n' + link) : link;
                var openWa = function (text, copyText) {
                    if (copyText !== false && navigator.clipboard && navigator.clipboard.writeText) {
                        navigator.clipboard.writeText(text).catch(function () {});
                    }
                    window.open('https://wa.me/?text=' + encodeURIComponent(text), '_blank');
                };
                // Móvil: compartir la imagen real adjunta (archivo ya precargado)
                if (blob && window.File && navigator.canShare) {
                    var file = new File([blob], 'poster.' + ext, { type: blob.type || 'image/jpeg' });
                    if (navigator.canShare({ files: [file] })) {
                        navigator.share({ files: [file], text: full }).catch(function (err) {
                            if (err && err.name === 'AbortError') return;
                            openWa(full);
                            attachForDesktop(blob, ext);
                        });
                        return;
                    }
                }
                // Escritorio o sin soporte: texto + imagen por portapapeles o descarga
                var pp = modalEl._posterPromise;
                openWa(poster && !pp ? (poster + '\n\n' + full) : full, !pp);
                if (pp) pp.then(function (b) { if (b) attachForDesktop(b, ext); });
            });
        }
    });
})();
