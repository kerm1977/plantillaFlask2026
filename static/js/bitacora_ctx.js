/* ══ BLINDADO — BITÁCORA — menú contextual del editor ══
   Pulsación larga (o clic derecho) sobre texto → formato;
   sobre imagen/video/iframe → alinear, tamaño, eliminar.
   Al mantener presionado se selecciona la palabra sola;
   el menú permite ampliar a palabra o párrafo completo. */
/* global Wysiwyg, btResizeMedia, btMediaSel, _btAutoSave,
          _btCtxPoint, _btSelPalabra, _btSelParrafo */

let _btCtxEl = null;
let _btCtxTimer = null;
let _btCtxSel = null;
let _btCtxNoClick = false; // suprime el clic que sigue a la pulsación larga

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

/* La selección por punto de contacto vive en bitacora_sel.js */

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

/* Envuelve la selección en un span con tamaño de fuente ±2px */
function _btFontSize(delta) {
  Wysiwyg.restaurarSeleccion('btEditor');
  const s = window.getSelection();
  if (!s.rangeCount || s.isCollapsed) return;
  const r = s.getRangeAt(0);
  const ref = r.startContainer.nodeType === 3
    ? r.startContainer.parentElement : r.startContainer;
  const cur = ref ? parseFloat(getComputedStyle(ref).fontSize) || 16 : 16;
  const span = document.createElement('span');
  span.style.fontSize = Math.max(8, Math.min(72, cur + delta * 2)) + 'px';
  try { r.surroundContents(span); }
  catch (e) { span.appendChild(r.extractContents()); r.insertNode(span); }
  const nr = document.createRange();
  nr.selectNodeContents(span);
  s.removeAllRanges();
  s.addRange(nr);
  Wysiwyg.guardarSeleccion('btEditor');
}

/* Quita el tamaño personalizado de la selección → tamaño predeterminado */
function _btFontReset() {
  Wysiwyg.restaurarSeleccion('btEditor');
  const s = window.getSelection();
  if (!s.rangeCount) return;
  const r = s.getRangeAt(0);
  const ed = document.getElementById('btEditor');
  ed.querySelectorAll('[style]').forEach(el => {
    if (!r.intersectsNode(el)) return;
    el.style.fontSize = '';
    if (!el.getAttribute('style').trim()) {
      if (el.tagName === 'SPAN' && !el.className) {
        el.replaceWith(...Array.from(el.childNodes));
      } else el.removeAttribute('style');
    }
  });
  Wysiwyg.guardarSeleccion('btEditor');
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
    _btCtxBtn('bi-zoom-in', 'Aumentar texto',
      () => _btFontSize(1), {keep: true}),
    _btCtxBtn('bi-zoom-out', 'Disminuir texto',
      () => _btFontSize(-1), {keep: true}),
    _btCtxBtn('bi-arrow-counterclockwise', 'Restaurar texto',
      () => _btFontReset(), {keep: true}),
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
      _btCtxNoClick = true;  // el clic del levantar-dedo no borra la selección
      _btCtxAbrir(t.clientX, t.clientY, tgt);
    }, 550);
  });
  ed.addEventListener('click', (e) => {
    if (_btCtxNoClick) {
      _btCtxNoClick = false;
      e.preventDefault();
      e.stopPropagation();
    }
  }, true);
  ['touchend', 'touchmove', 'touchcancel'].forEach(ev =>
    ed.addEventListener(ev, () => clearTimeout(_btCtxTimer), {passive: true}));
  document.addEventListener('click', (e) => {
    if (_btCtxEl && !_btCtxEl.contains(e.target)) _btCtxCerrar();
  });
  document.addEventListener('scroll', _btCtxCerrar, true);
});
