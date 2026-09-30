// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
async function checkExistingResponse(nombre) {
    const res = await fetch(`/api/forms/${FORM_ID}/my_response?nombre=${encodeURIComponent(nombre)}`);
    const data = await res.json();
    if (data.found) {
        editingResponseId = data.response_id;
        if (document.getElementById('pf_email')) document.getElementById('pf_email').value = data.email;
        if (document.getElementById('pf_telefono')) document.getElementById('pf_telefono').value = data.telefono;
        if (document.getElementById('pf_edad') && data.edad) document.getElementById('pf_edad').value = data.edad;
        if (document.getElementById('pf_tipo_sangre')) document.getElementById('pf_tipo_sangre').value = data.tipo_sangre || '';
        if (document.getElementById('pf_alergias')) document.getElementById('pf_alergias').value = data.alergias || '';
        if (document.getElementById('pf_enfermedades')) document.getElementById('pf_enfermedades').value = data.enfermedades_cronicas || '';
        if (document.getElementById('pf_contacto_nombre')) document.getElementById('pf_contacto_nombre').value = data.contacto_emergencia_nombre || '';
        if (document.getElementById('pf_contacto_telefono')) document.getElementById('pf_contacto_telefono').value = data.contacto_emergencia_telefono || '';
        if (document.getElementById('pf_pasaporte')) document.getElementById('pf_pasaporte').value = data.pasaporte || '';
        if (document.getElementById('pf_fecha_nacimiento_dia') && data.fecha_nacimiento_dia) document.getElementById('pf_fecha_nacimiento_dia').value = data.fecha_nacimiento_dia;
        if (document.getElementById('pf_fecha_nacimiento_mes') && data.fecha_nacimiento_mes) document.getElementById('pf_fecha_nacimiento_mes').value = data.fecha_nacimiento_mes;
        if (document.getElementById('pf_fecha_nacimiento_anio') && data.fecha_nacimiento_anio) document.getElementById('pf_fecha_nacimiento_anio').value = data.fecha_nacimiento_anio;
        for (const f of formFields) {
            const val = data.answers[String(f.id)];
            if (val === undefined || val === null) continue;
            if (f.field_type === 'text' || f.field_type === 'textarea') {
                const input = document.querySelector(`[data-field-id="${f.id}"]`);
                if (input) input.value = val;
            } else if (f.field_type === 'radio') {
                const radio = document.querySelector(`input[name="field_${f.id}"][value="${val}"]`);
                if (radio) radio.checked = true;
            } else if (f.field_type === 'checkbox' && Array.isArray(val)) {
                val.forEach(v => {
                    const cb = document.querySelector(`input[name="field_${f.id}"][value="${v}"]`);
                    if (cb) cb.checked = true;
                });
            }
        }
        document.getElementById('editBanner').classList.remove('d-none');
        document.getElementById('btnSubmit').innerHTML = '<i class="bi bi-pencil-square me-1"></i>Actualizar Respuesta';
    }
}

