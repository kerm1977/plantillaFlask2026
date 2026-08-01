// ==========================================
// FUNCIONES DE ELIMINACIÓN DE PUBLICACIONES
// ==========================================

async function deleteEvento(id, nombre) {
    abrirModalBorrarUnificado({
        titulo: 'Eliminar Evento',
        mensaje: '¿Estás seguro de que deseas eliminar este evento? Esta acción no se puede deshacer.',
        nombre: nombre || 'este evento',
        onConfirmar: async () => {
            try {
                const res = await fetch(`/api/publicaciones/${id}`, { method: 'DELETE' });
                const d = await res.json();
                if (d.ok) window.location.reload();
                else alert(d.error || 'Error al eliminar');
            } catch (err) {
                alert('Error de conexión');
            }
        }
    });
}

async function toggleEvento(id, btn) {
    const res = await fetch(`/api/publicaciones/${id}/toggle`, { method: 'POST' });
    const d   = await res.json();
    if (d.ok) window.location.reload();
}
