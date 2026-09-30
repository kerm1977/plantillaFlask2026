// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
  function caminataCambiarFuente(fuente) {
    const preview = document.getElementById('caminataPreview');
    if (!preview || !fuente || fuente === 'current') return;
    if (caminataAplicarMultiseleccion({fontFamily: fuente})) return;
    caminataRestaurarSeleccion();
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
    guardarCaminataFormateo();
  }

  function caminataConvertirEnlaces() {
    const preview = document.getElementById('caminataPreview');
    if (!preview) return false;
    const sel = window.getSelection();
    const activeRange = sel && sel.rangeCount ? sel.getRangeAt(0) : null;
    const activeNode = activeRange && activeRange.collapsed ? activeRange.startContainer : null;
    let caretTarget = null;
    let changed = false;
    const walker = document.createTreeWalker(preview, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        if (!node.parentElement || node.parentElement.closest('a, code, pre, script, style')) return NodeFilter.FILTER_REJECT;
        return /(?:https?:\/\/|www\.)[^\s<>"']+/i.test(node.data) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
      }
    });
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach(node => {
      const text = node.data;
      const regex = /(?:https?:\/\/|www\.)[^\s<>"']+/gi;
      const fragment = document.createDocumentFragment();
      let cursor = 0;
      let match;
      let nodeChanged = false;
      while ((match = regex.exec(text))) {
        let urlText = match[0];
        const trailing = urlText.match(/[.,;:!?)]*$/)?.[0] || '';
        urlText = urlText.slice(0, urlText.length - trailing.length);
        if (!urlText) continue;
        fragment.appendChild(document.createTextNode(text.slice(cursor, match.index)));
        const link = document.createElement('a');
        link.href = urlText.toLowerCase().startsWith('www.') ? `https://${urlText}` : urlText;
        link.textContent = urlText;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        fragment.appendChild(link);
        if (trailing) fragment.appendChild(document.createTextNode(trailing));
        cursor = match.index + match[0].length;
        nodeChanged = true;
      }
      if (!nodeChanged) return;
      const tail = document.createTextNode(text.slice(cursor));
      fragment.appendChild(tail);
      if (node === activeNode) caretTarget = tail;
      node.replaceWith(fragment);
      changed = true;
    });
    if (caretTarget && sel) {
      const caret = document.createRange();
      caret.setStart(caretTarget, caretTarget.length);
      caret.collapse(true);
      sel.removeAllRanges();
      sel.addRange(caret);
      caminataRange = caret.cloneRange();
    }
    if (changed) guardarCaminataFormateo();
    return changed;
  }

  function caminataInsertarLineaHorizontal() {
    const preview = document.getElementById('caminataPreview');
    if (!preview || !caminataRange) return;
    caminataRestaurarSeleccion();
    const sel = window.getSelection();
    if (!sel.rangeCount) return;
    const range = sel.getRangeAt(0).cloneRange();
    if (!preview.contains(range.commonAncestorContainer)) return;
    range.collapse(false);
    const hr = document.createElement('hr');
    range.insertNode(hr);
    const after = document.createRange();
    after.setStartAfter(hr);
    after.collapse(true);
    sel.removeAllRanges();
    sel.addRange(after);
    caminataRange = after.cloneRange();
    preview.focus();
    actualizarBotonesAlineacion(false);
    guardarCaminataFormateo();
  }

  function caminataWrapTag(tag) {
    const preview = document.getElementById('caminataPreview');
    if (!preview) return;
    caminataRestaurarSeleccion();
    preview.focus();
    const sel = window.getSelection();
    if (sel.rangeCount === 0 || sel.getRangeAt(0).collapsed) return;
    const range = sel.getRangeAt(0);
    try {
      const wrapper = document.createElement(tag);
      range.surroundContents(wrapper);
    } catch (e) {
      const frag = range.extractContents();
      if (!frag || !frag.textContent) return;
      const wrapper = document.createElement(tag);
      wrapper.appendChild(frag);
      range.insertNode(wrapper);
    }
    guardarCaminataFormateo();
  }

  function caminataTransformarTexto(accion) {
    const preview = document.getElementById('caminataPreview');
    if (!preview || !accion) return;
    const multi = caminataElementosMultiseleccionados();
    if (multi.length) {
      multi.forEach(el => {
        const text = el.textContent;
        if (accion === 'uppercase') el.textContent = text.toUpperCase();
        else if (accion === 'lowercase') el.textContent = text.toLowerCase();
        else if (accion === 'titlecase') el.textContent = text.toLowerCase().replace(/(?:^|\s)\S/g, m => m.toUpperCase());
        el.removeAttribute('data-caminata-multiselect');
      });
      _caminataMultiseleccionActiva = false;
      guardarCaminataFormateo();
      return;
    }
    caminataRestaurarSeleccion();
    const sel = window.getSelection();
    if (!sel.rangeCount || sel.getRangeAt(0).collapsed) return;
    const range = sel.getRangeAt(0);
    const nodes = [];
    const walker = document.createTreeWalker(preview, NodeFilter.SHOW_TEXT, { acceptNode: (n) => {
      try { return (range.intersectsNode ? range.intersectsNode(n) : true) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT; } catch(e) { return NodeFilter.FILTER_REJECT; }
    }});
    let t;
    while ((t = walker.nextNode())) nodes.push(t);
    if (nodes.length === 0) return;
    let changed = false;
    nodes.forEach(node => {
      const full = node.textContent;
      let start = 0, end = full.length;
      if (node === range.startContainer) start = range.startOffset;
      if (node === range.endContainer) end = range.endOffset;
      if (start >= end) return;
      const original = full.substring(start, end);
      let transformed = original;
      if (accion === 'uppercase') transformed = original.toUpperCase();
      else if (accion === 'lowercase') transformed = original.toLowerCase();
      else if (accion === 'titlecase') transformed = original.toLowerCase().replace(/(?:^|\s)\S/g, (m) => m.toUpperCase());
      if (transformed !== original) {
        node.textContent = full.substring(0, start) + transformed + full.substring(end);
        changed = true;
      }
    });
    if (changed) preview.focus();
    guardarCaminataFormateo();
  }

  function caminataBloquesSeleccionados() {
    const preview = document.getElementById('caminataPreview');
    const sel = window.getSelection();
    if (!preview || sel.rangeCount === 0) return [];
    const bloques = Array.from(preview.querySelectorAll('p, div:not(.caminata-embed), h1, h2, h3, h4, h5, h6, li, blockquote'));
    const r = sel.getRangeAt(0);
    if (r.collapsed) {
      let node = r.commonAncestorContainer;
      if (node.nodeType === Node.TEXT_NODE) node = node.parentElement;
      while (node && node !== preview) {
        if (bloques.includes(node)) return [node];
        node = node.parentElement;
      }
      return [];
    }
    return bloques.filter(el => sel.containsNode(el, true));
  }

  function caminataInterlineado(valor) {
    const multi = caminataElementosMultiseleccionados();
    if (multi.length && valor) {
      const blocks = new Set(multi.map(el => el.closest('p, div, h1, h2, h3, h4, h5, h6, li, blockquote')).filter(Boolean));
      blocks.forEach(el => { el.style.lineHeight = valor; });
      multi.forEach(el => el.removeAttribute('data-caminata-multiselect'));
      _caminataMultiseleccionActiva = false;
      guardarCaminataFormateo();
      return;
    }
    caminataRestaurarSeleccion();
    const bloques = caminataBloquesSeleccionados();
    if (bloques.length === 0 || !valor) return;
    document.getElementById('caminataPreview').focus();
    bloques.forEach(el => { el.style.lineHeight = valor; });
    guardarCaminataFormateo();
  }

  function caminataCapitular() {
    caminataRestaurarSeleccion();
    const bloques = caminataBloquesSeleccionados();
    if (bloques.length === 0) return;
    document.getElementById('caminataPreview').focus();
    bloques.forEach(el => { el.classList.toggle('caminata-capital'); });
    guardarCaminataFormateo();
  }