async function submitForm(e) {
    e.preventDefault();
    const telEl = document.getElementById('pf_telefono');
    if (telEl && telEl.value && telEl.value.replace(/\D/g,'').length !== 8) {
        telEl.classList.add('is-invalid');
        telEl.focus();
        return;
    }
    
    // Validar edad mínima de 15 años
    const diaEl = document.getElementById('pf_fecha_nacimiento_dia');
    const mesEl = document.getElementById('pf_fecha_nacimiento_mes');
    const anioEl = document.getElementById('pf_fecha_nacimiento_anio');
    if (diaEl && mesEl && anioEl) {
        const dia = parseInt(diaEl.value);
        const mes = parseInt(mesEl.value);
        const anio = parseInt(anioEl.value);
        if (dia && mes && anio) {
            const fechaNacimiento = new Date(anio, mes - 1, dia);
            const hoy = new Date();
            const edadMinima = 15;
            const fechaMinima = new Date(hoy.getFullYear() - edadMinima, hoy.getMonth(), hoy.getDate());
            
            if (fechaNacimiento > fechaMinima) {
                alert('Debe tener al menos 15 años para completar este formulario');
                anioEl.classList.add('is-invalid');
                anioEl.focus();
                return;
            }
        }
    }
    
    const btn = document.getElementById('btnSubmit');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Enviando...';

    const answers = {};
    for (const f of formFields) {
        if (f.field_type === 'text' || f.field_type === 'textarea') {
            const input = document.querySelector(`[data-field-id="${f.id}"]`);
            answers[f.id] = input ? input.value : '';
        } else if (f.field_type === 'radio') {
            const checked = document.querySelector(`input[name="field_${f.id}"]:checked`);
            answers[f.id] = checked ? checked.value : '';
        } else if (f.field_type === 'checkbox') {
            const checked = document.querySelectorAll(`input[name="field_${f.id}"]:checked`);
            answers[f.id] = Array.from(checked).map(c => c.value);
        } else if (f.field_type === 'file') {
            const fileInput = document.querySelector(`[data-field-id="${f.id}"][data-type="file"]`);
            if (fileInput && fileInput.files.length > 0) {
                const fd = new FormData();
                fd.append('file', fileInput.files[0]);
                fd.append('field_id', f.id);
                const uploadRes = await fetch(`/api/forms/${FORM_ID}/submit_file`, { method: 'POST', body: fd });
                const uploadData = await uploadRes.json();
                answers[f.id] = uploadData.path || '';
            } else {
                answers[f.id] = '';
            }
        }
    }

    const payload = {
        answers: answers,
        nombre_completo: document.getElementById('pf_nombre')?.value || '',
        cedula: document.getElementById('pf_cedula')?.value || '',
        email: document.getElementById('pf_email')?.value || '',
        telefono: document.getElementById('pf_telefono')?.value || '',
        edad: document.getElementById('pf_edad')?.value || '',
        tipo_sangre: document.getElementById('pf_tipo_sangre')?.value || '',
        alergias: document.getElementById('pf_alergias')?.value || '',
        enfermedades_cronicas: document.getElementById('pf_enfermedades')?.value || '',
        contacto_emergencia_nombre: document.getElementById('pf_contacto_nombre')?.value || '',
        contacto_emergencia_telefono: document.getElementById('pf_contacto_telefono')?.value || '',
        pasaporte: document.getElementById('pf_pasaporte')?.value || '',
        fecha_nacimiento_dia: document.getElementById('pf_fecha_nacimiento_dia')?.value || '',
        fecha_nacimiento_mes: document.getElementById('pf_fecha_nacimiento_mes')?.value || '',
        fecha_nacimiento_anio: document.getElementById('pf_fecha_nacimiento_anio')?.value || '',
    };

    let res;
    if (editingResponseId) {
        res = await fetch(`/api/forms/${FORM_ID}/response/${editingResponseId}`, {
            method: 'PUT', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload)
        });
    } else {
        res = await fetch(`/api/forms/${FORM_ID}/submit`, {
            method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload)
        });
    }
    const data = await res.json();

    if (data.ok) {
        document.getElementById('publicForm').classList.add('d-none');
        document.getElementById('resultPanel').classList.remove('d-none');

        if (FORM_TYPE === 'examen' && data.score !== undefined) {
            document.getElementById('scorePanel').classList.remove('d-none');
            document.getElementById('scoreValue').textContent = data.score + '%';
            document.getElementById('scoreDetail').textContent = `${data.correct} de ${data.total} correctas`;
        }

        let msg = editingResponseId
            ? 'Tu respuesta ha sido actualizada correctamente.'
            : 'Tu información ha sido registrada exitosamente.';
        document.getElementById('resultMsg').textContent = msg;

        if (data.answers_summary) {
            document.getElementById('summaryText').textContent = data.answers_summary;
            document.getElementById('summaryPanel').classList.remove('d-none');
        }

        if (data.admin_msg) {
            const JENNY_PHONE = '50686529837';
            const KENNETH_PHONE = '50686227500';
            document.getElementById('btnSendJenny').href = `https://wa.me/${JENNY_PHONE}?text=${data.admin_msg}`;
            document.getElementById('btnSendKenneth').href = `https://wa.me/${KENNETH_PHONE}?text=${data.admin_msg}`;
            document.getElementById('adminSendPanel').classList.remove('d-none');
        }

        if (ALLOW_EDIT && FORM_TYPE !== 'examen') {
            if (!editingResponseId && data.response_id) {
                editingResponseId = data.response_id;
            }
            if (data.edit_token) {
                window._lastEditToken = data.edit_token;
            }
            document.getElementById('editLinkPanel').classList.remove('d-none');
        }

        if (data.whatsapp_url) {
            setTimeout(() => { window.open(data.whatsapp_url, '_blank'); }, 1500);
        }
    } else {
        alert(data.error || 'Error al enviar');
        btn.disabled = false;
        btn.innerHTML = editingResponseId
            ? '<i class="bi bi-pencil-square me-1"></i>Actualizar Respuesta'
            : '<i class="bi bi-send me-1"></i>Enviar Respuesta';
    }
}

function resetForNewEntry() {
    ['pf_nombre','pf_cedula','pf_email','pf_telefono','pf_edad','pf_fecha','pf_tipo_sangre','pf_alergias','pf_enfermedades','pf_contacto_nombre','pf_contacto_telefono','pf_pasaporte','pf_fecha_nacimiento_dia','pf_fecha_nacimiento_mes','pf_fecha_nacimiento_anio'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });
    document.querySelectorAll('#dynamicFields input, #dynamicFields textarea').forEach(el => {
        if (el.type === 'checkbox' || el.type === 'radio') el.checked = false;
        else el.value = '';
    });
    editingResponseId = null;
    document.getElementById('editBanner').classList.add('d-none');
    document.getElementById('btnSubmit').disabled = false;
    document.getElementById('btnSubmit').innerHTML = '<i class="bi bi-send me-1"></i>Enviar Respuesta';
    document.getElementById('resultPanel').classList.add('d-none');
    document.getElementById('publicForm').classList.remove('d-none');
    window.scrollTo({top: 0, behavior: 'smooth'});
}

function editMySelection() {
    const token = window._lastEditToken || EDIT_TOKEN;
    if (token) {
        window.location.href = `${window.location.origin}${FORM_EDIT_BASE}/editar/${token}`;
        return;
    }
    document.getElementById('resultPanel').classList.add('d-none');
    document.getElementById('publicForm').classList.remove('d-none');
    document.getElementById('editBanner').classList.remove('d-none');
    document.getElementById('btnSubmit').disabled = false;
    document.getElementById('btnSubmit').innerHTML = '<i class="bi bi-pencil-square me-1"></i>Actualizar Respuesta';
}

loadFields();
