// Picker de emojis para el editor de notas
(function() {
    'use strict';

    const EMOJIS = `
😀 😃 😄 😁 😆 😅 🤣 😂 🙂 🙃 😉 😊 😇 🥰 😍 🤩 😘 😗 😚 😙 😋 😛 😜 🤪 😝 🤑 🤗 🤭 🤫 🤔 🤐 🤨 😐 😑 😶 😏 😒 🙄 😬 🤥 😌 😔 😪 🤤 😴 😷 🤒 🤕 🤢 🤮 🤧 🥵 🥶 🥴 😵 🤯 🤠 🥳 😎 🤓 🧐 😕 😟 🙁 ☹️ 😮 😯 😲 😳 🥺 😦 😧 😨 😰 😥 😢 😭 😱 😖 😣 😞 😓 😩 😫 😤 😡 😠 🤬 😈 👿 💀 ☠️ 💩 🤡 👹 👺 👻 👽 👾 🤖 🙈 🙉 🙊
👍 👎 👊 ✊ 🤛 🤜 🤞 ✌️ 🤟 🤘 👌 🤏 👈 👉 👆 👇 ☝️ ✋ 🤚 🖐️ 🖖 👋 🤙 💪 🖕 ✍️ 🙏
❤️ 🧡 💛 💚 💙 💜 🖤 🤍 🤎 💔 💕 💞 💓 💗 💖 💘 💝 💟 💋 💌 💯 💢 💥 💫 💦 💨
🐶 🐱 🐭 🐹 🐰 🦊 🐻 🐼 🐨 🐯 🦁 🐮 🐷 🐸 🐵 🐔 🐧 🐦 🐤 🦆 🦅 🦉 🦇 🐺 🐴 🦄 🐝 🦋 🐞 🐜 🕷️ 🦕 🐙 🦀 🐠 🐬 🐳 🦈
🍏 🍎 🍌 🍉 🍓 🍍 🥑 🍕 🍔 🍟 🌭 🍿 🥗 🍜 🍣 🍰 🍫 ☕ 🍺 🍷
⚽ 🏀 🏈 🎾 🏐 🎱 🏓 🏸 🥊 🎽 🎿 🎪 🎨 🎧 🎵 🎶 🎹 🎸 🎺 🥁 🎬 🎮 🎰 🎲
🚗 🚕 🚙 🚌 🚓 🚑 🚒 🚚 🚛 🚜 🏍️ 🚲 🛴 🚨 ✈️ 🚀 🛸 🏠 🏡 🏢 🏰 🗼 🗽 ⛪
🖥️ 💻 📱 ☎️ 📺 📻 ⏰ 🔋 💡 💸 💵 💶 💰 💳 💎 🔧 🔨 🔩 ⚙️ 🔬 💊 💉 🧹 🛍️ 🛒 🎁 🎈 🎉 🏆 🥇 🥈 🥉
🌑 🌒 🌓 🌔 🌕 🌖 🌗 🌘 🌙 ☀️ 🌝 🌞 ⭐ 🌟 ✨ ⚡ 🔥 💥 ☄️ ⛅ 🌧️ ❄️ ☃️ 🌈 ☔ 💧 🌊
    `.replace(/\s+/g, ' ').trim().split(' ').filter(e => e);

    let pickerModal = null;
    let currentEditorId = null;
    let currentAlign = 'left';

    function buildEmojiGrid() {
        const grid = document.getElementById('emojiGrid');
        if (!grid) return;
        grid.innerHTML = '';
        EMOJIS.forEach(function(emoji) {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'btn btn-light p-0 m-0 border-0 rounded-2 emoji-item';
            btn.style = 'width: 38px; height: 38px; font-size: 1.5em; line-height: 1;';
            btn.textContent = emoji;
            btn.title = emoji;
            btn.onclick = function() { insertSelectedEmoji(emoji); };
            grid.appendChild(btn);
        });
    }

    function setEmojiAlign(align) {
        currentAlign = align;
        document.querySelectorAll('.emoji-align-btn').forEach(function(btn) {
            btn.classList.remove('btn-orange');
            btn.classList.add('btn-light');
            if (btn.dataset.align === align) {
                btn.classList.remove('btn-light');
                btn.classList.add('btn-orange');
            }
        });
    }

    function insertSelectedEmoji(emoji) {
        const editor = currentEditorId ? document.getElementById(currentEditorId) : null;
        if (!editor) return;
        editor.focus();
        let html;
        if (currentAlign === 'left') {
            html = '<span style="font-size:1.6em; line-height:1.2;">' + emoji + '</span>';
        } else {
            html = '<div style="text-align:' + currentAlign + '; font-size:1.6em; line-height:1.2;"><span>' + emoji + '</span></div>';
        }
        document.execCommand('insertHTML', false, html);
        if (pickerModal) pickerModal.hide();
        if (typeof updateNoteProgress === 'function') updateNoteProgress();
        if (typeof schedulePubSave === 'function') schedulePubSave();
    }

    window.openEmojiPicker = function(editorId) {
        currentEditorId = editorId;
        setEmojiAlign('left');
        if (!pickerModal) {
            const modalEl = document.getElementById('emojiPickerModal');
            if (modalEl && typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                pickerModal = new bootstrap.Modal(modalEl);
            }
        }
        if (pickerModal) pickerModal.show();
    };

    window.setEmojiAlign = setEmojiAlign;

    // ---- MENÚ CONTEXTUAL DE IMÁGENES ----
    let currentContextImage = null;
    let contextMenuEl = null;

    function getOrCreateImageContextMenu() {
        if (contextMenuEl) return contextMenuEl;
        contextMenuEl = document.createElement('div');
        contextMenuEl.className = 'position-fixed bg-white rounded-3 shadow-lg p-2 d-none';
        contextMenuEl.style.zIndex = '9999';
        contextMenuEl.style.minWidth = '160px';
        contextMenuEl.innerHTML = `
            <div class="small fw-bold text-muted mb-1">Alinear</div>
            <div class="d-flex gap-1 mb-2 justify-content-between">
                <button class="btn btn-sm btn-light rounded-pill" onclick="imgAlign('left')" title="Izquierda"><i class="bi bi-text-left"></i></button>
                <button class="btn btn-sm btn-light rounded-pill" onclick="imgAlign('center')" title="Centro"><i class="bi bi-text-center"></i></button>
                <button class="btn btn-sm btn-light rounded-pill" onclick="imgAlign('right')" title="Derecha"><i class="bi bi-text-right"></i></button>
            </div>
            <div class="small fw-bold text-muted mb-1">Tamaño</div>
            <div class="d-flex gap-1 mb-2">
                <button class="btn btn-sm btn-light rounded-pill flex-grow-1" onclick="imgResize(-10)" title="Reducir"><i class="bi bi-dash-lg"></i></button>
                <button class="btn btn-sm btn-light rounded-pill flex-grow-1" onclick="imgResize(10)" title="Aumentar"><i class="bi bi-plus-lg"></i></button>
            </div>
            <div class="small fw-bold text-muted mb-1">Capas</div>
            <div class="d-grid gap-1">
                <button class="btn btn-sm btn-light text-start" onclick="imgLayer('top')">Arriba del texto</button>
                <button class="btn btn-sm btn-light text-start" onclick="imgLayer('bottom')">Abajo del texto</button>
                <button class="btn btn-sm btn-light text-start" onclick="imgLayer('back')">Al fondo del texto</button>
                <button class="btn btn-sm btn-light text-start" onclick="imgLayer('front')">Por encima del texto</button>
            </div>
        `;
        document.body.appendChild(contextMenuEl);
        document.addEventListener('click', function(e) {
            if (contextMenuEl && !contextMenuEl.contains(e.target)) hideImageContextMenu();
        });
        document.addEventListener('scroll', hideImageContextMenu, true);
        return contextMenuEl;
    }

    function hideImageContextMenu() {
        if (contextMenuEl) contextMenuEl.classList.add('d-none');
    }

    function setupImageContextMenu() {
        ['noteContentEditor', 'pubContentEditor'].forEach(function(id) {
            const editor = document.getElementById(id);
            if (!editor) return;
            editor.addEventListener('contextmenu', function(e) {
                const img = e.target.closest('img');
                if (!img) return;
                e.preventDefault();
                currentContextImage = img;
                const menu = getOrCreateImageContextMenu();
                const x = Math.min(e.clientX, window.innerWidth - 170);
                const y = Math.min(e.clientY, window.innerHeight - 240);
                menu.style.left = x + 'px';
                menu.style.top = y + 'px';
                menu.classList.remove('d-none');
            });
        });
    }

    window.imgAlign = function(align) {
        if (!currentContextImage) return;
        currentContextImage.style.position = 'relative';
        currentContextImage.style.zIndex = '0';
        currentContextImage.style.opacity = '1';
        if (align === 'left') {
            currentContextImage.style.float = 'left';
            currentContextImage.style.margin = '0 10px 10px 0';
            currentContextImage.style.display = 'inline-block';
            currentContextImage.style.clear = 'none';
        } else if (align === 'right') {
            currentContextImage.style.float = 'right';
            currentContextImage.style.margin = '0 0 10px 10px';
            currentContextImage.style.display = 'inline-block';
            currentContextImage.style.clear = 'none';
        } else if (align === 'center') {
            currentContextImage.style.float = 'none';
            currentContextImage.style.display = 'block';
            currentContextImage.style.margin = '10px auto';
            currentContextImage.style.clear = 'both';
        }
        hideImageContextMenu();
        if (typeof schedulePubSave === 'function') schedulePubSave();
    };

    window.imgResize = function(delta) {
        if (!currentContextImage) return;
        const parent = currentContextImage.parentElement || currentContextImage;
        const parentWidth = parent.clientWidth || currentContextImage.clientWidth;
        const currentPct = (currentContextImage.clientWidth / parentWidth) * 100;
        let newPct = currentPct + delta;
        if (newPct < 20) newPct = 20;
        if (newPct > 100) newPct = 100;
        currentContextImage.style.width = newPct + '%';
        currentContextImage.style.maxWidth = '100%';
        hideImageContextMenu();
        if (typeof schedulePubSave === 'function') schedulePubSave();
    };

    window.imgLayer = function(layer) {
        if (!currentContextImage) return;
        currentContextImage.style.position = 'relative';
        if (layer === 'top') {
            currentContextImage.style.verticalAlign = 'top';
            currentContextImage.style.zIndex = '0';
            currentContextImage.style.opacity = '1';
        } else if (layer === 'bottom') {
            currentContextImage.style.verticalAlign = 'bottom';
            currentContextImage.style.zIndex = '0';
            currentContextImage.style.opacity = '1';
        } else if (layer === 'back') {
            currentContextImage.style.zIndex = '-1';
            currentContextImage.style.opacity = '0.5';
        } else if (layer === 'front') {
            currentContextImage.style.zIndex = '10';
            currentContextImage.style.opacity = '1';
        }
        hideImageContextMenu();
        if (typeof schedulePubSave === 'function') schedulePubSave();
    };

    document.addEventListener('DOMContentLoaded', buildEmojiGrid);
    document.addEventListener('DOMContentLoaded', setupImageContextMenu);
})();
