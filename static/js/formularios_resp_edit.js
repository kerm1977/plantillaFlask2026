// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
function editResponseAdmin(index) {
    const data = window._responsesData, r = data.responses[index];
    window._editingResponse = {id: r.id, formId: currentResponsesFormId};
    let html = `<div class="row g-2 mb-3">
        <div class="col-12"><label class="fw-semibold small text-muted">Nombre completo</label>
            <input type="text" class="form-control form-control-sm" id="erNombre" value="${r.nombre_completo || ''}"></div>
        ${data.show_cedula ? `<div class="col-6"><label class="fw-semibold small text-muted">Cédula</label>
            <input type="text" class="form-control form-control-sm" id="erCedula" value="${r.cedula || ''}"></div>` : ''}
        <div class="col-6"><label class="fw-semibold small text-muted">Email</label>
            <input type="email" class="form-control form-control-sm" id="erEmail" value="${r.email || ''}"></div>
        <div class="col-6"><label class="fw-semibold small text-muted">Telefono</label>
            <input type="tel" class="form-control form-control-sm" id="erTelefono" value="${r.telefono || ''}"></div>
        ${data.show_ficha_medica ? `
        <div class="col-12"><hr class="my-1"><small class="fw-bold text-danger"><i class="bi bi-heart-pulse me-1"></i>Ficha Médica</small></div>
        <div class="col-6"><label class="fw-semibold small text-muted">Tipo de Sangre</label>
            <select class="form-select form-select-sm" id="erTipoSangre">
                <option value="">No lo sé</option>
                <option value="No recibo transfusiones" ${r.tipo_sangre==='No recibo transfusiones'?'selected':''}>No recibo transfusiones</option>
                <option value="A+" ${r.tipo_sangre==='A+'?'selected':''}>A+</option>
                <option value="A-" ${r.tipo_sangre==='A-'?'selected':''}>A-</option>
                <option value="B+" ${r.tipo_sangre==='B+'?'selected':''}>B+</option>
                <option value="B-" ${r.tipo_sangre==='B-'?'selected':''}>B-</option>
                <option value="AB+" ${r.tipo_sangre==='AB+'?'selected':''}>AB+</option>
                <option value="AB-" ${r.tipo_sangre==='AB-'?'selected':''}>AB-</option>
                <option value="O+" ${r.tipo_sangre==='O+'?'selected':''}>O+</option>
                <option value="O-" ${r.tipo_sangre==='O-'?'selected':''}>O-</option>
            </select></div>
        <div class="col-6"><label class="fw-semibold small text-muted">Alergias</label>
            <input type="text" class="form-control form-control-sm" id="erAlergias" value="${r.alergias || ''}"></div>
        <div class="col-12"><label class="fw-semibold small text-muted">Enfermedades Crónicas</label>
            <input type="text" class="form-control form-control-sm" id="erEnfermedades" value="${r.enfermedades_cronicas || ''}"></div>
        <div class="col-6"><label class="fw-semibold small text-muted">Nombre Contacto Emergencia</label>
            <input type="text" class="form-control form-control-sm" id="erContactoNombre" value="${r.contacto_emergencia_nombre || ''}"></div>
        <div class="col-6"><label class="fw-semibold small text-muted">Teléfono Contacto Emergencia</label>
            <input type="tel" class="form-control form-control-sm" id="erContactoTelefono" value="${r.contacto_emergencia_telefono || ''}"></div>` : ''}
        ${data.show_pasaporte ? `
        <div class="col-12"><hr class="my-1"><small class="fw-bold text-primary"><i class="bi bi-passport me-1"></i>Pasaporte</small></div>
        <div class="col-12"><label class="fw-semibold small text-muted">Número de Pasaporte</label>
            <input type="text" class="form-control form-control-sm" id="erPasaporte" value="${r.pasaporte || ''}"></div>` : ''}
        ${data.show_fecha_nacimiento ? `
        <div class="col-12"><hr class="my-1"><small class="fw-bold text-success"><i class="bi bi-calendar3 me-1"></i>Fecha de Nacimiento</small></div>
        <div class="col-4"><label class="fw-semibold small text-muted">Día</label>
            <input type="number" class="form-control form-control-sm" id="erFechaNacimientoDia" value="${r.fecha_nacimiento_dia || ''}" min="1" max="31"></div>
        <div class="col-4"><label class="fw-semibold small text-muted">Mes</label>
            <input type="number" class="form-control form-control-sm" id="erFechaNacimientoMes" value="${r.fecha_nacimiento_mes || ''}" min="1" max="12"></div>
        <div class="col-4"><label class="fw-semibold small text-muted">Año</label>
            <input type="number" class="form-control form-control-sm" id="erFechaNacimientoAnio" value="${r.fecha_nacimiento_anio || ''}" min="1900" max="2025"></div>` : ''}
    </div><hr class="my-2">`;
    data.fields.forEach(f => {
        const rawVal = r.answers[String(f.id)];
        let fieldHtml = '';
        if (f.field_type === 'radio' && f.options && f.options.length) {
            const currentVal = Array.isArray(rawVal) ? rawVal[0] : (rawVal || '');
            fieldHtml = f.options.map(o => `<div class="form-check"><input class="form-check-input" type="radio" name="field_er_${f.id}" data-field-id="${f.id}" value="${o}" ${currentVal===o?'checked':''}><label class="form-check-label small">${o}</label></div>`).join('');
        } else if (f.field_type === 'checkbox' && f.options && f.options.length) {
            const currentVals = Array.isArray(rawVal) ? rawVal : (rawVal ? [rawVal] : []);
            fieldHtml = f.options.map(o => `<div class="form-check"><input class="form-check-input" type="checkbox" name="field_er_${f.id}" data-field-id="${f.id}" value="${o}" ${currentVals.includes(o)?'checked':''}><label class="form-check-label small">${o}</label></div>`).join('');
        } else {
            const textVal = Array.isArray(rawVal) ? rawVal.join(', ') : (rawVal || '');
            fieldHtml = `<input type="text" class="form-control form-control-sm" data-field-id="${f.id}" value="${String(textVal).replace(/"/g,'&quot;')}">`;
        }
        html += `<div class="mb-3 p-2 rounded-3" style="background:rgba(0,0,0,0.02);border:1px solid rgba(0,0,0,0.06);">
            <label class="fw-semibold small text-muted d-block mb-1">${f.label}</label>${fieldHtml}</div>`;
    });
    document.getElementById('editResponseBody').innerHTML = html;
    const erModal = document.getElementById('editResponseModal');
    if (erModal.parentElement !== document.body) document.body.appendChild(erModal);
    new bootstrap.Modal(erModal).show();
}

