// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
// evento_guard.js - Protege el modal Crear/Editar Evento contra
// pérdida de datos: marca "dirty" con cualquier input del usuario y
// pide confirmación antes de cerrar si hay información sin guardar.
(function () {
    'use strict';
    document.addEventListener('DOMContentLoaded', function () {
        var modalEl = document.getElementById('eventoModal');
        var form = document.getElementById('createEventForm');
        var descartarModalEl = document.getElementById('eventoDescartarModal');
        var descartarBtn = document.getElementById('eventoDescartarBtn');
        if (!modalEl || !form || !descartarModalEl || !descartarBtn) return;

        var dirty = false;
        var allowClose = false;

        // Al abrirse (crear o editar), el formulario ya viene poblado:
        // se considera "limpio" a partir de ese momento.
        modalEl.addEventListener('shown.bs.modal', function () { dirty = false; });

        // Solo eventos reales del usuario (isTrusted), no asignaciones por código.
        form.addEventListener('input', function (e) { if (e.isTrusted) dirty = true; });
        form.addEventListener('change', function (e) { if (e.isTrusted) dirty = true; });

        // Toda vía de cierre (X, Escape, hide() programático) pasa por aquí.
        modalEl.addEventListener('hide.bs.modal', function (e) {
            if (!dirty || allowClose) return;
            e.preventDefault();
            bootstrap.Modal.getOrCreateInstance(descartarModalEl).show();
        });

        descartarBtn.addEventListener('click', function () {
            allowClose = true;
            bootstrap.Modal.getOrCreateInstance(descartarModalEl).hide();
            bootstrap.Modal.getOrCreateInstance(modalEl).hide();
            allowClose = false;
            dirty = false;
        });
    });
})();
