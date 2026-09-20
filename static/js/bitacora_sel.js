/* ══ BLINDADO — BITÁCORA — selección por punto de contacto ══
   Palabra y párrafo bajo el dedo/cursor para el menú contextual. */
/* global Wysiwyg */

let _btCtxPoint = null;   // {x, y} del último toque/clic

/* Rango en un punto de pantalla (Chrome/Android + Firefox) */
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

/* Selecciona la palabra bajo el dedo/cursor — expande a los
   bordes de la palabra manualmente (funciona en todos los móviles) */
function _btSelPalabra() {
  if (!_btCtxPoint) return;
  const r = _btRangoEnPunto(_btCtxPoint.x, _btCtxPoint.y);
  if (!r) return;
  const s = window.getSelection();
  const n = r.startContainer;
  const esPalabra = c => /[\wáéíóúñü]/i.test(c);
  if (n.nodeType === 3) {
    const t = n.textContent;
    let a = r.startOffset, b = r.startOffset;
    while (a > 0 && esPalabra(t[a - 1])) a--;
    while (b < t.length && esPalabra(t[b])) b++;
    if (a !== b) { s.setBaseAndExtent(n, a, n, b); }
    else {
      s.setBaseAndExtent(n, r.startOffset, n, r.startOffset);
      try { s.modify('expand', 'word'); } catch (e) {}
    }
  } else {
    s.setBaseAndExtent(n, r.startOffset, n, r.startOffset);
    try { s.modify('expand', 'word'); } catch (e) {}
  }
  Wysiwyg.guardarSeleccion('btEditor');
}

/* Selecciona el párrafo completo donde se tocó */
function _btSelParrafo() {
  let n = null;
  if (_btCtxPoint) {
    const r = _btRangoEnPunto(_btCtxPoint.x, _btCtxPoint.y);
    if (r) n = r.startContainer;
  }
  if (!n) {
    const s0 = window.getSelection();
    n = s0.rangeCount ? s0.anchorNode : null;
  }
  if (n && n.nodeType === 3) n = n.parentNode;
  const bloque = n && n.closest
    ? n.closest('p, div, li, blockquote, h1, h2, h3, h4, h5, h6') : null;
  if (!bloque || bloque.id === 'btEditor') { _btSelPalabra(); return; }
  const s = window.getSelection();
  const r = document.createRange();
  r.selectNodeContents(bloque);
  s.removeAllRanges();
  s.addRange(r);
  Wysiwyg.guardarSeleccion('btEditor');
}
