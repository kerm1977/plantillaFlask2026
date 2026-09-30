// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
function abrirModalCompartir(modo) {
    document.getElementById('compartirEnlaceInput').value = 'Generando enlace...';
    const modalEl = document.getElementById('compartirUsuarioModal');
    if (modalEl) {
        modalEl.addEventListener('shown.bs.modal', function onShow() {
            modalEl.removeEventListener('shown.bs.modal', onShow);
            generarEnlacePublico();
        });
        new bootstrap.Modal(modalEl).show();
    }
}

async function generarEnlacePublico() {
    try {
        const r = await fetch('/api/admin/generar_enlace_publico', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ accion: 'crear', user_id: null })
        });
        if (!r.ok) {
            const text = await r.text();
            mostrarAlerta('Error del servidor (' + r.status + '): ' + text.replace(/<[^>]+>/g, ' ').trim().slice(0, 200), 'error');
            return;
        }
        const d = await r.json();
        if (d.url) {
            document.getElementById('compartirEnlaceInput').value = d.url;
        } else {
            mostrarAlerta(d.error || 'No se pudo generar el enlace.', 'error');
        }
    } catch (e) {
        console.error('Error al generar enlace:', e);
        mostrarAlerta('Error de conexión: ' + (e.message || 'No se pudo contactar al servidor.'), 'error');
    }
}

function copiarEnlacePublico() {
    const input = document.getElementById('compartirEnlaceInput');
    if (!input || !input.value) {
        mostrarAlerta('Primero generá un enlace.', 'warning');
        return;
    }
    navigator.clipboard.writeText(input.value).then(function() {
        mostrarAlerta('Enlace copiado al portapapeles.', 'success');
    }).catch(function() {
        input.select();
        document.execCommand('copy');
        mostrarAlerta('Enlace copiado al portapapeles.', 'success');
    });
}

function compartirWhatsApp() {
    const input = document.getElementById('compartirEnlaceInput');
    if (!input || !input.value) {
        mostrarAlerta('Primero generá un enlace.', 'warning');
        return;
    }
    const mensaje = encodeURIComponent('Hola, te comparto este enlace para gestionar usuarios: ' + input.value);
    window.open('https://wa.me/?text=' + mensaje, '_blank');
}

let currentSelectedUserId = null, currentSelectedUserName = "", currentSelectedUserObj = null;
let allContacts = [], filteredContacts = [];
const DASH_PAGE_SIZE = 25;

function _dashMsg(cls, html) {
    const el = document.getElementById('dashDbMsg'); if (!el) return;
    el.className = `alert ${cls} rounded-3 py-2 small`; el.innerHTML = html; el.classList.remove('d-none');
}
async function dashExportJSON() {
    _dashMsg('alert-info','<span class="spinner-border spinner-border-sm me-2"></span>Generando exportación');
    try {
        const r = await fetch('/api/admin/db/export');
        if (!r.ok) { const d = await r.json(); throw new Error(d.error); }
        const blob = await r.blob(), cd = r.headers.get('Content-Disposition')||'';
        const name = (cd.match(/filename="?([^"]+)"?/)||[])[1]||'db_export.json';
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement('a'); a.href=url; a.download=name; a.click(); URL.revokeObjectURL(url);
        _dashMsg('alert-success','<i class="bi bi-check-circle-fill me-2"></i>JSON descargado.');
    } catch(e) { _dashMsg('alert-danger',`<i class="bi bi-x-circle-fill me-2"></i>${e.message}`); }
}
async function dashExportExcel() {
    _dashMsg('alert-info','<span class="spinner-border spinner-border-sm me-2"></span>Generando Excel');
    try {
        const r=await fetch('/api/admin/db/export'); if(!r.ok){const d=await r.json();throw new Error(d.error);}
        const data=await r.json(), wb=XLSX.utils.book_new();
        const names={users:'Usuarios',hikers:'CRM Caminantes',events:'Eventos',event_registrations:'Inscripciones',notifications:'Notificaciones',site_content:'Contenido Sitio'};
        Object.entries(data.tables).forEach(([k,rows])=>{if(rows.length)XLSX.utils.book_append_sheet(wb,XLSX.utils.json_to_sheet(rows),names[k]||k);});
        XLSX.writeFile(wb,`db_export_${new Date().toISOString().slice(0,10).replace(/-/g,'')}.xlsx`);
        _dashMsg('alert-success','<i class="bi bi-check-circle-fill me-2"></i>Excel descargado.');
    } catch(e) { _dashMsg('alert-danger',`<i class="bi bi-x-circle-fill me-2"></i>${e.message}`); }
}
async function dashImportJSON(input) {
    const file=input.files[0]; if(!file) return;
    _dashMsg('alert-info','<span class="spinner-border spinner-border-sm me-2"></span>Importando datos');
    try {
        const json=JSON.parse(await file.text());
        const r=await fetch('/api/admin/db/import',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(json)});
        const d=await r.json();
        if(d.ok){const summary=Object.entries(d.stats).map(([t,v])=>`<b>${t}</b>: +${v.added} nuevos, ${v.skipped} existentes`).join(' · ');
            _dashMsg('alert-success',`<i class="bi bi-check-circle-fill me-2"></i>Importado  ${summary}`); loadAllUsers();}
        else{throw new Error(d.error||'Error desconocido');}
    } catch(e){_dashMsg('alert-danger',`<i class="bi bi-x-circle-fill me-2"></i>${e.message}`);}
    input.value='';
}

