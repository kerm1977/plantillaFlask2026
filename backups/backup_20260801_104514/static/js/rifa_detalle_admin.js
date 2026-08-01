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
                btn.className = 'btn btn-sm rounded-pill me-1 btn-success';
                btn.innerHTML = '<i class="bi bi-cash-stack"></i>';
                btn.title = 'Marcar como no pagado';
                // Mostrar sello PAGADO y quitar cancelado si existiera
                const cancelado = card.querySelector('.cancelado-stamp');
                if (cancelado) cancelado.remove();
                const oldPagado = card.querySelector('.pagado-stamp');
                if (oldPagado) oldPagado.remove();
                const stamp = document.createElement('div');
                stamp.className = 'position-absolute top-50 start-50 translate-middle pagado-stamp';
                stamp.style.cssText = 'z-index:10;transform:translate(-50%,-50%) rotate(-15deg);pointer-events:none;';
                stamp.innerHTML = '<span class="badge rounded-pill" style="font-size:1.5rem;padding:0.5rem 1rem;background:rgba(40,167,69,0.15);color:#28a745;border:3px solid #28a745;font-weight:800;letter-spacing:2px;">PAGADO</span>';
                card.appendChild(stamp);
            } else {
                btn.className = 'btn btn-sm rounded-pill me-1 btn-outline-secondary';
                btn.innerHTML = '<i class="bi bi-cash"></i>';
                btn.title = 'Marcar como pagado';
                // Quitar sello PAGADO, sin mostrar cancelado
                const pagado = card.querySelector('.pagado-stamp');
                if (pagado) pagado.remove();
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
    const query = document.getElementById('searchInput').value.trim();
    const resultsDiv = document.getElementById('searchResults');
    
    if (query.length < 1) {
        resultsDiv.innerHTML = '';
        return;
    }
    
    const rifaId = window.RIFA_CONFIG ? window.RIFA_CONFIG.id : 0;
    fetch(`/api/rifas/${rifaId}/search?q=${encodeURIComponent(query)}`)
        .then(r => r.json())
        .then(data => {
            if (data.results && data.results.length > 0) {
                resultsDiv.innerHTML = data.results.map(r => `
                    <div class="alert alert-info rounded-3 mb-1 py-2">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <span class="badge bg-primary rounded-pill me-2">${r.number}</span>
                                <strong>${r.customer_name}</strong>
                                <small class="text-muted d-block">${r.customer_phone}</small>
                            </div>
                            <span class="badge ${r.is_paid ? 'bg-success' : 'bg-warning'} rounded-pill">
                                ${r.is_paid ? 'Pagado' : 'Pendiente'}
                            </span>
                        </div>
                    </div>
                `).join('');
            } else {
                resultsDiv.innerHTML = `
                    <div class="alert alert-secondary rounded-3 mb-0 py-2">
                        <small class="text-muted">Número disponible o no encontrado</small>
                    </div>
                `;
            }
        })
        .catch(err => {
            console.error('Error searching:', err);
        });
}
