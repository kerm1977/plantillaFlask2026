/* ══ BITÁCORA — lógica independiente del mini blog ══ */
/* global Wysiwyg */

let btEntryId = null;
let btMediaSel = null;

function _btEditor() { return document.getElementById('btEditor'); }

/* Init del formulario (nueva/editar) */
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

/* Visibilidad: mostrar selector de usuarios solo en "seleccion" */
function btToggleCompartir() {
  const v = document.getElementById('btVisibilidad');
  const box = document.getElementById('btCompartirBox');
  if (box) box.style.display = (v && v.value === 'seleccion') ? 'block' : 'none';
}

/* Enlace wa.me estilo rastreo */
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

/* Resize de media con +/− */
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

/* Guardar (todas las páginas) */
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

/* Eliminar entrada (doble confirmación) */
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

/* Exportar y compartir */
function btCopiarEnlace(url) {
  navigator.clipboard.writeText(url).then(
    () => alert('Enlace copiado'),
    () => prompt('Copiá el enlace:', url));
}
