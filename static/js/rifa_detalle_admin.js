// ==========================================
// FUNCIONES DE ADMIN Y BÚSQUEDA DE RIFA DETALLE
// ==========================================

async function togglePayment(phone) {
    try {
        const rifaId = window.RIFA_CONFIG ? window.RIFA_CONFIG.id : 0;
        const res = await fetch(`/api/rifas/${rifaId}/toggle-payment/${phone}`, { method: 'POST' });
        const data = await res.json();
        if (data.ok) {
            // Recargar página para asegurar estado correcto desde servidor
            window.location.reload();
        } else {
            alert(data.error || 'Error al actualizar estado de pago');
        }
    } catch (err) {
        alert('Error de conexión');
    }
}

function superClearNumbers(phone) {
    abrirModalBorrarUnificado({
        titulo: 'Liberar Números',
        mensaje: '¿Liberar todos los números de este cliente?',
        nombre: phone,
        onConfirmar: () => {
            const rifaId = window.RIFA_CONFIG ? window.RIFA_CONFIG.id : 0;
            fetch(`/api/rifas/${rifaId}/admin-release`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({phone: phone})
            })
            .then(r => r.json())
            .then(data => {
                if (data.ok) { alert(`¡${data.count} números liberados!`); window.location.reload(); }
                else { alert(data.error || 'Error'); }
            });
        }
    });
}

function shareRaffle() {
    const url = window.location.href;
    const rifaName = window.RIFA_CONFIG ? window.RIFA_CONFIG.name : 'Rifa';
    if (navigator.share) { navigator.share({title: rifaName, url: url}); }
    else { navigator.clipboard.writeText(url).then(() => { alert('¡Enlace copiado!'); }); }
}

function searchSelections() {
    const query = document.getElementById('searchInput').value.trim().toLowerCase();
    const selectionCards = document.querySelectorAll('.row.g-3 > div');
    
    selectionCards.forEach(card => {
        if (query.length < 1) {
            card.style.display = '';
            return;
        }
        
        const cardText = card.textContent.toLowerCase();
        if (cardText.includes(query)) {
            card.style.display = '';
        } else {
            card.style.display = 'none';
        }
    });
}
