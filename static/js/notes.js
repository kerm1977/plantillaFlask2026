// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
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
let noteOptionsModal = null;
let confirmDeleteTodoModal = null;
let todoToDeleteBtn = null;

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
    const noteOptionsEl = document.getElementById('noteOptionsModal');
    if (noteOptionsEl) {
        noteOptionsModal = new bootstrap.Modal(noteOptionsEl);
    }
    const confirmDeleteTodoEl = document.getElementById('confirmDeleteTodoModal');
    if (confirmDeleteTodoEl) {
        confirmDeleteTodoModal = new bootstrap.Modal(confirmDeleteTodoEl);
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
    setupNoteAutoSaveListeners();
    if (typeof collabLeave === 'function') collabLeave();
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
    setupNoteAutoSaveListeners();
    if (typeof collabJoin === 'function') collabJoin('note-' + id, 'noteContentEditor');
}

function setupNoteAutoSaveListeners() {
    const editor = document.getElementById('noteContentEditor');
    const titleInput = document.getElementById('noteTitleInput');
    if (editor) editor.oninput = scheduleNoteAutoSave;
    if (titleInput) titleInput.oninput = scheduleNoteAutoSave;
}