async function saveEditedResponse() {
    const ctx = window._editingResponse; if (!ctx) return;
    const answers = {}, fieldIds = new Set();
    document.querySelectorAll('#editResponseBody [data-field-id]').forEach(el => fieldIds.add(el.dataset.fieldId));
    fieldIds.forEach(fid => {
        const inputs = document.querySelectorAll(`#editResponseBody [data-field-id="${fid}"]`);
        if (!inputs.length) return;
        const t = inputs[0].type;
        if (t === 'radio') { const ch = document.querySelector(`#editResponseBody [data-field-id="${fid}"]:checked`); answers[fid] = ch ? ch.value : ''; }
        else if (t === 'checkbox') { answers[fid] = Array.from(document.querySelectorAll(`#editResponseBody [data-field-id="${fid}"]:checked`)).map(c=>c.value); }
        else { answers[fid] = inputs[0].value; }
    });
    const res = await fetch(`/api/forms/admin/responses/${ctx.id}`, {
        method:'PUT', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({
            nombre_completo: document.getElementById('erNombre').value,
            cedula: document.getElementById('erCedula')?.value || '',
            email: document.getElementById('erEmail').value,
            telefono: document.getElementById('erTelefono').value,
            tipo_sangre: document.getElementById('erTipoSangre')?.value || '',
            alergias: document.getElementById('erAlergias')?.value || '',
            enfermedades_cronicas: document.getElementById('erEnfermedades')?.value || '',
            contacto_emergencia_nombre: document.getElementById('erContactoNombre')?.value || '',
            contacto_emergencia_telefono: document.getElementById('erContactoTelefono')?.value || '',
            pasaporte: document.getElementById('erPasaporte')?.value || '',
            fecha_nacimiento_dia: document.getElementById('erFechaNacimientoDia')?.value || '',
            fecha_nacimiento_mes: document.getElementById('erFechaNacimientoMes')?.value || '',
            fecha_nacimiento_anio: document.getElementById('erFechaNacimientoAnio')?.value || '',
            answers
        })
    });
    const d = await res.json();
    if (d.ok) { bootstrap.Modal.getInstance(document.getElementById('editResponseModal')).hide(); viewResponses(ctx.formId); }
    else { alert(d.error || 'Error al guardar'); }
}

