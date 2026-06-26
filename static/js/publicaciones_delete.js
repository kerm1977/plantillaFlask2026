// ==========================================
// FUNCIONES DE ELIMINACIÓN DE PUBLICACIONES
// ==========================================

let deletePubId = null;

async function deleteEvento(id, nombre) {
    deletePubId = id;
    document.getElementById('deletePubName').textContent = nombre || 'este evento';
    const modal = new bootstrap.Modal(document.getElementById('deletePubModal'));
    modal.show();
}

async function processDeletePub() {
    if (!deletePubId) return;
    const btn = document.getElementById('btnConfirmDeletePub');
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Eliminando...';
    btn.disabled = true;
    
    try {
        const res = await fetch(`/api/publicaciones/${deletePubId}`, { method: 'DELETE' });
        const d = await res.json();
        if (d.ok) {
            bootstrap.Modal.getInstance(document.getElementById('deletePubModal')).hide();
            window.location.reload();
        } else {
            alert(d.error || 'Error al eliminar');
            btn.innerHTML = 'Sí, eliminar evento';
            btn.disabled = false;
        }
    } catch (err) {
        alert('Error de conexión');
        btn.innerHTML = 'Sí, eliminar evento';
        btn.disabled = false;
    }
}

async function toggleEvento(id, btn) {
    const res = await fetch(`/api/publicaciones/${id}/toggle`, { method: 'POST' });
    const d   = await res.json();
    if (d.ok) window.location.reload();
}
