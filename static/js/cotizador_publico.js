// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
let claveGuardada = '';
let passwordModal;
let whatsappModal;
let detalleModal;
let confirmDeleteModal;
let eliminarPendiente = null;
let lugaresVisibles = [];
let paginaActual = {};

document.addEventListener('DOMContentLoaded', function() {
    passwordModal = new bootstrap.Modal(document.getElementById('passwordModal'));
    whatsappModal = new bootstrap.Modal(document.getElementById('whatsappModal'));
    detalleModal = new bootstrap.Modal(document.getElementById('detalleModal'));
    confirmDeleteModal = new bootstrap.Modal(document.getElementById('confirmDeleteModal'));

    document.getElementById('buscadorCotizador').addEventListener('input', filtrarLugares);

    _prepararCodigos();

    const claveSession = sessionStorage.getItem('transaviClave');
    if(claveSession) {
        verificarClave(claveSession);
    } else {
        passwordModal.show();
    }
});

async function verificarClave(claveExterna) {
    const clave = (claveExterna || document.getElementById('clave').value).trim();
    if(!clave) {
        showClaveError('Ingrese la clave de acceso.');
        return;
    }
    const res = await fetch('/cotizadores/' + slug + '/verificar', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({clave})});
    const d = await res.json().catch(() => ({error:'Error del servidor'}));
    if(d.ok) {
        sessionStorage.setItem('transaviClave', clave);
        claveGuardada = clave;
        passwordModal.hide();
        document.getElementById('cotizadorSection').classList.remove('d-none');
        lugaresVisibles = lugaresData;
        renderLugares(lugaresVisibles);
    } else {
        showClaveError(d.error || 'Clave incorrecta. Por favor, verifique e intente de nuevo.');
        if(claveExterna) {
            document.getElementById('clave').value = claveExterna;
            passwordModal.show();
        }
    }
}

function showClaveError(mensaje) {
    if(typeof mostrarAlerta === 'function') mostrarAlerta(mensaje, 'error', 1100);
    else alert(mensaje);
}

function toggleClaveVisibilidad() {
    const input = document.getElementById('clave');
    const icon = document.getElementById('toggleClave');
    if(input.type === 'password') {
        input.type = 'text';
        icon.classList.replace('bi-eye-slash', 'bi-eye');
    } else {
        input.type = 'password';
        icon.classList.replace('bi-eye', 'bi-eye-slash');
    }
}
function _limpiarTexto(texto) {
    return (texto || '').toString().toLowerCase()
        .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
        .replace(/[,..\s]/g, '');
}
function filtrarLugares() {
    const termino = _limpiarTexto(document.getElementById('buscadorCotizador').value);
    if(!termino) {
        lugaresVisibles = lugaresData;
    } else {
        lugaresVisibles = lugaresData.filter(l => {
            const precioLimpio = _limpiarTexto(l.precio).replace(/\D/g, '');
            const datos = [
                l.nombre, l.provincia, l.duracion, l.fecha_ida, l.fecha_regreso,
                l.hora, l.moneda, l.precio, precioLimpio, l.codigo || ''
            ].join(' ');
            return _limpiarTexto(datos).includes(termino);
        });
    }
    paginaActual = {};
    renderLugares(lugaresVisibles);
}
function renderLugares(data) {
    // Agrupar lugares por provincia
    const grupos = {};
    data.forEach(l => {
        const provincia = l.provincia || 'Sin provincia';
        if(!grupos[provincia]) grupos[provincia] = [];
        grupos[provincia].push(l);
    });

    if(Object.keys(grupos).length === 0) {
        document.getElementById('lugaresContainer').innerHTML = `
            <div class="col-12 text-center text-muted py-5">
                <i class="bi bi-search fs-1 d-block mb-2"></i>
                No se encontraron lugares con esos criterios.
            </div>
        `;
        return;
    }

    let html = '';
    let idx = 0;
    const porPagina = 12;
    for(const [provincia, lugares] of Object.entries(grupos)) {
        const provId = 'prov-' + idx;
        const pagina = paginaActual[provincia] || 1;
        const totalPaginas = Math.ceil(lugares.length / porPagina);
        const inicio = (pagina - 1) * porPagina;
        const visibles = lugares.slice(inicio, inicio + porPagina);

        html += `
            <div class="col-12 mb-4">
                <h4 class="fw-bold text-orange mb-0 text-center" style="cursor:pointer" onclick="toggleProvincia('${provId}')">
                    ${provincia} <i class="bi bi-chevron-down ms-2" id="icon-${provId}"></i>
                </h4>
                <div class="text-center mt-2">
                    <button onclick="exportarProvinciaWhatsApp('${provincia.replace(/'/g, "\\'")}')" class="btn btn-sm btn-outline-success rounded-pill fw-bold">
                        <i class="bi bi-whatsapp me-1"></i>Cotizar por provincia
                    </button>
                </div>
                <hr class="mt-2 mb-3">
            </div>
            <div class="col-12 collapse show provincia-grupo" id="${provId}">
                <div class="row g-4">
        `;
        html += visibles.map(l => `
            <div class="col-12 col-md-6 col-lg-4 mb-3">
                <div class="card h-100 border-0 shadow-sm" style="background:linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(248,249,250,0.9) 100%);backdrop-filter:blur(10px);border-radius:15px;">
                    <div class="card-body p-4 d-flex flex-column justify-content-between">
                        <div>
                            <h6 class="fw-bold text-truncate mb-2" title="${l.nombre}">${l.nombre}</h6>
                        </div>
                        <div class="d-flex gap-2 mt-auto">
                            <button onclick="verDetalle(${l.id})" class="btn btn-outline-orange rounded-pill flex-fill fw-bold">
                                <i class="bi bi-eye me-1"></i>Ver más
                            </button>
                            <button onclick="exportarLugarWhatsApp(${l.id})" class="btn btn-outline-success rounded-pill flex-fill fw-bold">
                                <i class="bi bi-whatsapp me-1"></i>WhatsApp
                            </button>
                        </div>
                        <hr class="my-3">
                        <div class="input-group input-group-sm">
                            <span class="input-group-text ${l.moneda=='colones'?'bg-success text-white':'bg-primary text-white'}">${l.moneda=='colones'?'₡':'$'}</span>
                            <input type="number" class="form-control fw-bold" id="precio_${l.id}" value="${(l.precio == null || l.precio === '' || l.precio === undefined) ? '' : Math.trunc(parseFloat(l.precio))}" oninput="guardarPrecio(${l.id}, this.value)" placeholder="Precio">
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
        html += `</div>`;
        if(totalPaginas > 1) {
            html += `
                <nav class="mt-3">
                    <ul class="pagination justify-content-center">
                        <li class="page-item ${pagina===1?'disabled':''}">
                            <button class="page-link" onclick="cambiarPagina('${provincia.replace(/'/g, "\\'")}', ${pagina-1})" ${pagina===1?'disabled':''}>Anterior</button>
                        </li>
                        <li class="page-item disabled">
                            <span class="page-link">Página ${pagina} de ${totalPaginas}</span>
                        </li>
                        <li class="page-item ${pagina===totalPaginas?'disabled':''}">
                            <button class="page-link" onclick="cambiarPagina('${provincia.replace(/'/g, "\\'")}', ${pagina+1})" ${pagina===totalPaginas?'disabled':''}>Siguiente</button>
                        </li>
                    </ul>
                </nav>
            `;
        }
        html += `</div>`;
        idx++;
    }
    document.getElementById('lugaresContainer').innerHTML = html;
}
