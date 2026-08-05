// Sistema de Notas Administrativas
let notesModal = null;
let currentNoteId = null;
let notesData = [];

document.addEventListener('DOMContentLoaded', function() {
    const modalEl = document.getElementById('notesModal');
    if (modalEl) {
        notesModal = new bootstrap.Modal(modalEl);
    }
});

function openNotesModal() {
    if (notesModal) {
        loadNotes();
        notesModal.show();
    }
}

async function loadNotes() {
    try {
        const r = await fetch('/api/notes');
        const data = await r.json();
        if (data.notes) {
            notesData = data.notes;
            renderNotesList();
        }
    } catch (e) {
        console.error('Error cargando notas:', e);
    }
}

function renderNotesList() {
    const container = document.getElementById('notesList');
    if (!notesData.length) {
        container.innerHTML = `
            <div class="col-12 text-center py-4 text-muted">
                <i class="bi bi-journal fs-1 mb-2 d-block"></i>
                No tienes notas aún
            </div>
        `;
        return;
    }
    container.innerHTML = notesData.map(n => `
        <div class="col-12 col-md-6">
            <div class="glass-panel rounded-3 p-3 h-100 position-relative">
                <h6 class="fw-bold text-dark mb-1">${escapeHtml(n.title)}</h6>
                <p class="small text-muted mb-2 text-truncate">${escapeHtml(stripHtml(n.content))}</p>
                <small class="text-secondary">Actualizado: ${formatDate(n.updated_at)}</small>
                <div class="position-absolute top-0 end-0 p-2">
                    <button class="btn btn-sm btn-light rounded-circle" onclick="editNote(${n.id})" title="Editar">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-danger rounded-circle" onclick="deleteNote(${n.id})" title="Eliminar">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

function createNewNote() {
    currentNoteId = null;
    document.getElementById('noteTitleInput').value = '';
    document.getElementById('noteContentEditor').innerHTML = '';
    document.getElementById('notesListContainer').classList.add('d-none');
    document.getElementById('noteEditorContainer').classList.remove('d-none');
    document.getElementById('createNoteBtnContainer').classList.add('d-none');
}

function editNote(id) {
    const note = notesData.find(n => n.id === id);
    if (!note) return;
    currentNoteId = id;
    document.getElementById('noteTitleInput').value = note.title;
    document.getElementById('noteContentEditor').innerHTML = note.content;
    document.getElementById('notesListContainer').classList.add('d-none');
    document.getElementById('noteEditorContainer').classList.remove('d-none');
    document.getElementById('createNoteBtnContainer').classList.add('d-none');
}

function cancelEdit() {
    currentNoteId = null;
    document.getElementById('notesListContainer').classList.remove('d-none');
    document.getElementById('noteEditorContainer').classList.add('d-none');
    document.getElementById('createNoteBtnContainer').classList.remove('d-none');
}

async function saveNote() {
    const title = document.getElementById('noteTitleInput').value.trim() || 'Sin título';
    const content = document.getElementById('noteContentEditor').innerHTML;
    
    try {
        let url = '/api/notes';
        let method = 'POST';
        if (currentNoteId) {
            url = `/api/notes/${currentNoteId}`;
            method = 'PUT';
        }
        
        const r = await fetch(url, {
            method: method,
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({title, content})
        });
        const data = await r.json();
        if (data.ok) {
            await loadNotes();
            cancelEdit();
        }
    } catch (e) {
        console.error('Error guardando nota:', e);
        alert('Error al guardar la nota');
    }
}

async function deleteNote(id) {
    if (!confirm('¿Eliminar esta nota?')) return;
    try {
        const r = await fetch(`/api/notes/${id}`, {method: 'DELETE'});
        const data = await r.json();
        if (data.ok) {
            await loadNotes();
        }
    } catch (e) {
        console.error('Error eliminando nota:', e);
    }
}

// WYSIWYG Commands
function execCmd(command) {
    document.execCommand(command, false, null);
    document.getElementById('noteContentEditor').focus();
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

// Image Export (JPG/PNG)
function exportNoteJPG() {
    exportNoteImage('image/jpeg', 'jpg');
}

function exportNotePNG() {
    exportNoteImage('image/png', 'png');
}

function exportNoteImage(format, ext) {
    const title = document.getElementById('noteTitleInput').value || 'nota';
    const content = document.getElementById('noteContentEditor').innerHTML;
    
    // Crear canvas temporal
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    canvas.width = 800;
    canvas.height = 600;
    
    // Fondo blanco
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Título
    ctx.fillStyle = '#000000';
    ctx.font = 'bold 24px Arial';
    ctx.fillText(title, 20, 40);
    
    // Contenido (simplificado - texto plano)
    ctx.font = '16px Arial';
    const plainText = stripHtml(content);
    const lines = wrapText(ctx, plainText, 760);
    let y = 80;
    lines.forEach(line => {
        if (y < canvas.height - 20) {
            ctx.fillText(line, 20, y);
            y += 24;
        }
    });
    
    // Descargar
    const url = canvas.toDataURL(format);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title}.${ext}`;
    a.click();
}

// WhatsApp Share
function shareNoteWhatsApp() {
    const title = document.getElementById('noteTitleInput').value || 'Nota';
    const content = stripHtml(document.getElementById('noteContentEditor').innerHTML);
    const text = `*${title}*\n\n${content}`;
    const url = `https://wa.me/?text=${encodeURIComponent(text)}`;
    window.open(url, '_blank');
}

// Utilities
function escapeHtml(text) {
    if (!text) return '';
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function stripHtml(html) {
    const tmp = document.createElement('div');
    tmp.innerHTML = html;
    return tmp.textContent || tmp.innerText || '';
}

function formatDate(isoString) {
    const d = new Date(isoString);
    return d.toLocaleDateString('es-CR', {day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'});
}

function wrapText(ctx, text, maxWidth) {
    const words = text.split(' ');
    const lines = [];
    let currentLine = '';
    
    words.forEach(word => {
        const testLine = currentLine + (currentLine ? ' ' : '') + word;
        const metrics = ctx.measureText(testLine);
        if (metrics.width > maxWidth && currentLine) {
            lines.push(currentLine);
            currentLine = word;
        } else {
            currentLine = testLine;
        }
    });
    if (currentLine) lines.push(currentLine);
    return lines;
}
