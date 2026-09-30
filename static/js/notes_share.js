// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
// Enlace Público (colaborativo, sin clave)
async function shareCurrentNote() {
    if (!currentNoteId) {
        alert('Primero guarda la nota para poder generar el enlace público.');
        return;
    }
    try {
        const r = await fetch(`/api/notes/${currentNoteId}/share`, {method: 'POST'});
        const data = await r.json();
        if (data.ok) {
            const fullUrl = window.location.origin + data.url;
            const input = document.getElementById('notePublicLinkInput');
            if (input) input.value = fullUrl;
            if (noteOptionsModal) noteOptionsModal.hide();
            if (notePublicLinkModal) notePublicLinkModal.show();
        } else {
            alert(data.error || 'Error al generar el enlace público');
        }
    } catch (e) {
        console.error('Error generando enlace público:', e);
        alert('Error de conexión al generar el enlace');
    }
}

function copyPublicLink() {
    const input = document.getElementById('notePublicLinkInput');
    if (!input || !input.value) return;
    input.select();
    navigator.clipboard.writeText(input.value).then(() => {
        const btn = document.getElementById('copyPublicLinkBtn');
        if (btn) {
            const old = btn.innerHTML;
            btn.innerHTML = '<i class="bi bi-check-lg me-1"></i>Copiado';
            setTimeout(() => { btn.innerHTML = old; }, 1500);
        }
    }).catch(() => {
        document.execCommand('copy');
    });
}

async function unshareCurrentNote() {
    if (!currentNoteId) return;
    if (!confirm('¿Desactivar el enlace público? Nadie podrá seguir usándolo.')) return;
    try {
        const r = await fetch(`/api/notes/${currentNoteId}/unshare`, {method: 'POST'});
        const data = await r.json();
        if (data.ok) {
            if (notePublicLinkModal) notePublicLinkModal.hide();
        }
    } catch (e) {
        console.error('Error desactivando enlace:', e);
    }
}

// JSON Export/Import por nota individual
function exportSingleNoteJSON() {
    const title = document.getElementById('noteTitleInput').value.trim() || 'Sin título';
    const content = document.getElementById('noteContentEditor').innerHTML;
    const data = {
        title,
        content,
        exported_at: new Date().toISOString()
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title.replace(/[^a-z0-9\u00C0-\u024F\u1E00-\u1EFF]/gi, '_')}.json`;
    a.click();
    URL.revokeObjectURL(url);
}

function importSingleNoteJSON() {
    document.getElementById('singleJsonImportInput').click();
}

async function handleSingleJSONImport(input) {
    const file = input.files[0];
    if (!file) return;
    try {
        const text = await file.text();
        const data = JSON.parse(text);
        document.getElementById('noteTitleInput').value = data.title || '';
        document.getElementById('noteContentEditor').innerHTML = data.content || '';
        attachCheckboxListeners();
        updateNoteProgress();
    } catch (e) {
        console.error('Error importando JSON de nota:', e);
        alert('Archivo JSON inválido');
    }
    input.value = '';
}

// JSON Export/Import
async function exportNotesJSON() {
    try {
        const r = await fetch('/api/notes/export-json');
        const data = await r.json();
        if (data.ok) {
            const blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `notas_backup_${new Date().toISOString().split('T')[0]}.json`;
            a.click();
            URL.revokeObjectURL(url);
        }
    } catch (e) {
        console.error('Error exportando JSON:', e);
    }
}

function importNotesJSON() {
    document.getElementById('jsonImportInput').click();
}

async function handleJSONImport(input) {
    const file = input.files[0];
    if (!file) return;
    try {
        const text = await file.text();
        const data = JSON.parse(text);
        const r = await fetch('/api/notes/import-json', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        const result = await r.json();
        if (result.ok) {
            alert(`Se importaron ${result.imported} notas`);
            await loadNotes();
        }
    } catch (e) {
        console.error('Error importando JSON:', e);
        alert('Error al importar el archivo JSON');
    }
    input.value = '';
}

