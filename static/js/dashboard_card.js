// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
function mostrarCardUsuario(data) {
    const card = data.card || {};
    document.getElementById('ucCardName').textContent = card.name || 'Usuario';
    document.getElementById('ucCardCedula').textContent = card.cedula ? `Cédula: ${card.cedula}` : '';
    document.getElementById('ucCardEmail').textContent = card.email || 'No registrado';
    document.getElementById('ucCardPhone').textContent = card.phone || 'No registrado';
    document.getElementById('ucCardBlood').textContent = card.blood || 'No registrado';
    document.getElementById('ucCardPuntos').textContent = (card.puntos !== undefined ? card.puntos : 0) + ' puntos';
    document.getElementById('ucCardPasaporte').textContent = card.pasaporte || 'No registrado';
    document.getElementById('ucCardEmergencyName').textContent = card.emergency_name || 'No registrado';
    document.getElementById('ucCardEmergencyPhone').textContent = card.emergency_phone || 'No registrado';
    const cardLink = document.getElementById('ucCardLink');
    if (cardLink && data.card_url) cardLink.href = data.card_url;

    const alergiasWrapper = document.getElementById('ucCardAlergiasWrapper');
    if (card.alergias && card.alergias !== 'Ninguna') {
        alergiasWrapper.classList.remove('d-none');
        document.getElementById('ucCardAlergias').textContent = card.alergias;
    } else {
        alergiasWrapper.classList.add('d-none');
    }
    const enfWrapper = document.getElementById('ucCardEnfermedadesWrapper');
    if (card.enfermedades && card.enfermedades !== 'Ninguna') {
        enfWrapper.classList.remove('d-none');
        document.getElementById('ucCardEnfermedades').textContent = card.enfermedades;
    } else {
        enfWrapper.classList.add('d-none');
    }

    const qrImg = document.getElementById('ucCardQR');
    qrImg.src = data.qr_base64 ? `data:image/png;base64,${data.qr_base64}` : '';

    const modalEl = document.getElementById('usuarioCardModal');
    if (modalEl) new bootstrap.Modal(modalEl).show();
}

async function mostrarQRUsuario() {
    const contactId = currentSelectedUserObj ? currentSelectedUserObj.id : currentSelectedUserId;
    if (!contactId) {
        mostrarAlerta('Este registro no tiene contacto vinculado.', 'warning');
        return;
    }
    try {
        const r = await fetch(`/api/admin/usuario-card/${contactId}`);
        const d = await r.json();
        if (!r.ok) {
            mostrarAlerta(d.error || 'No se pudo generar el código QR.', 'warning');
            return;
        }
        mostrarCardUsuario(d);
    } catch (e) {
        mostrarAlerta('Error de conexión. Intenta nuevamente.', 'error');
    }
}

const _formFieldMap = {
    'crearUsuarioForm': {
        name: 'cuName', last_name_1: 'cuLastName1', last_name_2: 'cuLastName2',
        email: 'cuEmail', phone_input: 'cuPhone', phone_select: 'cuDynamicSelect', phone_container: 'cuDynamicContainer',
        pasaporte: 'cuPasaporte', tipo_sangre: 'cuSangre',
        dia: 'cuDia', mes: 'cuMes', anio: 'cuAnio',
        alergias: 'cuAlergias', enfermedades: 'cuEnfermedades',
        emergency_container: 'cuEmergencyContainer'
    },
    'adminEditUserForm': {
        name: 'editName', last_name_1: 'editLastName1', last_name_2: 'editLastName2',
        email: 'editEmail', phone_select: 'editDynamicSelect', phone_container: 'editDynamicContainer',
        pasaporte: 'editPasaporte', tipo_sangre: 'editSangre',
        dia: 'editDia', mes: 'editMes', anio: 'editAnio',
        alergias: 'editAlergias', enfermedades: 'editEnfermedades',
        emergency_container: 'editEmergencyContainer'
    }
};

