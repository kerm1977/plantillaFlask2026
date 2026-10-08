// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
// invitacion.js - Invitación personalizada 9:16 por WhatsApp (dashboard)
const Invitacion = (function () {
    let personas = [];
    let eventos = [];
    const FAV_KEY = 'inv_favs_v1';

    const PARAM_KEY = 'inv_params_v1';
    const PARAM_IDS = { pos: 'invPos', band: 'invBand', blur: 'invBlur',
                        fnombre: 'invFnombre', finfo: 'invFinfo', fboton: 'invFboton' };
    let _ajusteTimer = null;

    function norm(s) {
        return (s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
    }
    function params() {
        const p = {};
        for (const k in PARAM_IDS) p[k] = document.getElementById(PARAM_IDS[k]).value;
        return p;
    }
    function urlPng() {
        const ev = document.getElementById('invEvento').value;
        const ced = document.getElementById('invCedula').value;
        if (!(ev && ced)) return '';
        const q = new URLSearchParams(params()).toString();
        return `/api/invitacion.png?evento=${ev}&cedula=${ced}&${q}`;
    }
    // Persistir ajustes + refrescar vista previa (con debounce)
    function ajuste() {
        for (const k in PARAM_IDS)
            document.getElementById(PARAM_IDS[k] + 'Val').textContent =
                document.getElementById(PARAM_IDS[k]).value + '%';
        localStorage.setItem(PARAM_KEY, JSON.stringify(params()));
        if (_ajusteTimer) clearTimeout(_ajusteTimer);
        _ajusteTimer = setTimeout(actualizar, 350);
    }
    function cargarParams() {
        let saved = {};
        try { saved = JSON.parse(localStorage.getItem(PARAM_KEY)) || {}; } catch (e) {}
        for (const k in PARAM_IDS) {
            if (saved[k] !== undefined) document.getElementById(PARAM_IDS[k]).value = saved[k];
            document.getElementById(PARAM_IDS[k] + 'Val').textContent =
                document.getElementById(PARAM_IDS[k]).value + '%';
        }
    }

    function pintarLista() {
        const lista = document.getElementById('invLista');
        const t = norm(document.getElementById('invBuscar').value);
        const res = personas.filter(function (p) {
            return !t || norm(p.nombre_completo + ' ' + p.cedula + ' ' + (p.telefono || '')).indexOf(t) !== -1;
        }).slice(0, 25);
        lista.innerHTML = res.map(function (p) {
            return '<button type="button" class="list-group-item list-group-item-action py-1 px-3 small" ' +
                'onclick="Invitacion.elegir(\'' + p.cedula + '\')">' +
                (p.nombre_completo || '') + ' <span class="text-muted">(' + p.cedula + ')</span></button>';
        }).join('');
    }

    // ── Invitaciones recientes (localStorage): evento reutilizable ──
    function favs() {
        try { return JSON.parse(localStorage.getItem(FAV_KEY)) || []; }
        catch (e) { return []; }
    }
    function pintarFavs() {
        const c = document.getElementById('invFavs');
        const f = favs();
        c.innerHTML = f.length ? f.map(function (x) {
            return '<span class="btn-group btn-group-sm">' +
                '<button type="button" class="btn btn-outline-success rounded-start-pill" ' +
                'onclick="Invitacion.usarFav(\'' + x.id + '\')" title="Usar esta invitación">' +
                '<i class="bi bi-envelope-paper me-1"></i>' + x.nombre + '</button>' +
                '<button type="button" class="btn btn-outline-danger rounded-end-pill px-2" ' +
                'onclick="Invitacion.borrarFav(\'' + x.id + '\')" title="Quitar">&times;</button></span>';
        }).join('') : '<span class="text-muted small">Las invitaciones que envíes o descargues quedan aquí para reutilizarlas.</span>';
    }
    function usarFav(id) {
        document.getElementById('invEvento').value = id;
        document.getElementById('invCedula').value = '';
        document.getElementById('invBuscar').value = '';
        actualizar();
        document.getElementById('invBuscar').focus();
    }
    function borrarFav(id) {
        localStorage.setItem(FAV_KEY, JSON.stringify(favs().filter(function (x) { return String(x.id) !== String(id); })));
        pintarFavs();
    }
    function usada() {
        const sel = document.getElementById('invEvento');
        const ev = eventos.find(function (e) { return String(e.id) === sel.value; });
        if (!ev) return;
        const f = favs().filter(function (x) { return String(x.id) !== String(ev.id); });
        f.unshift({ id: ev.id, nombre: ev.nombre, puntos: ev.puntos, fecha: ev.fecha });
        localStorage.setItem(FAV_KEY, JSON.stringify(f.slice(0, 10)));
        pintarFavs();
    }

    function elegir(cedula) {
        const p = personas.find(function (x) { return x.cedula === cedula; });
        document.getElementById('invCedula').value = cedula;
        document.getElementById('invBuscar').value = p ? (p.nombre_completo + ' (' + p.cedula + ')') : cedula;
        document.getElementById('invLista').innerHTML = '';
        actualizar();
    }

    function actualizar() {
        const url = urlPng();
        const evSel = document.getElementById('invEvento');
        const ev = eventos.find(function (e) { return String(e.id) === evSel.value; });
        const prev = document.getElementById('invPreview');
        const res = document.getElementById('invResumen');
        if (url) {
            prev.innerHTML = '<img src="' + url + '" class="img-fluid rounded-4" style="max-height:420px;" alt="Invitación">';
            res.textContent = ev ? (ev.nombre + (ev.puntos ? ' · +' + ev.puntos + ' puntos' : '')) : '';
        } else {
            prev.innerHTML = '<span class="text-muted small">Elegí evento y persona para ver la invitación</span>';
            res.textContent = '';
        }
        document.getElementById('invDescargar').href = url || '#';
        document.getElementById('invDescargar').classList.toggle('disabled', !url);
    }

    async function abrir() {
        const modal = new bootstrap.Modal(document.getElementById('invitacionModal'));
        modal.show();
        if (!eventos.length) {
            try {
                const [r1, r2] = await Promise.all([
                    fetch('/api/invitacion/eventos').then(function (r) { return r.json(); }),
                    fetch('/api/admin/hikers').then(function (r) { return r.json(); })
                ]);
                eventos = r1.eventos || [];
                personas = r2.hikers || r2 || [];
            } catch (e) { /* sin datos */ }
            const sel = document.getElementById('invEvento');
            sel.innerHTML = '<option value="">Elegí el evento...</option>' +
                eventos.map(function (e) {
                    return '<option value="' + e.id + '">' + e.nombre +
                        (e.puntos ? ' (+' + e.puntos + ' pts)' : '') + '</option>';
                }).join('');
        }
        // Preselección: la persona del expediente abierto
        const ced = (window.currentSelectedUserObj && currentSelectedUserObj.crm_cedula) || '';
        if (ced) elegir(ced);
        cargarParams();
        pintarLista();
        pintarFavs();
        actualizar();
    }

    async function whatsapp() {
        const url = urlPng();
        if (!url) { alert('Elegí evento y persona primero.'); return; }
        const ev = eventos.find(function (e) { return String(e.id) === document.getElementById('invEvento').value; });
        const p = personas.find(function (x) { return x.cedula === document.getElementById('invCedula').value; });
        usada();
        const tel = p && p.telefono ? '506' + String(p.telefono).replace(/\D/g, '') : '';
        const texto = '¡' + (p ? p.nombre_completo : '') + ', estás invitado(a) a "' +
            (ev ? ev.nombre : 'nuestra actividad') + '"' +
            (ev && ev.fecha ? ' el ' + ev.fecha : '') +
            (ev && ev.puntos ? '. ¡Ganás ' + ev.puntos + ' puntos por participar!' : '.') +
            ' Te adjuntamos tu invitación personalizada.';
        try {
            const blob = await (await fetch(url)).blob();
            const file = new File([blob], 'invitacion.png', { type: 'image/png' });
            if (navigator.canShare && navigator.canShare({ files: [file] })) {
                await navigator.share({ files: [file], text: texto });
                return;
            }
        } catch (e) { /* fallback abajo */ }
        // Fallback: descarga la imagen y abre el chat de WhatsApp
        const a = document.createElement('a');
        a.href = url; a.download = 'invitacion.png';
        document.body.appendChild(a); a.click(); a.remove();
        window.open('https://wa.me/' + tel + '?text=' + encodeURIComponent(texto), '_blank');
    }

    return { abrir: abrir, filtrar: pintarLista, elegir: elegir, actualizar: actualizar,
             whatsapp: whatsapp, usarFav: usarFav, borrarFav: borrarFav, usada: usada,
             ajuste: ajuste };
})();

function mostrarInvitacion() { Invitacion.abrir(); }
