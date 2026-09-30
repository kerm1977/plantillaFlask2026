// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
let currentResponsesFormId = null;

async function viewResponses(formId) {
    currentResponsesFormId = formId;
    // Cargar números de reserva de ESTE formulario
    try {
        const res = await fetch(`/api/forms/${formId}/reservation-numbers`);
        const data = await res.json();
        reservationNumbers = data.reservation_numbers || '';
    } catch (e) {
        console.error('Error cargando números de reserva:', e);
        reservationNumbers = '';
    }
    const data = await (await fetch(`/api/forms/${formId}/responses`)).json();
    window._responsesData = data;
    document.getElementById('responsesTitle').textContent = `Respuestas (${data.responses.length})`;
    if (!data.responses.length) {
        document.getElementById('responsesTable').innerHTML = '<p class="text-muted text-center py-4">Sin respuestas aun.</p>';
    } else {
        const showCedula = data.show_cedula;
        const reservationOpts = (r) => reservationNumbers.split('\n').filter(n => n.trim()).map(n =>
            `<option value="${n.trim()}" ${r.reservation_number === n.trim() ? 'selected' : ''}>${n.trim()}</option>`
        ).join('');
        const fieldRow = (label, val, wide) => {
            if (val === undefined || val === null || val === '') return '';
            return `<div class="${wide ? 'col-12' : 'col-12 col-md-6'} resp-field">
                <div class="resp-label">${label}</div>
                <div class="resp-value">${val}</div>
            </div>`;
        };
        const cards = data.responses.map((r, i) => {
            const fechaNac = (r.fecha_nacimiento_dia && r.fecha_nacimiento_mes && r.fecha_nacimiento_anio)
                ? `${r.fecha_nacimiento_dia}/${r.fecha_nacimiento_mes}/${r.fecha_nacimiento_anio}` : '';
            let fieldsHtml = '';
            if (showCedula) fieldsHtml += fieldRow('Cédula', r.cedula);
            fieldsHtml += fieldRow('Email', r.email);
            fieldsHtml += fieldRow('Teléfono', fmtTel506(r.telefono, data.show_pasaporte));
            fieldsHtml += fieldRow('Edad', r.edad);
            if (r.score !== null && r.score !== undefined)
                fieldsHtml += fieldRow('Nota', `<span class="badge rounded-pill ${r.score>=70?'bg-success':'bg-danger'}">${r.score}%</span>`);
            if (data.show_pasaporte) fieldsHtml += fieldRow('Pasaporte', r.pasaporte);
            if (data.show_fecha_nacimiento) fieldsHtml += fieldRow('Fecha de Nacimiento', fechaNac);
            if (data.show_ficha_medica) {
                fieldsHtml += fieldRow('Tipo de Sangre', r.tipo_sangre);
                fieldsHtml += fieldRow('Alergias', r.alergias, true);
                fieldsHtml += fieldRow('Enfermedades Crónicas', r.enfermedades_cronicas, true);
                const emerg = (r.contacto_emergencia_nombre || '') + (r.contacto_emergencia_telefono ? ' • ' + fmtTel506(r.contacto_emergencia_telefono, data.show_pasaporte) : '');
                fieldsHtml += fieldRow('Contacto de Emergencia', emerg.trim() || '', true);
            }
            data.fields.forEach(f => {
                let val = r.answers[String(f.id)];
                if (Array.isArray(val)) val = val.join(', ');
                fieldsHtml += fieldRow(f.label, val, true);
            });
            if (!fieldsHtml) fieldsHtml = '<div class="col-12 text-muted small fst-italic">Sin datos proporcionados.</div>';
            return `<div class="col-12 col-lg-6">
                <div class="accordion">
                    <div class="accordion-item border-0 rounded-4 overflow-hidden mb-2">
                        <h2 class="accordion-header">
                            <button class="accordion-button collapsed fw-bold text-dark" type="button"
                                    data-bs-toggle="collapse" data-bs-target="#respBody${r.id}" aria-expanded="false">
                                <i class="bi bi-person-vcard me-2 text-orange"></i>#${i+1} — ${r.nombre_completo || 'Sin nombre'}
                                ${r.reservation_number ? `<span class="badge bg-warning text-dark rounded-pill ms-2"><i class="bi bi-ticket-perforated me-1"></i>${r.reservation_number}</span>` : ''}
                            </button>
                        </h2>
                        <div id="respBody${r.id}" class="accordion-collapse collapse" data-bs-parent="#responsesTable">
                            <div class="accordion-body">
                            <div class="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-2 pt-2 border-top">
                                <div class="text-secondary small">${r.submitted_at || ''}</div>
                                <div class="d-flex gap-1">
                                    <button class="btn btn-sm rounded-pill py-0 px-2" style="background:rgba(13,110,253,0.1);color:#0d6efd;border:1px solid rgba(13,110,253,0.2);" onclick="viewResponseDetail(${i})" title="Ver"><i class="bi bi-eye" style="font-size:0.75rem;"></i></button>
                                    <button class="btn btn-sm rounded-pill py-0 px-2" style="background:rgba(255,140,0,0.1);color:#ff8c00;border:1px solid rgba(255,140,0,0.2);" onclick="editResponseAdmin(${i})" title="Editar"><i class="bi bi-pencil" style="font-size:0.75rem;"></i></button>
                                    <button class="btn btn-sm rounded-pill py-0 px-2" style="background:rgba(220,53,69,0.08);color:#dc3545;border:1px solid rgba(220,53,69,0.15);" onclick="deleteResponse(${r.id})" title="Borrar"><i class="bi bi-trash3" style="font-size:0.75rem;"></i></button>
                                </div>
                            </div>
                            <div class="mb-2">
                                <select class="form-select form-select-sm" onchange="assignReservationNumber(${r.id}, this.value)" style="font-size:0.8rem;max-width:220px;">
                                    <option value="">Sin número de reserva</option>
                                    ${reservationOpts(r)}
                                </select>
                            </div>
                            <div class="row g-2">${fieldsHtml}</div>
                        </div>
                    </div>
                </div>
                </div>
            </div>`;
        }).join('');
        document.getElementById('responsesTable').innerHTML = `<div class="row g-3">${cards}</div>`;
    }
    const viewer = document.getElementById('responsesViewer');
    const wasHidden = viewer.classList.contains('d-none');
    document.getElementById('formsList').classList.add('d-none');
    viewer.classList.remove('d-none');
    if (wasHidden) history.pushState({fv: 'responses'}, '');
}

