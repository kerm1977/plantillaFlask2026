// Edición colaborativa en tiempo real para notas (Socket.IO)
(function() {
    'use strict';

    let socket = null;
    let currentRoom = null;
    let currentEditorId = null;
    let applyingRemote = false;
    let broadcastTimeout = null;
    let boundInputFn = null;
    let boundCursorFn = null;
    const clientId = 'c-' + Math.random().toString(36).substr(2, 9);
    const clientColor = ['#ff8c00', '#0d6efd', '#20c997', '#e83e8c', '#6f42c1', '#fd7e14'][Math.floor(Math.random() * 6)];
    const remoteCursors = {};

    function ensureSocket() {
        if (socket) return socket;
        if (typeof io === 'undefined') return null;
        socket = io();
        socket.on('note_edit', function(data) {
            if (!data || data.clientId === clientId) return;
            applyRemoteContent(data.content);
        });
        socket.on('note_cursor', function(data) {
            if (!data || data.clientId === clientId) return;
            showRemoteCursor(data);
        });
        return socket;
    }

    function getCaretCharacterOffset(element) {
        let caretOffset = 0;
        const sel = window.getSelection();
        if (sel && sel.rangeCount > 0 && element.contains(sel.anchorNode)) {
            const range = sel.getRangeAt(0).cloneRange();
            range.selectNodeContents(element);
            range.setEnd(sel.anchorNode, sel.anchorOffset);
            caretOffset = range.toString().length;
        }
        return caretOffset;
    }

    function restoreCaretPosition(element, offset) {
        const range = document.createRange();
        range.selectNodeContents(element);
        let nodeStack = [element], node, charCount = 0, found = false;
        while (!found && (node = nodeStack.pop())) {
            if (node.nodeType === 3) {
                const nextCharCount = charCount + node.length;
                if (offset >= charCount && offset <= nextCharCount) {
                    range.setStart(node, offset - charCount);
                    range.collapse(true);
                    found = true;
                }
                charCount = nextCharCount;
            } else {
                let i = node.childNodes.length;
                while (i--) nodeStack.push(node.childNodes[i]);
            }
        }
        if (found) {
            const sel = window.getSelection();
            sel.removeAllRanges();
            sel.addRange(range);
        }
    }

    function applyRemoteContent(html) {
        const editor = document.getElementById(currentEditorId);
        if (!editor || html === undefined) return;
        if (editor.innerHTML === html) return;
        const isFocused = document.activeElement === editor;
        const savedOffset = isFocused ? getCaretCharacterOffset(editor) : null;
        applyingRemote = true;
        editor.innerHTML = html;
        if (isFocused && savedOffset !== null) {
            try { restoreCaretPosition(editor, savedOffset); } catch (e) {}
        }
        applyingRemote = false;
        if (typeof attachCheckboxListeners === 'function') attachCheckboxListeners();
        if (typeof updateNoteProgress === 'function') updateNoteProgress();
        editor.querySelectorAll('input.note-check').forEach(function(ch) {
            const li = ch.closest('li');
            if (li) ch.checked = li.getAttribute('data-checked') === 'true';
        });
    }

    function positionFlagAtOffset(editor, flag, offset) {
        try {
            const range = document.createRange();
            let nodeStack = [editor], node, charCount = 0, found = false;
            while (!found && (node = nodeStack.pop())) {
                if (node.nodeType === 3) {
                    const next = charCount + node.length;
                    if (offset >= charCount && offset <= next) {
                        range.setStart(node, Math.max(0, offset - charCount));
                        range.collapse(true);
                        found = true;
                    }
                    charCount = next;
                } else {
                    let i = node.childNodes.length;
                    while (i--) nodeStack.push(node.childNodes[i]);
                }
            }
            if (!found) return;
            const rect = range.getBoundingClientRect();
            if (!rect || (rect.top === 0 && rect.left === 0)) return;
            flag.style.left = (rect.left + window.scrollX) + 'px';
            flag.style.top = (rect.top + window.scrollY - 22) + 'px';
        } catch (e) {}
    }

    function showRemoteCursor(data) {
        const editor = document.getElementById(currentEditorId);
        if (!editor) return;
        let flag = remoteCursors[data.clientId];
        if (!flag) {
            flag = document.createElement('div');
            flag.className = 'collab-cursor-flag';
            flag.style.position = 'absolute';
            flag.style.background = data.color || '#ff8c00';
            flag.style.color = '#fff';
            flag.style.fontSize = '0.65rem';
            flag.style.fontWeight = '600';
            flag.style.padding = '2px 8px';
            flag.style.borderRadius = '10px';
            flag.style.zIndex = '20';
            flag.style.pointerEvents = 'none';
            flag.style.whiteSpace = 'nowrap';
            flag.style.boxShadow = '0 2px 6px rgba(0,0,0,0.25)';
            flag.textContent = '✏️ Escribiendo...';
            document.body.appendChild(flag);
            remoteCursors[data.clientId] = flag;
        }
        positionFlagAtOffset(editor, flag, data.offset || 0);
        clearTimeout(flag.__hideTimeout);
        flag.__hideTimeout = setTimeout(function() {
            flag.remove();
            delete remoteCursors[data.clientId];
        }, 3000);
    }

    function broadcastContent() {
        if (!socket || !currentRoom || applyingRemote) return;
        const editor = document.getElementById(currentEditorId);
        if (!editor) return;
        clearTimeout(broadcastTimeout);
        broadcastTimeout = setTimeout(function() {
            socket.emit('note_edit', {room: currentRoom, content: editor.innerHTML, clientId: clientId});
        }, 300);
    }

    function broadcastCursor() {
        if (!socket || !currentRoom) return;
        const editor = document.getElementById(currentEditorId);
        if (!editor) return;
        const offset = getCaretCharacterOffset(editor);
        socket.emit('note_cursor', {room: currentRoom, offset: offset, clientId: clientId, color: clientColor});
    }

    window.collabLeave = function() {
        const editor = currentEditorId ? document.getElementById(currentEditorId) : null;
        if (editor && boundInputFn) editor.removeEventListener('input', boundInputFn);
        if (editor && boundCursorFn) {
            editor.removeEventListener('keyup', boundCursorFn);
            editor.removeEventListener('click', boundCursorFn);
        }
        if (socket && currentRoom) socket.emit('leave_note', {room: currentRoom});
        Object.values(remoteCursors).forEach(function(f) { f.remove(); });
        Object.keys(remoteCursors).forEach(function(k) { delete remoteCursors[k]; });
        currentRoom = null;
        currentEditorId = null;
        boundInputFn = null;
        boundCursorFn = null;
    };

    window.collabJoin = function(room, editorId) {
        if (!room || !editorId) return;
        window.collabLeave();
        ensureSocket();
        if (!socket) return;
        currentRoom = room;
        currentEditorId = editorId;
        socket.emit('join_note', {room: room});
        const editor = document.getElementById(editorId);
        if (!editor) return;
        boundInputFn = broadcastContent;
        boundCursorFn = broadcastCursor;
        editor.addEventListener('input', boundInputFn);
        editor.addEventListener('keyup', boundCursorFn);
        editor.addEventListener('click', boundCursorFn);
    };
})();
