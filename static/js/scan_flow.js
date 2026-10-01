// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
// scan_flow.js - Flujo del modal de escaneo: buscar cédula, asignar puntos, WhatsApp
(function () {
    'use strict';
    var modal = null;
    var scanned = null;   // {kind: 'caminata'|'evento', id: n}
    var mode = 'award';   // 'award' = asignar puntos | 'estado' = enviar estado de cuenta
    var searchTimer = null;

    function $(id) { return document.getElementById(id); }

    function showStep(stepId) {
        ['scanStepCamera', 'scanStepCedula', 'scanStepResult'].forEach(function (s) {
            var el = $(s);
            if (el) el.classList.add('d-none');
        });
        var step = $(stepId);
        if (step) step.classList.remove('d-none');
    }

    function startCamera() {
        showStep('scanStepCamera');
        window.ScanCam.start('scanReader', onScan);
    }

    function onScan(payload, err) {
        if (err || !payload || !payload.id) {
            showResult(false, err ? 'No se pudo acceder a la cámara. Revisá los permisos.' : 'Código no reconocido.');
            return;
        }
        scanned = payload;
        mode = 'award';
        fetch('/api/scan/info/' + payload.kind + '/' + payload.id)
            .then(function (r) { return r.json(); })
            .then(function (d) {
                if (!d.ok) { showResult(false, d.error || 'Código no encontrado.'); return; }
                showCedulaStep(d.nombre + (d.puntos ? ' · ' + d.puntos + ' puntos' : ''), 'Asignar');
            })
            .catch(function () { showResult(false, 'Error de conexión.'); });
    }

    function showCedulaStep(titulo, btnTexto) {
        $('scanEventName').textContent = titulo;
        $('scanConfirmBtn').innerHTML = '<i class="bi bi-check-lg me-1"></i>' + btnTexto;
        $('scanSearchInput').value = '';
        $('scanCedulaInput').value = '';
        $('scanSearchResults').innerHTML = '';
        showStep('scanStepCedula');
        $('scanSearchInput').focus();
    }

    function startEstadoFlow() {
        mode = 'estado';
        showCedulaStep('Enviar estado de cuenta', 'Buscar');
    }

    function showResult(ok, msg, opts) {
        opts = opts || {};
        showStep('scanStepResult');
        $('scanResultIcon').innerHTML = ok
            ? '<i class="bi bi-check-circle-fill text-success"></i>'
            : '<i class="bi bi-x-circle-fill text-danger"></i>';
        $('scanResultMsg').textContent = msg;
        var estadoBtn = $('scanEstadoBtn');
        var regBtn = $('scanRegisterBtn');
        var prev = $('scanEstadoPreview');
        var shareBtn = $('scanShareBtn');
        estadoBtn.classList.add('d-none');
        regBtn.classList.add('d-none');
        prev.classList.add('d-none');
        shareBtn.classList.add('d-none');
        if (opts.estadoTexto) {
            prev.textContent = opts.estadoTexto;
            prev.classList.remove('d-none');
            shareBtn.dataset.texto = opts.estadoTexto;
            shareBtn.classList.remove('d-none');
        }
        if (ok && opts.estadoUrl) {
            estadoBtn.href = opts.estadoUrl;
            estadoBtn.classList.remove('d-none');
        }
        if (opts.showRegister) regBtn.classList.remove('d-none');
    }

    function sendEstado() {
        var cedula = ($('scanCedulaInput').value || '').replace(/\D/g, '');
        if (!cedula) { alert('Ingresá un número de cédula.'); return; }
        fetch('/api/scan/estado', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cedula: cedula })
        })
            .then(function (r) { return r.json(); })
            .then(function (d) {
                if (d.ok) {
                    showResult(true, 'Estado de cuenta de ' + d.nombre + ' (total: ' + d.total + ' pts)',
                        { estadoUrl: d.estado_whatsapp_url, estadoTexto: d.estado_texto });
                } else {
                    showResult(false, d.error || 'No se pudo generar el estado.',
                        { showRegister: d.code === 'not_found' });
                }
            })
            .catch(function () { showResult(false, 'Error de conexión.'); });
    }

    function award() {
        var cedula = ($('scanCedulaInput').value || '').replace(/\D/g, '');
        if (!cedula) { alert('Ingresá un número de cédula.'); return; }
        fetch('/api/scan/award', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ kind: scanned.kind, id: scanned.id, cedula: cedula })
        })
            .then(function (r) { return r.json(); })
            .then(function (d) {
                if (d.ok) {
                    showResult(true, '+' + d.puntos_ganados + ' pts a ' + d.nombre + ' (total: ' + d.total + ')',
                        { estadoUrl: d.estado_whatsapp_url });
                } else {
                    showResult(false, d.error || 'Error al asignar puntos.',
                        { showRegister: d.code === 'not_found' });
                }
            })
            .catch(function () { showResult(false, 'Error de conexión.'); });
    }

    function buscar() {
        var q = $('scanSearchInput').value.trim();
        var box = $('scanSearchResults');
        if (q.length < 2) { box.innerHTML = ''; return; }
        fetch('/api/scan/hikers?q=' + encodeURIComponent(q))
            .then(function (r) { return r.json(); })
            .then(function (d) {
                box.innerHTML = '';
                (d.results || []).forEach(function (h) {
                    var b = document.createElement('button');
                    b.type = 'button';
                    b.className = 'list-group-item list-group-item-action';
                    b.innerHTML = '<span class="scan-result-ced">' + h.cedula + '</span> · ' +
                        h.nombre + (h.telefono ? ' · ' + h.telefono : '');
                    b.onclick = function () {
                        $('scanCedulaInput').value = h.cedula;
                        box.innerHTML = '';
                    };
                    box.appendChild(b);
                });
                if (!(d.results || []).length) {
                    box.innerHTML = '<div class="list-group-item small text-muted">Sin coincidencias</div>';
                }
            })
            .catch(function () { /* silencioso */ });
    }

    document.addEventListener('DOMContentLoaded', function () {
        var btn = $('btnScanFloat');
        var modalEl = $('scanModal');
        if (!btn || !modalEl) return;
        modal = new bootstrap.Modal(modalEl);

        btn.addEventListener('click', function (e) {
            e.preventDefault();
            modal.show();
            startCamera();
        });

        modalEl.addEventListener('hidden.bs.modal', function () {
            window.ScanCam.stop();
            scanned = null;
        });

        $('scanConfirmBtn').addEventListener('click', function () {
            if (mode === 'estado') sendEstado(); else award();
        });
        $('scanCedulaInput').addEventListener('keydown', function (e) {
            if (e.key === 'Enter') { if (mode === 'estado') sendEstado(); else award(); }
        });
        $('scanNextBtn').addEventListener('click', startCamera);
        $('scanEstadoFlowBtn').addEventListener('click', startEstadoFlow);
        $('scanEstadoFromCedulaBtn').addEventListener('click', startEstadoFlow);
        $('scanShareBtn').addEventListener('click', function () {
            var texto = this.dataset.texto || '';
            if (navigator.share) {
                navigator.share({ title: 'Estado de cuenta - La Tribu', text: texto }).catch(function () {});
            } else if (navigator.clipboard) {
                navigator.clipboard.writeText(texto).then(function () { alert('Estado copiado al portapapeles.'); });
            }
        });
        $('scanBackBtn').addEventListener('click', startCamera);
        $('scanSearchInput').addEventListener('input', function () {
            clearTimeout(searchTimer);
            searchTimer = setTimeout(buscar, 300);
        });
    });
})();
