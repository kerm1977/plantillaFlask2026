/* ══ BLINDADO — BITÁCORA — núcleo del mini blog (independiente) ══
   Autoguardado: cada cambio se guarda solo tras ~1.2s. */
/* global Wysiwyg, btPages, btPageIdx, _btSyncPagina, _btRenderPagesUI */

let btEntryId = null;
let btMediaSel = null;
let _btSaveTimer = null;

function _btEditor() { return document.getElementById('btEditor'); }

function _btStatus(txt, color) {
  const st = document.getElementById('btSaveStatus');
  if (st) { st.textContent = txt; st.style.color = color || '#6c757d'; }
}

/* Cada cambio agenda un guardado silencioso */
function _btAutoSave() {
  _btStatus('Cambios sin guardar…', '#856404');
  clearTimeout(_btSaveTimer);
  _btSaveTimer = setTimeout(() => _btGuardarInterno(false), 1200);
}

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
    Wysiwyg.setupUploadListeners('btEditor', '/api/upload-image', _btAutoSave);
  }
  ed.addEventListener('input', _btAutoSave);
  ed.addEventListener('click', (e) => {
    const t = e.target.closest('img, video, iframe');
    btMediaSel = t;
    const tools = document.getElementById('btMediaTools');
    if (!tools) return;
    tools.style.display = t ? 'flex' : 'none';
    if (t) _btMediaPct(t);
  });
  // Los botones de la barra de formato no disparan 'input' en todos
  // los navegadores: cualquier clic dentro de los acordeones agenda guardado.
  const ac = document.getElementById('btAcordeon');
  if (ac) ac.addEventListener('click', () => setTimeout(_btAutoSave, 300));
  ['btTitulo', 'btDescripcion', 'btVisibilidad'].forEach(id => {
    const el = document.getElementById(id);
    if (el) { el.addEventListener('input', _btAutoSave);
              el.addEventListener('change', _btAutoSave); }
  });
  document.querySelectorAll('.bt-share-check').forEach(c =>
    c.addEventListener('change', _btAutoSave));
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
  _btAutoSave();
}

function _btPayload() {
  _btSyncPagina();
  return {
    titulo: document.getElementById('btTitulo').value,
    descripcion: document.getElementById('btDescripcion').value,
    visibilidad: document.getElementById('btVisibilidad').value,
    compartir: Array.from(document.querySelectorAll('.bt-share-check:checked'))
      .map(c => parseInt(c.value, 10)),
    paginas: btPages
  };
}

async function _btGuardarInterno(redirigir) {
  _btStatus('Guardando…', '#0d6efd');
  const url = btEntryId ? '/api/bitacora/' + btEntryId + '/guardar'
                        : '/api/bitacora/guardar';
  try {
    const r = await fetch(url, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(_btPayload())
    });
    const data = await r.json();
    if (data.ok) {
      if (!btEntryId) btEntryId = data.id;
      _btStatus('Guardado ' + new Date().toLocaleTimeString(), '#198754');
      if (redirigir) window.location.href = data.url;
    } else {
      _btStatus('Error al guardar', '#dc3545');
      if (redirigir) alert(data.error || 'Error al guardar');
    }
  } catch (e) {
    _btStatus('Sin conexión — pendiente de guardar', '#dc3545');
  }
}

/* Botón Guardar: guarda y abre la entrada */
function btGuardar() { _btGuardarInterno(true); }

/* Eliminar entrada — modal del tema con triple confirmación */
let _btDelId = null;
let _btDelPaso = 1;

function _btDelRender() {
  document.querySelectorAll('#btDelEntryModal .bt-del-txt').forEach(p => {
    p.style.display = parseInt(p.dataset.paso, 10) === _btDelPaso
      ? 'block' : 'none';
  });
  document.getElementById('btDelEntryNext').style.display =
    _btDelPaso < 3 ? 'inline-block' : 'none';
  document.getElementById('btDelEntryGo').style.display =
    _btDelPaso === 3 ? 'inline-block' : 'none';
}

function btDelEntryPaso() {
  _btDelPaso = Math.min(3, _btDelPaso + 1);
  _btDelRender();
}

function btConfirmarDelEntry() {
  fetch('/api/bitacora/' + _btDelId + '/eliminar', {method: 'POST'})
    .then(r => r.json())
    .then(d => {
      if (d.ok) {
        if (location.pathname.includes('/bitacora/' + _btDelId)) {
          window.location.href = '/bitacora';
        } else location.reload();
      } else alert(d.error || 'Error al eliminar');
    });
}

function btEliminar(id) {
  const modal = document.getElementById('btDelEntryModal');
  if (!modal) {  // respaldo si el modal no está en la página
    if (!confirm('¿Eliminar esta entrada?')) return;
    if (!confirm('Se borrarán todas sus páginas. ¿Confirmás?')) return;
    if (!confirm('Última confirmación: es irreversible.')) return;
    _btDelId = id; btConfirmarDelEntry(); return;
  }
  _btDelId = id;
  _btDelPaso = 1;
  _btDelRender();
  bootstrap.Modal.getOrCreateInstance(modal).show();
}
