// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
function _initTripleConfirmModal() {
    const modalEl = document.getElementById('tripleConfirmDeleteModal');
    if (!modalEl) return null;
    return bootstrap.Modal.getOrCreateInstance(modalEl);
}

function _actualizarTripleConfirm(nombre) {
    const titleEl = document.getElementById('tripleConfirmTitle');
    const msgEl = document.getElementById('tripleConfirmMessage');
    const inputGroup = document.getElementById('tripleConfirmInputGroup');
    const input = document.getElementById('tripleConfirmInput');
    const btn = document.getElementById('tripleConfirmBtn');
    if (titleEl) titleEl.textContent = `Paso ${_tripleConfirmStep} de 3`;
    if (input) input.value = '';
    if (inputGroup) inputGroup.classList.add('d-none');
    if (btn) {
        btn.classList.remove('btn-danger');
        btn.classList.add('btn-outline-danger');
        btn.textContent = 'Continuar';
        btn.disabled = false;
    }
    if (_tripleConfirmStep === 1 && msgEl) {
        msgEl.innerHTML = `¿Seguro que deseas eliminar a <strong>${nombre}</strong>?`;
    } else if (_tripleConfirmStep === 2 && msgEl) {
        msgEl.innerHTML = `¿Realmente deseas eliminar a <strong>${nombre}</strong>?`;
    } else if (msgEl) {
        msgEl.innerHTML = `Esta acción es irreversible. Escribe <strong>ELIMINAR</strong> para confirmar.`;
        if (inputGroup) inputGroup.classList.remove('d-none');
        if (btn) {
            btn.classList.remove('btn-outline-danger');
            btn.classList.add('btn-danger');
            btn.textContent = 'Eliminar definitivamente';
        }
    }
}

function abrirTripleConfirmEliminar(nombre, onFinal) {
    const modal = _initTripleConfirmModal();
    if (!modal) return;
    _tripleConfirmStep = 1;
    _tripleConfirmCallback = onFinal;
    _actualizarTripleConfirm(nombre);
    modal.show();
}

function avanzarTripleConfirm() {
    const nombre = currentSelectedUserName || 'este contacto';
    const input = document.getElementById('tripleConfirmInput');
    if (_tripleConfirmStep === 3) {
        if (!input || input.value.trim().toUpperCase() !== 'ELIMINAR') {
            mostrarAlerta('Debes escribir ELIMINAR para confirmar.', 'warning');
            return;
        }
        const modal = _initTripleConfirmModal();
        if (typeof _tripleConfirmCallback === 'function') _tripleConfirmCallback();
        if (modal) modal.hide();
        return;
    }
    _tripleConfirmStep++;
    _actualizarTripleConfirm(nombre);
}

async function _ejecutarEliminacionUsuario() {
    const btn = document.getElementById('tripleConfirmBtn');
    const original = btn ? btn.innerHTML : '';
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Eliminando...';
    }
    try {
        const delId = currentSelectedUserObj ? currentSelectedUserObj.id : currentSelectedUserId;
        const response = await fetch(`/api/admin/delete_user/${delId}`, { method: 'DELETE' });
        const result = await response.json();
        if (response.ok && result.success) {
            const modal = _initTripleConfirmModal();
            if (modal) modal.hide();
            mostrarAlerta('Usuario eliminado permanentemente.', 'success');
            showUsersList(); loadAllUsers();
        } else {
            mostrarAlerta(result.error || 'No se pudo eliminar el usuario.', 'error');
        }
    } catch(err) { mostrarAlerta('Error al intentar eliminar el usuario.', 'error'); }
    finally { if (btn) { btn.disabled = false; btn.innerHTML = original; } }
}

function confirmDeleteUser() {
    const delId = currentSelectedUserObj ? currentSelectedUserObj.id : currentSelectedUserId;
    if (!delId) {
        mostrarAlerta('Abra la ficha de un contacto para eliminarlo.', 'warning');
        return;
    }
    abrirTripleConfirmEliminar(currentSelectedUserName || 'este contacto', _ejecutarEliminacionUsuario);
}
