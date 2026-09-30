// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
// WYSIWYG reutilizable para La Tribu — parte formato/texto
const Wysiwyg = (function() {
  'use strict';

  function _editor(editorId) { return document.getElementById(editorId); }

  const _selecciones = {};

  function guardarSeleccion(editorId) {
    const ed = _editor(editorId);
    if (!ed) return;
    const sel = window.getSelection();
    if (!sel.rangeCount) return;
    const range = sel.getRangeAt(0);
    if (ed.contains(range.commonAncestorContainer)) {
      _selecciones[editorId] = range.cloneRange();
    }
  }

  function restaurarSeleccion(editorId) {
    const ed = _editor(editorId);
    const sel = window.getSelection();
    if (!ed || !sel) return;
    const r = sel.rangeCount ? sel.getRangeAt(0) : null;
    if (r && ed.contains(r.commonAncestorContainer) && !r.collapsed) return;
    if (_selecciones[editorId]) {
      ed.focus();
      sel.removeAllRanges();
      sel.addRange(_selecciones[editorId]);
      delete _selecciones[editorId];
    }
  }

  function execCmd(editorId, command, arg) {
    restaurarSeleccion(editorId);
    try { document.execCommand('styleWithCSS', false, true); } catch(e) {}
    document.execCommand(command, false, arg || null);
    const ed = _editor(editorId);
    if (ed) ed.focus();
  }

  function clearFormat(editorId, capitalClass) {
    capitalClass = capitalClass || 'caminata-capital';
    const preview = _editor(editorId);
    if (!preview) return;
    preview.focus();
    const sel = window.getSelection();
    let range;
    if (sel.rangeCount === 0 || sel.getRangeAt(0).collapsed) {
      range = document.createRange();
      range.selectNodeContents(preview);
      sel.removeAllRanges();
      sel.addRange(range);
    } else {
      range = sel.getRangeAt(0);
    }
    try { document.execCommand('styleWithCSS', false, true); } catch(e) {}
    document.execCommand('removeFormat', false, null);
    preview.querySelectorAll('.' + capitalClass).forEach(el => el.classList.remove(capitalClass));
    preview.querySelectorAll('li').forEach(li => {
      const p = document.createElement('p');
      p.innerHTML = li.innerHTML;
      li.replaceWith(p);
    });
    preview.querySelectorAll('ul, ol').forEach(list => {
      list.replaceWith(...Array.from(list.childNodes));
    });
    preview.querySelectorAll('p, span, b, i, u, s, strike, font, mark, strong, em, li, div, h1, h2, h3, h4, h5, h6, blockquote').forEach(el => el.removeAttribute('style'));
    const all = document.createRange();
    all.selectNodeContents(preview);
    sel.removeAllRanges();
    sel.addRange(all);
    try { document.execCommand('styleWithCSS', false, true); } catch(e) {}
    document.execCommand('justifyFull', false, null);
    preview.querySelectorAll('p, li, div, h1, h2, h3, h4, h5, h6, blockquote').forEach(el => { el.style.lineHeight = 'normal'; });
    sel.removeAllRanges();
  }

  function highlight(editorId, color) {
    if (!color) return;
    restaurarSeleccion(editorId);
    try { document.execCommand('styleWithCSS', false, true); } catch(e) {}
    const ed = _editor(editorId);
    if (ed) ed.focus();
    document.execCommand('hiliteColor', false, color);
  }

  function marcarSeleccion(editorId, selectId) {
    const select = document.getElementById(selectId);
    if (select) highlight(editorId, select.value);
  }

  function cambiarFuente(editorId, fuente) {
    const preview = _editor(editorId);
    if (!preview || !fuente || fuente === 'current') return;
    restaurarSeleccion(editorId);
    const sel = window.getSelection();
    if (!sel.rangeCount || sel.getRangeAt(0).collapsed) return;
    const range = sel.getRangeAt(0);
    const span = document.createElement('span');
    span.style.setProperty('font-family', JSON.stringify(fuente));
    try {
      range.surroundContents(span);
    } catch (e) {
      const frag = range.extractContents();
      span.appendChild(frag);
      range.insertNode(span);
    }
    const r = document.createRange();
    r.selectNodeContents(span);
    sel.removeAllRanges();
    sel.addRange(r);
    preview.focus();
  }

  function wrapTag(editorId, tag) {
    const preview = _editor(editorId);
    if (!preview) return;
    restaurarSeleccion(editorId);
    const sel = window.getSelection();
    if (sel.rangeCount === 0 || sel.getRangeAt(0).collapsed) return;
    const range = sel.getRangeAt(0);
    try {
      const wrapper = document.createElement(tag);
      range.surroundContents(wrapper);
    } catch (e) {
      const text = range.toString();
      if (!text) return;
      document.execCommand('insertHTML', false, '<' + tag + '>' + text.replace(/</g, '&lt;').replace(/>/g, '&gt;') + '</' + tag + '>');
    }
    preview.focus();
  }

  function transformarTexto(editorId, accion) {
    const preview = _editor(editorId);
    if (!preview || !accion) return;
    restaurarSeleccion(editorId);
    const sel = window.getSelection();
    if (!sel.rangeCount) return;
    const text = sel.toString();
    if (!text) return;
    let out = text;
    if (accion === 'uppercase') out = text.toUpperCase();
    else if (accion === 'lowercase') out = text.toLowerCase();
    else if (accion === 'titlecase') out = text.toLowerCase().replace(/(?:^|\s)\S/g, (m) => m.toUpperCase());
    document.execCommand('insertText', false, out);
    preview.focus();
  }

  function bloquesSeleccionados(editorId) {
    const preview = _editor(editorId);
    const sel = window.getSelection();
    if (!preview || sel.rangeCount === 0 || sel.getRangeAt(0).collapsed) return [];
    const bloques = Array.from(preview.querySelectorAll('p, div, h1, h2, h3, h4, h5, h6, li, blockquote'));
    return bloques.filter(el => sel.containsNode(el, true));
  }

  function interlineado(editorId, valor) {
    restaurarSeleccion(editorId);
    const bloques = bloquesSeleccionados(editorId);
    if (bloques.length === 0 || !valor) return;
    const preview = _editor(editorId);
    if (preview) preview.focus();
    bloques.forEach(el => { el.style.lineHeight = valor; });
  }

  function capitular(editorId, capitalClass) {
    capitalClass = capitalClass || 'caminata-capital';
    restaurarSeleccion(editorId);
    const bloques = bloquesSeleccionados(editorId);
    if (bloques.length === 0) return;
    const preview = _editor(editorId);
    if (preview) preview.focus();
    bloques.forEach(el => { el.classList.toggle(capitalClass); });
  }

  function cita(editorId) {
    const preview = _editor(editorId);
    if (!preview) return;
    restaurarSeleccion(editorId);
    const sel = window.getSelection();
    if (!sel.rangeCount) return;
    const range = sel.getRangeAt(0);
    if (range.collapsed) return;
    const bloques = bloquesSeleccionados(editorId);
    if (bloques.length > 0) {
      const todosBlockquote = bloques.every(el => el.tagName === 'BLOCKQUOTE');
      try { document.execCommand('styleWithCSS', false, true); } catch(e){}
      document.execCommand('formatBlock', false, todosBlockquote ? 'p' : 'blockquote');
    } else {
      const bq = document.createElement('blockquote');
      try {
        range.surroundContents(bq);
      } catch (e) {
        const frag = range.extractContents();
        bq.appendChild(frag);
        range.insertNode(bq);
      }
      const r = document.createRange();
      r.selectNodeContents(bq);
      sel.removeAllRanges();
      sel.addRange(r);
    }
    preview.focus();
  }

  function formatBlock(editorId, tag) {
    restaurarSeleccion(editorId);
    try { document.execCommand('styleWithCSS', false, true); } catch(e) {}
    const preview = _editor(editorId);
    if (preview) preview.focus();
    document.execCommand('formatBlock', false, tag);
  }

  function eliminarSeleccion(editorId) {
    const preview = _editor(editorId);
    const sel = window.getSelection();
    if (!sel.rangeCount) return;
    let node = sel.getRangeAt(0).commonAncestorContainer;
    if (node.nodeType === Node.TEXT_NODE) node = node.parentElement;
    let el = node;
    while (el && el.id !== editorId) {
      const esVideo = (el.classList && el.classList.contains('caminata-embed')) || (el.style && el.style.paddingBottom === '56.25%');
      if (esVideo) {
        const r = document.createRange();
        r.selectNode(el);
        sel.removeAllRanges();
        sel.addRange(r);
        if (preview) preview.focus();
        try { document.execCommand('styleWithCSS', false, true); } catch(e) {}
        document.execCommand('delete');
        return;
      }
      el = el.parentElement;
    }
  }

  function getContent(editorId) { const p = _editor(editorId); return p ? p.innerHTML : ''; }

  function setContent(editorId, html) { const p = _editor(editorId); if (p) p.innerHTML = html || ''; }

  return { execCmd, clearFormat, highlight, marcarSeleccion, cambiarFuente, wrapTag,
    transformarTexto, bloquesSeleccionados, interlineado, capitular, cita, formatBlock,
    eliminarSeleccion, getContent, setContent, guardarSeleccion, restaurarSeleccion };
})();
