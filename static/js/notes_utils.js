// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
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
            const newText = after ? escapeHtml(after) : 'Nueva tarea';
            newLi.innerHTML = `<input class="form-check-input note-check flex-shrink-0" type="checkbox" onchange="toggleTodoCheck(this)" contenteditable="false"><span class="form-check-label flex-grow-1">${newText}</span><button class="btn btn-sm btn-link text-danger p-0 ms-1" type="button" onclick="deleteTodoItem(this)" contenteditable="false" tabindex="-1"><i class="bi bi-trash"></i></button>`;
            li.after(newLi);
            const newLabel = newLi.querySelector('.form-check-label');
            if (newLabel) {
                const newRange = document.createRange();
                newRange.selectNodeContents(newLabel);
                if (after) newRange.collapse(true);
                sel.removeAllRanges();
                sel.addRange(newRange);
            }
            updateNoteProgress();
            scheduleNoteAutoSave();
        }
    });
    // Sincronizar estados visuales al cargar nota
    editor.querySelectorAll('input.note-check').forEach(ch => {
        const li = ch.closest('li');
        if (li) {
            const isChecked = li.getAttribute('data-checked') === 'true';
            ch.checked = isChecked;
            const label = li.querySelector('.form-check-label');
            if (label) {
                label.classList.toggle('text-decoration-line-through', isChecked);
                label.classList.toggle('text-muted', isChecked);
            }
        }
    });
    updateNoteProgress();
    normalizeTodoItems(editor);
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

function htmlToWhatsApp(html) {
    const tmp = document.createElement('div');
    tmp.innerHTML = html;
    return convertNodeToWhatsApp(tmp).replace(/\n{3,}/g, '\n\n').trim();
}

function convertNodeToWhatsApp(node) {
    let out = '';
    Array.from(node.childNodes).forEach(child => {
        if (child.nodeType === 3) {
            out += child.textContent
                .replace(/\*/g, '\\*')
                .replace(/_/g, '\\_')
                .replace(/~/g, '\\~')
                .replace(/`/g, '\\`');
            return;
        }
        if (child.nodeType !== 1) return;
        const tag = child.tagName.toLowerCase();
        if (tag === 'br') {
            out += '\n';
        } else if (tag === 'h1' || tag === 'h2' || tag === 'h3' || tag === 'h4' || tag === 'h5' || tag === 'h6') {
            out += '*' + convertNodeToWhatsApp(child).trim() + '*\n';
        } else if (tag === 'p' || tag === 'div') {
            const text = convertNodeToWhatsApp(child).trim();
            if (text) out += text + '\n';
        } else if (tag === 'b' || tag === 'strong') {
            out += '*' + convertNodeToWhatsApp(child).trim() + '*';
        } else if (tag === 'i' || tag === 'em') {
            out += '_' + convertNodeToWhatsApp(child).trim() + '_';
        } else if (tag === 's' || tag === 'strike' || tag === 'del') {
            out += '~' + convertNodeToWhatsApp(child).trim() + '~';
        } else if (tag === 'u') {
            out += convertNodeToWhatsApp(child);
        } else if (tag === 'a') {
            const href = child.getAttribute('href') || '';
            out += convertNodeToWhatsApp(child).trim() + ' (' + href + ')';
        } else if (tag === 'img') {
            out += '[imagen]';
        } else if (tag === 'hr') {
            out += '---\n';
        } else if (tag === 'ul' || tag === 'ol') {
            Array.from(child.children).forEach((li, idx) => {
                if (li.tagName.toLowerCase() !== 'li') return;
                if (li.classList.contains('todo-item')) {
                    const cb = li.querySelector('input.note-check');
                    const checked = cb && (cb.checked || cb.hasAttribute('checked') || li.getAttribute('data-checked') === 'true');
                    const label = li.querySelector('.form-check-label');
                    const text = label ? label.textContent : convertNodeToWhatsApp(li);
                    out += (checked ? '[x]' : '[ ]') + ' ' + text.trim() + '\n';
                } else {
                    const marker = tag === 'ul' ? '•' : (idx + 1) + '.';
                    out += marker + ' ' + convertNodeToWhatsApp(li).trim() + '\n';
                }
            });
        } else if (tag === 'li') {
            if (child.classList.contains('todo-item')) {
                const cb = child.querySelector('input.note-check');
                const checked = cb && (cb.checked || cb.hasAttribute('checked') || child.getAttribute('data-checked') === 'true');
                const label = child.querySelector('.form-check-label');
                const text = label ? label.textContent : convertNodeToWhatsApp(child);
                out += (checked ? '[x]' : '[ ]') + ' ' + text.trim() + '\n';
            } else {
                out += '• ' + convertNodeToWhatsApp(child).trim() + '\n';
            }
        } else if (tag === 'span') {
            if (child.classList.contains('text-decoration-line-through')) {
                out += '~' + convertNodeToWhatsApp(child).trim() + '~';
            } else {
                out += convertNodeToWhatsApp(child);
            }
        } else {
            out += convertNodeToWhatsApp(child);
        }
    });
    return out;
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
