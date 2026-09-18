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
    var pendingStop = null, pendingAction = 'stop';
    var ocultos = {}; // eventos cuya tarjeta "Nueva" se ocultó

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
            ? '<button class="btn btn-success rounded-pill px-3 animate-blink" onclick="rkPedirDetener(' + s.id + ')"><i class="bi bi-broadcast me-1"></i>En vivo — tocar para detener</button>'
            : '<button class="btn btn-success rounded-pill px-3" onclick="rkIniciarSesion(' + (s.event_id || 0) + ')"><i class="bi bi-broadcast me-1"></i>Iniciar esta sesión</button>';
    }

    function cardSesion(s) {
        var urlVer = BASE + '/rastreo/' + s.view_token;
        return '' +
        '<div class="accordion-item border-0 rounded-4 overflow-hidden shadow-sm mb-3">' +
          '<h2 class="accordion-header"><button class="accordion-button collapsed fw-bold text-dark" ' +
                  'type="button" data-bs-toggle="collapse" data-bs-target="#rkSes_' + s.id + '">' +
            '<i class="bi bi-geo-alt me-2 text-orange"></i>' + s.evento + badge(s) +
          '</button></h2>' +
          '<div id="rkSes_' + s.id + '" class="accordion-collapse collapse" data-bs-parent="#rkAccTodo">' +
            '<div class="accordion-body">' +
              '<div class="small text-muted mb-3">Creada: ' + s.created_at +
                ' &middot; Puntos GPS: <span id="rkPuntos_' + s.id + '" class="fw-bold text-dark">' + s.puntos + '</span>' +
                ' <button class="btn btn-sm btn-outline-secondary rounded-pill ms-1" onclick="rkBuscarPuntos(' + s.id + ')"><i class="bi bi-arrow-repeat me-1"></i>Buscar puntos GPS</button></div>' +
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
              (!s.active ? '<div class="mt-3"><button class="btn btn-sm btn-outline-danger rounded-pill px-3" ' +
                  'onclick="rkPedirEliminar(' + s.id + ')"><i class="bi bi-trash me-1"></i>Eliminar sesión</button></div>' : '') +
            '</div>' +
          '</div>' +
        '</div>';
    }

    function stubCard(evId) {
        var nombre = (window.RK_EVENTOS || {})[evId] || ('Evento ' + evId);
        return '' +
        '<div class="accordion-item border-0 rounded-4 overflow-hidden shadow-sm mb-3">' +
          '<h2 class="accordion-header"><button class="accordion-button fw-bold text-dark" type="button" ' +
                  'data-bs-toggle="collapse" data-bs-target="#rkStub">' +
            '<i class="bi bi-geo-alt me-2 text-orange"></i>' + nombre +
            '<span class="badge text-bg-warning text-dark ms-2">Nueva — sin sesión</span>' +
          '</button></h2>' +
          '<div id="rkStub" class="accordion-collapse collapse show" data-bs-parent="#rkAccTodo">' +
            '<div class="accordion-body">' +
              '<p class="small text-muted">Este evento todavía no tiene sesión de rastreo. Al iniciarla se generan sus enlaces fijos.</p>' +
              '<button class="btn btn-success rounded-pill px-3 me-2" onclick="rkIniciarSesion(' + evId + ')"><i class="bi bi-broadcast me-1"></i>Iniciar esta sesión</button>' +
              '<button class="btn btn-sm btn-outline-danger rounded-pill px-3" onclick="rkPedirOcultar(' + evId + ')"><i class="bi bi-trash me-1"></i>Eliminar</button>' +
            '</div>' +
          '</div>' +
        '</div>';
    }

    function cargar() {
        var abierto = cont.querySelector('.collapse.show'), abrirId = abierto ? abierto.id : null;
        fetch('/api/rastreo/sessions').then(function (r) { return r.json(); })
            .then(function (lista) {
                var evSel = parseInt(selEv.value || '0', 10);
                var html = '';
                if (evSel && !ocultos[evSel] && !lista.some(function (s) { return s.event_id === evSel; })) {
                    html += stubCard(evSel);
                }
                html += lista.map(cardSesion).join('');
                cont.innerHTML = html || '<div class="text-muted small">Sin sesiones todavía.</div>';
                dotH.className = 'rk-dot me-2 ' +
                    (lista.some(function (s) { return s.active; }) ? 'on animate-blink' : 'off');
                var el = abrirId && document.getElementById(abrirId);
                if (el) el.classList.add('show');
            })
            .catch(function () { cont.innerHTML = '<div class="text-danger small">Error cargando sesiones.</div>'; });
    }

    function pintarTx(sid, texto, clase) {
        tx = { sid: sid, texto: texto, clase: clase };
        var el = document.getElementById('rkTxSt_' + sid);
        if (el) { el.textContent = texto; el.className = 'small ' + clase; }
    }

    function arrancarGps(sid, token) {
        pintarTx(sid, 'Obteniendo señal GPS...', 'text-warning fw-bold');
        RK_GPS.start(token, function (est, d) {
            if (est === 'ok') pintarTx(sid, 'Transmitiendo · ' + d.total + ' pts · ±' + Math.round(d.acc || 0) + 'm', 'text-success fw-bold');
            else if (est === 'offline') pintarTx(sid, 'Sin conexión — reintentando', 'text-danger');
            else if (est === 'stopped') pintarTx(sid, 'Sesión detenida', 'text-danger');
            else if (est === 'geoerr') pintarTx(sid, 'Error GPS (' + d.code + ') — revisá el permiso de ubicación', 'text-danger fw-bold');
        });
    }

    window.rkCopiar = copiar;

    window.rkIniciarSesion = function (evId) {
        if (!navigator.geolocation) { alert('Este dispositivo no soporta GPS.'); return; }
        var code = document.getElementById('rkCodigo').value.trim();
        fetch('/api/rastreo/session', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ event_id: evId || null, code: code,
                                   show_track: document.getElementById('rkTrack').checked })
        }).then(function (r) { return r.json(); })
          .then(function (d) {
              if (d.error) { alert(d.error); return; }
              localStorage.setItem('rk_tx', JSON.stringify({ sid: d.session.id, token: d.session.tx_token }));
              tx.sid = d.session.id;
              arrancarGps(d.session.id, d.session.tx_token);
              cargar();
          });
    };

    // Textos del modal de doble confirmación según acción: [título, msg1, msg2, botón final]
    var TXT_MODAL = {
        stop:   ['Vas a detener el servicio', '¿Estás seguro de que querés detener la transmisión en vivo?',
                 'Todas las personas van a perder la posición actual del grupo. Esta acción no se puede deshacer.', 'Sí, detener'],
        delete: ['Vas a eliminar esta sesión', 'Se borran la sesión, sus enlaces y todos sus puntos GPS. ¿Estás seguro?',
                 'El enlace de familiares dejará de funcionar para siempre. Esta acción no se puede deshacer.', 'Sí, eliminar'],
        hide:   ['Vas a quitar esta tarjeta', 'Es solo una vista previa para crear la sesión — no hay datos que borrar. ¿Estás seguro?',
                 'Podés mostrarla de nuevo seleccionando la caminata en el selector de arriba.', 'Sí, quitar']
    };

    function abrirModal(accion, sid) {
        pendingStop = sid;
        pendingAction = accion;
        var $ = function (id) { return document.getElementById(id); }, m = TXT_MODAL[accion];
        $('rkStopT1').textContent = m[0];
        $('rkStopM1').textContent = m[1];
        $('rkStopM2').textContent = m[2];
        $('rkStopBtn2').textContent = m[3];
        $('rkStopP1').classList.remove('d-none');
        $('rkStopP2').classList.add('d-none');
        new bootstrap.Modal($('rkModalStop')).show();
    }

    window.rkPedirDetener = function (sid) { abrirModal('stop', sid); };
    window.rkPedirEliminar = function (sid) { abrirModal('delete', sid); };
    window.rkPedirOcultar = function (evId) { abrirModal('hide', evId); };

    window.rkStopPaso2 = function () {
        document.getElementById('rkStopP1').classList.add('d-none');
        document.getElementById('rkStopP2').classList.remove('d-none');
    };

    window.rkStopConfirmado = function () {
        bootstrap.Modal.getInstance(document.getElementById('rkModalStop')).hide();
        if (pendingAction === 'delete') {
            fetch('/api/rastreo/session/' + pendingStop, { method: 'DELETE' }).then(cargar);
        } else if (pendingAction === 'hide') {
            ocultos[pendingStop] = 1;
            cargar();
        } else {
            RK_GPS.stop();
            localStorage.removeItem('rk_tx');
            fetch('/api/rastreo/session/' + pendingStop + '/stop', { method: 'POST' }).then(cargar);
        }
    };

    window.rkBuscarPuntos = function (sid) {
        fetch('/api/rastreo/sessions').then(function (r) { return r.json(); }).then(function (lista) {
            var s = lista.find(function (x) { return x.id === sid; });
            var el = document.getElementById('rkPuntos_' + sid);
            if (s && el) el.textContent = s.puntos;
        });
    };

    // Reanudar transmisión local si la página se recargó a mitad de caminata
    function reanudar() {
        var t = null;
        try { t = JSON.parse(localStorage.getItem('rk_tx')); } catch (e) {}
        if (t && t.token && !RK_GPS.isRunning()) arrancarGps(t.sid, t.token);
    }
    selEv.addEventListener('change', function () {
        delete ocultos[parseInt(selEv.value || '0', 10)];
        cargar();
    });
    cargar(); reanudar(); setInterval(cargar, 15000);
})();
