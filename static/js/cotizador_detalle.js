// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
function actualizarPrecio(id, valor) {
    const l = lugaresData.find(x => x.id === id);
    if(l) l.precio = valor;
}
function toggleProvincia(id) {
    const el = document.getElementById(id);
    if(!el) return;
    const icon = document.getElementById('icon-' + id);
    if(el.classList.contains('show')) {
        el.classList.remove('show');
        if(icon) icon.className = 'bi bi-chevron-right ms-2';
    } else {
        el.classList.add('show');
        if(icon) icon.className = 'bi bi-chevron-down ms-2';
    }
}
function cambiarPagina(provincia, pagina) {
    paginaActual[provincia] = Math.max(1, pagina);
    renderLugares(lugaresVisibles);
}
function verDetalle(id) {
    const l = lugaresData.find(x => x.id === id);
    if(!l) return;
    lugarDetalleId = id;
    document.getElementById('detalleTitulo').textContent = l.nombre;
    document.getElementById('detalleProvincia').textContent = l.provincia || 'Sin provincia';
    const duracionBadge = document.getElementById('detalleDuracion');
    duracionBadge.textContent = l.duracion == '1_dia' ? '1 día' : 'Múltiples';
    duracionBadge.className = 'badge ' + (l.duracion == '1_dia' ? 'bg-info' : 'bg-warning text-dark');
    document.getElementById('detalleFechaIda').textContent = l.fecha_ida || 'Por definir';
    document.getElementById('detalleFechaRegreso').textContent = l.fecha_regreso || 'Por definir';
    document.getElementById('detalleFechaRegreso').parentElement.style.display = l.duracion == 'multiples_dias' ? 'block' : 'none';
    document.getElementById('detalleHora').textContent = l.hora || 'Por definir';
    const tipo = l.tipo_caminata || 'circular';
    const tipoBadge = document.getElementById('detalleTipo');
    tipoBadge.textContent = (tipo == 'lineal' ? 'Lineal' : 'Circular');
    tipoBadge.className = 'badge ms-1 ' + (tipo == 'lineal' ? 'bg-dark text-white' : 'bg-secondary');
    const mapaIda = document.getElementById('detalleMapaIda');
    const mapaRegreso = document.getElementById('detalleMapaRegreso');
    mapaIda.style.display = 'inline-flex';
    if(tipo == 'lineal') {
        mapaIda.innerHTML = '<i class="bi bi-geo-alt-fill me-1"></i>Mapa de inicio';
        mapaRegreso.style.display = 'inline-flex';
        if(l.maps_ida) {
            mapaIda.href = l.maps_ida;
            mapaIda.classList.remove('disabled');
        } else {
            mapaIda.href = '#';
            mapaIda.classList.add('disabled');
        }
        if(l.maps_regreso) {
            mapaRegreso.href = l.maps_regreso;
            mapaRegreso.classList.remove('disabled');
        } else {
            mapaRegreso.href = '#';
            mapaRegreso.classList.add('disabled');
        }
    } else {
        mapaIda.innerHTML = '<i class="bi bi-geo-alt-fill me-1"></i>Mapa';
        mapaRegreso.style.display = 'none';
        mapaIda.style.display = 'inline-flex';
        if(l.maps_ida) {
            mapaIda.href = l.maps_ida;
            mapaIda.classList.remove('disabled');
        } else {
            mapaIda.href = '#';
            mapaIda.classList.add('disabled');
        }
    }
    renderHistorial(l);
    detalleModal.show();
}
function renderHistorial(l) {
    const ul = document.getElementById('detalleHistorial');
    const historial = l.precios_historial || [];
    if(historial.length === 0) {
        ul.innerHTML = '<li class="list-group-item text-muted small">Sin historial de precios</li>';
        return;
    }
    const moneda = l.moneda == 'colones' ? '₡' : '$';
    const html = historial.slice().reverse().map((h, i) => {
        const originalIdx = historial.length - 1 - i;
        let precio = h.precio;
        if(precio === null || precio === undefined) precio = 'Sin precio';
        const precioText = typeof precio === 'number' ? Number(precio).toLocaleString(undefined, {maximumFractionDigits: 0}) : precio;
        const fecha = h.fecha ? new Date(h.fecha).toLocaleString('es-CR') : 'Sin fecha';
        let botonEliminar = '';
        if(esSuper) {
            botonEliminar = `<button onclick="eliminarHistorial(${l.id}, ${originalIdx})" class="btn btn-sm btn-outline-danger border-0 p-0 ms-2" title="Eliminar"><i class="bi bi-trash"></i></button>`;
        }
        return `<li class="list-group-item d-flex justify-content-between align-items-center small"><span class="fw-semibold">${moneda}${precioText}</span><span class="text-muted small">${fecha}${botonEliminar}</span></li>`;
    }).join('');
    ul.innerHTML = html;
}
function eliminarHistorial(lugarId, idx) {
    eliminarPendiente = {lugarId, idx};
    confirmDeleteModal.show();
}
async function confirmarEliminarHistorial() {
    if(!eliminarPendiente) return;
    const {lugarId, idx} = eliminarPendiente;
    eliminarPendiente = null;
    try {
        const res = await fetch('/api/cotizadores/lugar/' + lugarId + '/precio-historial', {
            method: 'DELETE',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({index: idx})
        });
        const d = await res.json();
        if(d.ok) {
            const l = lugaresData.find(x => x.id === lugarId);
            if(l) {
                l.precios_historial = d.precios_historial;
                renderHistorial(l);
            }
        } else {
            alert(d.error || 'Error');
        }
    } catch(e) {
        alert('Error de conexion: ' + e.message);
    }
}
let guardarPrecioTimers = {};
let guardarPrecioSeq = {};

