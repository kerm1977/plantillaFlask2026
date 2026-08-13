// Sistema de Notas Administrativas
let notesModal = null;
let noteViewModal = null;
let noteLinkModal = null;
let noteImageModal = null;
let noteImageEditModal = null;
let noteImageViewModal = null;
let currentNoteId = null;
let currentViewNote = null;
let currentImageFile = null;
let currentEditImage = null;
let notesData = [];
let notesPage = 1;
const NOTES_PER_PAGE = 10;
let deleteNotePendiente = null;
let confirmDeleteNoteModal1, confirmDeleteNoteModal2, confirmDeleteNoteModal3;
let notePublicLinkModal = null;

document.addEventListener('DOMContentLoaded', function() {
    const modalEl = document.getElementById('notesModal');
    if (modalEl) {
        notesModal = new bootstrap.Modal(modalEl);
    }
    const viewModalEl = document.getElementById('noteViewModal');
    if (viewModalEl) {
        noteViewModal = new bootstrap.Modal(viewModalEl);
    }
    const linkModalEl = document.getElementById('noteLinkModal');
    if (linkModalEl) {
        noteLinkModal = new bootstrap.Modal(linkModalEl);
    }
    const imageModalEl = document.getElementById('noteImageModal');
    if (imageModalEl) {
        noteImageModal = new bootstrap.Modal(imageModalEl);
    }
    const imageEditModalEl = document.getElementById('noteImageEditModal');
    if (imageEditModalEl) {
        noteImageEditModal = new bootstrap.Modal(imageEditModalEl);
    }
    const imageViewModalEl = document.getElementById('noteImageViewModal');
    if (imageViewModalEl) {
        noteImageViewModal = new bootstrap.Modal(imageViewModalEl);
    }
    const confirmDeleteNoteEl1 = document.getElementById('confirmDeleteNoteModal1');
    if (confirmDeleteNoteEl1) {
        confirmDeleteNoteModal1 = new bootstrap.Modal(confirmDeleteNoteEl1);
    }
    const confirmDeleteNoteEl2 = document.getElementById('confirmDeleteNoteModal2');
    if (confirmDeleteNoteEl2) {
        confirmDeleteNoteModal2 = new bootstrap.Modal(confirmDeleteNoteEl2);
    }
    const confirmDeleteNoteEl3 = document.getElementById('confirmDeleteNoteModal3');
    if (confirmDeleteNoteEl3) {
        confirmDeleteNoteModal3 = new bootstrap.Modal(confirmDeleteNoteEl3);
    }
    const notePublicLinkEl = document.getElementById('notePublicLinkModal');
    if (notePublicLinkEl) {
        notePublicLinkModal = new bootstrap.Modal(notePublicLinkEl);
    }
    try { document.execCommand('styleWithCSS', false, true); } catch(e) {}

    // Detectar clic en imágenes del editor para verlas
    const editor = document.getElementById('noteContentEditor');
    if (editor) {
        editor.addEventListener('click', function(e) {
            const img = e.target.closest('img');
            if (img && editor.contains(img)) {
                e.preventDefault();
                e.stopPropagation();
                openImageView(img);
            }
        });
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

let notesFilteredData = [];

function filterNotesLive() {
    const input = document.getElementById('notesSearchInput');
    if (!input) return;
    const q = input.value.trim().toLowerCase();
    notesPage = 1;
    if (!q) {
        notesFilteredData = [];
        renderNotesList();
        return;
    }
    notesFilteredData = notesData.filter(n => {
        const inTitle = n.title.toLowerCase().includes(q);
        const inContent = stripHtml(n.content).toLowerCase().includes(q);
        const inDate = formatDate(n.updated_at).toLowerCase().includes(q) || formatDate(n.created_at).toLowerCase().includes(q);
        return inTitle || inContent || inDate;
    });
    renderNotesList();
}

function renderNotesList() {
    const container = document.getElementById('notesList');
    const dataToRender = notesFilteredData.length || document.getElementById('notesSearchInput')?.value.trim() ? notesFilteredData : notesData;
    if (!dataToRender.length) {
        container.innerHTML = `
            <div class="col-12 text-center py-4 text-muted">
                <i class="bi bi-journal fs-1 mb-2 d-block"></i>
                ${notesData.length ? 'No se encontraron notas' : 'No tienes notas aún'}
            </div>
        `;
        return;
    }
    const totalPages = Math.ceil(dataToRender.length / NOTES_PER_PAGE) || 1;
    if (notesPage > totalPages) notesPage = totalPages;
    const start = (notesPage - 1) * NOTES_PER_PAGE;
    const end = start + NOTES_PER_PAGE;
    const pageData = dataToRender.slice(start, end);
    
    let html = pageData.map(n => {
        const plainText = stripHtml(n.content);
        const preview = plainText.length > 150 ? plainText.substring(0, 150) + '...' : plainText;
        return `
        <div class="col-12 col-md-6">
            <div class="glass-panel rounded-3 p-3 h-100 position-relative">
                <h6 class="fw-bold text-dark mb-1">${escapeHtml(n.title)}</h6>
                <p class="small text-muted mb-2" style="display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical; overflow: hidden;">${escapeHtml(preview)}</p>
                <small class="text-secondary">Actualizado: ${formatDate(n.updated_at)}</small>
                <div class="position-absolute top-0 end-0 p-2 d-flex gap-1">
                    <button class="btn btn-sm btn-info rounded-circle" onclick="viewNote(${n.id})" title="Ver nota">
                        <i class="bi bi-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-light rounded-circle" onclick="editNote(${n.id})" title="Editar">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-danger rounded-circle" onclick="deleteNote(${n.id})" title="Eliminar">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </div>
        </div>
    `}).join('');
    
    if (totalPages > 1) {
        html += `
            <div class="col-12 d-flex justify-content-center align-items-center gap-2 mt-3">
                <button class="btn btn-sm btn-light rounded-pill" onclick="changeNotesPage(-1)" ${notesPage <= 1 ? 'disabled' : ''}>
                    <i class="bi bi-chevron-left"></i>
                </button>
                <span class="small text-muted">Página ${notesPage} de ${totalPages}</span>
                <button class="btn btn-sm btn-light rounded-pill" onclick="changeNotesPage(1)" ${notesPage >= totalPages ? 'disabled' : ''}>
                    <i class="bi bi-chevron-right"></i>
                </button>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

function changeNotesPage(delta) {
    const dataToRender = notesFilteredData.length || document.getElementById('notesSearchInput')?.value.trim() ? notesFilteredData : notesData;
    const totalPages = Math.ceil(dataToRender.length / NOTES_PER_PAGE) || 1;
    notesPage += delta;
    if (notesPage < 1) notesPage = 1;
    if (notesPage > totalPages) notesPage = totalPages;
    renderNotesList();
}

function createNewNote() {
    currentNoteId = null;
    document.getElementById('noteTitleInput').value = '';
    document.getElementById('noteContentEditor').innerHTML = '';
    document.getElementById('notesListContainer').classList.add('d-none');
    document.getElementById('noteEditorContainer').classList.remove('d-none');
    document.getElementById('createNoteBtnContainer').classList.add('d-none');
    document.getElementById('noteProgressContainer').classList.add('d-none');
    attachCheckboxListeners();
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
    attachCheckboxListeners();
    updateNoteProgress();
}

function cancelEdit() {
    currentNoteId = null;
    document.getElementById('notesListContainer').classList.remove('d-none');
    document.getElementById('noteEditorContainer').classList.add('d-none');
    document.getElementById('createNoteBtnContainer').classList.remove('d-none');
}

function viewNote(id) {
    const note = notesData.find(n => n.id === id);
    if (!note) return;
    currentViewNote = note;
    const headerTitle = document.getElementById('noteViewTitle');
    const bodyTitle = document.getElementById('noteViewBodyTitle');
    if (headerTitle) headerTitle.textContent = note.title;
    if (bodyTitle) bodyTitle.textContent = note.title;
    document.getElementById('noteViewContent').innerHTML = note.content;
    updateNoteViewProgress();
    if (noteViewModal) noteViewModal.show();
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
            listItems += `<li class="list-group-item d-flex align-items-start gap-2 p-2 todo-item" data-checked="false"><input class="form-check-input note-check flex-shrink-0" type="checkbox" id="${cid}" onchange="toggleTodoCheck(this)" contenteditable="false"><label class="form-check-label flex-grow-1" for="${cid}" contenteditable="true">${escapeHtml(line.trim())}</label></li>`;
        });
        document.execCommand('insertHTML', false, `<ul class="list-group list-group-flush todo-list mb-2">${listItems}</ul>`);
    } else {
        const html = `<ul class="list-group list-group-flush todo-list mb-2"><li class="list-group-item d-flex align-items-start gap-2 p-2 todo-item" data-checked="false"><input class="form-check-input note-check flex-shrink-0" type="checkbox" id="${id}" onchange="toggleTodoCheck(this)" contenteditable="false"><label class="form-check-label flex-grow-1" for="${id}" contenteditable="true">Nueva tarea</label></li></ul>`;
        document.execCommand('insertHTML', false, html);
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

function openImageView(img) {
    currentEditImage = img;
    const viewImg = document.getElementById('noteImageViewReal');
    if (viewImg) viewImg.src = img.src;
    if (noteImageViewModal) noteImageViewModal.show();
}

function openImageEditFromView() {
    if (!currentEditImage) return;
    if (noteImageViewModal) noteImageViewModal.hide();
    openImageEdit(currentEditImage);
}

function moveImageToTop() {
    if (!currentEditImage) return;
    const editor = document.getElementById('noteContentEditor');
    editor.insertBefore(currentEditImage, editor.firstChild);
    if (noteImageViewModal) noteImageViewModal.hide();
}

function moveImageToBottom() {
    if (!currentEditImage) return;
    const editor = document.getElementById('noteContentEditor');
    editor.appendChild(currentEditImage);
    if (noteImageViewModal) noteImageViewModal.hide();
}

function openImageEdit(img) {
    currentEditImage = img;
    const preview = document.getElementById('noteImageEditPreview');
    const sizeSlider = document.getElementById('noteImageEditSizeSlider');
    const blurSlider = document.getElementById('noteImageEditBlurSlider');
    const opacitySlider = document.getElementById('noteImageEditOpacitySlider');
    
    if (preview) preview.src = img.src;
    
    const style = img.getAttribute('style') || '';
    let currentWidth = 100;
    let currentBlur = 0;
    let currentOpacity = 100;
    
    const wMatch = style.match(/max-width:\s*(\d+)%/);
    if (wMatch) currentWidth = parseInt(wMatch[1], 10);
    const bMatch = style.match(/blur\((\d+(?:\.\d+)?)px\)/);
    if (bMatch) currentBlur = parseFloat(bMatch[1]);
    const oMatch = style.match(/opacity\((\d+)%\)/);
    if (oMatch) currentOpacity = parseInt(oMatch[1], 10);
    
    if (sizeSlider) sizeSlider.value = currentWidth;
    if (blurSlider) blurSlider.value = currentBlur;
    if (opacitySlider) opacitySlider.value = currentOpacity;
    
    updateImageEditPreview();
    if (noteImageEditModal) noteImageEditModal.show();
}

function updateImageEditPreview() {
    const sizeSlider = document.getElementById('noteImageEditSizeSlider');
    const blurSlider = document.getElementById('noteImageEditBlurSlider');
    const opacitySlider = document.getElementById('noteImageEditOpacitySlider');
    const preview = document.getElementById('noteImageEditPreview');
    const sizeValue = document.getElementById('noteImageEditSizeValue');
    const blurValue = document.getElementById('noteImageEditBlurValue');
    const opacityValue = document.getElementById('noteImageEditOpacityValue');
    
    if (sizeSlider) {
        if (preview) preview.style.maxWidth = sizeSlider.value + '%';
        if (sizeValue) sizeValue.textContent = sizeSlider.value + '%';
    }
    if (blurSlider) {
        if (blurValue) blurValue.textContent = blurSlider.value + 'px';
    }
    if (opacitySlider) {
        if (opacityValue) opacityValue.textContent = opacitySlider.value + '%';
    }
    
    if (preview && blurSlider && opacitySlider) {
        const filter = `blur(${blurSlider.value}px) opacity(${opacitySlider.value}%)`;
        preview.style.filter = filter;
    }
}

function applyImageEdit() {
    if (!currentEditImage) return;
    const sizeSlider = document.getElementById('noteImageEditSizeSlider');
    const blurSlider = document.getElementById('noteImageEditBlurSlider');
    const opacitySlider = document.getElementById('noteImageEditOpacitySlider');
    if (sizeSlider) currentEditImage.style.maxWidth = sizeSlider.value + '%';
    if (blurSlider && opacitySlider) {
        currentEditImage.style.filter = `blur(${blurSlider.value}px) opacity(${opacitySlider.value}%)`;
    }
    if (noteImageEditModal) noteImageEditModal.hide();
    currentEditImage = null;
}

function deleteImageEdit() {
    if (!currentEditImage) return;
    currentEditImage.remove();
    if (noteImageEditModal) noteImageEditModal.hide();
    currentEditImage = null;
}

function insertImage() {
    currentImageFile = null;
    document.getElementById('noteImageFile').value = '';
    document.getElementById('noteImagePreview').src = '';
    document.getElementById('noteImagePreviewContainer').classList.add('d-none');
    if (noteImageModal) noteImageModal.show();
}

function previewNoteImage(input) {
    if (input.files && input.files[0]) {
        currentImageFile = input.files[0];
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('noteImagePreview').src = e.target.result;
            document.getElementById('noteImagePreviewContainer').classList.remove('d-none');
            updateImageSizePreview();
        };
        reader.readAsDataURL(currentImageFile);
    }
}

function updateImageSizePreview() {
    const slider = document.getElementById('noteImageSizeSlider');
    const preview = document.getElementById('noteImagePreview');
    const valueDisplay = document.getElementById('noteImageSizeValue');
    if (slider) {
        if (preview) preview.style.maxWidth = slider.value + '%';
        if (valueDisplay) valueDisplay.textContent = slider.value + '%';
    }
}

async function applyNoteImage() {
    if (!currentImageFile) return;
    
    const formData = new FormData();
    formData.append('image', currentImageFile);
    
    try {
        const r = await fetch('/api/notes/upload-image', {
            method: 'POST',
            body: formData
        });
        const data = await r.json();
        if (data.ok) {
            const width = document.getElementById('noteImageSizeSlider')?.value || 100;
            document.getElementById('noteContentEditor').focus();
            document.execCommand('insertHTML', false, `<img src="${data.url}" class="img-fluid rounded-3 my-2 note-image" style="max-width: ${width}%;" alt="Imagen de nota">`);
            noteImageModal.hide();
            currentImageFile = null;
            document.getElementById('noteImageFile').value = '';
            document.getElementById('noteImagePreview').src = '';
            document.getElementById('noteImagePreviewContainer').classList.add('d-none');
        } else {
            alert(data.error || 'Error al subir imagen');
        }
    } catch (e) {
        console.error('Error subiendo imagen:', e);
        alert('Error de conexión al subir imagen');
    }
}

function toggleTodoCheck(checkbox) {
    const li = checkbox ? checkbox.closest('li') : null;
    if (!li) return;
    const checked = checkbox.checked;
    li.setAttribute('data-checked', checked ? 'true' : 'false');
    const label = li.querySelector('label');
    if (label) {
        label.classList.toggle('text-decoration-line-through', checked);
        label.classList.toggle('text-muted', checked);
    }
    updateNoteProgress();
    updateNoteViewProgress();
}

function updateNoteProgress() {
    updateNoteProgressFor('noteContentEditor', 'noteProgressText', 'noteProgressBar', 'noteProgressContainer');
}

function updateNoteViewProgress() {
    updateNoteProgressFor('noteViewContent', 'noteViewProgressText', 'noteViewProgressBar', 'noteViewProgressContainer');
}

function updateNoteProgressFor(contentId, textId, barId, containerId) {
    const container = document.getElementById(contentId);
    if (!container) return;
    const checks = container.querySelectorAll('input.note-check');
    const textEl = document.getElementById(textId);
    const barEl = document.getElementById(barId);
    const contEl = containerId ? document.getElementById(containerId) : null;
    if (checks.length === 0) {
        if (contEl) contEl.classList.add('d-none');
        return;
    }
    const checked = Array.from(checks).filter(c => c.checked).length;
    const percent = Math.round((checked / checks.length) * 100);
    if (contEl) contEl.classList.remove('d-none');
    if (textEl) textEl.textContent = `${checked}/${checks.length} - ${percent}%`;
    if (barEl) {
        barEl.style.width = `${percent}%`;
        barEl.setAttribute('aria-valuenow', percent);
    }
}

function attachCheckboxListeners() {
    const editor = document.getElementById('noteContentEditor');
    editor.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            const label = e.target.closest('label');
            if (label) {
                const li = label.closest('li');
                const ul = li ? li.closest('ul') : null;
                if (!ul) return;
                e.preventDefault();
                const id = 'note-check-' + Date.now() + '-' + Math.random().toString(36).substr(2, 5);
                const newLi = document.createElement('li');
                newLi.className = 'list-group-item d-flex align-items-center gap-2 p-2 todo-item';
                newLi.setAttribute('data-checked', 'false');
                newLi.innerHTML = `<input class="form-check-input note-check flex-shrink-0" type="checkbox" id="${id}" onchange="toggleTodoCheck(this)" contenteditable="false"><label class="form-check-label flex-grow-1" for="${id}" contenteditable="true">Nueva tarea</label>`;
                li.after(newLi);
                const newLabel = newLi.querySelector('label');
                if (newLabel) {
                    newLabel.focus();
                    const range = document.createRange();
                    range.selectNodeContents(newLabel);
                    range.collapse(true);
                    const sel = window.getSelection();
                    sel.removeAllRanges();
                    sel.addRange(range);
                }
                updateNoteProgress();
            }
        }
    });
    // Sincronizar estados visuales al cargar nota
    editor.querySelectorAll('input.note-check').forEach(ch => {
        const li = ch.closest('li');
        if (li) {
            const isChecked = li.getAttribute('data-checked') === 'true';
            ch.checked = isChecked;
            const label = li.querySelector('label');
            if (label) {
                label.classList.toggle('text-decoration-line-through', isChecked);
                label.classList.toggle('text-muted', isChecked);
            }
        }
    });
    updateNoteProgress();
}

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

// Image Export (JPG/PNG/PDF)
function exportNoteJPG() {
    exportNoteImage('image/jpeg', 'jpg');
}

function exportNotePNG() {
    exportNoteImage('image/png', 'png');
}

function exportNotePDF() {
    exportNoteToPDF(
        document.getElementById('noteTitleInput').value || 'nota',
        document.getElementById('noteContentEditor').innerHTML
    );
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

// View Modal Export Functions
function exportViewNoteJPG() {
    if (!currentViewNote) return;
    exportNoteImageFromData(currentViewNote.title, currentViewNote.content, 'image/jpeg', 'jpg');
}

function exportViewNotePNG() {
    if (!currentViewNote) return;
    exportNoteImageFromData(currentViewNote.title, currentViewNote.content, 'image/png', 'png');
}

function exportViewNotePDF() {
    if (!currentViewNote) return;
    exportNoteToPDF(currentViewNote.title, currentViewNote.content);
}

function exportViewNoteWhatsApp() {
    if (!currentViewNote) return;
    const text = `*${currentViewNote.title}*\n\n${stripHtml(currentViewNote.content)}`;
    const url = `https://wa.me/?text=${encodeURIComponent(text)}`;
    window.open(url, '_blank');
}

async function exportNoteImageFromData(title, content, format, ext) {
    // Crear contenedor temporal fuera de la vista para renderizar con html2canvas
    const temp = document.createElement('div');
    temp.style.width = '800px';
    temp.style.padding = '30px';
    temp.style.background = '#ffffff';
    temp.style.color = '#000000';
    temp.style.fontFamily = 'Arial, sans-serif';
    temp.style.position = 'fixed';
    temp.style.left = '-9999px';
    temp.style.top = '0';
    temp.style.zIndex = '-1';
    temp.innerHTML = `
        <div style="text-align:center; margin-bottom:10px;">
            <h2 style="margin:0; font-size:28px; font-weight:bold;">${escapeHtml(title)}</h2>
            <hr style="border:0; border-top:2px solid #ff8c00; margin:10px 0;">
        </div>
        <div id="exportNoteContent" style="font-size:16px; line-height:1.6;">${content}</div>
    `;
    document.body.appendChild(temp);
    
    try {
        const canvas = await html2canvas(temp, {
            scale: 2,
            useCORS: true,
            allowTaint: true,
            backgroundColor: '#ffffff',
            width: 800
        });
        const url = canvas.toDataURL(format);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${title.replace(/[^a-z0-9\u00C0-\u024F\u1E00-\u1EFF]/gi, '_')}.${ext}`;
        a.click();
    } catch (e) {
        console.error('Error exportando imagen:', e);
        alert('Error al generar la imagen. Verifica que html2canvas esté cargado.');
    } finally {
        document.body.removeChild(temp);
    }
}

function exportNoteImage(format, ext) {
    const title = document.getElementById('noteTitleInput').value || 'nota';
    const content = document.getElementById('noteContentEditor').innerHTML;
    exportNoteImageFromData(title, content, format, ext);
}

async function exportNoteToPDF(title, content) {
    const temp = document.createElement('div');
    temp.style.width = '800px';
    temp.style.padding = '30px';
    temp.style.background = '#ffffff';
    temp.style.color = '#000000';
    temp.style.fontFamily = 'Arial, sans-serif';
    temp.style.position = 'fixed';
    temp.style.left = '-9999px';
    temp.style.top = '0';
    temp.style.zIndex = '-1';
    temp.innerHTML = `
        <div style="text-align:center; margin-bottom:10px;">
            <h2 style="margin:0; font-size:28px; font-weight:bold;">${escapeHtml(title)}</h2>
            <hr style="border:0; border-top:2px solid #ff8c00; margin:10px 0;">
        </div>
        <div style="font-size:16px; line-height:1.6;">${content}</div>
    `;
    document.body.appendChild(temp);
    
    try {
        const canvas = await html2canvas(temp, {
            scale: 2,
            useCORS: true,
            allowTaint: true,
            backgroundColor: '#ffffff',
            width: 800
        });
        const imgData = canvas.toDataURL('image/jpeg', 0.95);
        const response = await fetch('/api/notes/export-pdf', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({title: title, image: imgData})
        });
        if (!response.ok) {
            const errJson = await response.json().catch(() => ({error: 'Error desconocido del servidor'}));
            console.error('Server PDF error:', errJson);
            throw new Error(errJson.error || 'Error del servidor');
        }
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${title.replace(/[^a-z0-9\u00C0-\u024F\u1E00-\u1EFF]/gi, '_')}.pdf`;
        a.click();
        URL.revokeObjectURL(url);
    } catch (e) {
        console.error('Error exportando PDF:', e);
        alert('Error al generar el PDF.');
    } finally {
        document.body.removeChild(temp);
    }
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
    // Convertir a zona horaria de Costa Rica (UTC-6)
    const options = {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        timeZone: 'America/Costa_Rica'
    };
    return d.toLocaleDateString('es-CR', options);
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
