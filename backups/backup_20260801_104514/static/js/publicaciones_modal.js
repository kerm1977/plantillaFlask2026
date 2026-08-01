// ==========================================
// FUNCIONES DE MODAL DE PUBLICACIONES
// ==========================================

let _pubModal = null;
let _editingPubId = null;

function _getPubModal() {
    if (!_pubModal) {
        const el = document.getElementById('pubModal');
        if (el.parentElement !== document.body) document.body.appendChild(el);
        _pubModal = new bootstrap.Modal(el);
    }
    return _pubModal;
}

function showCreateModal() {
    _editingPubId = null;
    _resetForm();
    document.getElementById('pubModalTitle').innerHTML = '<i class="bi bi-calendar-plus me-2 text-orange"></i>Nuevo Evento';
    document.getElementById('pubSubmitTxt').textContent = 'Guardar Evento';
    document.getElementById('pubFormMsg').innerHTML = '';
    _getPubModal().show();
}

function toggleTipoFields() {
    const tipo = document.getElementById('pubTipo').value;
    document.getElementById('fieldsRifa').classList.toggle('d-none', tipo !== 'Rifa');
    document.getElementById('fieldsCaminata').classList.toggle('d-none', tipo !== 'Caminata');
}

function previewImg(input, previewId) {
    const img = document.getElementById(previewId);
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = e => { img.src = e.target.result; img.classList.remove('d-none'); };
        reader.readAsDataURL(input.files[0]);
    }
}
