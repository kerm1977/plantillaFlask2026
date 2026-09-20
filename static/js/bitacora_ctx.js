/* ══ BLINDADO — BITÁCORA — menú contextual del editor ══
   Pulsación larga (o clic derecho) sobre texto → formato;
   sobre imagen/video/iframe → alinear, tamaño, eliminar.
   Al mantener presionado se selecciona la palabra sola;
   el menú permite ampliar a palabra o párrafo completo. */
/* global Wysiwyg, btResizeMedia, btMediaSel, _btAutoSave */

let _btCtxEl = null;
let _btCtxTimer = null;
let _btCtxSel = null;
let _btCtxPoint = null;   // {x, y} del último toque/clic

function _btCtxCerrar() {
  if (_btCtxEl) { _btCtxEl.remove(); _btCtxEl = null; }
}

/* opts: keep = no cerrar el menú; save = false omite el autoguardado */
function _btCtxBtn(icono, texto, fn, opts) {
  opts = opts || {};
  const b = document.createElement('button');
  b.type = 'button';
  b.className = 'bt-ctx-btn';
  b.innerHTML = '<i class="bi ' + icono + ' me-2"></i>' + texto;
  b.onclick = (e) => {
    e.stopPropagation();
    fn();
    if (opts.save !== false) _btAutoSave();
    if (!opts.keep) _btCtxCerrar();
  };
  return b;
}

/* ── Selección por punto de contacto ── */
function _btRangoEnPunto(x, y) {
  if (document.caretRangeFromPoint) {
    return document.caretRangeFromPoint(x, y);
  }
  if (document.caretPositionFromPoint) {
    const p = document.caretPositionFromPoint(x, y);
    if (!p) return null;
    const r = document.createRange();
    r.setStart(p.offsetNode, p.offset);
    r.collapse(true);
    return r;
  }
  return null;
}

/* Selecciona la palabra bajo el dedo/cursor */
function _btSelPalabra() {
  if (!_btCtxPoint) return;
  const r = _btRangoEnPunto(_btCtxPoint.x, _btCtxPoint.y);
  if (!r) return;
  const s = window.getSelection();
  s.setBaseAndExtent(r.startContainer, r.startOffset,
                     r.startContainer, r.startOffset);
  try { s.modify('expand', 'word'); } catch (e) {}
  Wysiwyg.guardarSeleccion('btEditor');
}

/* Selecciona el párrafo completo donde está la selección */
function _btSelParrafo() {
  const s = window.getSelection();
  if (!s.rangeCount) { _btSelPalabra(); }
  if (!s.rangeCount) return;
  let n = s.anchorNode;
  if (n && n.nodeType === 3) n = n.parentNode;
  const bloque = n && n.closest
    ? n.closest('p, div, li, blockquote, h1, h2, h3, h4, h5, h6') : null;
  if (!bloque || bloque.id === 'btEditor') return;
  const r = document.createRange();
  r.selectNodeContents(bloque);
  s.removeAllRanges();
  s.addRange(r);
  Wysiwyg.guardarSeleccion('btEditor');
}

/* El menú se fija al borde derecho de la pantalla, a la altura del toque,
   para no superponerse al texto seleccionado. */
function _btCtxPos(el, x, y) {
  document.body.appendChild(el);
  const r = el.getBoundingClientRect();
  el.style.left = 'auto';
  el.style.right = '8px';
  el.style.top = Math.max(8,
    Math.min(y - r.height / 2, window.innerHeight - r.height - 8)) + 'px';
}

function _btCtxMenu(items, x, y) {
  _btCtxCerrar();
  const m = document.createElement('div');
  m.className = 'bt-ctx';
  items.forEach(it => m.appendChild(it));
  _btCtxEl = m;
  _btCtxPos(m, x, y);
}