function _setPhoneField(phone, map) {
    const direct = map.phone_input ? document.getElementById(map.phone_input) : null;
    const select = document.getElementById(map.phone_select);
    const container = document.getElementById(map.phone_container);
    if (direct) {
        direct.value = phone ? phone.replace(/[^0-9]/g, '') : '';
        if (select) select.value = '';
        if (container) container.innerHTML = '';
        return;
    }
    if (!select || !container) return;
    if (phone) {
        select.value = 'Telefono';
        container.innerHTML = `<div class="mb-2"><span class="text-orange me-2"><i class="bi bi-phone"></i></span>
            <input type="tel" name="phone" class="input-bulma" placeholder="Digite el número telefónico" inputmode="numeric" pattern="[0-9]*"
            oninput="this.value=this.value.replace(/[^0-9]/g,'')" maxlength="15" value="${phone.replace(/[^0-9]/g,'')}"></div>
            <small class="text-muted d-block ps-2">Solo números permitidos.</small>`;
    } else {
        select.value = '';
        container.innerHTML = '';
    }
}

function _setEmergencyContacts(nombres, telefonos, map) {
    const container = document.getElementById(map.emergency_container);
    if (!container) return;
    container.innerHTML = '';
    const max = Math.max(nombres.length, telefonos.length, 1);
    for (let i = 0; i < max; i++) {
        const nombre = nombres[i] || '';
        const telefono = telefonos[i] || '';
        if (map.emergency_container === 'cuEmergencyContainer') {
            container.insertAdjacentHTML('beforeend', buildCreateEmergencyRow(nombre, telefono));
        } else {
            container.insertAdjacentHTML('beforeend', buildEditEmergencyRow(nombre, telefono));
        }
    }
}

function _marcarCamposFaltantes(formId) {
    const form = document.getElementById(formId);
    if (!form) return;
    const campos = form.querySelectorAll('.input-bulma, .select-bulma, .textarea-bulma');
    campos.forEach(function(el) {
        if (el.id === 'cuCedula' || el.id === 'editCedula') return;
        if (el.id === 'cuDynamicSelect' || el.id === 'editDynamicSelect') return;
        const val = (el.value || '').trim();
        const isSelect = el.tagName === 'SELECT';
        const empty = !val || (isSelect && val === '');
        if (empty) {
            el.classList.add('is-danger');
        } else {
            el.classList.remove('is-danger');
        }
    });
}

const _cedulaCheckTimers = {};

function checkCedulaExistente(cedula, formId) {
    cedula = (cedula || '').replace(/[^0-9]/g, '');
    if (_cedulaCheckTimers[formId]) clearTimeout(_cedulaCheckTimers[formId]);
    if (!cedula || cedula.length < 5) return;
    _cedulaCheckTimers[formId] = setTimeout(function() {
        const map = _formFieldMap[formId];
        if (!map) return;

        fetch(`/api/admin/hiker_by_cedula/${cedula}`)
            .then(r => r.json().then(d => ({ r, d })))
            .then(({ r, d }) => {
                if (!r.ok || !d.found) return;

                document.getElementById(map.name).value = d.name || '';
                document.getElementById(map.last_name_1).value = d.last_name_1 || '';
                document.getElementById(map.last_name_2).value = d.last_name_2 || '';
                if (d.email) document.getElementById(map.email).value = d.email;

                _setPhoneField(d.phone || '', map);

                document.getElementById(map.pasaporte).value = d.pasaporte || '';
                document.getElementById(map.tipo_sangre).value = d.tipo_sangre || '';

                if (d.fecha_nacimiento && /^\d{4}-\d{2}-\d{2}$/.test(d.fecha_nacimiento)) {
                    const [anio, mes, dia] = d.fecha_nacimiento.split('-');
                    document.getElementById(map.dia).value = dia;
                    document.getElementById(map.mes).value = mes;
                    document.getElementById(map.anio).value = anio;
                } else {
                    document.getElementById(map.dia).value = '';
                    document.getElementById(map.mes).value = '';
                    document.getElementById(map.anio).value = '';
                }

                document.getElementById(map.alergias).value = d.alergias || '';
                document.getElementById(map.enfermedades).value = d.enfermedades_cronicas || '';

                const nombres = (d.contacto_emergencia_nombre || '').split(' | ').filter(Boolean);
                const telefonos = (d.contacto_emergencia_telefono || '').split(' | ').filter(Boolean);
                _setEmergencyContacts(nombres, telefonos, map);

                _marcarCamposFaltantes(formId);
            })
            .catch(() => {});
    }, 600);
}

