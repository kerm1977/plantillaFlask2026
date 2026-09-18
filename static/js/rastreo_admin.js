// ══ BLINDADO — RASTREO EN VIVO ══
// Código probado y estable. NO modificar sin revisar el flujo completo.
// Panel de administración del rastreo en vivo
(function () {
    'use strict';
    var cont  = document.getElementById('rkSesiones');
    var dotH  = document.getElementById('rkDotHeader');
    var selEv = document.getElementById('rkEvento');
    var BASE  = location.origin;
    var tx    = { sid: null, texto: '', clase: '' };
    var pendingStop = null;

    function copiar(texto, btn) {
        if (navigator.clipboard) navigator.clipboard.writeText(texto);
        var old = btn.textContent;
        btn.textContent = '¡Copiado!';
        setTimeout(function () { btn.textContent = old; }, 1500);
    }

    function badge(s) {
        return s.active ? '<span class="badge text-bg-success animate-blink ms-2">En vivo</span>'
                        : '<span class="badge text-bg-secondary ms-2">Detenida</span>';
    }

    function botonTx(s) {
        return s.active
            ? '<button class="btn btn-success rounded-pill px-3 animate-blink" ' +
              'onclick="rkPedirDetener(' + s.id + ')">' +
              '<i class="bi bi-broadcast me-1"></i>En vivo — tocar para detener</button>'
            : '<button class="btn btn-success rounded-pill px-3" ' +
              'onclick="rkIniciarSesion(' + (s.event_id || 0) + ')">' +
              '<i class="bi bi-broadcast me-1"></i>Iniciar esta sesión</button>';
    }

    function cardSesion(s) {
        var urlVer = BASE + '/rastreo/' + s.view_token;
        return '' +
        '<div class="accordion-item border-0 rounded-4 overflow-hidden shadow-sm mb-3">' +
          '<h2 class="accordion-header">' +
            '<button class="accordion-button collapsed fw-bold text-dark" type="button" ' +
                    'data-bs-toggle="collapse" data-bs-target="#rkSes_' + s.id + '">' +
              '<i class="bi bi-geo-alt me-2 text-orange"></i>' + s.evento + badge(s) +
            '</button>' +
          '</h2>' +
          '<div id="rkSes_' + s.id + '" class="accordion-collapse collapse" data-bs-parent="#rkAccTodo">' +
            '<div class="accordion-body">' +
              '<div class="small text-muted mb-3">Creada: ' + s.created_at +
                ' &middot; Puntos GPS: <span id="rkPuntos_' + s.id + '" class="fw-bold text-dark">' + s.puntos + '</span>' +
                ' <button class="btn btn-sm btn-outline-secondary rounded-pill ms-1" ' +
                        'onclick="rkBuscarPuntos(' + s.id + ')">' +
                  '<i class="bi bi-arrow-repeat me-1"></i>Buscar puntos GPS</button></div>' +
              '<label class="form-label fw-bold small mb-1">Enlace fijo para familiares</label>' +
              '<div class="input-group input-group-sm mb-3">' +
                '<input class="form-control" readonly value="' + urlVer + '">' +
                '<button class="btn btn-outline-secondary" onclick="rkCopiar(\'' + urlVer + '\', this)">Copiar</button>' +
              '</div>' +
              '<div class="d-flex align-items-center gap-2 flex-wrap">' +
                botonTx(s) +
                '<span id="rkTxSt_' + s.id + '" class="small ' + tx.clase + '">' +
                  (tx.sid === s.id ? tx.texto : '') + '</span>' +
              '</div>' +
              (!s.active
                ? '<div class="mt-3"><button class="btn btn-sm btn-outline-danger rounded-pill px-3" ' +
                  'onclick="rkBorrar(' + s.id + ')"><i class="bi bi-trash me-1"></i>Eliminar sesión</button></div>'
                : '') +
            '</div>' +
          '</div>' +
        '</div>';
    }

    function stubCard(evId) {
        var nombre = (window.RK_EVENTOS || {})[evId] || ('Evento ' + evId);
        return '' +
        '<div class="accordion-item border-0 rounded-4 overflow-hidden shadow-sm mb-3">' +
          '<h2 class="accordion-header">' +
            '<button class="accordion-button fw-bold text-dark" type="button" ' +
                    'data-bs-toggle="collapse" data-bs-target="#rkStub">' +
              '<i class="bi bi-geo-alt me-2 text-orange"></i>' + nombre +
              '<span class="badge text-bg-secondary ms-2">Sin sesión</span>' +
            '</button>' +
          '</h2>' +
          '<div id="rkStub" class="accordion-collapse collapse show" data-bs-parent="#rkAccTodo">' +
            '<div class="accordion-body">' +
              '<p class="small text-muted">Este evento todavía no tiene sesión de rastreo. ' +
                'Al iniciarla se generan sus enlaces fijos.</p>' +
              '<button class="btn btn-success rounded-pill px-3" onclick="rkIniciarSesion(' + evId + ')">' +
                '<i class="bi bi-broadcast me-1"></i>Iniciar esta sesión</button>' +
            '</div>' +
          '</div>' +
        '</div>';
    }

    function cargar() {
        var abierto = cont.querySelector('.collapse.show');
        var abrirId = abierto ? abierto.id : null;
        fetch('/api/rastreo/sessions').then(function (r) { return r.json(); })
            .then(function (lista) {
                var evSel = parseInt(selEv.value || '0', 10);
                var html = '';
                if (evSel && !lista.some(function (s) { return s.event_id === evSel; })) {
                    html += stubCard(evSel);
                }
                html += lista.map(cardSesion).join('');
                cont.innerHTML = html || '<div class="text-muted small">Sin sesiones todavía.</div>';
                dotH.className = 'rk-dot me-2 ' +
                    (lista.some(function (s) { return s.active; }) ? 'on animate-blink' : 'off');
                if (abrirId) {
                    var el = document.getElementById(abrirId);
                    if (el) el.classList.add('show');
                }
            })
            .catch(function () {
                cont.innerHTML = '<div class="text-danger small">Error cargando sesiones.</div>';
            });
    }

    function pintarTx(sid, texto, clase) {
        tx = { sid: sid, texto: texto, clase: clase };
        var el = document.getElementById('rkTxSt_' + sid);
        if (el) { el.textContent = texto; el.className = 'small ' + clase; }
    }

    function arrancarGps(sid, token) {
        pintarTx(sid, 'Obteniendo señal GPS...', 'text-warning fw-bold');
        RK_GPS.start(token, function (est, d) {
            if (est === 'ok') {
                pintarTx(sid, 'Transmitiendo · ' + d.total + ' pts · ±' +
                    Math.round(d.acc || 0) + 'm', 'text-success fw-bold');
            } else if (est === 'offline') {
                pintarTx(sid, 'Sin conexión — reintentando', 'text-danger');
            } else if (est === 'stopped') {
                pintarTx(sid, 'Sesión detenida', 'text-danger');
            } else if (est === 'geoerr') {
                pintarTx(sid, 'Error GPS (' + d.code + ') — revisá el permiso de ubicación', 'text-danger fw-bold');
            }
        });
    }

    window.rkCopiar = copiar;

    window.rkIniciarSesion = function (evId) {
        if (!navigator.geolocation) { alert('Este dispositivo no soporta GPS.'); return; }
        var code = document.getElementById('rkCodigo').value.trim();
        var trk  = document.getElementById('rkTrack').checked;
        fetch('/api/rastreo/session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ event_id: evId || null, code: code, show_track: trk })
        }).then(function (r) { return r.json(); })
          .then(function (d) {
              if (d.error) { alert(d.error); return; }
              var s = d.session;
              localStorage.setItem('rk_tx', JSON.stringify({ sid: s.id, token: s.tx_token }));
              tx.sid = s.id;
              arrancarGps(s.id, s.tx_token);
              cargar();
          });
    };

    window.rkPedirDetener = function (sid) {
        pendingStop = sid;
        document.getElementById('rkStopP1').classList.remove('d-none');
        document.getElementById('rkStopP2').classList.add('d-none');
        new bootstrap.Modal(document.getElementById('rkModalStop')).show();
    };

    window.rkStopPaso2 = function () {
        document.getElementById('rkStopP1').classList.add('d-none');
        document.getElementById('rkStopP2').classList.remove('d-none');
    };

    window.rkStopConfirmado = function () {
        bootstrap.Modal.getInstance(document.getElementById('rkModalStop')).hide();
        RK_GPS.stop();
        localStorage.removeItem('rk_tx');
        fetch('/api/rastreo/session/' + pendingStop + '/stop', { method: 'POST' }).then(cargar);
    };

    window.rkBuscarPuntos = function (sid) {
        fetch('/api/rastreo/sessions').then(function (r) { return r.json(); })
            .then(function (lista) {
                var s = lista.find(function (x) { return x.id === sid; });
                var el = document.getElementById('rkPuntos_' + sid);
                if (s && el) el.textContent = s.puntos;
            });
    };

    window.rkBorrar = function (id) {
        if (!confirm('¿Eliminar esta sesión y todos sus puntos GPS?')) return;
        fetch('/api/rastreo/session/' + id, { method: 'DELETE' }).then(cargar);
    };

    // Reanudar transmisión local si la página se recargó a mitad de caminata
    function reanudar() {
        try {
            var t = JSON.parse(localStorage.getItem('rk_tx') || 'null');
            if (t && t.token && !RK_GPS.isRunning()) arrancarGps(t.sid, t.token);
        } catch (e) {}
    }
    selEv.addEventListener('change', cargar);
    cargar(); reanudar(); setInterval(cargar, 15000);
})();
