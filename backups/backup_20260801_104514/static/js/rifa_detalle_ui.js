// ==========================================
// FUNCIONES DE UI DE RIFA DETALLE
// ==========================================

let selectedNumbers = [];
let acTimeout = null;
let userDataModal, clearModal;

document.addEventListener('DOMContentLoaded', function() {
    const rifaId = window.RIFA_CONFIG ? window.RIFA_CONFIG.id : 0;
    // Cargar selecciones guardadas del localStorage
    try {
        const saved = localStorage.getItem('raffleSelection_' + rifaId);
        if (saved) {
            const data = JSON.parse(saved);
            selectedNumbers = data.numbers || [];
        }
    } catch (e) {
        console.warn('Error cargando selecciones del localStorage:', e);
        selectedNumbers = [];
    }
    // Actualizar estado visual de los botones con las selecciones cargadas
    selectedNumbers.forEach(num => {
        const btn = document.querySelector(`.number-btn[data-number="${num}"]`);
        if (btn) btn.classList.add('btn-primary');
    });
    updateSelectionPanel();
    updateMobileSelectButton();
    const rifaPanel = document.getElementById('rifaDetailsPanel');
    if (rifaPanel) {
        rifaPanel.addEventListener('hide.bs.collapse', () => {
            document.getElementById('rifaToggleBtn').innerHTML = '<i class="bi bi-eye me-1"></i><span>Ver Rifa</span>';
        });
        rifaPanel.addEventListener('show.bs.collapse', () => {
            document.getElementById('rifaToggleBtn').innerHTML = '<i class="bi bi-eye-slash me-1"></i><span>Ocultar Detalles</span>';
        });
    }
    const modalCedulaInput = document.getElementById('modalCedula');
    if (modalCedulaInput) {
        modalCedulaInput.addEventListener('input', function() {
            const query = this.value.trim();
            const resultsDiv = document.getElementById('modalAutocompleteResults');
            if (acTimeout) clearTimeout(acTimeout);
            if (query.length < 2) { resultsDiv.style.display = 'none'; return; }
            acTimeout = setTimeout(() => {
                fetch(`/api/hikers/search?q=${encodeURIComponent(query)}`)
                    .then(r => r.json())
                    .then(data => {
                        if (data.hikers && data.hikers.length > 0) {
                            resultsDiv.innerHTML = data.hikers.map(h =>
                                `<a href="#" class="list-group-item list-group-item-action"
                                   onclick="selectHiker('${h.cedula}', '${h.nombre_completo}', '${h.telefono || ''}')"
                                   data-cedula="${h.cedula}">
                                   <strong>${h.nombre_completo}</strong> <small class="text-muted">(${h.cedula})</small></a>`
                            ).join('');
                            resultsDiv.style.display = 'block';
                        } else { resultsDiv.style.display = 'none'; }
                    });
            }, 300);
        });
    }
});

function saveToLocalStorage() {
    const rifaId = window.RIFA_CONFIG ? window.RIFA_CONFIG.id : 0;
    localStorage.setItem('raffleSelection_' + rifaId, JSON.stringify({numbers: selectedNumbers, timestamp: new Date().toISOString()}));
}
function clearLocalStorage() {
    const rifaId = window.RIFA_CONFIG ? window.RIFA_CONFIG.id : 0;
    localStorage.removeItem('raffleSelection_' + rifaId);
}

function selectHiker(cedula, nombre, telefono) {
    document.getElementById('modalCedula').value = nombre + ' (' + cedula + ')';
    if (telefono) document.getElementById('modalPhone').value = telefono;
    document.getElementById('modalAutocompleteResults').style.display = 'none';
}

function deseleccionarNumeros() {
    selectedNumbers.forEach(num => { const btn = document.querySelector(`.number-btn[data-number="${num}"]`); if (btn) btn.classList.remove('btn-primary'); });
    selectedNumbers = [];
    clearLocalStorage();
    updateSelectionPanel();
    updateMobileSelectButton();
}

function toggleNumber(num) {
    const index = selectedNumbers.indexOf(num);
    const btn = document.querySelector(`.number-btn[data-number="${num}"]`);
    if (index > -1) { selectedNumbers.splice(index, 1); btn.classList.remove('btn-primary'); }
    else { selectedNumbers.push(num); btn.classList.add('btn-primary'); }
    saveToLocalStorage();
    updateSelectionPanel();
    updateMobileSelectButton();
}

function updateSelectionPanel() {
    const panel = document.getElementById('selectionPanel');
    if (selectedNumbers.length === 0) { panel.classList.add('d-none'); return; }
    panel.classList.remove('d-none');
    document.getElementById('selectedNumbersDisplay').innerHTML = selectedNumbers.map(num => `<span class="badge bg-primary rounded-pill">${num}</span>`).join('');
    const price = window.RIFA_CONFIG ? window.RIFA_CONFIG.price : 0;
    document.getElementById('totalPrice').textContent = selectedNumbers.length * price;
}

function updateMobileSelectButton() {
    const mobileBtn = document.getElementById('mobileSelectBtn');
    if (!mobileBtn) return;
    
    if (selectedNumbers.length > 0) {
        mobileBtn.style.background = 'linear-gradient(135deg, #28a745, #20c997)';
        mobileBtn.style.color = 'white';
        mobileBtn.style.boxShadow = '0 4px 15px rgba(40, 167, 69, 0.4)';
        mobileBtn.querySelector('i').classList.add('animate-bounce');
    } else {
        mobileBtn.style.background = 'transparent';
        mobileBtn.style.color = '';
        mobileBtn.style.boxShadow = '';
        mobileBtn.querySelector('i').classList.remove('animate-bounce');
    }
}
