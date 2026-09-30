// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
const nombresMes = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'];
let calendarioActual = new Date();
let idBorrar = null;

function fechasConActividad() {
    return new Set(eventosDB.map(ev => ev.fecha_completa).filter(f => f));
}

function renderCalendario() {
    const cont = document.getElementById('calendarioActividades');
    const anio = calendarioActual.getFullYear();
    const mes = calendarioActual.getMonth();
    const primerDia = new Date(anio, mes, 1).getDay();
    const diasMes = new Date(anio, mes + 1, 0).getDate();
    const fechas = fechasConActividad();
    const hoy = new Date();
    const hoyStr = `${hoy.getFullYear()}-${String(hoy.getMonth() + 1).padStart(2, '0')}-${String(hoy.getDate()).padStart(2, '0')}`;
    let html = `
        <div class="d-flex justify-content-between align-items-center mb-3">
            <button class="btn btn-sm btn-outline-orange rounded-pill" onclick="cambiarMes(-1)"><i class="bi bi-chevron-left"></i></button>
            <h5 class="fw-bold text-orange mb-0">${nombresMes[mes]} ${anio}</h5>
            <button class="btn btn-sm btn-outline-orange rounded-pill" onclick="cambiarMes(1)"><i class="bi bi-chevron-right"></i></button>
        </div>
        <div class="calendario-grid">
            <div class="calendario-dia-header">Dom</div>
            <div class="calendario-dia-header">Lun</div>
            <div class="calendario-dia-header">Mar</div>
            <div class="calendario-dia-header">Mié</div>
            <div class="calendario-dia-header">Jue</div>
            <div class="calendario-dia-header">Vie</div>
            <div class="calendario-dia-header">Sáb</div>
    `;
    for (let i = 0; i < primerDia; i++) html += '<div></div>';
    for (let d = 1; d <= diasMes; d++) {
        const mesStr = String(mes + 1).padStart(2, '0');
        const diaStr = String(d).padStart(2, '0');
        const fechaStr = `${anio}-${mesStr}-${diaStr}`;
        let clases = 'calendario-dia';
        if (fechas.has(fechaStr)) clases += ' con-actividad';
        if (fechaStr === hoyStr) clases += ' dia-hoy';
        html += `<a href="/eventos?fecha=${fechaStr}" class="${clases}" style="color:inherit;text-decoration:none;">${d}</a>`;
    }
    html += '</div>';
    cont.innerHTML = html;
}

function cambiarMes(delta) {
    calendarioActual.setMonth(calendarioActual.getMonth() + delta);
    renderCalendario();
}

function toggleCalendario() {
    const cont = document.getElementById('calendarioActividades');
    const icon = document.getElementById('iconToggleCalendario');
    const text = document.getElementById('textToggleCalendario');
    const collapsed = cont.classList.toggle('d-none');
    localStorage.setItem('gestorFechasCalendario', collapsed ? 'collapsed' : 'expanded');
    icon.className = collapsed ? 'bi bi-chevron-down' : 'bi bi-chevron-up';
    text.textContent = collapsed ? 'Mostrar' : 'Ocultar';
}

function aplicarEstadoCalendario() {
    const cont = document.getElementById('calendarioActividades');
    const icon = document.getElementById('iconToggleCalendario');
    const text = document.getElementById('textToggleCalendario');
    const estado = localStorage.getItem('gestorFechasCalendario');
    const collapsed = estado === 'collapsed';
    if (collapsed) cont.classList.add('d-none');
    else cont.classList.remove('d-none');
    icon.className = collapsed ? 'bi bi-chevron-down' : 'bi bi-chevron-up';
    text.textContent = collapsed ? 'Mostrar' : 'Ocultar';
}

function pedirBorrarFecha(id, nombre) {
    idBorrar = id;
    document.getElementById('borrarNombre').textContent = nombre;
    new bootstrap.Modal(document.getElementById('confirmBorrarModal')).show();
}

async function confirmarBorrarFecha() {
    if (!idBorrar) return;
    const btn = document.getElementById('btnConfirmarBorrar');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Borrando…';
    try {
        const res = await fetch(`/api/eventos/${idBorrar}/borrar-fecha`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await res.json();
        if (data.ok) {
            const ev = eventosDB.find(e => e.id === idBorrar);
            const fechaAnterior = ev ? ev.fecha_completa : '';
            if (ev) {
                ev.fecha_completa = '';
                ev.fecha_anterior = fechaAnterior;
                ev.historial_fechas = ev.historial_fechas || [];
                ev.historial_fechas.unshift({
                    fecha: '',
                    cambiado_at: new Date().toLocaleString('es-ES', {day:'2-digit', month:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit'})
                });
            }
            document.getElementById(`badge-${idBorrar}`).textContent = '—';
            const antEl = document.getElementById(`anterior-${idBorrar}`);
            if (antEl && fechaAnterior) {
                const antFmt = new Date(fechaAnterior + 'T00:00:00').toLocaleDateString('es-ES', {day:'2-digit', month:'short', year:'numeric'});
                antEl.textContent = `Fecha anterior: ${antFmt}`;
                antEl.classList.remove('d-none');
            }
            renderHistorial(idBorrar);
            document.getElementById(`input-${idBorrar}`).value = '';
            document.getElementById(`fila-${idBorrar}`).classList.remove('fila-editando');
            document.getElementById(`btn-${idBorrar}`).classList.add('d-none');
            document.getElementById(`listo-${idBorrar}`).textContent = '✓ Fecha borrada';
            document.getElementById(`listo-${idBorrar}`).className = 'text-success small fw-semibold';
            renderCalendario();
            const modal = bootstrap.Modal.getInstance(document.getElementById('confirmBorrarModal'));
            if (modal) modal.hide();
        } else {
            alert(data.error || 'Error al borrar la fecha.');
        }
    } catch (err) {
        alert('Error de conexión.');
    } finally {
        btn.disabled = false;
        btn.innerHTML = 'Sí, borrar';
    }
}

