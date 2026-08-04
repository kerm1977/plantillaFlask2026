// routes/agenda.py
// Buscador de agenda médica con PIN maestro

let agendaSearchModal = null;
let _originalConfirmClearNumbers = null;
let masterPin = '';
let agendaSearchTimeout = null;

document.addEventListener('DOMContentLoaded', function() {
    const modalEl = document.getElementById('agendaSearchModal');
    if (modalEl) {
        agendaSearchModal = new bootstrap.Modal(modalEl);
    }

    // Sobrescribe confirmClearNumbers solo si existe (rifa detail) SIN tocar el archivo original
    if (typeof window.confirmClearNumbers === 'function' && !_originalConfirmClearNumbers) {
        _originalConfirmClearNumbers = window.confirmClearNumbers;
        window.confirmClearNumbers = enhancedConfirmClearNumbers;
    }

    const searchInput = document.getElementById('agendaSearchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            clearTimeout(agendaSearchTimeout);
            const q = this.value.trim();
            const resultsDiv = document.getElementById('agendaSearchResults');
            if (!q || q.length < 2) { resultsDiv.innerHTML = ''; return; }
            agendaSearchTimeout = setTimeout(() => performAgendaSearch(q), 350);
        });
    }
});

function enhancedConfirmClearNumbers() {
    const pinInput = document.getElementById('clearPin');
    const pin = pinInput ? pinInput.value.trim() : '';
    if (pin) {
        verifyMasterAndOpen(pin);
    } else if (_originalConfirmClearNumbers) {
        _originalConfirmClearNumbers();
    }
}

async function verifyMasterAndOpen(pin) {
    try {
        const r = await fetch('/api/agenda/search', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({master_pin: pin, q: ''})
        });
        if (r.ok) {
            masterPin = pin;
            if (typeof clearModal !== 'undefined' && clearModal) clearModal.hide();
            const pinInput = document.getElementById('clearPin');
            if (pinInput) pinInput.value = '';
            if (agendaSearchModal) agendaSearchModal.show();
        } else if (_originalConfirmClearNumbers) {
            _originalConfirmClearNumbers();
        }
    } catch (e) {
        if (_originalConfirmClearNumbers) _originalConfirmClearNumbers();
    }
}

async function performAgendaSearch(q) {
    if (!masterPin) return;
    const resultsDiv = document.getElementById('agendaSearchResults');
    resultsDiv.innerHTML = '<div class="text-secondary small text-center py-3">Buscando...</div>';
    try {
        const r = await fetch('/api/agenda/search', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({master_pin: masterPin, q: q})
        });
        const data = await r.json();
        if (data.ok && data.hikers) renderAgendaResults(data.hikers);
        else resultsDiv.innerHTML = '<div class="text-secondary small text-center py-3">No se encontraron resultados</div>';
    } catch (e) {
        resultsDiv.innerHTML = '<div class="text-danger small text-center py-3">Error de conexión</div>';
    }
}

function renderAgendaResults(hikers) {
    const resultsDiv = document.getElementById('agendaSearchResults');
    if (!hikers.length) {
        resultsDiv.innerHTML = '<div class="text-secondary small text-center py-3">No se encontraron resultados</div>';
        return;
    }
    resultsDiv.innerHTML = hikers.map(h => `
        <div class="list-group-item border-0 rounded-3 mb-2 p-3" style="background:rgba(255,255,255,0.65);">
            <div class="fw-bold text-dark">${escapeHtml(h.nombre_completo || 'Sin nombre')}</div>
            <div class="small text-secondary">Cédula: ${escapeHtml(h.cedula || '-')} | Tel: ${escapeHtml(h.telefono || '-')} | Sangre: ${escapeHtml(h.tipo_sangre || '-')}</div>
            ${h.pasaporte ? `<div class="small text-secondary">Pasaporte: ${escapeHtml(h.pasaporte)}</div>` : ''}
            ${h.fecha_nacimiento ? `<div class="small text-secondary">Nacimiento: ${escapeHtml(h.fecha_nacimiento)}</div>` : ''}
            ${h.alergias ? `<div class="small text-danger mt-1"><strong>Alergias:</strong> ${escapeHtml(h.alergias)}</div>` : ''}
            ${h.enfermedades_cronicas ? `<div class="small text-warning mt-1"><strong>Crónicas:</strong> ${escapeHtml(h.enfermedades_cronicas)}</div>` : ''}
            ${h.contacto_emergencia_nombre ? `<div class="small text-muted mt-1">Emergencia: ${escapeHtml(h.contacto_emergencia_nombre)} ${escapeHtml(h.contacto_emergencia_telefono || '')}</div>` : ''}
            ${h.pin_secreto ? `<div class="small text-info mt-1">PIN: ${escapeHtml(h.pin_secreto)}</div>` : ''}
        </div>
    `).join('');
}

function escapeHtml(text) {
    if (text === null || text === undefined) return '';
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
