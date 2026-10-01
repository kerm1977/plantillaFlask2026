// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
// puntos_eventos.js - Panel admin de eventos de puntos (crear, toggles, borrar)
(function () {
    'use strict';

    async function post(url, payload) {
        const r = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload || {})
        });
        return r.json();
    }

    window.peToggle = async function (id, campo) {
        const d = await post('/api/puntos-eventos/' + id + '/toggle', { campo: campo });
        if (d.ok) { window.location.reload(); }
        else { alert(d.error || 'Error'); }
    };

    window.peBorrar = async function (id) {
        if (!confirm('¿Eliminar este evento de puntos?')) return;
        const d = await post('/api/puntos-eventos/' + id + '/borrar');
        if (d.ok) { window.location.reload(); }
        else { alert(d.error || 'Error'); }
    };

    document.addEventListener('DOMContentLoaded', function () {
        const form = document.getElementById('peForm');
        if (!form) return;
        form.addEventListener('submit', async function (e) {
            e.preventDefault();
            const d = await post('/api/puntos-eventos', {
                nombre: document.getElementById('peNombre').value,
                puntos: document.getElementById('pePuntos').value,
                descripcion: document.getElementById('peDesc').value,
                publico: document.getElementById('pePublico').checked
            });
            if (d.ok) { window.location.reload(); }
            else { alert(d.error || 'Error al crear el evento'); }
        });
    });
})();
