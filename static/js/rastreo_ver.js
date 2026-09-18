// ══ BLINDADO — RASTREO EN VIVO ══
// Código probado y estable. NO modificar sin revisar el flujo completo.
// Visor de ubicación en vivo — espectadores (familiares)
(function () {
    'use strict';
    var TOKEN = window.RK_VIEW_TOKEN;
    var code = sessionStorage.getItem('rk_code_' + TOKEN) || '';
    var map = null, marker = null, circulo = null, rastro = null;
    var timer = null, primerFix = true;

    var gate  = document.getElementById('rkGate');
    var mapa  = document.getElementById('rkMapa');
    var codeI = document.getElementById('rkCode');
    var err   = document.getElementById('rkCodeErr');
    var dot   = document.getElementById('rkDot');
    var estEl = document.getElementById('rkEstado');
    var gpsEl = document.getElementById('rkGps');
    var hora  = document.getElementById('rkHora');
    var aviso = document.getElementById('rkAviso');
    var filaEst = document.getElementById('rkEstadoFila');
    var ultimoLl = null;

    function initMap() {
        // En táctil el dedo desplaza la PÁGINA (no el mapa); en PC la rueda igual.
        // El mapa se reubica con el botón "Ubicar al grupo".
        map = L.map('map', {
            scrollWheelZoom: false,
            dragging: !L.Browser.touch
        }).setView([9.93, -84.08], 8); // Costa Rica por defecto
        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; OpenStreetMap'
        }).addTo(map);
        marker = L.marker([0, 0], { opacity: 0 }).addTo(map);
        rastro = L.polyline([], { color: '#f58c1f', weight: 4 }).addTo(map);
    }

    function status(ok, texto) {
        dot.className = 'rk-dot ' +
            (ok === true ? 'on' : ok === false ? 'off' : '');
        estEl.textContent = texto;
    }

    function pintar(data) {
        gpsEl.textContent = '· ' + (data.total || 0) + ' GPS';
        if (!data.last) {
            status(data.active ? null : false,
                   data.active ? 'Esperando señal...' : 'Sin transmisión');
            hora.textContent = 'sin señal todavía';
            aviso.classList.remove('d-none');
            aviso.textContent = data.active
                ? 'El coordinador todavía no empezó a transmitir.'
                : 'No hay posiciones registradas en esta sesión.';
            return;
        }
        // En línea solo si la sesión sigue activa y el último ping es reciente
        var online = data.active && data.last.age <= 90;
        if (!data.active) {
            status(false, 'Transmisión terminada');
            aviso.classList.remove('d-none');
            aviso.textContent = 'La transmisión terminó. Esta es la última posición conocida.';
        } else if (online) {
            status(true, 'En línea');
            aviso.classList.add('d-none');
        } else {
            status(false, 'Sin conexión');
            aviso.classList.remove('d-none');
            aviso.textContent = 'El coordinador no tiene señal en este momento ' +
                '(sin cobertura o dispositivo apagado). Esta es su última posición conocida.';
        }
        hora.textContent = data.last.ts;

        var ll = [data.last.lat, data.last.lng];
        ultimoLl = ll;
        marker.setLatLng(ll).setOpacity(1)
            .bindTooltip('Grupo La Tribu', { permanent: false });
        if (circulo) { circulo.remove(); circulo = null; }
        if (data.last.acc && data.last.acc < 5000) {
            circulo = L.circle(ll, {
                radius: data.last.acc, color: '#f58c1f',
                weight: 1, fillOpacity: 0.12
            }).addTo(map);
        }
        rastro.setLatLngs(data.show_track ? data.points : []);
        if (primerFix) {
            primerFix = false;
            if (data.show_track && data.points.length > 1) {
                map.fitBounds(rastro.getBounds().pad(0.2));
            } else {
                map.setView(ll, 15);
            }
        }
    }

    function poll() {
        fetch('/api/rastreo/' + TOKEN + '/status?code=' + encodeURIComponent(code))
            .then(function (r) {
                if (r.status === 403) { volverAlCodigo(); return null; }
                return r.json();
            })
            .then(function (d) { if (d) pintar(d); })
            .catch(function () { status(false, 'Sin conexión'); });
    }

    function volverAlCodigo() {
        sessionStorage.removeItem('rk_code_' + TOKEN);
        clearInterval(timer);
        mapa.classList.add('d-none');
        gate.classList.remove('d-none');
        err.classList.remove('d-none');
        codeI.value = '';
    }

    window.rkEntrar = function () {
        code = (codeI.value || '').trim();
        if (!code) { err.classList.remove('d-none'); return; }
        fetch('/api/rastreo/' + TOKEN + '/status?code=' + encodeURIComponent(code))
            .then(function (r) {
                if (r.status === 403) { err.classList.remove('d-none'); return; }
                return r.json();
            })
            .then(function (d) {
                if (!d) return;
                sessionStorage.setItem('rk_code_' + TOKEN, code);
                gate.classList.add('d-none');
                mapa.classList.remove('d-none');
                if (!map) initMap();
                setTimeout(function () { map.invalidateSize(); }, 100);
                pintar(d);
                timer = setInterval(poll, 10000);
            })
            .catch(function () { err.classList.remove('d-none'); });
    };

    // Botón "Ubicar al grupo": centra el mapa en la última posición conocida
    window.rkUbicar = function () {
        if (map && ultimoLl) map.setView(ultimoLl, Math.max(map.getZoom(), 15));
    };

    // Tocar el indicador de estado fuerza una actualización inmediata
    filaEst.addEventListener('click', poll);

    codeI.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') rkEntrar();
    });

    // Auto-entrar si el código ya se ingresó en esta pestaña
    if (code) {
        codeI.value = code;
        rkEntrar();
    }
})();
