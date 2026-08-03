// ==========================================
// FUNCIONES DE ADMIN Y BÚSQUEDA DE RIFA DETALLE
// ==========================================

async function togglePayment(phone) {
    try {
        const rifaId = window.RIFA_CONFIG ? window.RIFA_CONFIG.id : 0;
        const res = await fetch(`/api/rifas/${rifaId}/toggle-payment/${phone}`, { method: 'POST' });
        const data = await res.json();
        if (data.ok) {
            const btn = document.getElementById(`payBtn_${phone}`);
            const card = document.getElementById(`card_${phone}`);
            if (data.is_paid) {
                btn.className = 'btn btn-sm rounded-pill btn-success';
                btn.innerHTML = '<i class="bi bi-cash-stack"></i>';
                btn.title = 'Marcar como no pagado';
                // Actualizar badge pequeño en lugar de overlay
                const cardBody = card.querySelector('.card-body');
                const headerDiv = cardBody.querySelector('.d-flex.justify-content-between');
                let badge = headerDiv.querySelector('.badge');
                if (!badge) {
                    badge = document.createElement('span');
                    badge.className = 'badge rounded-pill';
                    badge.style.cssText = 'font-size:0.65rem;padding:0.2rem 0.5rem;background:rgba(40,167,69,0.1);color:#28a745;border:1px solid #28a745;';
                    headerDiv.appendChild(badge);
                }
                badge.textContent = 'PAGADO';
                badge.style.cssText = 'font-size:0.65rem;padding:0.2rem 0.5rem;background:rgba(40,167,69,0.1);color:#28a745;border:1px solid #28a745;';
            } else {
                btn.className = 'btn btn-sm rounded-pill btn-outline-secondary';
                btn.innerHTML = '<i class="bi bi-cash"></i>';
                btn.title = 'Marcar como pagado';
                // Quitar badge PAGADO
                const cardBody = card.querySelector('.card-body');
                const headerDiv = cardBody.querySelector('.d-flex.justify-content-between');
                const badge = headerDiv.querySelector('.badge');
                if (badge) badge.remove();
            }
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
