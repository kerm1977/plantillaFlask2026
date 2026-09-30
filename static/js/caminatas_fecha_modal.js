// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
function mfHoyCR() {
    // Fecha actual en Costa Rica (UTC-6) como objeto {y, m, d}
    const s = new Date().toLocaleString('en-US', { timeZone: 'America/Costa_Rica' });
    const h = new Date(s);
    return { y: h.getFullYear(), m: h.getMonth() + 1, d: h.getDate() };
}

function _mfPoblar(idSel, desde, hasta, elegido, etiquetas) {
    const sel = document.getElementById(idSel);
    sel.innerHTML = '';
    for (let v = desde; v <= hasta; v++) {
        const o = document.createElement('option');
        o.value = v;
        o.textContent = etiquetas ? etiquetas[v - desde] : v;
        if (v === elegido) o.selected = true;
        sel.appendChild(o);
    }
}

function abrirSelectorFecha(id, fechaActual, dias, nombre, estado) {
    _mfEvId = id;
    document.getElementById('mfNombre').textContent = nombre || '';
    const estRadio = document.querySelector(`input[name="mfEstado"][value="${estado || ''}"]`);
    if (estRadio) estRadio.checked = true;
    const hoy = mfHoyCR();
    let y = hoy.y, m = hoy.m, d = hoy.d;
    if (fechaActual && /^\d{4}-\d{2}-\d{2}$/.test(fechaActual)) {
        const p = fechaActual.split('-');
        y = +p[0]; m = +p[1]; d = +p[2];
        if (y < hoy.y) y = hoy.y;                    // nunca año pasado
    }
    _mfPoblar('mfMes', 1, 12, m, MF_MESES);
    _mfPoblar('mfAnio', hoy.y, hoy.y + 4, y);
    _mfPoblar('mfDia', 1, 31, d);
    _mfPoblar('mfDias', 1, 15, Math.min(dias || 1, 15),
              Array.from({length: 15}, (_, i) => (i + 1) === 1 ? '1 día' : (i + 1) + ' días'));
    mfValidar();
    bootstrap.Modal.getOrCreateInstance(document.getElementById('modalFechaRapida')).show();
}

function _mfFechaSel() {
    const d = +document.getElementById('mfDia').value;
    const m = +document.getElementById('mfMes').value;
    const y = +document.getElementById('mfAnio').value;
    const maxD = new Date(y, m, 0).getDate();
    if (d > maxD) { document.getElementById('mfDia').value = maxD; }
    return `${y}-${String(m).padStart(2, '0')}-${String(Math.min(d, maxD)).padStart(2, '0')}`;
}

async function mfValidar() {
    const aviso = document.getElementById('mfAviso');
    const btn = document.getElementById('mfBtnMover');
    const fecha = _mfFechaSel();
    const hoy = mfHoyCR();
    const hoyStr = `${hoy.y}-${String(hoy.m).padStart(2, '0')}-${String(hoy.d).padStart(2, '0')}`;
    aviso.className = 'small text-center mt-2 mb-0 fw-semibold';
    if (fecha < hoyStr) {                          // jamás fecha pasada
        aviso.textContent = 'No se puede mover a una fecha anterior a hoy.';
        aviso.classList.add('pasada');
        btn.disabled = true;
        return;
    }
    try {
        const res = await fetch(`/api/eventos/ocupados/${fecha}`, { cache: 'no-store' });
        const data = await res.json();
        const otros = (data.eventos || []).filter(e => e.id !== _mfEvId);
        if (otros.length) {
            aviso.textContent = 'Ese día ya está: ' + otros.map(e => e.nombre).join(', ');
            aviso.classList.add('ocupado');
        } else {
            aviso.textContent = 'Fecha libre ✓';
            aviso.classList.add('libre');
        }
    } catch (e) { aviso.textContent = ''; }
    btn.disabled = false;
}

async function confirmarFechaRapida() {
    const fecha = _mfFechaSel();
    const dias = +document.getElementById('mfDias').value;
    try {
        const res = await fetch(`/api/eventos/${_mfEvId}/fecha`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ fecha, dias, estado: (document.querySelector('input[name="mfEstado"]:checked') || {}).value || '' })
        });
        const data = await res.json();
        if (!res.ok || !data.ok) { alert(data.error || 'No se pudo cambiar la fecha.'); return; }
        location.reload();   // el evento queda reordenado en el mes nuevo
    } catch (e) {
        alert('Error de conexión al cambiar la fecha.');
    }
}

