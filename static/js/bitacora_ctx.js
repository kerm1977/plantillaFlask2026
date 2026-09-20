/* ══ BITÁCORA — menú contextual del editor ══
   Pulsación larga (o clic derecho) sobre texto → formato;
   sobre imagen/video/iframe → alinear, tamaño, eliminar. */
/* global Wysiwyg, btResizeMedia, btMediaSel */

let _btCtxEl = null;
let _btCtxTimer = null;
let _btCtxSel = null;

function _btCtxCerrar() {
  if (_btCtxEl) { _btCtxEl.remove(); _btCtxEl = null; }
}

function _btCtxBtn(icono, texto, fn) {
  const b = document.createElement('button');
  b.type = 'button';
  b.className = 'bt-ctx-btn';
  b.innerHTML = '<i class="bi ' + icono + ' me-2"></i>' + texto;
  b.onclick = (e) => { e.stopPropagation(); fn(); _btCtxCerrar(); };
  return b;
}

function _btCtxPos(el, x, y) {
  document.body.appendChild(el);
  const r = el.getBoundingClientRect();
  el.style.left = Math.max(8, Math.min(x, window.innerWidth - r.width - 8)) + 'px';
  el.style.top = Math.max(8, Math.min(y, window.innerHeight - r.height - 8)) + 'px';
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
    _btCtxBtn('bi-type-bold', 'Negrita', () => Wysiwyg.execCmd(ed, 'bold')),
    _btCtxBtn('bi-type-italic', 'Itálica', () => Wysiwyg.execCmd(ed, 'italic')),
    _btCtxBtn('bi-type-underline', 'Subrayado', () => Wysiwyg.execCmd(ed, 'underline')),
    _btCtxBtn('bi-highlighter', 'Resaltar amarillo',
      () => document.execCommand('hiliteColor', false, '#ffff99')),
    _btCtxBtn('bi-text-left', 'Alinear a la izquierda',
      () => Wysiwyg.execCmd(ed, 'justifyLeft')),
    _btCtxBtn('bi-text-center', 'Centrado',
      () => Wysiwyg.execCmd(ed, 'justifyCenter')),
    _btCtxBtn('bi-text-right', 'Alinear a la derecha',
      () => Wysiwyg.execCmd(ed, 'justifyRight')),
    _btCtxBtn('bi-fonts', 'Cambiar fuente', () => _btCtxFuentes(x, y)),
    _btCtxBtn('bi-trash', 'Eliminar',
      () => document.execCommand('delete')),
  ];
  _btCtxMenu(items, x, y);
}

function _btCtxFuentes(x, y) {
  const ed = 'btEditor';
  _btCtxMenu([
    _btCtxBtn('bi-arrow-left', 'Volver', () => _btCtxTexto(x, y)),
    _btCtxBtn('bi-fonts', 'Fuente actual',
      () => document.execCommand('fontName', false, '')),
    _btCtxBtn('bi-fonts', 'Bienvenidos a la tribu',
      () => document.execCommand('fontName', false, 'Uncial Antiqua')),
    _btCtxBtn('bi-fonts', 'Ronda',
      () => document.execCommand('fontName', false, 'Ronda')),
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
  if (typeof Wysiwyg !== 'undefined' && Wysiwyg.guardarSeleccion) {
    Wysiwyg.guardarSeleccion('btEditor');
  }
  const media = target.closest('img, video, iframe');
  if (media) _btCtxMedia(media, x, y);
  else _btCtxTexto(x, y);
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
    _btCtxTimer = setTimeout(() => _btCtxAbrir(t.clientX, t.clientY, tgt), 550);
  }, {passive: true});
  ['touchend', 'touchmove', 'touchcancel'].forEach(ev =>
    ed.addEventListener(ev, () => clearTimeout(_btCtxTimer), {passive: true}));
  document.addEventListener('click', (e) => {
    if (_btCtxEl && !_btCtxEl.contains(e.target)) _btCtxCerrar();
  });
  document.addEventListener('scroll', _btCtxCerrar, true);
});
