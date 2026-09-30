// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
        let pubSaveTimeout = null;
        let pubDeferredInstallEvent = null;
        let pubConfirmDeleteTodoModal = null;
        let pubTodoToDeleteBtn = null;

        window.addEventListener('beforeinstallprompt', function(e) {
            e.preventDefault();
            pubDeferredInstallEvent = e;
            const btn = document.getElementById('pubInstallBtn');
            if (btn) btn.style.display = 'inline-block';
        });

        function pubInstallShortcut() {
            if (pubDeferredInstallEvent) {
                pubDeferredInstallEvent.prompt();
                pubDeferredInstallEvent.userChoice.finally(() => {
                    pubDeferredInstallEvent = null;
                    const btn = document.getElementById('pubInstallBtn');
                    if (btn) btn.style.display = 'none';
                });
            } else {
                const isIOS = /iphone|ipad|ipod/i.test(navigator.userAgent);
                if (isIOS) {
                    alert('En iPhone/iPad: toca el botón "Compartir" y luego "Agregar a pantalla de inicio".');
                } else {
                    alert('Abre el menú de tu navegador (⋮) y selecciona "Instalar app" o "Agregar a pantalla de inicio".');
                }
            }
        }

        document.addEventListener('DOMContentLoaded', function() {
            try { document.execCommand('styleWithCSS', false, true); } catch(e) {}
            const editor = document.getElementById('pubContentEditor');
            const titleInput = document.getElementById('pubTitleInput');
            const pubConfirmDeleteTodoEl = document.getElementById('pubConfirmDeleteTodoModal');
            if (pubConfirmDeleteTodoEl) {
                pubConfirmDeleteTodoModal = new bootstrap.Modal(pubConfirmDeleteTodoEl);
            }
            editor.addEventListener('input', schedulePubSave);
            editor.addEventListener('keydown', pubHandleEnter);
            titleInput.addEventListener('input', schedulePubSave);
            editor.querySelectorAll('input.note-check').forEach(ch => {
                const li = ch.closest('li');
                if (li) {
                    const isChecked = li.getAttribute('data-checked') === 'true';
                    ch.checked = isChecked;
                }
            });
            pubNormalizeTodoItems(editor);
            if (typeof collabJoin === 'function') {
                collabJoin('pub-' + PUB_TOKEN, 'pubContentEditor');
            }
        });

        function pubExecCmd(command) {
            try { document.execCommand('styleWithCSS', false, true); } catch(e) {}
            document.execCommand(command, false, null);
            document.getElementById('pubContentEditor').focus();
            schedulePubSave();
        }

        function pubInsertCheckbox() {
            const editor = document.getElementById('pubContentEditor');
            editor.focus();
            const html = `<ul class="list-group list-group-flush todo-list mb-2"><li class="list-group-item d-flex align-items-start gap-2 p-2 todo-item" data-checked="false"><input class="form-check-input note-check flex-shrink-0" type="checkbox" onchange="pubToggleCheck(this)" contenteditable="false"><span class="form-check-label flex-grow-1 new-todo-focus">Nueva tarea</span><button class="btn btn-sm btn-link text-danger p-0 ms-1" type="button" onclick="pubDeleteTodoItem(this)" contenteditable="false" tabindex="-1"><i class="bi bi-trash"></i></button></li></ul>`;
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
            schedulePubSave();
        }

        function pubToggleCheck(checkbox) {
            const li = checkbox.closest('li');
            if (!li) return;
            li.setAttribute('data-checked', checkbox.checked ? 'true' : 'false');
            schedulePubSave();
        }

        function pubDeleteTodoItem(btn) {
            pubTodoToDeleteBtn = btn;
            if (pubConfirmDeleteTodoModal) {
                pubConfirmDeleteTodoModal.show();
            } else {
                const li = btn.closest('li');
                if (li) {
                    li.remove();
                    schedulePubSave();
                }
                pubTodoToDeleteBtn = null;
            }
        }

        function pubConfirmDeleteTodo() {
            if (pubConfirmDeleteTodoModal) pubConfirmDeleteTodoModal.hide();
            if (pubTodoToDeleteBtn) {
                const li = pubTodoToDeleteBtn.closest('li');
                if (li) {
                    li.remove();
                    schedulePubSave();
                }
            }
            pubTodoToDeleteBtn = null;
        }

        function pubCancelDeleteTodo() {
            pubTodoToDeleteBtn = null;
            if (pubConfirmDeleteTodoModal) pubConfirmDeleteTodoModal.hide();
        }

        function pubNormalizeTodoItems(editor) {
            editor.querySelectorAll('li.todo-item').forEach(li => {
                const input = li.querySelector('input.note-check');
                const label = li.querySelector('.form-check-label');
                if (input) {
                    input.setAttribute('contenteditable', 'false');
                    input.setAttribute('onchange', 'pubToggleCheck(this)');
                    input.removeAttribute('id');
                }
                if (label) {
                    label.removeAttribute('contenteditable');
                    label.removeAttribute('for');
                    label.classList.remove('new-todo-focus');
                }
                if (!li.querySelector('button[onclick^="pubDeleteTodoItem"]')) {
                    const btn = document.createElement('button');
                    btn.className = 'btn btn-sm btn-link text-danger p-0 ms-1';
                    btn.type = 'button';
                    btn.setAttribute('contenteditable', 'false');
                    btn.setAttribute('tabindex', '-1');
                    btn.setAttribute('onclick', 'pubDeleteTodoItem(this)');
                    btn.innerHTML = '<i class="bi bi-trash"></i>';
                    li.appendChild(btn);
                }
            });
        }

        function pubInsertLink() {
            const text = window.getSelection().toString();
            const displayText = text || prompt('Texto del enlace:', '');
            if (displayText === null) return;
            let url = prompt('URL del enlace (https://...):', '');
            if (!url) return;
            if (!/^https?:\/\//i.test(url)) url = 'https://' + url;
            document.getElementById('pubContentEditor').focus();
            document.execCommand('insertHTML', false, `<a href="${url}" target="_blank" rel="noopener">${displayText || url}</a>`);
            schedulePubSave();
        }

        async function pubUploadImage(input) {
            const file = input.files[0];
            if (!file) return;
            const formData = new FormData();
            formData.append('image', file);
            try {
                const r = await fetch(`/api/notes/public/${PUB_TOKEN}/upload-image`, {method: 'POST', body: formData});
                const data = await r.json();
                if (data.ok) {
                    document.getElementById('pubContentEditor').focus();
                    document.execCommand('insertHTML', false, `<img src="${data.url}" class="img-fluid rounded-3 my-2" style="max-width:100%;" alt="Imagen">`);
                    schedulePubSave();
                } else {
                    alert(data.error || 'Error al subir imagen');
                }
            } catch(e) {
                alert('Error de conexión al subir imagen');
            }
            input.value = '';
        }

        function pubHandleEnter(e) {
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
                const newText = after ? escapeHtmlTodoPub(after) : 'Nueva tarea';
                newLi.innerHTML = `<input class="form-check-input note-check flex-shrink-0" type="checkbox" onchange="pubToggleCheck(this)" contenteditable="false"><span class="form-check-label flex-grow-1">${newText}</span><button class="btn btn-sm btn-link text-danger p-0 ms-1" type="button" onclick="pubDeleteTodoItem(this)" contenteditable="false" tabindex="-1"><i class="bi bi-trash"></i></button>`;
                li.after(newLi);
                const newLabel = newLi.querySelector('.form-check-label');
                if (newLabel) {
                    const newRange = document.createRange();
                    newRange.selectNodeContents(newLabel);
                    if (after) newRange.collapse(true);
                    sel.removeAllRanges();
                    sel.addRange(newRange);
                }
                schedulePubSave();
            }
        }

        function escapeHtmlTodoPub(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function schedulePubSave() {
            const statusEl = document.getElementById('pubSaveStatus');
            if (statusEl) statusEl.textContent = 'Escribiendo...';
            clearTimeout(pubSaveTimeout);
            pubSaveTimeout = setTimeout(savePublicNote, 900);
        }

        async function savePublicNote() {
            const statusEl = document.getElementById('pubSaveStatus');
            const title = document.getElementById('pubTitleInput').value.trim() || 'Sin título';
            const content = document.getElementById('pubContentEditor').innerHTML;
            try {
                const r = await fetch(`/api/notes/public/${PUB_TOKEN}`, {
                    method: 'PUT',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({title, content})
                });
                const data = await r.json();
                if (data.ok && statusEl) {
                    statusEl.innerHTML = '<i class="bi bi-check-circle text-success me-1"></i>Guardado';
                    setTimeout(() => { if (statusEl.textContent.includes('Guardado')) statusEl.textContent = ''; }, 2000);
                }
            } catch(e) {
                if (statusEl) statusEl.innerHTML = '<i class="bi bi-exclamation-circle text-danger me-1"></i>Error al guardar';
            }
        }
