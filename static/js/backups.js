// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
let _pendingRestoreId = null;
let _restoreModal = null;
let _folderModal = null;

document.addEventListener('DOMContentLoaded', () => {
    _restoreModal = new bootstrap.Modal(document.getElementById('restoreModal'));
    _folderModal = new bootstrap.Modal(document.getElementById('folderModal'));
    loadBackups();
});

async function loadBackups() {
    const list = document.getElementById('backupList');
    list.innerHTML = '<div class="text-center py-5 text-muted"><div class="spinner-border spinner-border-sm text-orange me-2"></div>Cargando...</div>';
    try {
        const r    = await fetch('/api/admin/backup/list');
        const data = await r.json();
        if (data.error) { list.innerHTML = `<p class="text-danger">${data.error}</p>`; return; }
        document.getElementById('backupCount').textContent = data.length;
        if (data.length === 0) {
            list.innerHTML = '<p class="text-center text-muted py-4 fst-italic">No hay respaldos todavía. ¡Crea el primero!</p>';
            return;
        }
        list.innerHTML = '';
        data.forEach(b => {
            const date   = new Date(b.created_at + 'Z');
            const dateStr = date.toLocaleString('es-CR', { dateStyle:'medium', timeStyle:'short' });
            const sizeMB = (b.size / 1048576).toFixed(2);
            const autoTag = b.auto
                ? '<span class="badge bg-warning text-dark rounded-pill ms-2" style="font-size:0.65rem;">AUTO</span>'
                : '';
            list.innerHTML += `
            <div class="backup-card p-3 mb-3 ${b.auto ? 'auto-backup' : ''}">
                <div class="d-flex justify-content-between align-items-start gap-2 flex-wrap">
                    <div style="min-width:0;">
                        <div class="fw-bold text-dark text-truncate">${b.name}${autoTag}</div>
                        ${b.description ? `<div class="text-muted small mt-1">${b.description}</div>` : ''}
                        <div class="mt-1 d-flex flex-wrap gap-2 align-items-center">
                            <span class="badge bg-light text-secondary border size-badge"><i class="bi bi-calendar3 me-1"></i>${dateStr}</span>
                            <span class="badge bg-light text-secondary border size-badge"><i class="bi bi-file-zip me-1"></i>${sizeMB} MB</span>
                        </div>
                    </div>
                    <div class="d-flex gap-2 flex-shrink-0 flex-wrap">
                        <button class="btn btn-sm btn-outline-secondary rounded-pill px-3"
                                onclick="downloadBackup('${b.id}')" title="Descargar ZIP">
                            <i class="bi bi-download"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-success rounded-pill px-3"
                                onclick="openBackupFolder('${b.id}')" title="Abrir carpeta con esta versión">
                            <i class="bi bi-folder2-open"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-orange rounded-pill px-3 text-dark fw-bold"
                                onclick="openRestoreModal('${b.id}','${b.name.replace(/'/g,"\\'")}') " title="Restaurar esta versión">
                            <i class="bi bi-arrow-counterclockwise me-1"></i>Restaurar
                        </button>
                        <button class="btn btn-sm btn-outline-danger rounded-pill px-3"
                                onclick="deleteBackup('${b.id}', this)" title="Eliminar respaldo">
                            <i class="bi bi-trash-fill"></i>
                        </button>
                    </div>
                </div>
            </div>`;
        });
    } catch(e) {
        list.innerHTML = '<p class="text-danger">Error de conexión.</p>';
    }
}

async function createBackup() {
    const name = document.getElementById('backupName').value.trim();
    const desc = document.getElementById('backupDesc').value.trim();
    if (!name) { document.getElementById('backupName').focus(); return; }
    const btn = document.getElementById('btnCreateBackup');
    const msg = document.getElementById('createMsg');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Creando...';
    msg.className = 'mt-3';
    msg.innerHTML = '<div class="alert alert-info rounded-3 py-2"><i class="bi bi-hourglass-split me-2"></i>Comprimiendo archivos y base de datos…</div>';
    try {
        const r    = await fetch('/api/admin/backup/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, description: desc })
        });
        const data = await r.json();
        if (data.ok) {
            msg.innerHTML = '<div class="alert alert-success rounded-3 py-2"><i class="bi bi-check-circle-fill me-2"></i>Respaldo creado correctamente.</div>';
            document.getElementById('backupName').value = '';
            document.getElementById('backupDesc').value = '';
            loadBackups();
        } else {
            msg.innerHTML = `<div class="alert alert-danger rounded-3 py-2"><i class="bi bi-x-circle-fill me-2"></i>${data.error}</div>`;
        }
    } catch(e) {
        msg.innerHTML = '<div class="alert alert-danger rounded-3 py-2">Error de red.</div>';
    }
    btn.disabled = false;
    btn.innerHTML = '<i class="bi bi-cloud-upload-fill me-1"></i> Guardar';
}