async function enviarPrecio(id, nuevo) {
    const l = lugaresData.find(x => x.id === id);
    if(!l) return;
    const seq = (guardarPrecioSeq[id] || 0) + 1;
    guardarPrecioSeq[id] = seq;
    try {
        const precios = {[id]: nuevo};
        const res = await fetch('/cotizadores/' + slug + '/guardar', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({clave:claveGuardada,precios})});
        const d = await res.json();
        if(!d.ok) { alert(d.error || 'Error al guardar precio'); return; }
        // Ignorar respuestas desfasadas
        if (guardarPrecioSeq[id] !== seq) return;
        const guardado = d.guardados ? d.guardados[id] : null;
        if(guardado) {
            l.precio = guardado.precio;
            l.precios_historial = guardado.precios_historial || l.precios_historial;
        }
        const input = document.getElementById('precio_'+id);
        if(input) input.value = (l.precio == null || l.precio === '') ? '' : Math.trunc(parseFloat(l.precio));
        renderHistorial(l);
    } catch(e) {
        alert('Error de conexion: ' + e.message);
    }
}

function guardarPrecio(id, valor) {
    const l = lugaresData.find(x => x.id === id);
    if(!l) return;
    const nuevo = valor ? parseFloat(valor) : null;
    if(l.precio == nuevo) return;
    clearTimeout(guardarPrecioTimers[id]);
    guardarPrecioTimers[id] = setTimeout(() => enviarPrecio(id, nuevo), 800);
}
async function guardarPrecios() {
    const precios = {};
    lugaresData.forEach(l => {
        if (l.precio !== null && l.precio !== undefined) precios[l.id] = l.precio;
    });
    try {
        const res = await fetch('/cotizadores/' + slug + '/guardar', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({clave:claveGuardada,precios})});
        const d = await res.json();
        if(!d.ok) { alert(d.error || 'Error'); return; }
        if(d.guardados) {
            Object.entries(d.guardados).forEach(([key, guardado]) => {
                const lid = parseInt(key);
                const ll = lugaresData.find(x => x.id === lid);
                if(ll) {
                    ll.precio = guardado.precio;
                    ll.precios_historial = guardado.precios_historial || ll.precios_historial;
                    const input = document.getElementById('precio_'+lid);
                    if(input) input.value = ll.precio == null ? '' : ll.precio;
                }
            });
        }
        alert('Precios guardados correctamente');
    } catch(e) {
        alert('Error de conexion: ' + e.message);
    }
}
