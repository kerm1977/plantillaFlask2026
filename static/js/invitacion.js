// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
// invitacion.js - Invitación personalizada 9:16 por WhatsApp (dashboard)
const Invitacion = (function () {
    let personas = [];
    let eventos = [];

    function norm(s) {
        return (s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
    }
    function urlPng() {
        const ev = document.getElementById('invEvento').value;
        const ced = document.getElementById('invCedula').value;
        return (ev && ced) ? `/api/invitacion.png?evento=${ev}&cedula=${ced}` : '';
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
        pintarLista();
        actualizar();
    }

    async function whatsapp() {
        const url = urlPng();
        if (!url) { alert('Elegí evento y persona primero.'); return; }
        const ev = eventos.find(function (e) { return String(e.id) === document.getElementById('invEvento').value; });
        const p = personas.find(function (x) { return x.cedula === document.getElementById('invCedula').value; });
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

    return { abrir: abrir, filtrar: pintarLista, elegir: elegir, actualizar: actualizar, whatsapp: whatsapp };
})();

function mostrarInvitacion() { Invitacion.abrir(); }
