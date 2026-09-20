/* ══ BITÁCORA — lógica independiente del mini blog ══ */
/* global Wysiwyg */

let btEntryId = null;
let btMediaSel = null;
let btPages = [];       // HTML de cada página, en orden
let btPageIdx = 0;      // página que se está editando
let btDragIdx = null;   // índice arrastrado en el dropdown

function _btEditor() { return document.getElementById('btEditor'); }
function _btPaginaNombre(i) { return 'Página ' + (i + 1); }

/* ── Init del formulario ── */
function btInitForm(entryId, paginas) {
  btEntryId = entryId;
  btPages = (paginas && paginas.length) ? paginas : [''];
  btPageIdx = 0;
  btToggleCompartir();
  const ed = _btEditor();
  if (!ed) return;
  ed.innerHTML = btPages[0];
  ed.style.textAlign = 'justify';
  if (typeof Wysiwyg !== 'undefined' && Wysiwyg.setupUploadListeners) {
    Wysiwyg.setupUploadListeners('btEditor', '/api/upload-image');
  }
  ed.addEventListener('click', (e) => {
    const t = e.target.closest('img, video, iframe');
    btMediaSel = t;
    const tools = document.getElementById('btMediaTools');
    if (!tools) return;
    tools.style.display = t ? 'flex' : 'none';
    if (t) _btMediaPct(t);
  });
  _btRenderPagesUI();
}

/* ── Páginas: dropdown con ↑↓ y drag&drop ── */
function _btSyncPagina() {
  if (_btEditor()) btPages[btPageIdx] = _btEditor().innerHTML;
}

function _btRenderPagesUI() {
  const menu = document.getElementById('btPagesMenu');
  const lbl = document.getElementById('btPageLbl');
  if (lbl) lbl.textContent = _btPaginaNombre(btPageIdx);
  if (!menu) return;
  menu.innerHTML = '';
  btPages.forEach((_, i) => {
    const li = document.createElement('li');
    const it = document.createElement('div');
    it.className = 'dropdown-item d-flex align-items-center gap-2 bt-page-item'
      + (i === btPageIdx ? ' active' : '');
    it.draggable = true;
    it.innerHTML = '<i class="bi bi-grip-vertical text-muted"></i>' +
      '<span class="flex-grow-1">' + _btPaginaNombre(i) + '</span>' +
      '<button class="btn btn-sm btn-light rounded-circle py-0 px-1" title="Subir"><i class="bi bi-arrow-up"></i></button>' +
      '<button class="btn btn-sm btn-light rounded-circle py-0 px-1" title="Bajar"><i class="bi bi-arrow-down"></i></button>';
    const [btnUp, btnDown] = it.querySelectorAll('button');
    btnUp.onclick = (e) => { e.stopPropagation(); btMoverPagina(i, -1); };
    btnDown.onclick = (e) => { e.stopPropagation(); btMoverPagina(i, 1); };
    it.onclick = () => btSelPagina(i);
    it.ondragstart = () => { btDragIdx = i; };
    it.ondragover = (e) => e.preventDefault();
    it.ondrop = (e) => { e.preventDefault(); btSoltarPagina(i); };
    li.appendChild(it);
    menu.appendChild(li);
  });
}

function btSelPagina(i) {
  _btSyncPagina();
  btPageIdx = i;
  _btEditor().innerHTML = btPages[i];
  btMediaSel = null;
  const tools = document.getElementById('btMediaTools');
  if (tools) tools.style.display = 'none';
  _btRenderPagesUI();
}

function btAgregarPagina() {
  _btSyncPagina();
  btPages.push('');
  btPageIdx = btPages.length - 1;
  _btEditor().innerHTML = '';
  _btRenderPagesUI();
}

function btMoverPagina(i, dir) {
  const j = i + dir;
  if (j < 0 || j >= btPages.length) return;
  _btSyncPagina();
  const tmp = btPages[i]; btPages[i] = btPages[j]; btPages[j] = tmp;
  if (btPageIdx === i) btPageIdx = j; else if (btPageIdx === j) btPageIdx = i;
  _btRenderPagesUI();
}

