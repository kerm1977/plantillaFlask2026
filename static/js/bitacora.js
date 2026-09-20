/* ══ BITÁCORA — lógica independiente del mini blog ══ */
/* global Wysiwyg */

let btEntryId = null;
let btMediaSel = null;

function _btEditor() { return document.getElementById('btEditor'); }

/* Inicializa el formulario (nueva/editar) */
function btInitForm(entryId) {
  btEntryId = entryId;
  btToggleCompartir();
  const ed = _btEditor();
  if (!ed) return;
  ed.style.textAlign = 'justify';
  if (typeof Wysiwyg !== 'undefined' && Wysiwyg.setupUploadListeners) {
    Wysiwyg.setupUploadListeners('btEditor', '/api/upload-image');
  }
  ed.addEventListener('click', (e) => {
    const t = e.target.closest('img, video, iframe');
    btMediaSel = t;
    const tools = document.getElementById('btMediaTools');
    if (!tools) return;
    if (t) { tools.style.display = 'flex'; _btMediaPct(t); }
    else tools.style.display = 'none';
  });
}

/* Muestra/oculta el selector de usuarios según el toggle privada */
function btToggleCompartir() {
  const p = document.getElementById('btPrivada');
  const box = document.getElementById('btCompartirBox');
  if (box) box.style.display = (p && p.checked) ? 'none' : 'block';
}

/* Inserta un enlace wa.me estilo rastreo en la posición del cursor */
function btInsertarWhatsApp() {
  const num = prompt('Número de WhatsApp (solo dígitos, con código de país):', '506');
  if (!num) return;
  const limpio = num.replace(/\D/g, '');
  if (!limpio) return;
  const msg = prompt('Mensaje (opcional):', '') || '';
  const url = 'https://wa.me/' + limpio +
    (msg ? '?text=' + encodeURIComponent(msg) : '');
  const html = '<a href="' + url + '" target="_blank" rel="noopener" ' +
    'class="bt-wa-link">WhatsApp — La Tribu</a>';
  _btEditor().focus();
  document.execCommand('insertHTML', false, html);
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
  let pct = _btPct(el) + dir * 10;
  pct = Math.max(20, Math.min(100, pct));
  el.style.width = pct + '%';
  el.style.maxWidth = '100%';
  el.style.height = 'auto';
  _btMediaPct(el);
}

/* Guardar entrada (crear o actualizar) */
async function btGuardar() {
  const compartir = Array.from(document.querySelectorAll('.bt-share-check:checked'))
    .map(c => parseInt(c.value, 10));
  const payload = {
    titulo: document.getElementById('btTitulo').value,
    descripcion: document.getElementById('btDescripcion').value,
    privada: document.getElementById('btPrivada').checked,
    compartir: compartir,
    contenido: _btEditor().innerHTML
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

/* Eliminar con doble confirmación */
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
