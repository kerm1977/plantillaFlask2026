/* ══ BLINDADO — BITÁCORA — selección por punto de contacto ══
   Palabra y párrafo bajo el dedo/cursor para el menú contextual,
   y alineación de bloques (izq/centro/der/justificado). */
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

/* ── Alineación de bloques ──
   execCommand('justify*') no actúa sobre texto suelto: esta función
   aplica text-align directo a los bloques que toca la selección. */
const _BT_BLOQUES = 'p, div, li, blockquote, h1, h2, h3, h4, h5, h6';

function _btBloquesDeRango(r, ed) {
  const bloques = [];
  ed.querySelectorAll(_BT_BLOQUES).forEach(el => {
    try { if (r.intersectsNode(el)) bloques.push(el); } catch (e) {}
  });
  // solo los más internos (no duplicar el padre que contiene otro bloque)
  return bloques.filter(b => !bloques.some(o => o !== b && b.contains(o)));
}

function btAlinear(lado) {
  const mapa = {left: 'left', center: 'center',
                right: 'right', justify: 'justify'};
  const ed = document.getElementById('btEditor');
  if (!ed || !mapa[lado]) return;
  Wysiwyg.restaurarSeleccion('btEditor');
  const s = window.getSelection();
  const r = s.rangeCount ? s.getRangeAt(0) : null;
  // si no hay bloques, envolver el contenido suelto en un <p>
  if (!ed.querySelector(_BT_BLOQUES)) {
    const p = document.createElement('p');
    while (ed.firstChild) p.appendChild(ed.firstChild);
    ed.appendChild(p);
  }
  let bloques = r ? _btBloquesDeRango(r, ed) : [];
  if (!bloques.length) {
    // caret suelto dentro del editor: crear párrafo en el punto
    try { document.execCommand('styleWithCSS', false, true); } catch (e) {}
    document.execCommand('formatBlock', false, 'p');
    const s2 = window.getSelection();
    bloques = s2.rangeCount ? _btBloquesDeRango(s2.getRangeAt(0), ed) : [];
  }
  bloques.forEach(el => { el.style.textAlign = mapa[lado]; });
  Wysiwyg.guardarSeleccion('btEditor');
}
