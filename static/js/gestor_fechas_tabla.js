// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
function renderTabla(lista) {
    const grid = document.getElementById('contenedorCards');
    grid.innerHTML = '';

    if (lista.length === 0) {
        document.getElementById('sinEventos').classList.remove('d-none');
        document.getElementById('contenedorTabla').classList.add('d-none');
        return;
    }
    document.getElementById('sinEventos').classList.add('d-none');
    document.getElementById('contenedorTabla').classList.remove('d-none');

    lista.forEach((ev, idx) => {
        const fechaFormateada = ev.fecha_completa
            ? new Date(ev.fecha_completa + 'T00:00:00').toLocaleDateString('es-ES', {day:'2-digit', month:'short', year:'numeric'})
            : '—';

        const col = document.createElement('div');
        col.className = 'col-12 col-md-6 col-lg-4';
        col.innerHTML = `
            <div class="card h-100 border-0 shadow-sm" id="fila-${ev.id}" style="background:linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(248,249,250,0.9) 100%);backdrop-filter:blur(10px);border-radius:15px;">
                <div class="card-body d-flex flex-column">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <span class="text-muted small">#${idx + 1}</span>
                        <span class="badge-fecha" id="badge-${ev.id}">${fechaFormateada}</span>
                    </div>
                    <h6 class="fw-bold text-dark mb-3 flex-grow-1" style="font-size:.95rem;">
                        <a href="/detalles_evento/${ev.id}" class="text-dark text-decoration-none hover-orange">${ev.nombre}</a>
                    </h6>
                    <div class="mb-2">
                        <label class="form-label small text-muted mb-1">Nueva fecha</label>
                        <input type="date" class="input-fecha w-100" id="input-${ev.id}"
                               value="${ev.fecha_completa || ''}"
                               onchange="marcarCambio(${ev.id})" />
                        <small class="text-muted d-block mt-1 ${(ev.fecha_anterior || '') ? '' : 'd-none'}" style="font-size:.75rem;" id="anterior-${ev.id}">Fecha anterior: ${ev.fecha_anterior ? new Date(ev.fecha_anterior + 'T00:00:00').toLocaleDateString('es-ES', {day:'2-digit', month:'short', year:'numeric'}) : '—'}</small>
                        <div class="mt-2 ${(ev.historial_fechas || []).length ? '' : 'd-none'}" id="historial-${ev.id}" style="font-size:.75rem;"></div>
                    </div>
                    <div class="d-flex align-items-center justify-content-between mt-auto gap-2">
                        <div class="d-flex align-items-center gap-2">
                            <button class="btn btn-outline-orange btn-sm rounded-pill px-3 d-none"
                                    id="btn-${ev.id}"
                                    onclick="guardarFecha(${ev.id}, '${ev.nombre.replace(/'/g,"\\'")}')">
                                <i class="bi bi-check2 me-1"></i>Guardar
                            </button>
                            <button class="btn btn-outline-danger btn-sm rounded-pill px-3"
                                    onclick="pedirBorrarFecha(${ev.id}, '${ev.nombre.replace(/'/g,"\\'")}')">
                                <i class="bi bi-trash me-1"></i>Borrar
                            </button>
                        </div>
                        <span class="text-muted small" id="listo-${ev.id}">—</span>
                    </div>
                </div>
            </div>
        `;
        grid.appendChild(col);
        renderHistorial(ev.id);
    });
}

function marcarCambio(id) {
    document.getElementById(`fila-${id}`).classList.add('fila-editando');
    document.getElementById(`btn-${id}`).classList.remove('d-none');
    document.getElementById(`listo-${id}`).classList.add('d-none');
}

function renderHistorial(id) {
    const ev = eventosDB.find(e => e.id === id);
    const cont = document.getElementById(`historial-${id}`);
    if (!cont || !ev) return;
    const historial = ev.historial_fechas || [];
    if (historial.length > 0) {
        cont.classList.remove('d-none');
        const items = historial.map(h => {
            const f = h.fecha ? new Date(h.fecha + 'T00:00:00').toLocaleDateString('es-ES', {day:'2-digit', month:'short', year:'numeric'}) : '—';
            return `<li class="d-flex justify-content-between align-items-center mb-1"><span class="text-muted" style="font-size:.7rem;">${h.cambiado_at}</span><span class="fw-semibold">${f}</span></li>`;
        }).join('');
        cont.innerHTML = `<small class="fw-bold text-orange d-block mb-1" style="font-size:.8rem;">Fechas asignadas:</small><ul class="list-unstyled mb-0">${items}</ul>`;
    } else {
        cont.classList.add('d-none');
        cont.innerHTML = '';
    }
}

async function guardarFecha(id, nombre) {
    const input = document.getElementById(`input-${id}`);
    const nuevaFecha = input.value;
    if (!nuevaFecha) { alert('Selecciona una fecha válida'); return; }

    const btn = document.getElementById(`btn-${id}`);
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Guardando…';

    try {
        const res = await fetch(`/api/eventos/${id}/mover-fecha`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nueva_fecha: nuevaFecha })
        });

        if (res.ok) {
            const fechaFmt = new Date(nuevaFecha + 'T00:00:00')
                .toLocaleDateString('es-ES', {day:'2-digit', month:'short', year:'numeric'});
            document.getElementById(`badge-${id}`).textContent = fechaFmt;
            document.getElementById(`fila-${id}`).classList.remove('fila-editando');
            btn.classList.add('d-none');
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-check2 me-1"></i>Guardar';
            document.getElementById(`listo-${id}`).textContent = '✓ Guardado';
            document.getElementById(`listo-${id}`).classList.remove('d-none');
            document.getElementById(`listo-${id}`).className = 'text-success small fw-semibold';

            // Actualizar referencia visual de fecha anterior
            const ev = eventosDB.find(e => e.id === id);
            const fechaAnterior = ev ? ev.fecha_completa : '';
            if (ev) {
                ev.fecha_completa = nuevaFecha;
                ev.fecha_anterior = fechaAnterior;
                ev.historial_fechas = ev.historial_fechas || [];
                ev.historial_fechas.unshift({
                    fecha: nuevaFecha,
                    cambiado_at: new Date().toLocaleString('es-ES', {day:'2-digit', month:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit'})
                });
            }
            const antEl = document.getElementById(`anterior-${id}`);
            if (antEl && fechaAnterior) {
                const antFmt = new Date(fechaAnterior + 'T00:00:00').toLocaleDateString('es-ES', {day:'2-digit', month:'short', year:'numeric'});
                antEl.textContent = `Fecha anterior: ${antFmt}`;
                antEl.classList.remove('d-none');
            }
            renderHistorial(id);

            // Refrescar calendario
            renderCalendario();

            // Mostrar toast
            document.getElementById('toastMsg').textContent = `"${nombre}" → ${fechaFmt}`;
            new bootstrap.Toast(document.getElementById('toastOk'), { delay: 3000 }).show();
        } else {
            alert('Error al guardar la fecha. Intenta de nuevo.');
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-check2 me-1"></i>Guardar';
        }
    } catch (err) {
        alert('Error de conexión.');
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-check2 me-1"></i>Guardar';
    }
}

function filtrarEventos() {
    const q = document.getElementById('buscador').value.toLowerCase();
    const filtrados = q ? eventosDB.filter(ev => ev.nombre.toLowerCase().includes(q)) : eventosDB;
    renderTabla(filtrados);
}

renderTabla(eventosDB);
renderCalendario();
aplicarEstadoCalendario();