window.addEventListener('popstate', () => { backToList(); });

// Antepone +506 a teléfonos cuando el formulario solicita pasaporte
function fmtTel506(tel, showPasaporte) {
    if (!tel || !showPasaporte) return tel || '';
    const d = String(tel).replace(/\D/g, '');
    if (!d) return tel;
    return `+506 ${d.startsWith('506') ? d.slice(3) : d}`;
}

function viewResponseDetail(index) {
    const data = window._responsesData, r = data.responses[index];
    let html = '';
    
    // Header info card
    html += `<div class="text-center mb-4">
        <div class="fw-bold fs-4 text-dark mb-1">${r.nombre_completo || 'Sin nombre'}</div>
        ${r.reservation_number ? `<div class="badge bg-warning text-dark rounded-pill px-3 py-1 mb-2"><i class="bi bi-ticket-perforated me-1"></i>Reserva: ${r.reservation_number}</div>` : ''}
        <div class="text-secondary small">${r.submitted_at}</div>
    </div>`;
    
    // Contact info section
    html += `<div class="row g-3 mb-4">`;
    if (r.cedula) html += `<div class="col-12"><label class="form-label fw-semibold text-secondary">Cédula</label><div class="form-control glass-input rounded-3 py-2">${r.cedula}</div></div>`;
    if (r.email) html += `<div class="col-12"><label class="form-label fw-semibold text-secondary">Email</label><div class="form-control glass-input rounded-3 py-2">${r.email}</div></div>`;
    if (r.telefono) html += `<div class="col-12"><label class="form-label fw-semibold text-secondary">Teléfono</label><div class="form-control glass-input rounded-3 py-2">${fmtTel506(r.telefono, data.show_pasaporte)}</div></div>`;
    if (r.edad) html += `<div class="col-6"><label class="form-label fw-semibold text-secondary">Edad</label><div class="form-control glass-input rounded-3 py-2">${r.edad}</div></div>`;
    if (r.score !== null && r.score !== undefined) html += `<div class="col-6"><label class="form-label fw-semibold text-secondary">Nota</label><div class="form-control glass-input rounded-3 py-2 ${r.score>=70?'text-success':'text-danger'}">${r.score}%</div></div>`;
    html += `</div>`;
    
    // Passport info
    if (data.show_pasaporte) {
        html += `<div class="mb-4">
            <h6 class="fw-bold text-dark mb-2"><i class="bi bi-passport me-2"></i>Pasaporte</h6>
            <label class="form-label fw-semibold text-secondary">Número</label>
            <div class="form-control glass-input rounded-3 py-2">${r.pasaporte || '-'}</div>
        </div>`;
    }
    
    // Birth date
    if (data.show_fecha_nacimiento) {
        const fechaNac = r.fecha_nacimiento_dia && r.fecha_nacimiento_mes && r.fecha_nacimiento_anio 
            ? `${r.fecha_nacimiento_dia}/${r.fecha_nacimiento_mes}/${r.fecha_nacimiento_anio}` 
            : '-';
        html += `<div class="mb-4">
            <h6 class="fw-bold text-dark mb-2"><i class="bi bi-calendar3 me-2"></i>Fecha de Nacimiento</h6>
            <div class="form-control glass-input rounded-3 py-2">${fechaNac}</div>
        </div>`;
    }
    
    // Medical info
    if (data.show_ficha_medica) {
        html += `<div class="mb-4">
            <h6 class="fw-bold text-dark mb-2"><i class="bi bi-heart-pulse me-2"></i>Ficha Médica</h6>
            <div class="row g-3">
                <div class="col-12"><label class="form-label fw-semibold text-secondary">Tipo de Sangre</label><div class="form-control glass-input rounded-3 py-2">${r.tipo_sangre || '-'}</div></div>
                <div class="col-12"><label class="form-label fw-semibold text-secondary">Alergias</label><div class="form-control glass-input rounded-3 py-2">${r.alergias || '-'}</div></div>
                <div class="col-12"><label class="form-label fw-semibold text-secondary">Enfermedades Crónicas</label><div class="form-control glass-input rounded-3 py-2">${r.enfermedades_cronicas || '-'}</div></div>
                <div class="col-12"><label class="form-label fw-semibold text-secondary">Contacto de Emergencia</label><div class="form-control glass-input rounded-3 py-2">${r.contacto_emergencia_nombre || '-'} ${r.contacto_emergencia_telefono ? '• '+fmtTel506(r.contacto_emergencia_telefono, data.show_pasaporte) : ''}</div></div>
            </div>
        </div>`;
    }
    
    // Form fields section
    html += `<div class="mb-2">
        <h6 class="fw-bold text-dark mb-2"><i class="bi bi-ui-checks me-2"></i>Respuestas del Formulario</h6>
        <div class="row g-3">`;
    data.fields.forEach(f => {
        let val = r.answers[String(f.id)];
        if (Array.isArray(val)) val = val.join(', ');
        val = (val !== undefined && val !== null && val !== '') ? val : '-';
        html += `<div class="col-12">
            <label class="form-label fw-semibold text-secondary">${f.label}</label>
            <div class="form-control glass-input rounded-3 py-2 fw-medium">${val}</div>
        </div>`;
    });
    html += `</div></div>`;
    
    document.getElementById('responseDetailBody').innerHTML = html;
    document.getElementById('responseDetailName').textContent = r.nombre_completo || 'Detalle';
    const rdModal = document.getElementById('responseDetailModal');
    if (rdModal.parentElement !== document.body) document.body.appendChild(rdModal);
    new bootstrap.Modal(rdModal).show();
}