function downloadBackup(id) {
    window.location.href = `/api/admin/backup/download/${id}`;
}

function openRestoreModal(id, name) {
    _pendingRestoreId = id;
    document.getElementById('restoreModalName').textContent = name;
    _restoreModal.show();
}

async function confirmRestore() {
    if (!_pendingRestoreId) return;
    const btn = document.getElementById('btnConfirmRestore');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Restaurando...';
    try {
        const r    = await fetch(`/api/admin/backup/restore/${_pendingRestoreId}`, { method: 'POST' });
        const data = await r.json();
        _restoreModal.hide();
        if (data.ok) {
            document.body.innerHTML = `
            <div style="display:flex;align-items:center;justify-content:center;height:100vh;background:#fff9f2;flex-direction:column;gap:1rem;font-family:sans-serif;">
                <div style="font-size:3rem;">✅</div>
                <h2 style="color:#ff8c00;font-weight:900;">Versión restaurada</h2>
                <p style="color:#666;text-align:center;max-width:380px;">El servidor se está reiniciando con la versión seleccionada.<br>Espera 5 segundos y recarga la página.</p>
                <div id="countdown" style="font-size:2rem;font-weight:bold;color:#ff8c00;">5</div>
            </div>`;
            let s = 5;
            const t = setInterval(() => {
                s--;
                document.getElementById('countdown').textContent = s;
                if (s <= 0) { clearInterval(t); window.location.href = '/'; }
            }, 1000);
        } else {
            alert('Error al restaurar: ' + (data.error || 'desconocido'));
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-arrow-counterclockwise me-1"></i>Restaurar';
        }
    } catch(e) {
        alert('Error de red durante la restauración.');
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-arrow-counterclockwise me-1"></i>Restaurar';
    }
}

async function openBackupsFolder() {
    await loadFolderInfo();
    _folderModal.show();
}

async function openBackupFolder(id) {
    await loadFolderInfo(id);
    _folderModal.show();
}

async function loadFolderInfo(highlightId) {
    try {
        const r = await fetch('/api/admin/backup/folder');
        if (!r.ok) { const d = await r.json(); throw new Error(d.error || 'No se pudo cargar'); }
        const d = await r.json();
        document.getElementById('folderPath').textContent = d.path;
        const list = document.getElementById('folderList');
        list.innerHTML = '';
        if (!d.files.length) {
            list.innerHTML = '<p class="text-muted fst-italic">La carpeta está vacía.</p>';
            return;
        }
        d.files.forEach(f => {
            const sizeMB = (f.size / 1048576).toFixed(2);
            const dt = new Date(f.modified + 'Z').toLocaleString('es-CR', { dateStyle:'medium', timeStyle:'short' });
            const row = document.createElement('div');
            row.className = 'd-flex justify-content-between align-items-center border-bottom py-2';
            if (highlightId && f.name.includes(highlightId)) row.classList.add('bg-warning', 'bg-opacity-25', 'rounded-2', 'px-2');
            row.innerHTML = `<span class="text-truncate me-2" style="max-width:55%" title="${f.name}">${f.name}</span><span class="text-muted text-nowrap">${sizeMB} MB · ${dt}</span>`;
            list.appendChild(row);
        });
    } catch (e) {
        alert('Error al cargar la carpeta: ' + e.message);
    }
}

async function deleteBackup(id, btnEl) {
    abrirModalBorrarUnificado({
        titulo: 'Borrar Respaldo',
        mensaje: '¿Eliminar este respaldo permanentemente?',
        onConfirmar: async () => {
            btnEl.disabled = true;
            try {
                const r = await fetch(`/api/admin/backup/delete/${id}`, { method: 'DELETE' });
                const d = await r.json();
                if (d.ok) loadBackups();
                else alert(d.error || 'Error al eliminar');
            } catch(e) {
                alert('Error de red.');
                btnEl.disabled = false;
            }
        }
    });
}

// ============================
// EXPORTAR / IMPORTAR DB
// ============================
