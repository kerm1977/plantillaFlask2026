// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
function validarEventoForm() {
    const faltan = [];
    const fechaOK = (d, m, y) => {
        const dd = parseInt(d, 10), mm = parseInt(m, 10), yy = parseInt(y, 10);
        if (!dd || !mm || !yy) return false;
        const dt = new Date(yy, mm - 1, dd);
        return dt.getFullYear() === yy && dt.getMonth() === mm - 1 && dt.getDate() === dd;
    };
    const chk = (id, label, ok) => {
        const el = document.getElementById(id);
        if (el && !el.closest('.d-none') && !ok(el)) { el.classList.add('is-invalid'); faltan.push({ el, label }); }
    };
    const diaSeguro = document.getElementById('diaSeguroToggle').checked;
    const visitado = document.getElementById('visitado').value;
    const dias = parseInt(document.getElementById('dias').value) || 1;
    const g = id => document.getElementById(id).value;
    // Hoy en Costa Rica (UTC-6, sin horario de verano)
    const _h = mfHoyCR();
    const hoyStr = `${_h.y}-${String(_h.m).padStart(2, '0')}-${String(_h.d).padStart(2, '0')}`;
    const aIso = (d, m, y) => `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
    const marcaInvalida = (id, label) => {
        const el = document.getElementById(id);
        el.classList.add('is-invalid');
        faltan.push({ el, label });
    };

    chk('nombreLugar', 'Nombre del lugar', el => el.value.trim() !== '');
    chk('capacidad', 'Capacidad', el => el.value !== '');

    if (visitado === 'Programados') {
        if (document.getElementById('actividad').value === 'Internacional') {
            chk('fechaIda', 'Fecha del vuelo de ida', el => !!el.value);
            if (!faltan.length && g('fechaIda') < hoyStr)
                marcaInvalida('fechaIda', 'La fecha no puede ser pasada');
        } else if (dias === 1) {
            chk('monthUnica', 'Mes de la actividad', el => el.value !== '');
            chk('yearUnica', 'Año de la actividad', el => el.value !== '');
            if (!diaSeguro) chk('dayUnica', 'Día de la actividad', el => el.value !== '');
            if (!faltan.length) {
                const iso = aIso(diaSeguro ? 1 : g('dayUnica'), g('monthUnica'), g('yearUnica'));
                if (!diaSeguro && !fechaOK(g('dayUnica'), g('monthUnica'), g('yearUnica')))
                    marcaInvalida('dayUnica', 'Fecha válida (día/mes correctos)');
                else if (iso < hoyStr)
                    marcaInvalida('dayUnica', 'La fecha no puede ser pasada');
            }
        } else {
            chk('dayInicio', 'Día de inicio', el => el.value !== '');
            chk('monthInicio', 'Mes de inicio', el => el.value !== '');
            chk('yearInicio', 'Año de inicio', el => el.value !== '');
            chk('dayRegreso', 'Día de regreso', el => el.value !== '');
            chk('monthRegreso', 'Mes de regreso', el => el.value !== '');
            chk('yearRegreso', 'Año de regreso', el => el.value !== '');
            if (!faltan.length) {
                const dI = diaSeguro ? 1 : g('dayInicio'), dR = diaSeguro ? 1 : g('dayRegreso');
                const okI = diaSeguro || fechaOK(dI, g('monthInicio'), g('yearInicio'));
                const okR = diaSeguro || fechaOK(dR, g('monthRegreso'), g('yearRegreso'));
                const isoI = aIso(dI, g('monthInicio'), g('yearInicio'));
                const isoR = aIso(dR, g('monthRegreso'), g('yearRegreso'));
                if (!okI) marcaInvalida('dayInicio', 'Fecha de inicio válida');
                else if (isoI < hoyStr) marcaInvalida('dayInicio', 'La fecha de inicio no puede ser pasada');
                if (!okR) marcaInvalida('dayRegreso', 'Fecha de regreso válida');
                else if (isoR < isoI) marcaInvalida('dayRegreso', 'El regreso no puede ser antes del inicio');
            }
        }
    }

    if (!faltan.length) return true;
    mostrarAlerta('Falta completar: ' + faltan.map(f => f.label).join(' · '), 'warning');
    const primero = faltan[0].el;
    const acc = primero.closest('.accordion-collapse');
    if (acc) bootstrap.Collapse.getOrCreateInstance(acc).show();
    setTimeout(() => {
        primero.scrollIntoView({ behavior: 'smooth', block: 'center' });
        primero.focus({ preventScroll: true });
    }, 350);
    return false;
}

function abrirCrear() {
    eventoEditando = null;
    document.getElementById('caminata2027Title').innerHTML = '<i class="bi bi-calendar-plus text-orange me-2"></i>Crear Nuevo Evento';
    document.getElementById('submitEventBtn').innerHTML = '<i class="bi bi-save me-2"></i>Publicar Evento';
    document.getElementById('createEventForm').reset();
    document.getElementById('precio').value = '0';
    document.getElementById('reserva').value = '0';
    document.getElementById('kilometros').value = '';
    document.getElementById('anio').value = '2027';
    // Fecha por defecto: mes/año actuales de Costa Rica; el año no admite pasados
    const _hc = mfHoyCR();
    ['yearUnica', 'yearInicio', 'yearRegreso'].forEach(id => {
        const e = document.getElementById(id); if (e) { e.value = _hc.y; e.min = _hc.y; }
    });
    ['monthUnica', 'monthInicio', 'monthRegreso'].forEach(id => {
        const e = document.getElementById(id); if (e) e.value = String(_hc.m).padStart(2, '0');
    });
    ['dayUnica', 'dayInicio', 'dayRegreso'].forEach(id => {
        const e = document.getElementById(id); if (e) e.value = '';
    });
    const _fida = document.getElementById('fechaIda');
    if (_fida) _fida.min = `${_hc.y}-${String(_hc.m).padStart(2, '0')}-${String(_hc.d).padStart(2, '0')}`;
    document.getElementById('anioCol').style.display = 'none';
    document.getElementById('tipoTerreno').value = 'Lastre';
    document.getElementById('eventImagePreview').src = '/static/default.png';
    document.querySelectorAll('#incluyeWrapper input[type="checkbox"]').forEach(cb => cb.checked = false);
    document.getElementById('otrosDescContainer').classList.add('d-none');
    document.getElementById('otrosDescripcion').value = '';
    document.getElementById('diaSeguroToggle').checked = false;
    document.getElementById('logisticaSeguraToggle').checked = false;
    document.getElementById('altoRiesgoToggle').checked = false;
    Wysiwyg.setContent('itinerarioEditor', '');
    toggleDiaSeguro();
    toggleLogisticaSegura();
    toggleActividad();
    toggleDateInputs();
    toggleEstadoCampos('Pendiente');
    toggleCotizacionFields('Pendiente');
    colapsarAcordeonEvento();
    if (window.loadFlyerStateForId) loadFlyerStateForId('new');
    if (window.actualizarPreviewFlyer) actualizarPreviewFlyer();
    if (modalEvento) modalEvento.show();
}

// BLINDADO: cambio rápido de fecha — modal día/mes/año, solo superusuario.
let _mfEvId = null;
const MF_MESES = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio',
                  'Agosto','Septiembre','Octubre','Noviembre','Diciembre'];


function toggleAnio(val) {
    const col = document.getElementById('anioCol');
    if (col) col.style.display = (val === 'Año') ? 'block' : 'none';
}

function colapsarAcordeonEvento() {
    document.querySelectorAll('#infoCaminataAccordion .accordion-collapse').forEach(el => {
        const inst = bootstrap.Collapse.getInstance(el) || new bootstrap.Collapse(el, { toggle: false });
        inst.hide();
    });
    document.querySelectorAll('#infoCaminataAccordion .accordion-button').forEach(btn => btn.classList.add('collapsed'));
}

// Muestra/oculta las secciones del acordeón que solo aplican a eventos Programados
// (Fecha de Actividad, Logística de Salida, Lo que Incluye, Seguridad).
function toggleEstadoCampos(val) {
    const mostrar = (val === 'Programados');
    document.querySelectorAll('.solo-programados').forEach(el => {
        el.classList.toggle('d-none', !mostrar);
        if (!mostrar) {
            const collapse = el.querySelector('.accordion-collapse');
            if (collapse) {
                const inst = bootstrap.Collapse.getInstance(collapse) || new bootstrap.Collapse(collapse, { toggle: false });
                inst.hide();
            }
            const btn = el.querySelector('.accordion-button');
            if (btn) btn.classList.add('collapsed');
        }
    });
}

function toggleCotizacionFields(val) {
    const esCotizacion = (val === 'Cotización');
    document.querySelectorAll('.no-cotizacion').forEach(el => el.classList.toggle('d-none', esCotizacion));
    const precioLabel = document.getElementById('precioLabel');
    if (precioLabel) precioLabel.textContent = esCotizacion ? 'Precio de buseta' : 'Precio';
    const submitBtn = document.getElementById('submitEventBtn');
    if (submitBtn && esCotizacion) submitBtn.innerHTML = '<i class="bi bi-save me-2"></i>Guardar cotización';
    const capacidad = document.getElementById('capacidad');
    if (capacidad) capacidad.required = !esCotizacion;
    const reserva = document.getElementById('reserva');
    if (reserva) reserva.required = !esCotizacion;
}

function toggleActividad() {
    const act = document.getElementById('actividad').value;
    document.getElementById('nationalFields').classList.toggle('d-none', act === 'Internacional');
    document.getElementById('internationalFields').classList.toggle('d-none', act !== 'Internacional');
}

function toggleDateInputs() {
    const dias = parseInt(document.getElementById('dias').value) || 1;
    document.getElementById('singleDateGroup').classList.toggle('d-none', dias > 1);
    document.getElementById('rangeDateGroup').classList.toggle('d-none', dias <= 1);
}

function updateTimePreview() {
    const time = document.getElementById('horaSalida').value;
    const preview = document.getElementById('timePreview');
    if (!time || !preview) return;
    let [h, m] = time.split(':');
    let ampm = h >= 12 ? 'PM' : 'AM';
    h = h % 12 || 12;
    preview.innerText = `${h}:${m} ${ampm}`;
}

function toggleOtherDesc() {
    document.getElementById('otrosDescContainer').classList.toggle('d-none', !document.getElementById('modalCheckOtros').checked);
}

function toggleDiaSeguro() {
    const isSecure = document.getElementById('diaSeguroToggle').checked;
    document.querySelectorAll('.normal-day').forEach(el => el.classList.toggle('d-none', isSecure));
    document.querySelectorAll('.secure-day').forEach(el => el.classList.toggle('d-none', !isSecure));
}

function toggleLogisticaSegura() {
    const isSecure = document.getElementById('logisticaSeguraToggle').checked;
    document.querySelectorAll('.normal-logistics').forEach(el => el.classList.toggle('d-none', isSecure));
    document.querySelectorAll('.secure-logistics').forEach(el => el.classList.toggle('d-none', !isSecure));
}

