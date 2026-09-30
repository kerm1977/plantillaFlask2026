// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
function exportarCotizadoresJSON() {
    fetch('/api/cotizadores/export-json')
        .then(r => r.json())
        .then(d => {
            const blob = new Blob([JSON.stringify(d, null, 2)], {type:'application/json'});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'cotizadores_' + new Date().toISOString().slice(0,10) + '.json';
            a.click();
            URL.revokeObjectURL(url);
        })
        .catch(e => alert('Error al exportar: ' + e));
}
async function importarCotizadoresJSON(input) {
    const file = input.files[0];
    if(!file) return;
    if(!confirm('Esto reemplazara TODOS los cotizadores y lugares existentes. ¿Continuar?')) {
        input.value = '';
        return;
    }
    try {
        const texto = await file.text();
        const data = JSON.parse(texto);
        const res = await fetch('/api/cotizadores/import-json', {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify(data)
        });
        const d = await res.json();
        if(d.ok) {
            alert(`Importados ${d.importados} cotizadores`);
            location.reload();
        } else {
            alert(d.error || 'Error al importar');
        }
    } catch(e) {
        alert('Error al leer JSON: ' + e.message);
    } finally {
        input.value = '';
    }
}
function renderCotizados() {
    const cotizados = lugares.filter(l => l.precio != null && l.precio !== '');
    const countEl = document.getElementById('cotizadosCount');
    if(countEl) countEl.textContent = '(' + cotizados.length + ')';
    if(cotizados.length === 0) {
        document.getElementById('cotizadosContainer').innerHTML = '<div class="col-12 text-center text-muted py-3">No hay lugares cotizados aún.</div>';
        return;
    }
    const grupos = {};
    cotizados.forEach(l => {
        const p = (l.provincia || 'Sin provincia').trim();
        if(!grupos[p]) grupos[p] = [];
        grupos[p].push(l);
    });
    const html = Object.entries(grupos).map(([provincia, items]) => `
        <div class="col-12">
            <h6 class="fw-bold text-orange mb-2"><i class="bi bi-geo-alt-fill me-2"></i>${provincia}</h6>
            <ul class="list-group list-group-flush mb-3">
                ${items.map(l => `
                    <li class="list-group-item d-flex justify-content-between align-items-center bg-transparent px-0" style="border-bottom:1px solid rgba(0,0,0,0.05);">
                        <span class="fw-semibold small">${l.nombre}</span>
                        <span class="badge bg-success">${l.moneda == 'colones' ? '₡' : '$'}${Math.trunc(parseFloat(l.precio))}</span>
                    </li>
                `).join('')}
            </ul>
        </div>
    `).join('');
    document.getElementById('cotizadosContainer').innerHTML = html;
}

function _abreviaturaProvincia(nombre) {
    const limpio = (nombre || 'XX').toString().toUpperCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^A-Z0-9\s]/g, '').trim();
    const partes = limpio.split(/\s+/).filter(p => p);
    if(partes.length >= 2) {
        return partes.slice(0, 2).map(p => p[0]).join('');
    }
    return (partes[0] || 'XX').substring(0, 2);
}

function exportarCotizadosWhatsApp() {
    const cotizados = lugares.filter(l => l.precio != null && l.precio !== '');
    if(cotizados.length === 0) {
        alert('No hay lugares cotizados aún.');
        return;
    }
    const indices = {};
    const lineas = [];
    let orden = 1;
    cotizados.forEach(l => {
        const p = (l.provincia || 'Sin provincia').trim();
        if(!indices[p]) indices[p] = 0;
        indices[p]++;
        const codigo = _abreviaturaProvincia(p) + '-' + String(indices[p]).padStart(2, '0');
        const moneda = l.moneda == 'colones' ? '₡' : '$';
        const precio = Math.trunc(parseFloat(l.precio));
        lineas.push(`${orden}. ${codigo} ${l.nombre} - ${p} - ${moneda}${precio}`);
        orden++;
    });
    const texto = '*Cotizados*\n\n' + lineas.join('\n');
    window.open('https://wa.me/?text=' + encodeURIComponent(texto));
}

document.addEventListener('DOMContentLoaded', function() {
    confirmDeleteLugarModal1 = new bootstrap.Modal(document.getElementById('confirmDeleteLugarModal1'));
    confirmDeleteLugarModal2 = new bootstrap.Modal(document.getElementById('confirmDeleteLugarModal2'));
    confirmDeleteLugarModal3 = new bootstrap.Modal(document.getElementById('confirmDeleteLugarModal3'));
    renderLugares();
    renderCotizados();
});
