// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
// puntos_eventos.js - Panel admin de eventos de puntos (crear, toggles, editar, borrar)
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

    function avisar(msg) {
        if (typeof mostrarAlerta === 'function') mostrarAlerta(msg);
        else alert(msg);
    }

    // Activo (verde) / Inactivo (rojo relleno) y Público/Privado — actualiza en vivo
    window.peToggle = async function (id, campo) {
        const d = await post('/api/puntos-eventos/' + id + '/toggle', { campo: campo });
        if (!d.ok) { avisar(d.error || 'Error'); return; }
        const on = !!d[campo];
        if (campo === 'activo') {
            const btn = document.getElementById('peBtnActivo' + id);
            if (btn) {
                btn.classList.toggle('btn-success', on);
                btn.classList.toggle('btn-danger', !on);
                btn.title = on ? 'Desactivar' : 'Activar';
            }
            const badge = document.getElementById('peBadgeActivo' + id);
            if (badge) {
                badge.className = 'badge ' + (on ? 'bg-success' : 'bg-secondary');
                badge.textContent = on ? 'Activo' : 'Inactivo';
            }
        } else {
            const btn = document.getElementById('peBtnPublico' + id);
            if (btn) {
                btn.title = on ? 'Hacer privado' : 'Hacer público';
                btn.innerHTML = '<i class="bi bi-' + (on ? 'eye' : 'eye-slash') + '"></i>';
            }
            const badge = document.getElementById('peBadgePublico' + id);
            if (badge) {
                badge.className = 'badge ' + (on ? 'bg-info text-dark' : 'bg-dark');
                badge.textContent = on ? 'Público' : 'Privado';
            }
            if (window.PE_EVENTOS && window.PE_EVENTOS[id]) window.PE_EVENTOS[id].publico = on;
        }
    };

    window.peEditar = function (id) {
        const ev = (window.PE_EVENTOS || {})[id];
        if (!ev) return;
        document.getElementById('peEditId').value = id;
        document.getElementById('peEditNombre').value = ev.nombre;
        document.getElementById('peEditPuntos').value = ev.puntos;
        document.getElementById('peEditDesc').value = ev.descripcion;
        document.getElementById('peEditPublico').checked = !!ev.publico;
        bootstrap.Modal.getOrCreateInstance(document.getElementById('peEditModal')).show();
    };

    window.peGuardarEdicion = async function () {
        const id = document.getElementById('peEditId').value;
        const d = await post('/api/puntos-eventos/' + id + '/editar', {
            nombre: document.getElementById('peEditNombre').value,
            puntos: document.getElementById('peEditPuntos').value,
            descripcion: document.getElementById('peEditDesc').value,
            publico: document.getElementById('peEditPublico').checked
        });
        if (d.ok) { window.location.reload(); }
        else { avisar(d.error || 'Error al guardar'); }
    };

    window.peBorrar = function (id) {
        const ev = (window.PE_EVENTOS || {})[id] || {};
        abrirModalBorrarUnificado({
            titulo: 'Eliminar evento de puntos',
            mensaje: '¿Eliminar este evento? Solo se puede borrar si nadie recibió puntos todavía.',
            nombre: ev.nombre || '',
            onConfirmar: async function () {
                const d = await post('/api/puntos-eventos/' + id + '/borrar');
                if (d.ok) { window.location.reload(); }
                else { avisar(d.error || 'Error'); }
            }
        });
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
            else { avisar(d.error || 'Error al crear el evento'); }
        });
    });
})();
