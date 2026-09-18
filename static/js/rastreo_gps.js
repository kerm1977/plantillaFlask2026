// ══ BLINDADO — RASTREO EN VIVO ══
// Código probado y estable. NO modificar sin revisar el flujo completo.
// Transmisor GPS reutilizable: captura posiciones y las envía al servidor.
// Lo usa el panel de admin (y podría usarlo cualquier página).
window.RK_GPS = (function () {
    'use strict';
    var watchId = null, hbId = null, wakeLock = null, lastPos = null;
    var ultimo = 0, token = null, cb = null;
    var nativo = false, natId = null;
    var MIN_MS = 8000; // mínimo 8s entre envíos

    function pedirWakeLock() {
        if (!('wakeLock' in navigator)) return;
        navigator.wakeLock.request('screen')
            .then(function (w) { wakeLock = w; })
            .catch(function () {});
    }
    document.addEventListener('visibilitychange', function () {
        if (document.visibilityState === 'visible' && watchId !== null) pedirWakeLock();
    });

    function ping(lat, lng, acc) {
        fetch('/api/rastreo/ping/' + token, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lat: lat, lng: lng, acc: acc })
        }).then(function (r) {
            if (r.status === 410) { stop(); if (cb) cb('stopped'); return null; }
            return r.json();
        }).then(function (d) {
            if (d && d.ok && cb) cb('ok', { total: d.total, acc: acc });
        }).catch(function () {
            if (cb) cb('offline');
        });
    }

    function onPos(pos) {
        var a = Date.now();
        if (a - ultimo < MIN_MS) return;
        ultimo = a;
        lastPos = pos;
        if (cb) cb('pos', { lat: pos.coords.latitude,
                            lng: pos.coords.longitude,
                            acc: pos.coords.accuracy });
        ping(pos.coords.latitude, pos.coords.longitude, pos.coords.accuracy);
    }

    function onErr(e) {
        if (cb) cb('geoerr', { code: e ? e.code : 0 });
    }

    // Modo nativo: la app Android corre un servicio en primer plano que sigue
    // transmitiendo aunque la app esté minimizada o la pantalla apagada.
    function hayNativo() {
        return window.RkAndroid && typeof window.RkAndroid.startGps === 'function';
    }

    function startNativo() {
        nativo = true;
        watchId = 1; // marca de "corriendo" para isRunning()
        window.RkAndroid.startGps(token, location.origin);
        natId = setInterval(function () {
            try {
                var st = JSON.parse(window.RkAndroid.getStats() || '{}');
                if (st.corriendo === false) { stop(); if (cb) cb('stopped'); return; }
                if (cb) cb('ok', { total: st.puntos || 0, acc: st.acc });
            } catch (e) {}
        }, 10000);
        if (cb) cb('ok', { total: 0, acc: 0 });
    }

    function start(t, callback) {
        if (!navigator.geolocation && !hayNativo()) return false;
        stop();
        token = t;
        cb = callback || null;
        ultimo = 0;
        if (hayNativo()) { startNativo(); return true; }
        watchId = navigator.geolocation.watchPosition(onPos, onErr, {
            enableHighAccuracy: true, maximumAge: 5000, timeout: 20000
        });
        // Heartbeat: reenvía la última posición aunque el GPS no se mueva
        hbId = setInterval(function () {
            if (lastPos && watchId !== null) onPos(lastPos);
        }, 30000);
        pedirWakeLock();
        return true;
    }

    function stop() {
        if (nativo) {
            try { window.RkAndroid.stopGps(); } catch (e) {}
            nativo = false;
        }
        if (natId !== null) { clearInterval(natId); natId = null; }
        if (watchId !== null && watchId !== 1) navigator.geolocation.clearWatch(watchId);
        watchId = null;
        if (hbId !== null) clearInterval(hbId);
        hbId = null;
        if (wakeLock) { wakeLock.release().catch(function () {}); wakeLock = null; }
    }

    return {
        start: start,
        stop: stop,
        isRunning: function () { return watchId !== null; }
    };
})();
