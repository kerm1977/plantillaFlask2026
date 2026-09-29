// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
// Modal de doble confirmación para eliminar archivos (estilo app).
// Usa los helpers que multimedia.js expone en window._mm.
(function () {
    'use strict';
    const $ = id => document.getElementById(id);
    let _path = null, _step = 1;

    function pintar() {
        const t = $('mmDelTitle'), m = $('mmDelMsg'), b = $('mmDelBtn');
        if (_step === 1) {
            t.textContent = 'Paso 1 de 2';
            m.innerHTML = `¿Seguro que deseas eliminar <strong>${window._mm.trunc(_path.split('/').pop())}</strong>?`;
            b.className = 'btn btn-outline-danger rounded-pill px-4 shadow-sm fw-bold w-100';
            b.textContent = 'Continuar';
        } else {
            t.textContent = 'Paso 2 de 2';
            m.innerHTML = 'Esta acción es <strong>irreversible</strong>: el archivo se borra del servidor y <strong>no se puede recuperar</strong>.';
            b.className = 'btn btn-danger rounded-pill px-4 shadow-sm fw-bold w-100';
            b.innerHTML = '<i class="bi bi-trash-fill me-1"></i>Eliminar definitivamente';
        }
    }

    window.mmEliminar = function (path) {
        _path = path; _step = 1;
        pintar();
        new bootstrap.Modal($('mmDeleteModal')).show();
    };

    window.mmCerrarDel = function () {
        const m = bootstrap.Modal.getInstance($('mmDeleteModal'));
        if (m) m.hide();
    };

    window.mmDelAvanzar = async function () {
        if (_step === 1) {
            _step = 2; pintar(); return;
        }
        const btn = $('mmDelBtn');
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Eliminando…';
        try {
            await window._mm.api('/api/multimedia/delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: _path })
            });
            bootstrap.Modal.getInstance($('mmDeleteModal')).hide();
            window._mm.msg('Eliminado ✓', true);
            window._mm.cargar();
        } catch (e) { window._mm.msg(e.message, false); }
        finally { btn.disabled = false; }
    };
})();
