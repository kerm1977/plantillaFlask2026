// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
function showUsersList() {
    currentSelectedUserId = null; currentSelectedUserName = ""; currentSelectedUserObj = null;
    document.getElementById('adminUserDetails').classList.add('d-none');
    document.getElementById('adminUsersList').classList.remove('d-none');
}

function dashOptionCreateUser() {
    window.location.href = '/admin/crear-usuario';
}

function dashOptionEditUser() {
    if (!currentSelectedUserObj) {
        mostrarAlerta('Abra la ficha de un usuario para editarlo.', 'warning');
        return;
    }
    if (currentSelectedUserObj.type === 'hiker') {
        const cedula = currentSelectedUserObj.crm_cedula;
        if (cedula) window.location.href = `/editar_caminante/${cedula}`;
        else mostrarAlerta('Este registro CRM no tiene cédula editable.', 'warning');
        return;
    }
    openEditUserModal();
}

function dashOptionDeleteUser() {
    confirmDeleteUser();
}

function openEditUserModal() {
    if (!currentSelectedUserObj) {
        mostrarAlerta('Abra la ficha de un usuario para editarlo.', 'warning');
        return;
    }
    if (currentSelectedUserObj.type === 'hiker') {
        const cedula = currentSelectedUserObj.crm_cedula;
        if (cedula) window.location.href = `/editar_caminante/${cedula}`;
        else mostrarAlerta('Este registro CRM no tiene cédula editable.', 'warning');
        return;
    }
    // Editar usuario: página dedicada de hoja única (sin modal)
    window.location.href = `/admin/editar-usuario/${currentSelectedUserObj.id}`;
}

function handleEditDynamicSelect() {
    const select    = document.getElementById('editDynamicSelect').value;
    const container = document.getElementById('editDynamicContainer');
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

function buildEditEmergencyRow(nombre, telefono) {
    return `<div class="edit-emergency-row row g-3 mb-3 align-items-end">
        <div class="col-md-5">
            <label class="label-bulma" style="font-size:0.85rem;">Contacto de Emergencia</label>
            <input type="text" name="contacto_emergencia_nombre[]" class="input-bulma" placeholder="Ej: María (Esposa)" value="${nombre ? nombre.replace(/"/g, '&quot;') : ''}">
        </div>
        <div class="col-md-5">
            <label class="label-bulma" style="font-size:0.85rem;">Teléfono del Contacto</label>
            <input type="tel" name="contacto_emergencia_telefono[]" class="input-bulma" inputmode="numeric" pattern="[0-9]*" oninput="this.value=this.value.replace(/[^0-9]/g,'')" placeholder="88889999" value="${telefono ? telefono.replace(/[^0-9]/g,'') : ''}">
        </div>
        <div class="col-md-2 text-end">
            <button type="button" class="btn btn-outline-danger btn-sm rounded-pill" onclick="this.closest('.edit-emergency-row').remove()" title="Quitar contacto"><i class="bi bi-x-lg"></i></button>
        </div>
    </div>`;
}

function addEditEmergencyContact() {
    const container = document.getElementById('editEmergencyContainer');
    container.insertAdjacentHTML('beforeend', buildEditEmergencyRow('', ''));
}

async function toggleUserStatus() {
    const contactId = currentSelectedUserObj ? currentSelectedUserObj.id : currentSelectedUserId;
    if (!contactId) return;
    try {
        const response = await fetch(`/api/admin/toggle_status/${contactId}`, { method: 'POST' });
        const result   = await response.json();
        if (response.ok && result.success) {
            mostrarAlerta(`El estado del usuario ahora es: ${result.new_status}`, 'warning');
            showUsersList(); loadAllUsers();
        } else { mostrarAlerta(result.error || "No se pudo cambiar el estado del usuario.", 'error'); }
    } catch(err) { mostrarAlerta("Error de red al intentar comunicarse con el servidor.", 'error'); }
}

let _tripleConfirmStep = 0;
let _tripleConfirmCallback = null;

