// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
let noteAutoSaveTimeout = null;

function scheduleNoteAutoSave() {
    clearTimeout(noteAutoSaveTimeout);
    noteAutoSaveTimeout = setTimeout(autoSaveNote, 900);
}

async function autoSaveNote() {
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
        if (data.ok && !currentNoteId && data.id) {
            currentNoteId = data.id;
            if (typeof collabJoin === 'function') collabJoin('note-' + currentNoteId, 'noteContentEditor');
        }
    } catch (e) {
        console.error('Error en autoguardado de nota:', e);
    }
}

function openNoteOptionsModal() {
    if (noteOptionsModal) noteOptionsModal.show();
}

function cancelEdit() {
    currentNoteId = null;
    document.getElementById('notesListContainer').classList.remove('d-none');
    document.getElementById('noteEditorContainer').classList.add('d-none');
    document.getElementById('createNoteBtnContainer').classList.remove('d-none');
    if (typeof collabLeave === 'function') collabLeave();
}

function viewNote(id) {
    window.location.href = `/notas/${id}`;
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

function deleteNote(id) {
    deleteNotePendiente = id;
    if (confirmDeleteNoteModal1) confirmDeleteNoteModal1.show();
}

function mostrarConfirmarNota(paso) {
    if (deleteNotePendiente === null) return;
    if (paso === 2) {
        confirmDeleteNoteModal1._element.addEventListener('hidden.bs.modal', () => confirmDeleteNoteModal2.show(), {once:true});
        confirmDeleteNoteModal1.hide();
    } else if (paso === 3) {
        confirmDeleteNoteModal2._element.addEventListener('hidden.bs.modal', () => confirmDeleteNoteModal3.show(), {once:true});
        confirmDeleteNoteModal2.hide();
    }
}

async function confirmarEliminarNota() {
    if (deleteNotePendiente === null) return;
    const id = deleteNotePendiente;
    deleteNotePendiente = null;
    confirmDeleteNoteModal3.hide();
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
    // Aseguramos que el navegador use estilos CSS (text-align, etc.) en lugar de
    // atributos legacy. Sin esto, algunos navegadores móviles no aplican bien
    // la alineación (izquierda/derecha/justificado) en contenteditable.
    try { document.execCommand('styleWithCSS', false, true); } catch(e) {}
    document.getElementById('noteContentEditor').focus();
    document.execCommand(command, false, null);
    updateNoteProgress();
}

function insertCheckbox() {
    const editor = document.getElementById('noteContentEditor');
    editor.focus();
    const selection = window.getSelection();
    const selectedText = selection ? selection.toString() : '';
    const id = 'note-check-' + Date.now();
    
    if (selectedText) {
        const lines = selectedText.split('\n').filter(l => l.trim());
        let listItems = '';
        lines.forEach((line, idx) => {
            const cid = `${id}-${idx}`;
            const text = escapeHtml(line.trim());
            listItems += `<li class="list-group-item d-flex align-items-start gap-2 p-2 todo-item" data-checked="false"><input class="form-check-input note-check flex-shrink-0" type="checkbox" onchange="toggleTodoCheck(this)" contenteditable="false"><span class="form-check-label flex-grow-1">${text}</span><button class="btn btn-sm btn-link text-danger p-0 ms-1" type="button" onclick="deleteTodoItem(this)" contenteditable="false" tabindex="-1"><i class="bi bi-trash"></i></button></li>`;
        });
        document.execCommand('insertHTML', false, `<ul class="list-group list-group-flush todo-list mb-2">${listItems}</ul>`);
    } else {
        const html = `<ul class="list-group list-group-flush todo-list mb-2"><li class="list-group-item d-flex align-items-start gap-2 p-2 todo-item" data-checked="false"><input class="form-check-input note-check flex-shrink-0" type="checkbox" onchange="toggleTodoCheck(this)" contenteditable="false"><span class="form-check-label flex-grow-1 new-todo-focus">Nueva tarea</span><button class="btn btn-sm btn-link text-danger p-0 ms-1" type="button" onclick="deleteTodoItem(this)" contenteditable="false" tabindex="-1"><i class="bi bi-trash"></i></button></li></ul>`;
        document.execCommand('insertHTML', false, html);
        const newLabel = editor.querySelector('.new-todo-focus');
        if (newLabel) {
            const range = document.createRange();
            range.selectNodeContents(newLabel);
            const sel = window.getSelection();
            sel.removeAllRanges();
            sel.addRange(range);
            newLabel.classList.remove('new-todo-focus');
        }
    }
    
    document.getElementById('noteProgressContainer').classList.remove('d-none');
    updateNoteProgress();
}

function insertLink() {
    document.getElementById('noteLinkEditId').value = '';
    document.getElementById('noteLinkText').value = '';
    document.getElementById('noteLinkUrl').value = '';
    
    const selection = window.getSelection();
    if (selection.rangeCount > 0) {
        const node = selection.anchorNode ? selection.anchorNode.parentElement : null;
        if (node && node.tagName === 'A') {
            document.getElementById('noteLinkEditId').value = 'edit';
            document.getElementById('noteLinkText').value = node.textContent;
            document.getElementById('noteLinkUrl').value = node.getAttribute('href') || '';
        } else {
            document.getElementById('noteLinkText').value = selection.toString();
        }
    }
    
    if (noteLinkModal) noteLinkModal.show();
}

function applyNoteLink() {
    const text = document.getElementById('noteLinkText').value.trim();
    let url = document.getElementById('noteLinkUrl').value.trim();
    const isEdit = document.getElementById('noteLinkEditId').value === 'edit';
    if (!url) return;
    
    if (!/^https?:\/\//i.test(url)) {
        url = 'https://' + url;
    }
    
    document.getElementById('noteContentEditor').focus();
    const displayText = text || url;
    
    if (isEdit) {
        const selection = window.getSelection();
        const node = selection.anchorNode ? selection.anchorNode.parentElement : null;
        if (node && node.tagName === 'A') {
            node.textContent = displayText;
            node.setAttribute('href', url);
            noteLinkModal.hide();
            return;
        }
    }
    
    document.execCommand('insertHTML', false, `<a href="${escapeHtml(url)}" target="_blank" rel="noopener" class="text-orange fw-bold">${escapeHtml(displayText)}</a>`);
    noteLinkModal.hide();
}