function _btCtxTexto(x, y) {
  const ed = 'btEditor';
  const items = [
    _btCtxBtn('bi-cursor-text', 'Seleccionar palabra',
      () => _btSelPalabra(), {keep: true, save: false}),
    _btCtxBtn('bi-paragraph', 'Seleccionar párrafo',
      () => _btSelParrafo(), {keep: true, save: false}),
    _btCtxBtn('bi-type-bold', 'Negrita', () => Wysiwyg.execCmd(ed, 'bold')),
    _btCtxBtn('bi-type-italic', 'Itálica', () => Wysiwyg.execCmd(ed, 'italic')),
    _btCtxBtn('bi-type-underline', 'Subrayado', () => Wysiwyg.execCmd(ed, 'underline')),
    _btCtxBtn('bi-highlighter', 'Resaltar amarillo',
      () => Wysiwyg.execCmd(ed, 'hiliteColor', '#ffff99')),
    _btCtxBtn('bi-text-left', 'Alinear a la izquierda',
      () => Wysiwyg.execCmd(ed, 'justifyLeft')),
    _btCtxBtn('bi-text-center', 'Centrado',
      () => Wysiwyg.execCmd(ed, 'justifyCenter')),
    _btCtxBtn('bi-text-right', 'Alinear a la derecha',
      () => Wysiwyg.execCmd(ed, 'justifyRight')),
    _btCtxBtn('bi-fonts', 'Cambiar fuente',
      () => _btCtxFuentes(x, y), {keep: true, save: false}),
    _btCtxBtn('bi-trash', 'Eliminar',
      () => Wysiwyg.execCmd(ed, 'delete')),
  ];
  _btCtxMenu(items, x, y);
}

function _btCtxFuentes(x, y) {
  _btCtxMenu([
    _btCtxBtn('bi-arrow-left', 'Volver',
      () => _btCtxTexto(x, y), {keep: true, save: false}),
    _btCtxBtn('bi-fonts', 'Fuente actual',
      () => Wysiwyg.execCmd('btEditor', 'fontName', '')),
    _btCtxBtn('bi-fonts', 'Bienvenidos a la tribu',
      () => Wysiwyg.execCmd('btEditor', 'fontName', 'Uncial Antiqua')),
    _btCtxBtn('bi-fonts', 'Ronda',
      () => Wysiwyg.execCmd('btEditor', 'fontName', 'Ronda')),
  ], x, y);
}

function _btAlignMedia(lado) {
  const el = _btCtxSel;
  if (!el) return;
  el.style.float = lado === 'left' ? 'left' : lado === 'right' ? 'right' : 'none';
  el.style.display = lado === 'center' ? 'block' : '';
  el.style.margin = lado === 'center' ? '0.5rem auto'
    : lado === 'left' ? '0 1rem 0.5rem 0'
    : lado === 'right' ? '0 0 0.5rem 1rem' : '';
}

function _btCtxMedia(el, x, y) {
  _btCtxSel = el;
  btMediaSel = el;
  _btCtxMenu([
    _btCtxBtn('bi-text-left', 'A la izquierda', () => _btAlignMedia('left')),
    _btCtxBtn('bi-text-center', 'Al centro', () => _btAlignMedia('center')),
    _btCtxBtn('bi-text-right', 'A la derecha', () => _btAlignMedia('right')),
    _btCtxBtn('bi-plus-lg', 'Agrandar', () => btResizeMedia(1)),
    _btCtxBtn('bi-dash-lg', 'Achicar', () => btResizeMedia(-1)),
    _btCtxBtn('bi-trash', 'Eliminar', () => el.remove()),
  ], x, y);
}

function _btCtxAbrir(x, y, target) {
  _btCtxPoint = {x: x, y: y};
  const media = target.closest('img, video, iframe');
  if (media) { _btCtxMedia(media, x, y); return; }
  // Si no hay texto seleccionado, selecciona la palabra tocada
  const s = window.getSelection();
  if (!s.rangeCount || s.isCollapsed) _btSelPalabra();
  _btCtxTexto(x, y);
}

document.addEventListener('DOMContentLoaded', () => {
  const ed = document.getElementById('btEditor');
  if (!ed) return;
  ed.addEventListener('contextmenu', (e) => {
    e.preventDefault();
    _btCtxAbrir(e.clientX, e.clientY, e.target);
  });
  ed.addEventListener('touchstart', (e) => {
    const t = e.touches[0];
    const tgt = e.target;
    _btCtxTimer = setTimeout(() => {
      e.preventDefault();
      _btCtxAbrir(t.clientX, t.clientY, tgt);
    }, 550);
  });
  ['touchend', 'touchmove', 'touchcancel'].forEach(ev =>
    ed.addEventListener(ev, () => clearTimeout(_btCtxTimer), {passive: true}));
  document.addEventListener('click', (e) => {
    if (_btCtxEl && !_btCtxEl.contains(e.target)) _btCtxCerrar();
  });
  document.addEventListener('scroll', _btCtxCerrar, true);
});