async function deleteResponse(responseId) {
    abrirModalBorrarUnificado({
        titulo: 'Borrar Respuesta',
        mensaje: '¿Eliminar esta respuesta?',
        onConfirmar: async () => {
            const data = await (await fetch(`/api/forms/responses/${responseId}`, {method:'DELETE'})).json();
            if (data.ok) { viewResponses(currentResponsesFormId); }
            else { alert(data.error || 'Error al eliminar'); }
        }
    });
}

function copyResponsesTSV() {
    const data = window._responsesData;
    if (!data || !data.responses.length) { alert('Sin respuestas para copiar'); return; }
    // Construir encabezados
    const headers = ['Nombre'];
    if (data.show_cedula) headers.push('Cédula');
    headers.push('Email', 'Teléfono', 'Edad', 'Fecha');
    if (data.responses.some(r => r.score !== null && r.score !== undefined)) headers.push('Nota (%)');
    if (data.show_ficha_medica) headers.push('Tipo de Sangre', 'Alergias', 'Enfermedades Crónicas', 'Contacto Emergencia Nombre', 'Contacto Emergencia Teléfono');
    data.fields.forEach(f => headers.push(f.label));
    // Construir filas
    const rows = data.responses.map(r => {
        const row = [r.nombre_completo || ''];
        if (data.show_cedula) row.push(r.cedula || '');
        row.push(r.email || '', r.telefono || '', r.edad || '', r.submitted_at || '');
        if (data.responses.some(x => x.score !== null && x.score !== undefined)) {
            row.push(r.score !== null && r.score !== undefined ? r.score + '%' : '');
        }
        if (data.show_ficha_medica) {
            row.push(r.tipo_sangre || '', r.alergias || '', r.enfermedades_cronicas || '', r.contacto_emergencia_nombre || '', r.contacto_emergencia_telefono || '');
        }
        data.fields.forEach(f => {
            let val = r.answers[String(f.id)];
            if (Array.isArray(val)) val = val.join(', ');
            row.push(val !== undefined && val !== null ? String(val) : '');
        });
        return row;
    });
    // Unir con tabuladores (TSV — pega perfecto en Excel)
    const tsv = [headers, ...rows].map(row => row.map(c => String(c).replace(/\t/g, ' ')).join('\t')).join('\n');
    const btn = document.getElementById('btnCopyTSV');
    navigator.clipboard.writeText(tsv).then(() => {
        const orig = btn.innerHTML;
        btn.innerHTML = '<i class="bi bi-check2 me-1"></i>¡Copiado!';
        btn.classList.replace('btn-outline-secondary', 'btn-warning-orange');
        setTimeout(() => { btn.innerHTML = orig; btn.classList.replace('btn-warning-orange', 'btn-outline-secondary'); }, 2500);
    }).catch(() => alert('No se pudo copiar al portapapeles'));
}

// Variables globales para números de reserva
