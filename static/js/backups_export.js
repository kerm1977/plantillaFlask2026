// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
async function exportJSON() {
    const msg = document.getElementById('dbMsg');
    msg.className = 'mt-3 alert alert-info rounded-3 py-2 small';
    msg.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Generando exportación…';
    msg.classList.remove('d-none');
    try {
        const r = await fetch('/api/admin/db/export');
        if (!r.ok) { const d = await r.json(); throw new Error(d.error); }
        const blob = await r.blob();
        const cd   = r.headers.get('Content-Disposition') || '';
        const name = (cd.match(/filename="?([^"]+)"?/) || [])[1] || 'db_export.json';
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement('a'); a.href = url; a.download = name; a.click();
        URL.revokeObjectURL(url);
        msg.className = 'mt-3 alert alert-success rounded-3 py-2 small';
        msg.innerHTML = '<i class="bi bi-check-circle-fill me-2"></i>Exportación JSON descargada.';
    } catch(e) {
        msg.className = 'mt-3 alert alert-danger rounded-3 py-2 small';
        msg.innerHTML = `<i class="bi bi-x-circle-fill me-2"></i>Error: ${e.message}`;
    }
}

async function exportExcel() {
    const msg = document.getElementById('dbMsg');
    msg.className = 'mt-3 alert alert-info rounded-3 py-2 small';
    msg.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Generando Excel…';
    msg.classList.remove('d-none');
    try {
        const r    = await fetch('/api/admin/db/export');
        if (!r.ok) { const d = await r.json(); throw new Error(d.error); }
        const data = await r.json();
        const wb   = XLSX.utils.book_new();
        const sheetNames = {
            users: 'Usuarios', hikers: 'CRM Caminantes',
            events: 'Eventos', event_registrations: 'Inscripciones',
            notifications: 'Notificaciones', site_content: 'Contenido Sitio'
        };
        Object.entries(data.tables).forEach(([key, rows]) => {
            if (rows.length) {
                const ws = XLSX.utils.json_to_sheet(rows);
                XLSX.utils.book_append_sheet(wb, ws, sheetNames[key] || key);
            }
        });
        const ts = new Date().toISOString().slice(0,10).replace(/-/g,'');
        XLSX.writeFile(wb, `db_export_${ts}.xlsx`);
        msg.className = 'mt-3 alert alert-success rounded-3 py-2 small';
        msg.innerHTML = '<i class="bi bi-check-circle-fill me-2"></i>Archivo Excel descargado.';
    } catch(e) {
        msg.className = 'mt-3 alert alert-danger rounded-3 py-2 small';
        msg.innerHTML = `<i class="bi bi-x-circle-fill me-2"></i>Error: ${e.message}`;
    }
}

async function importJSON(input) {
    const file = input.files[0];
    if (!file) return;
    const msg = document.getElementById('dbMsg');
    msg.className = 'mt-3 alert alert-info rounded-3 py-2 small';
    msg.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Importando datos…';
    msg.classList.remove('d-none');
    try {
        const text = await file.text();
        const json = JSON.parse(text);
        const r    = await fetch('/api/admin/db/import', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(json)
        });
        const d = await r.json();
        if (d.ok) {
            const s = d.stats;
            const summary = Object.entries(s)
                .map(([t, v]) => `<b>${t}</b>: +${v.added} nuevos, ${v.skipped} existentes`)
                .join(' · ');
            msg.className = 'mt-3 alert alert-success rounded-3 py-2 small';
            msg.innerHTML = `<i class="bi bi-check-circle-fill me-2"></i>Importación completada — ${summary}`;
        } else {
            throw new Error(d.error || 'Error desconocido');
        }
    } catch(e) {
        msg.className = 'mt-3 alert alert-danger rounded-3 py-2 small';
        msg.innerHTML = `<i class="bi bi-x-circle-fill me-2"></i>Error: ${e.message}`;
    }
    input.value = '';
}