function btSoltarPagina(destino) {
  if (btDragIdx === null || btDragIdx === destino) return;
  _btSyncPagina();
  const actual = btPages[btPageIdx];
  const movida = btPages.splice(btDragIdx, 1)[0];
  btPages.splice(destino, 0, movida);
  btPageIdx = Math.max(0, btPages.indexOf(actual));
  btDragIdx = null;
  _btRenderPagesUI();
}

function btEliminarPagina(i) {
  if (btPages.length <= 1) { alert('Debe quedar al menos una página.'); return; }
  if (!confirm('¿Eliminar la ' + _btPaginaNombre(i) + '?')) return;
  btPages.splice(i, 1);
  if (btPageIdx >= btPages.length) btPageIdx = btPages.length - 1;
  _btEditor().innerHTML = btPages[btPageIdx];
  _btRenderPagesUI();
}

/* ── Visibilidad: mostrar selector de usuarios solo en "seleccion" ── */
function btToggleCompartir() {
  const v = document.getElementById('btVisibilidad');
  const box = document.getElementById('btCompartirBox');
  if (box) box.style.display = (v && v.value === 'seleccion') ? 'block' : 'none';
}

/* ── Enlace wa.me estilo rastreo ── */
function btInsertarWhatsApp() {
  const num = prompt('Número de WhatsApp (solo dígitos, con código de país):', '506');
  if (!num) return;
  const limpio = num.replace(/\D/g, '');
  if (!limpio) return;
  const msg = prompt('Mensaje (opcional):', '') || '';
  const url = 'https://wa.me/' + limpio +
    (msg ? '?text=' + encodeURIComponent(msg) : '');
  _btEditor().focus();
  document.execCommand('insertHTML', false,
    '<a href="' + url + '" target="_blank" rel="noopener" ' +
    'class="bt-wa-link">WhatsApp — La Tribu</a>');
}

/* ── Resize de media con +/− ── */
function _btPct(el) {
  const w = (el.style.width || '').replace('%', '');
  return w ? parseInt(w, 10) : 100;
}
function _btMediaPct(el) {
  const s = document.getElementById('btMediaPct');
  if (s) s.textContent = _btPct(el) + '%';
}
function btResizeMedia(dir) {
  const el = btMediaSel;
  if (!el) return;
  const pct = Math.max(20, Math.min(100, _btPct(el) + dir * 10));
  el.style.width = pct + '%';
  el.style.maxWidth = '100%';
  el.style.height = 'auto';
  _btMediaPct(el);
}

/* ── Guardar (todas las páginas) ── */
async function btGuardar() {
  _btSyncPagina();
  const payload = {
    titulo: document.getElementById('btTitulo').value,
    descripcion: document.getElementById('btDescripcion').value,
    visibilidad: document.getElementById('btVisibilidad').value,
    compartir: Array.from(document.querySelectorAll('.bt-share-check:checked'))
      .map(c => parseInt(c.value, 10)),
    paginas: btPages
  };
  const url = btEntryId ? '/api/bitacora/' + btEntryId + '/guardar'
                        : '/api/bitacora/guardar';
  const r = await fetch(url, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload)
  });
  const data = await r.json();
  if (data.ok) window.location.href = data.url;
  else alert(data.error || 'Error al guardar');
}

/* ── Eliminar entrada (doble confirmación) ── */
function btEliminar(id) {
  if (!confirm('¿Eliminar esta entrada de la bitácora?')) return;
  if (!confirm('Esta acción no se puede deshacer. ¿Confirmás?')) return;
  fetch('/api/bitacora/' + id + '/eliminar', {method: 'POST'})
    .then(r => r.json())
    .then(d => {
      if (d.ok) {
        if (location.pathname.includes('/bitacora/' + id)) {
          window.location.href = '/bitacora';
        } else location.reload();
      } else alert(d.error || 'Error al eliminar');
    });
}
