// ══ BLINDADO — RASTREO EN VIVO ══
// Código probado y estable. NO modificar sin revisar el flujo completo.
// Transmisor GPS del coordinador — watchPosition + ping al servidor
(function () {
    'use strict';
    var TOKEN = window.RK_TX_TOKEN;
    var watchId = null, hbId = null, wakeLock = null,
        ultimoEnvio = 0, total = 0, lastPos = null;
    var map, marker, circulo;
    var MIN_MS = 8000; // mínimo 8s entre envíos

    var dot    = document.getElementById('txDot');
    var estado = document.getElementById('txEstado');
    var ultimo = document.getElementById('txUltimo');
    var totalE = document.getElementById('txTotal');
    var accE   = document.getElementById('txAcc');
    var msg    = document.getElementById('txMsg');
    var btnS   = document.getElementById('btnStart');
    var btnP   = document.getElementById('btnStop');

    map = L.map('map').setView([9.93, -84.08], 8);
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19, attribution: '&copy; OpenStreetMap'
    }).addTo(map);

    function aviso(texto, esError) {
        msg.textContent = texto;
        msg.className = 'small mt-2 ' + (esError ? 'text-danger' : 'text-muted');
    }

    function enviar(pos) {
        var ahora = Date.now();
        if (ahora - ultimoEnvio < MIN_MS) return;
        ultimoEnvio = ahora;
        lastPos = pos;
        var lat = pos.coords.latitude, lng = pos.coords.longitude;
        var acc = pos.coords.accuracy;

        if (!marker) {
            marker = L.marker([lat, lng]).addTo(map);
            map.setView([lat, lng], 16);
        } else {
            marker.setLatLng([lat, lng]);
        }
        if (circulo) circulo.remove();
        circulo = L.circle([lat, lng], {
            radius: acc || 20, color: '#f58c1f', weight: 1, fillOpacity: 0.12
        }).addTo(map);
        accE.textContent = acc ? Math.round(acc) + ' m' : '—';

        fetch('/api/rastreo/ping/' + TOKEN, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lat: lat, lng: lng, acc: acc })
        }).then(function (r) {
            if (r.status === 410) { rkTxStop(); aviso('La sesión fue detenida por el administrador.', true); return null; }
            return r.json();
        }).then(function (d) {
            if (d && d.ok) {
                total = d.total;
                totalE.textContent = total;
                ultimo.textContent = new Date().toLocaleTimeString('es-CR');
                // Verde real: solo cuando el servidor ya recibió una posición
                if (dot.className !== 'dot on') {
                    dot.className = 'dot on';
                    estado.textContent = 'Transmitiendo en vivo';
                }
                aviso('Transmitiendo correctamente.');
            }
        }).catch(function () {
            aviso('Sin conexión — se reintentará en el próximo punto GPS.', true);
        });
    }

    function errorGeo(e) {
        var t = 'Error de GPS';
        if (e && e.code === 1) t = 'Permiso de ubicación denegado. Habilitalo en el navegador ' +
            '(Configuración del sitio > Ubicación). Si estás dentro de la app, abrí el enlace en Chrome.';
        if (e && e.code === 2) t = 'No se pudo obtener la posición GPS. Revisá que la ubicación del teléfono esté encendida.';
        if (e && e.code === 3) t = 'Tiempo de espera del GPS agotado. Reintentando...';
        estado.textContent = 'Esperando GPS';
        aviso(t, true);
    }

    // Mantener la pantalla encendida para que el SO no suspenda el GPS
    function pedirWakeLock() {
        if (!('wakeLock' in navigator)) return;
        navigator.wakeLock.request('screen').then(function (wl) {
            wakeLock = wl;
        }).catch(function () { /* sin wake lock, se sigue igual */ });
    }
    document.addEventListener('visibilitychange', function () {
        if (document.visibilityState === 'visible' && watchId !== null) {
            pedirWakeLock();
        }
    });

    window.rkTxStart = function () {
        if (!navigator.geolocation) { aviso('Este dispositivo no soporta GPS.', true); return; }
        watchId = navigator.geolocation.watchPosition(enviar, errorGeo, {
            enableHighAccuracy: true, maximumAge: 5000, timeout: 20000
        });
        pedirWakeLock();
        // Heartbeat: si el GPS no reporta movimiento, reenvía la última
        // posición cada 30s para que los espectadores sigan viendo "en línea"
        hbId = setInterval(function () {
            if (lastPos && watchId !== null) enviar(lastPos);
        }, 30000);
        // Amarillo hasta que llegue la primera posición real
        dot.className = 'dot wait';
        estado.textContent = 'Obteniendo señal GPS...';
        btnS.disabled = true;
        btnP.disabled = false;
        aviso('Buscando señal GPS... si tarda, verificá que el permiso de ubicación esté permitido.');
    };

    window.rkTxStop = function () {
        if (watchId !== null) navigator.geolocation.clearWatch(watchId);
        if (hbId !== null) clearInterval(hbId);
        if (wakeLock) { wakeLock.release().catch(function () {}); wakeLock = null; }
        hbId = null;
        watchId = null;
        dot.className = 'dot off';
        estado.textContent = 'Transmisión detenida';
        btnS.disabled = false;
        btnP.disabled = true;
    };
})();
