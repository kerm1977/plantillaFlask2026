// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
let pageSaveTimeout = null;

function pageEscapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function pageExecCmd(command) {
    try { document.execCommand('styleWithCSS', false, true); } catch(e) {}
    const editor = document.getElementById('notePageEditor');
    if (editor) editor.focus();
    document.execCommand(command, false, null);
    pageScheduleSave();
}

function pageInsertCheckbox() {
    const editor = document.getElementById('notePageEditor');
    if (!editor) return;
    editor.focus();
    const selection = window.getSelection();
    const selectedText = selection ? selection.toString() : '';
    const id = 'page-check-' + Date.now();

    if (selectedText) {
        const lines = selectedText.split('\n').filter(l => l.trim());
        let listItems = '';
        lines.forEach((line, idx) => {
            const cid = `${id}-${idx}`;
            const text = pageEscapeHtml(line.trim());
            listItems += `<li class="list-group-item d-flex align-items-start gap-2 p-2 todo-item" data-checked="false"><input class="form-check-input note-check flex-shrink-0" type="checkbox" onchange="pageToggleTodoCheck(this)" contenteditable="false"><span class="form-check-label flex-grow-1">${text}</span><button class="btn btn-sm btn-link text-danger p-0 ms-1" type="button" onclick="pageDeleteTodoItem(this)" contenteditable="false" tabindex="-1"><i class="bi bi-trash"></i></button></li>`;
        });
        document.execCommand('insertHTML', false, `<ul class="list-group list-group-flush todo-list mb-2">${listItems}</ul>`);
    } else {
        const html = `<ul class="list-group list-group-flush todo-list mb-2"><li class="list-group-item d-flex align-items-start gap-2 p-2 todo-item" data-checked="false"><input class="form-check-input note-check flex-shrink-0" type="checkbox" onchange="pageToggleTodoCheck(this)" contenteditable="false"><span class="form-check-label flex-grow-1 new-todo-focus">Nueva tarea</span><button class="btn btn-sm btn-link text-danger p-0 ms-1" type="button" onclick="pageDeleteTodoItem(this)" contenteditable="false" tabindex="-1"><i class="bi bi-trash"></i></button></li></ul>`;
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
    pageScheduleSave();
}

function pageInsertLink() {
    const text = window.getSelection().toString();
    const displayText = text || prompt('Texto del enlace:', '');
    if (displayText === null) return;
    let url = prompt('URL del enlace (https://...):', '');
    if (!url) return;
    if (!/^https?:\/\//i.test(url)) url = 'https://' + url;
    const editor = document.getElementById('notePageEditor');
    if (editor) editor.focus();
    document.execCommand('insertHTML', false, `<a href="${pageEscapeHtml(url)}" target="_blank" rel="noopener">${pageEscapeHtml(displayText || url)}</a>`);
    pageScheduleSave();
}

async function pageUploadImage(input) {
    const file = input.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('image', file);
    try {
        const r = await fetch('/api/notes/upload-image', { method: 'POST', body: formData });
        const data = await r.json();
        if (data.ok) {
            pageInsertImage(data.url);
        } else {
            mostrarAlerta(data.error || 'Error al subir imagen', 'error');
        }
    } catch(e) {
        mostrarAlerta('Error de conexión al subir imagen', 'error');
    }
    input.value = '';
}

function pageInsertImage(url, width = 100) {
    const editor = document.getElementById('notePageEditor');
    if (!editor) return;
    editor.focus();
    document.execCommand('insertHTML', false, `<img src="${pageEscapeHtml(url)}" class="img-fluid rounded-3 my-2" style="max-width:${width}%;" alt="Imagen">`);
    pageScheduleSave();
}

function pageToggleTodoCheck(checkbox) {
    const li = checkbox ? checkbox.closest('li') : null;
    if (!li) return;
    const checked = checkbox.checked;
    li.setAttribute('data-checked', checked ? 'true' : 'false');
    const label = li.querySelector('.form-check-label');
    if (label) {
        label.classList.toggle('text-decoration-line-through', checked);
        label.classList.toggle('text-muted', checked);
    }
    pageScheduleSave();
}

function pageDeleteTodoItem(btn) {
    const li = btn ? btn.closest('li') : null;
    if (li) li.remove();
    pageScheduleSave();
}

function pageScheduleSave() {
    clearTimeout(pageSaveTimeout);
    pageSaveTimeout = setTimeout(pageAutoSave, 900);
    const status = document.getElementById('notePageSaveStatus');
    if (status) status.innerHTML = '<i class="bi bi-pencil me-1"></i>Escribiendo...';
}

async function pageAutoSave() {
    const titleInput = document.getElementById('notePageTitle');
    const editor = document.getElementById('notePageEditor');
    if (!titleInput || !editor) return;
    const title = titleInput.value.trim() || 'Sin título';
    const content = editor.innerHTML;
    const status = document.getElementById('notePageSaveStatus');
    try {
        const r = await fetch(`/api/notes/${NOTE_ID}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({title, content})
        });
        const data = await r.json();
        if (data.ok) {
            if (status) status.innerHTML = '<i class="bi bi-check-circle text-success me-1"></i>Guardado';
            setTimeout(() => { if (status) status.textContent = ''; }, 2000);
        } else {
            if (status) status.innerHTML = '<i class="bi bi-exclamation-circle text-danger me-1"></i>Error';
        }
    } catch(e) {
        if (status) status.innerHTML = '<i class="bi bi-exclamation-circle text-danger me-1"></i>Error';
    }
}

async function savePageNote() {
    await pageAutoSave();
    mostrarAlerta('Nota guardada', 'success');
}

function exportPageNotePNG() {
    const title = document.getElementById('notePageTitle')?.value.trim() || 'nota';
    const content = document.getElementById('notePageEditor')?.innerHTML || '';
    if (typeof exportNoteImageFromData === 'function') {
        exportNoteImageFromData(title, content, 'image/png', 'png');
    }
}

function exportPageNotePDF() {
    const title = document.getElementById('notePageTitle')?.value.trim() || 'nota';
    const content = document.getElementById('notePageEditor')?.innerHTML || '';
    if (typeof exportNoteToPDF === 'function') {
        exportNoteToPDF(title, content);
    }
}

function sharePageNoteWhatsApp() {
    const title = document.getElementById('notePageTitle')?.value.trim() || 'nota';
    const content = document.getElementById('notePageEditor')?.innerHTML || '';
    let body = content;
    if (typeof htmlToWhatsApp === 'function') {
        body = htmlToWhatsApp(content);
    }
    window.open(`https://wa.me/?text=${encodeURIComponent(`*${title}*\n\n${body}`)}`, '_blank');
}

// Tecla Enter dentro de tareas para dividirlas
document.addEventListener('DOMContentLoaded', function() {
    const editor = document.getElementById('notePageEditor');
    if (!editor) return;
    editor.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            const sel = window.getSelection();
            if (!sel.rangeCount) return;
            const range = sel.getRangeAt(0);
            let node = range.commonAncestorContainer;
            if (node.nodeType === Node.TEXT_NODE) node = node.parentElement;
            const label = node ? node.closest('.form-check-label') : null;
            if (!label) return;
            const li = label.closest('li');
            const ul = li ? li.closest('ul') : null;
            if (!ul) return;
            e.preventDefault();
            const preCaretRange = range.cloneRange();
            preCaretRange.selectNodeContents(label);
            preCaretRange.setEnd(range.endContainer, range.endOffset);
            const before = preCaretRange.toString();
            const after = label.textContent.substring(before.length);
            label.textContent = before;
            const newLi = document.createElement('li');
            newLi.className = 'list-group-item d-flex align-items-start gap-2 p-2 todo-item';
            newLi.setAttribute('data-checked', 'false');
            const newText = after ? pageEscapeHtml(after) : 'Nueva tarea';
            newLi.innerHTML = `<input class="form-check-input note-check flex-shrink-0" type="checkbox" onchange="pageToggleTodoCheck(this)" contenteditable="false"><span class="form-check-label flex-grow-1">${newText}</span><button class="btn btn-sm btn-link text-danger p-0 ms-1" type="button" onclick="pageDeleteTodoItem(this)" contenteditable="false" tabindex="-1"><i class="bi bi-trash"></i></button>`;
            li.after(newLi);
            const newLabel = newLi.querySelector('.form-check-label');
            if (newLabel) {
                const newRange = document.createRange();
                newRange.selectNodeContents(newLabel);
                if (after) newRange.collapse(true);
                sel.removeAllRanges();
                sel.addRange(newRange);
            }
            pageScheduleSave();
        }
    });

    // Guardar también cuando se cierra el picker de emojis
    const emojiModal = document.getElementById('emojiPickerModal');
    if (emojiModal) {
        emojiModal.addEventListener('hidden.bs.modal', pageScheduleSave);
    }
});
