// BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
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

function deleteImageFromView() {
    if (!currentEditImage) return;
    currentEditImage.remove();
    currentEditImage = null;
    if (noteImageViewModal) noteImageViewModal.hide();
    updateNoteProgress();
    scheduleNoteAutoSave();
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
    const label = li.querySelector('.form-check-label');
    if (label) {
        label.classList.toggle('text-decoration-line-through', checked);
        label.classList.toggle('text-muted', checked);
    }
    updateNoteProgress();
    updateNoteViewProgress();
}

function deleteTodoItem(btn) {
    todoToDeleteBtn = btn;
    if (confirmDeleteTodoModal) {
        confirmDeleteTodoModal.show();
    } else {
        const li = btn.closest('li');
        if (li) {
            li.remove();
            updateNoteProgress();
            scheduleNoteAutoSave();
        }
        todoToDeleteBtn = null;
    }
}

function confirmDeleteTodo() {
    if (confirmDeleteTodoModal) confirmDeleteTodoModal.hide();
    if (todoToDeleteBtn) {
        const li = todoToDeleteBtn.closest('li');
        if (li) {
            li.remove();
            updateNoteProgress();
            scheduleNoteAutoSave();
        }
    }
    todoToDeleteBtn = null;
}

function cancelDeleteTodo() {
    todoToDeleteBtn = null;
    if (confirmDeleteTodoModal) confirmDeleteTodoModal.hide();
}

function normalizeTodoItems(editor) {
    editor.querySelectorAll('li.todo-item').forEach(li => {
        const input = li.querySelector('input.note-check');
        const label = li.querySelector('.form-check-label');
        if (input) {
            input.setAttribute('contenteditable', 'false');
            input.setAttribute('onchange', 'toggleTodoCheck(this)');
            input.removeAttribute('id');
        }
        if (label) {
            label.removeAttribute('contenteditable');
            label.removeAttribute('for');
            label.classList.remove('new-todo-focus');
        }
        if (!li.querySelector('button[onclick^="deleteTodoItem"]')) {
            const btn = document.createElement('button');
            btn.className = 'btn btn-sm btn-link text-danger p-0 ms-1';
            btn.type = 'button';
            btn.setAttribute('contenteditable', 'false');
            btn.setAttribute('tabindex', '-1');
            btn.setAttribute('onclick', 'deleteTodoItem(this)');
            btn.innerHTML = '<i class="bi bi-trash"></i>';
            li.appendChild(btn);
        }
    });
}

