// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
// Mini-Dropbox del dashboard: lista/sube/renombra/mueve/borra en uploads.
(function () {
    'use strict';
    let _files = [], _folders = [], _tipo = 'todas', _movePath = null;

    const $ = id => document.getElementById(id);
    const esc = s => String(s).replace(/[&<>"']/g, c =>
        ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    const fmtSize = b => b > 1048576 ? (b / 1048576).toFixed(1) + ' MB'
        : b > 1024 ? (b / 1024).toFixed(0) + ' KB' : b + ' B';

    function msg(text, ok) {
        const m = $('mmMsg');
        m.className = 'small mb-2 fw-semibold ' + (ok ? 'text-success' : 'text-danger');
        m.textContent = text;
        if (ok) setTimeout(() => m.classList.add('d-none'), 3000);
    }

    async function api(url, opts) {
        const r = await fetch(url, opts);
        const d = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(d.error || 'Error ' + r.status);
        return d;
    }

    async function cargar() {
        try {
            const d = await api('/api/multimedia/list');
            _files = d.files; _folders = d.folders;
            renderFiltros(); render();
        } catch (e) { msg(e.message, false); }
    }

    function renderFiltros() {
        const c = { imagen: 0, video: 0, audio: 0, otro: 0 };
        _files.forEach(f => c[f.tipo]++);
        $('mmTotalBadge').textContent = _files.length;
        $('mmAll').textContent = '(' + _files.length + ')';
        $('mmImg').textContent = '(' + c.imagen + ')';
        $('mmVid').textContent = '(' + c.video + ')';
        $('mmAud').textContent = '(' + c.audio + ')';
        $('mmOtr').textContent = '(' + c.otro + ')';
        const sel = $('mmFolderFilter'), cur = sel.value;
        sel.innerHTML = '<option value="">📂 Todas las carpetas</option>' +
            '<option value="__root__">📂 Raíz (uploads)</option>' +
            _folders.map(f => `<option value="${esc(f)}">📁 ${esc(f)}</option>`).join('');
        sel.value = cur;
    }

    function icono(f) {
        if (f.tipo === 'imagen')
            return `<img src="${f.url}" class="mm-thumb" loading="lazy" alt="">`;
        const ic = { video: 'bi-film text-danger', audio: 'bi-music-note-beamed text-primary' }[f.tipo]
            || 'bi-file-earmark text-secondary';
        const bg = { video: '#fdecec', audio: '#eef3ff' }[f.tipo] || '#f1f3f5';
        return `<div class="mm-icon" style="background:${bg}"><i class="bi ${ic}"></i></div>`;
    }

    function render() {
        const q = ($('mmSearch').value || '').toLowerCase();
        const fold = $('mmFolderFilter').value;
        const lista = _files.filter(f =>
            (_tipo === 'todas' || f.tipo === _tipo) &&
            (!q || f.name.toLowerCase().includes(q)) &&
            (!fold || (fold === '__root__' ? !f.folder : f.folder === fold)));
        $('mmGrid').innerHTML = lista.map(f => `
        <div class="col-6 col-md-3 col-lg-2">
          <div class="mm-file">
            <a href="${f.url}" target="_blank" title="Abrir">${icono(f)}</a>
            <div class="p-2">
              <div class="mm-name" title="${esc(f.path)}">${esc(f.name)}</div>
              <div class="d-flex justify-content-between align-items-center mt-1">
                <span class="badge text-bg-light mm-badge">${f.folder ? esc(f.folder) : 'raíz'}</span>
                <span class="text-muted" style="font-size:.62rem;">${fmtSize(f.size)}</span>
              </div>
              <div class="mm-actions d-flex gap-1 mt-1">
                <button class="btn btn-outline-secondary" title="Renombrar" onclick="mmRenombrar('${esc(f.path)}','${esc(f.name)}')"><i class="bi bi-pencil"></i></button>
                <button class="btn btn-outline-secondary" title="Mover" onclick="mmAbrirMove('${esc(f.path)}')"><i class="bi bi-folder-symlink"></i></button>
                <a class="btn btn-outline-secondary" title="Descargar" href="${f.url}" download="${esc(f.name)}"><i class="bi bi-download"></i></a>
                <button class="btn btn-outline-danger ms-auto" title="Eliminar" onclick="mmEliminar('${esc(f.path)}')"><i class="bi bi-trash"></i></button>
              </div>
            </div>
          </div>
        </div>`).join('') ||
            '<div class="col-12 text-center text-muted py-4">Sin archivos</div>';
    }

    // ---- Acciones (globales para onclick) ----
    window.mmRenombrar = async function (path, name) {
        const nuevo = prompt('Nuevo nombre:', name);
        if (!nuevo || nuevo === name) return;
        try { await api('/api/multimedia/rename', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ path, name: nuevo }) }); msg('Renombrado ✓', true); cargar(); }
        catch (e) { msg(e.message, false); }
    };

    window.mmAbrirMove = function (path) {
        _movePath = path;
        $('mmMoveName').textContent = path;
        $('mmMoveFolder').innerHTML = '<option value="">📂 Raíz (uploads)</option>' +
            _folders.map(f => `<option value="${esc(f)}">📁 ${esc(f)}</option>`).join('');
        new bootstrap.Modal($('mmMoveModal')).show();
    };

    window.mmConfirmarMove = async function () {
        try {
            await api('/api/multimedia/move', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ path: _movePath, folder: $('mmMoveFolder').value }) });
            bootstrap.Modal.getInstance($('mmMoveModal')).hide();
            msg('Movido ✓', true); cargar();
        } catch (e) { msg(e.message, false); }
    };

    window.mmEliminar = async function (path) {
        if (!confirm('¿Eliminar "' + path + '" definitivamente?')) return;
        try { await api('/api/multimedia/delete', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ path }) }); msg('Eliminado ✓', true); cargar(); }
        catch (e) { msg(e.message, false); }
    };

    window.mmNuevaCarpeta = async function () {
        const name = prompt('Nombre de la carpeta nueva (se crea dentro de uploads):');
        if (!name) return;
        try { await api('/api/multimedia/mkdir', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name }) }); msg('Carpeta creada ✓', true); cargar(); }
        catch (e) { msg(e.message, false); }
    };

    document.addEventListener('DOMContentLoaded', () => {
        if (!$('mmPanel')) return;
        $('mmSearch').addEventListener('input', render);
        $('mmFolderFilter').addEventListener('change', render);
        document.querySelectorAll('.mm-tab').forEach(b =>
            b.addEventListener('click', () => {
                document.querySelectorAll('.mm-tab').forEach(x => x.classList.remove('active'));
                b.classList.add('active'); _tipo = b.dataset.mmTipo; render();
            }));
        $('mmUploadInput').addEventListener('change', async ev => {
            const files = ev.target.files;
            if (!files.length) return;
            const fd = new FormData();
            const fold = $('mmFolderFilter').value;
            fd.append('folder', fold === '__root__' ? '' : fold);
            for (const f of files) fd.append('files', f);
            msg('Subiendo ' + files.length + ' archivo(s)…', true);
            try { await api('/api/multimedia/upload', { method: 'POST', body: fd }); msg('Subido ✓', true); cargar(); }
            catch (e) { msg(e.message, false); }
            ev.target.value = '';
        });
        $('mmPanel').addEventListener('shown.bs.collapse', () => { if (!_files.length) cargar(); }, { once: false });
        cargar();
    });
})();
