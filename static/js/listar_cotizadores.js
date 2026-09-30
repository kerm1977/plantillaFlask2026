// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
let paginaActual = {};
let eliminarLugarPendiente = null;
let confirmDeleteLugarModal1, confirmDeleteLugarModal2, confirmDeleteLugarModal3;
const STORAGE_KEY = 'cotizador_borrador';
function agregarLugar() {
    lugares.push({nombre:'',provincia:'',duracion:'1_dia',tipo_caminata:'circular',fecha_ida:'',fecha_regreso:'',hora:'',maps_ida:'',maps_regreso:'',moneda:'colones',order:lugares.length});
    renderLugares();
}
function eliminarLugar(idx) {
    eliminarLugarPendiente = idx;
    confirmDeleteLugarModal1.show();
}
function mostrarConfirmarLugar(paso) {
    if(eliminarLugarPendiente === null) return;
    if(paso === 2) {
        confirmDeleteLugarModal1._element.addEventListener('hidden.bs.modal', () => confirmDeleteLugarModal2.show(), {once:true});
        confirmDeleteLugarModal1.hide();
    } else if(paso === 3) {
        confirmDeleteLugarModal2._element.addEventListener('hidden.bs.modal', () => confirmDeleteLugarModal3.show(), {once:true});
        confirmDeleteLugarModal2.hide();
    }
}
function confirmarEliminarLugar() {
    if(eliminarLugarPendiente === null) return;
    confirmDeleteLugarModal3.hide();
    lugares.splice(eliminarLugarPendiente, 1);
    eliminarLugarPendiente = null;
    renderLugares();
}
function renderLugares() {
    const grupos = {};
    lugares.forEach((l, i) => {
        const p = (l.provincia || 'Sin provincia').trim();
        if(!grupos[p]) grupos[p] = [];
        grupos[p].push({l, i});
    });
    if(Object.keys(grupos).length === 0) {
        document.getElementById('lugaresContainer').innerHTML = '<div class="col-12 text-center text-muted py-3">No hay lugares.</div>';
        const count = document.getElementById('lugaresCount');
        if(count) count.textContent = '(0)';
        return;
    }
    const porPagina = 12;
    let html = '';
    let idx = 0;
    for(const [provincia, items] of Object.entries(grupos)) {
        const provId = 'prov-' + idx;
        let pagina = paginaActual[provincia] || 1;
        const totalPaginas = Math.ceil(items.length / porPagina);
        if(pagina > totalPaginas) pagina = totalPaginas || 1;
        paginaActual[provincia] = pagina;
        const inicio = (pagina - 1) * porPagina;
        const visibles = items.slice(inicio, inicio + porPagina);
        const cartas = visibles.map(({l, i}) => `
        <div class="col-12 col-md-6 col-lg-4 col-xl-3">
            <div class="card h-100 p-3 border-0 shadow-sm" style="background:linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(248,249,250,0.9) 100%);backdrop-filter:blur(10px);border-radius:15px;">
                <div class="row g-2">
                    <div class="col-12"><input class="form-control" placeholder="Nombre del lugar *" value="${l.nombre}" onchange="lugares[${i}].nombre=this.value"></div>
                    <div class="col-12">
                        <select class="form-select" onchange="lugares[${i}].provincia=this.value">
                            <option value="">Seleccionar provincia</option>
                            <option value="San José" ${l.provincia=='San José'?'selected':''}>San José</option>
                            <option value="Alajuela" ${l.provincia=='Alajuela'?'selected':''}>Alajuela</option>
                            <option value="Cartago" ${l.provincia=='Cartago'?'selected':''}>Cartago</option>
                            <option value="Heredia" ${l.provincia=='Heredia'?'selected':''}>Heredia</option>
                            <option value="Guanacaste" ${l.provincia=='Guanacaste'?'selected':''}>Guanacaste</option>
                            <option value="Puntarenas" ${l.provincia=='Puntarenas'?'selected':''}>Puntarenas</option>
                            <option value="Limón" ${l.provincia=='Limón'?'selected':''}>Limón</option>
                        </select>
                    </div>
                    <div class="col-6">
                        <select class="form-select" onchange="lugares[${i}].duracion=this.value;renderLugares()">
                            <option value="1_dia" ${l.duracion=='1_dia'?'selected':''}>1 día</option>
                            <option value="multiples_dias" ${l.duracion=='multiples_dias'?'selected':''}>Múltiples días</option>
                        </select>
                    </div>
                    <div class="col-6">
                        <select class="form-select" onchange="lugares[${i}].tipo_caminata=this.value;renderLugares()">
                            <option value="circular" ${l.tipo_caminata=='circular'?'selected':''}>Circular</option>
                            <option value="lineal" ${l.tipo_caminata=='lineal'?'selected':''}>Lineal</option>
                        </select>
                    </div>
                    <div class="col-6"><input type="date" class="form-control" value="${l.fecha_ida}" onchange="lugares[${i}].fecha_ida=this.value"></div>
                    <div class="col-6" style="display:${l.duracion=='multiples_dias'?'block':'none'}"><input type="date" class="form-control" value="${l.fecha_regreso}" onchange="lugares[${i}].fecha_regreso=this.value"></div>
                    <div class="col-6"><input type="time" class="form-control" value="${l.hora}" onchange="lugares[${i}].hora=this.value"></div>
                    <div class="col-6"><input type="url" class="form-control" placeholder="${l.tipo_caminata=='lineal'?'Mapa ida':'Mapa'}" value="${l.maps_ida}" onchange="lugares[${i}].maps_ida=this.value"></div>
                    <div class="col-6" style="display:${l.tipo_caminata=='lineal'?'block':'none'}"><input type="url" class="form-control" placeholder="Mapa regreso" value="${l.maps_regreso}" onchange="lugares[${i}].maps_regreso=this.value"></div>
                    <div class="col-6">
                        <select class="form-select" onchange="lugares[${i}].moneda=this.value">
                            <option value="colones" ${l.moneda=='colones'?'selected':''}>Colones</option>
                            <option value="dolares" ${l.moneda=='dolares'?'selected':''}>Dólares</option>
                        </select>
                    </div>
                    <div class="col-12"><button onclick="eliminarLugar(${i})" class="btn btn-sm btn-outline-danger w-100"><i class="bi bi-trash me-1"></i>Eliminar Lugar</button></div>
                </div>
            </div>
        </div>
        `).join('');
        html += `
            <div class="col-12 mb-2">
                <h5 class="fw-bold mb-0" style="cursor:pointer;" onclick="toggleProvincia('${provId}')">
                    ${provincia} <i class="bi bi-chevron-right ms-2 provincia-icon" id="icon-${provId}"></i>
                </h5>
                <hr class="mt-2 mb-3">
            </div>
            <div class="col-12 collapse provincia-grupo" id="${provId}">
                <div class="row g-2">${cartas}</div>
            </div>
        `;
        if(totalPaginas > 1) {
            html += `
            <div class="col-12 mb-4">
                <nav>
                    <ul class="pagination pagination-sm justify-content-center">
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
            </div>
            `;
        }
        idx++;
    }
    document.getElementById('lugaresContainer').innerHTML = html;
    const count = document.getElementById('lugaresCount');
    if(count) count.textContent = '(' + lugares.length + ')';
}
function cambiarPagina(provincia, pagina) {
    paginaActual[provincia] = Math.max(1, pagina);
    renderLugares();
}
function toggleProvincia(id) {
    const el = document.getElementById(id);
    if(!el) return;
    const abrir = !el.classList.contains('show');
    document.querySelectorAll('.provincia-grupo').forEach(x => x.classList.remove('show'));
    document.querySelectorAll('.provincia-icon').forEach(x => x.className = 'bi bi-chevron-right ms-2 provincia-icon');
    if(abrir) {
        el.classList.add('show');
        const icon = document.getElementById('icon-' + id);
        if(icon) icon.className = 'bi bi-chevron-down ms-2 provincia-icon';
    }
}
async function guardarCotizador() {
    const titulo = document.getElementById('titulo').value.trim();
    const nombre = document.getElementById('nombre').value.trim();
    const descripcion = document.getElementById('descripcion').value.trim();
    const clave = document.getElementById('clave').value.trim();
    const mostrar_titulo = document.getElementById('mostrar_titulo').checked;
    const mostrar_nombre = document.getElementById('mostrar_nombre').checked;
    const mostrar_descripcion = document.getElementById('mostrar_descripcion').checked;
    if(!nombre || !clave) return alert('Nombre y clave son obligatorios');
    if(lugares.length === 0) return alert('Agrega al menos un lugar');
    for(let l of lugares) {
        if(!l.nombre) return alert('Todos los lugares deben tener nombre');
    }
    try {
        const res = await fetch('/cotizadores/' + cotizadorId, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({titulo, nombre, descripcion, clave, mostrar_titulo, mostrar_nombre, mostrar_descripcion, lugares})
        });
        const d = await res.json();
        if(d.ok) {
            alert('Cotizador actualizado correctamente');
            location.reload();
        } else {
            alert(d.error || 'Error');
        }
    } catch(e) {
        alert('Error de conexión: ' + e.message);
    }
}
function copiarEnlacePublico() {
    const enlace = document.getElementById('enlacePublico');
    enlace.select();
    document.execCommand('copy');
    alert('Enlace público copiado al portapapeles');
}
