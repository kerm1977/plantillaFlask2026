// ==========================================
// FUNCIONES DE MODALES DE RIFA DETALLE
// ==========================================

function openUserDataModal() {
    if (selectedNumbers.length === 0) { alert('Primero selecciona números'); return; }
    if (!userDataModal) userDataModal = new bootstrap.Modal(document.getElementById('userDataModal'));
    document.getElementById('modalCedula').value = '';
    document.getElementById('modalPhone').value = '';
    document.getElementById('modalPin').value = '';
    document.getElementById('modalAutocompleteResults').style.display = 'none';
    
    const modalNumbersDiv = document.getElementById('modalSelectedNumbers');
    modalNumbersDiv.innerHTML = selectedNumbers.map(num => 
        `<span class="badge rounded-pill" style="background:rgba(40,167,69,0.15);color:#28a745;border:1px solid rgba(40,167,69,0.3);font-size:0.9rem;padding:0.4rem 0.7rem;">${num}</span>`
    ).join('');
    
    const price = window.RIFA_CONFIG ? window.RIFA_CONFIG.price : 0;
    const totalPrice = selectedNumbers.length * price;
    document.getElementById('modalTotalPrice').textContent = '₡' + totalPrice.toLocaleString();
    
    userDataModal.show();
}

function confirmUserData() {
    const cedula = document.getElementById('modalCedula').value.trim();
    const phone  = document.getElementById('modalPhone').value.trim();
    const pin    = document.getElementById('modalPin').value.trim();
    if (!cedula || !phone || !pin) { alert('Por favor completa todos los campos'); return; }
    if (pin.length !== 4 || !/^[A-Za-z0-9]{4}$/.test(pin)) { alert('El PIN debe tener exactamente 4 caracteres alfanuméricos (Ej: A1B2)'); return; }
    const rifaId = window.RIFA_CONFIG ? window.RIFA_CONFIG.id : 0;
    fetch(`/api/rifas/${rifaId}/select-multiple`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({numbers: selectedNumbers, customer_name: cedula, customer_phone: phone, customer_cedula: cedula, pin: pin})
    })
    .then(r => r.json())
    .then(data => {
        if (data.ok) { userDataModal.hide(); alert(`¡${selectedNumbers.length} números seleccionados exitosamente!`); clearLocalStorage(); window.location.reload(); }
        else { alert(data.error || 'Error al seleccionar'); }
    });
}

function openClearModal() {
    if (selectedNumbers.length === 0) { alert('No hay números seleccionados'); return; }
    openClearModalCard('');
}

function openClearModalCard(phone) {
    if (!clearModal) clearModal = new bootstrap.Modal(document.getElementById('clearModal'));
    document.getElementById('clearPhone').value = phone || '';
    document.getElementById('clearPin').value = '';
    clearModal.show();
}

function confirmClearNumbers() {
    const phone = document.getElementById('clearPhone').value.trim();
    const pin   = document.getElementById('clearPin').value.trim();
    if (!phone || !pin) { alert('Ingresa tu teléfono y PIN'); return; }
    const rifaId = window.RIFA_CONFIG ? window.RIFA_CONFIG.id : 0;
    fetch(`/api/rifas/${rifaId}/release-numbers`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({phone: phone, pin: pin})
    })
    .then(r => r.json())
    .then(data => {
        if (data.ok) { clearModal.hide(); alert(`¡${data.count} números liberados exitosamente!`); clearLocalStorage(); window.location.reload(); }
        else { alert(data.error || 'Error al liberar números'); }
    });
}

function toggleMobileSelection() { openUserDataModal(); }
