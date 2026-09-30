// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
function handleCreateDynamicSelect() {
    const select = document.getElementById('cuDynamicSelect').value;
    const container = document.getElementById('cuDynamicContainer');
    container.innerHTML = '';
    if (select === 'Telefono' || select === 'Whatsapp') {
        container.innerHTML = `<div class="mb-2"><span class="text-orange me-2"><i class="bi bi-phone"></i></span>
            <input type="tel" name="phone" class="input-bulma" placeholder="Digite el número telefónico" inputmode="numeric" pattern="[0-9]*"
            oninput="this.value=this.value.replace(/[^0-9]/g,'')" maxlength="15"></div>
            <small class="text-muted d-block ps-2">Solo números permitidos.</small>`;
    } else if (select === 'Facebook' || select === 'Instagram' || select === 'Direccion') {
        const fieldName = select === 'Direccion' ? 'address' : select.toLowerCase();
        container.innerHTML = `<div class="mt-2"><span class="text-orange me-2"><i class="bi bi-link-45deg"></i></span>
            <input type="url" name="${fieldName}" class="input-bulma" placeholder="https://ejemplo.com/perfil"></div>`;
    } else if (select === 'Fecha') {
        container.innerHTML = `<label class="label-bulma" style="font-size:0.85rem;">Fecha Especial</label>
            <input type="date" name="dob" class="input-bulma">`;
    } else if (select === 'Institucion') {
        container.innerHTML = `<input type="text" name="institution" class="input-bulma mb-2" placeholder="Nombre de la Institución/Empresa">`;
    } else if (select === 'Otro') {
        container.innerHTML = `<input type="text" name="other_info" class="input-bulma mt-2" placeholder="Descripción General" style="text-transform:capitalize;">`;
    }
}

function buildCreateEmergencyRow(nombre, telefono) {
    return `<div class="cu-emergency-row row g-3 mb-3 align-items-end">
        <div class="col-md-5">
            <label class="label-bulma" style="font-size:0.85rem;">Contacto de Emergencia</label>
            <input type="text" name="contacto_emergencia_nombre[]" class="input-bulma" placeholder="Ej: María (Esposa)" value="${nombre ? nombre.replace(/"/g, '&quot;') : ''}">
        </div>
        <div class="col-md-5">
            <label class="label-bulma" style="font-size:0.85rem;">Teléfono del Contacto</label>
            <input type="tel" name="contacto_emergencia_telefono[]" class="input-bulma" inputmode="numeric" pattern="[0-9]*" oninput="this.value=this.value.replace(/[^0-9]/g,'')" placeholder="88889999" value="${telefono ? telefono.replace(/[^0-9]/g,'') : ''}">
        </div>
        <div class="col-md-2 text-end">
            <button type="button" class="btn btn-outline-danger btn-sm rounded-pill" onclick="this.closest('.cu-emergency-row').remove()" title="Quitar contacto"><i class="bi bi-x-lg"></i></button>
        </div>
    </div>`;
}

function addCreateEmergencyContact() {
    const container = document.getElementById('cuEmergencyContainer');
    container.insertAdjacentHTML('beforeend', buildCreateEmergencyRow('', ''));
}

function toggleCedulaLock(formId, cedulaId) {
    if (CURRENT_USER_ROLE === 'Superusuario') return;
    const form = document.getElementById(formId);
    if (!form) return;
    const cedula = document.getElementById(cedulaId);
    if (!cedula) return;
    const hasValue = cedula.value.trim().length > 0;
    const fields = form.querySelectorAll('input:not([type="hidden"]):not([type="file"]):not([type="range"]), select, textarea');
    fields.forEach(function(el) {
        if (el.id === cedulaId) return;
        el.disabled = !hasValue;
        if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
            if (hasValue) {
                if (el.dataset.placeholderOriginal !== undefined) {
                    el.placeholder = el.dataset.placeholderOriginal;
                    delete el.dataset.placeholderOriginal;
                }
            } else {
                if (el.placeholder !== 'Primero ingrese el número de cédula') {
                    el.dataset.placeholderOriginal = el.placeholder;
                }
                el.placeholder = 'Primero ingrese el número de cédula';
            }
        }
    });
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) submitBtn.disabled = !hasValue;
}

