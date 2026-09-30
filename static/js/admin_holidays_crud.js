// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
async function guardarFeriado() {
    const id = document.getElementById('modal-id').value;
    const isCustom = document.getElementById('modal-custom').value === '1';
    const formData = armarFormData('modal-');
    if (isCustom) {
        formData.append('month', document.getElementById('modal-mes').value);
        formData.append('day', document.getElementById('modal-dia').value);
        formData.append('end_month', document.getElementById('modal-fin-mes').value);
        formData.append('end_day', document.getElementById('modal-fin-dia').value);
    }
    try {
        const res = await fetch('/api/holidays/' + id, {method: 'POST', body: formData});
        const d = await res.json();
        if (d.ok) {
            mostrarMensaje('Guardado correctamente', true);
            if (modalInstance) modalInstance.hide();
            setTimeout(() => window.location.reload(), 700);
        } else {
            mostrarMensaje(d.error || 'Error al guardar', false);
        }
    } catch (e) {
        mostrarMensaje('Error de red', false);
    }
}

async function guardarNuevoFeriado() {
    const formData = armarFormData('nuevo-');
    formData.append('month', document.getElementById('nuevo-mes').value);
    formData.append('day', document.getElementById('nuevo-dia').value);
    formData.append('end_month', document.getElementById('nuevo-fin-mes').value);
    formData.append('end_day', document.getElementById('nuevo-fin-dia').value);
    try {
        const res = await fetch('/api/holidays/custom', {method: 'POST', body: formData});
        const d = await res.json();
        if (d.ok) {
            mostrarMensaje('Trigger creado', true);
            if (nuevoModalInstance) nuevoModalInstance.hide();
            setTimeout(() => window.location.reload(), 700);
        } else {
            mostrarMensaje(d.error || 'Error al crear', false);
        }
    } catch (e) {
        mostrarMensaje('Error de red', false);
    }
}

async function eliminarFeriado(id) {
    if (!confirm('¿Eliminar este trigger personalizado?')) return;
    try {
        const res = await fetch('/api/holidays/custom/' + id, {method: 'DELETE'});
        const d = await res.json();
        if (d.ok) {
            mostrarMensaje('Eliminado', true);
            setTimeout(() => window.location.reload(), 700);
        } else {
            mostrarMensaje(d.error || 'Error al eliminar', false);
        }
    } catch (e) {
        mostrarMensaje('Error de red', false);
    }
}


function seleccionarTodasCanciones(seleccionar) {
    const select = document.getElementById('bg-songs');
    for (const opt of select.options) {
        opt.selected = seleccionar;
    }
}

async function guardarMusicaFondo() {
    const formData = new FormData();
    formData.append('enabled', document.getElementById('bg-enabled').checked ? 'true' : 'false');
    formData.append('random', document.getElementById('bg-random').checked ? 'true' : 'false');
    const select = document.getElementById('bg-songs');
    for (const opt of select.options) {
        if (opt.selected) formData.append('songs', opt.value);
    }
    try {
        const res = await fetch('/api/background-music', {method: 'POST', body: formData});
        const d = await res.json();
        if (d.ok) {
            mostrarMensaje('Música de fondo guardada', true);
        } else {
            mostrarMensaje(d.error || 'Error al guardar', false);
        }
    } catch (e) {
        mostrarMensaje('Error de red', false);
    }
}

async function guardarNotaActiva() {
    const noteId = document.getElementById('activeNoteSelect').value;
    const isPublic = document.getElementById('activeNotePublic').checked;
    const body = JSON.stringify({note_id: noteId, is_public: isPublic});
    try {
        const res = await fetch('/api/active-note', {method: 'POST', headers: {'Content-Type':'application/json'}, body});
        const d = await res.json();
        if (d.ok) {
            mostrarMensaje('Nota activa guardada', true);
        } else {
            mostrarMensaje(d.error || 'Error al guardar', false);
        }
    } catch (e) {
        mostrarMensaje('Error de red', false);
    }
}

async function limpiarNotaActiva() {
    try {
        const res = await fetch('/api/active-note', {method: 'DELETE'});
        const d = await res.json();
        if (d.ok) {
            document.getElementById('activeNoteSelect').value = '';
            document.getElementById('activeNotePublic').checked = false;
            mostrarMensaje('Nota activa desactivada', true);
        } else {
            mostrarMensaje(d.error || 'Error al desactivar', false);
        }
    } catch (e) {
        mostrarMensaje('Error de red', false);
    }
}
