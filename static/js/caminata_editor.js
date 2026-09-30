// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
  document.addEventListener('DOMContentLoaded', function() {
    try { document.execCommand('styleWithCSS', false, true); } catch(e) {}
  });

  let _caminataMultiseleccionActiva = false;
  let _caminataMarcandoSeleccion = false;

  function caminataElementosMultiseleccionados() {
    const preview = document.getElementById('caminataPreview');
    return preview ? Array.from(preview.querySelectorAll('[data-caminata-multiselect="true"]')) : [];
  }

  function caminataContenidoLimpio() {
    const preview = document.getElementById('caminataPreview');
    if (!preview) return '';
    const clone = preview.cloneNode(true);
    clone.querySelectorAll('[data-caminata-multiselect="true"]').forEach(el => {
      el.removeAttribute('data-caminata-multiselect');
      if (el.tagName === 'SPAN' && !el.attributes.length) el.replaceWith(...Array.from(el.childNodes));
    });
    return clone.innerHTML;
  }

  function actualizarEstadoMultiseleccion(message) {
    const button = document.getElementById('caminataMultiSelectButton');
    const status = document.getElementById('caminataSaveStatus');
    const count = caminataElementosMultiseleccionados().length;
    if (button) {
      button.classList.toggle('btn-success', _caminataMultiseleccionActiva);
      button.classList.toggle('btn-light', !_caminataMultiseleccionActiva);
      button.innerHTML = `<i class="bi bi-ui-checks me-1"></i>${_caminataMultiseleccionActiva ? `Multiselección (${count})` : 'Multiselección'}`;
      button.title = _caminataMultiseleccionActiva ? 'Seleccioná otro fragmento o aplicá un formato' : 'Activar multiselección';
    }
    if (status && message) status.textContent = message;
  }

  function caminataAlternarMultiseleccion() {
    _caminataMultiseleccionActiva = !_caminataMultiseleccionActiva;
    actualizarEstadoMultiseleccion(_caminataMultiseleccionActiva
      ? 'Multiselección activa: seleccioná un fragmento y soltá. Repetí para agregar más.'
      : 'Multiselección finalizada.');
  }

  function caminataAgregarRangoMultiseleccion() {
    if (!_caminataMultiseleccionActiva) return;
    const preview = document.getElementById('caminataPreview');
    const sel = window.getSelection();
    if (!preview || !sel.rangeCount || sel.getRangeAt(0).collapsed) return;
    const range = sel.getRangeAt(0);
    if (!preview.contains(range.commonAncestorContainer)) return;
    const marker = document.createElement('span');
    marker.dataset.caminataMultiselect = 'true';
    _caminataMarcandoSeleccion = true;
    try {
      range.surroundContents(marker);
    } catch (e) {
      const fragment = range.extractContents();
      marker.appendChild(fragment);
      range.insertNode(marker);
    }
    sel.removeAllRanges();
    setTimeout(() => { _caminataMarcandoSeleccion = false; }, 0);
    actualizarEstadoMultiseleccion(`${caminataElementosMultiseleccionados().length} fragmento(s) agregado(s). Seleccioná otro o aplicá un formato.`);
    actualizarBotonesAlineacion(false);
  }

  function caminataAplicarMultiseleccion(styles) {
    const selected = caminataElementosMultiseleccionados();
    if (!selected.length) return false;
    selected.forEach(el => {
      Object.entries(styles).forEach(([name, value]) => { el.style[name] = value; });
      el.removeAttribute('data-caminata-multiselect');
    });
    _caminataMultiseleccionActiva = false;
    actualizarEstadoMultiseleccion('Formato aplicado a toda la multiselección.');
    guardarCaminataFormateo();
    return true;
  }

  function caminataAlinear(align) {
    const preview = document.getElementById('caminataPreview');
    if (!preview) return;
    const css = align === 'full' ? 'justify' : align;
    const multi = caminataElementosMultiseleccionados();
    if (multi.length) {
      const blocks = new Set(multi.map(el => el.closest('p, div, h1, h2, h3, h4, h5, h6, li, blockquote, ul, ol')).filter(Boolean));
      blocks.forEach(el => { el.style.textAlign = css; });
      multi.forEach(el => el.removeAttribute('data-caminata-multiselect'));
      _caminataMultiseleccionActiva = false;
      actualizarBotonesAlineacion(false);
      guardarCaminataFormateo();
      return;
    }
    caminataRestaurarSeleccion();
    const sel = window.getSelection();
    if (!sel.rangeCount || sel.getRangeAt(0).collapsed) return;
    const bloques = caminataBloquesSeleccionados();
    if (bloques.length === 0) return;
    bloques.forEach(el => { el.style.textAlign = css; });
    guardarCaminataFormateo();
  }

  function caminataList(tipo) {
    const preview = document.getElementById('caminataPreview');
    if (!preview) return;
    caminataRestaurarSeleccion();
    const sel = window.getSelection();
    let node = null;
    if (sel.rangeCount > 0) node = sel.getRangeAt(0).commonAncestorContainer;
    if (node && node.nodeType === Node.TEXT_NODE) node = node.parentElement;
    let bloques = caminataBloquesSeleccionados();
    if (bloques.length === 0 && node) {
      const posibles = Array.from(preview.querySelectorAll('p, div:not(.caminata-embed), h1, h2, h3, h4, h5, h6, li, blockquote'));
      while (node && node !== preview) {
        if (posibles.includes(node)) { bloques = [node]; break; }
        node = node.parentElement;
      }
    }
    if (bloques.length === 0) return;
    const lists = new Set();
    bloques.forEach(el => {
      const list = el.closest && el.closest('ul, ol');
      if (list) lists.add(list);
    });
    if (lists.size === 1) {
      const list = Array.from(lists)[0];
      const parent = list.parentElement;
      Array.from(list.children).forEach(li => {
        const p = document.createElement('p');
        p.innerHTML = li.innerHTML;
        p.className = li.className || '';
        p.style.cssText = li.style.cssText;
        parent.insertBefore(p, list);
      });
      parent.removeChild(list);
    } else {
      const list = document.createElement(tipo);
      const parent = bloques[0].parentElement;
      bloques.forEach(el => {
        const li = document.createElement('li');
        li.innerHTML = el.innerHTML;
        li.className = el.className || '';
        li.style.cssText = el.style.cssText;
        list.appendChild(li);
      });
      parent.insertBefore(list, bloques[0]);
      bloques.forEach(el => parent.removeChild(el));
    }
    preview.focus();
    guardarCaminataFormateo();
  }

  function caminataExecCmd(command) {
    const preview = document.getElementById('caminataPreview');
    if (!preview) return;
    const multiStyles = {
      bold: {fontWeight: '700'},
      italic: {fontStyle: 'italic'},
      underline: {textDecoration: 'underline'},
      strikeThrough: {textDecoration: 'line-through'}
    };
    if (multiStyles[command] && caminataAplicarMultiseleccion(multiStyles[command])) return;
    if (command === 'justifyLeft' || command === 'justifyCenter' || command === 'justifyRight' || command === 'justifyFull') {
      const align = command.replace('justify', '').toLowerCase();
      caminataAlinear(align);
      return;
    }
    if (command === 'insertUnorderedList' || command === 'insertOrderedList') {
      caminataList(command === 'insertUnorderedList' ? 'ul' : 'ol');
      return;
    }
    if (command === 'undo' || command === 'redo') {
      navegarHistorialCaminata(command === 'undo' ? -1 : 1);
      return;
    }
    preview.focus();
    caminataRestaurarSeleccion();
    try { document.execCommand('styleWithCSS', false, true); } catch(e) {}
    document.execCommand(command, false, null);
    preview.focus();
    guardarCaminataFormateo();
  }

  function caminataHighlight(color) {
    if (!color) return;
    if (caminataAplicarMultiseleccion({backgroundColor: color})) return;
    caminataRestaurarSeleccion();
    try { document.execCommand('styleWithCSS', false, true); } catch(e) {}
    document.getElementById('caminataPreview').focus();
    document.execCommand('hiliteColor', false, color);
    guardarCaminataFormateo();
  }

  function caminataClearFormat() {
    const preview = document.getElementById('caminataPreview');
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
    // Quitar clases especiales
    preview.querySelectorAll('.caminata-capital').forEach(el => el.classList.remove('caminata-capital'));
    // Convertir viñetas y numeración a párrafos planos
    preview.querySelectorAll('li').forEach(li => {
      const p = document.createElement('p');
      p.innerHTML = li.innerHTML;
      li.replaceWith(p);
    });
    preview.querySelectorAll('ul, ol').forEach(list => {
      list.replaceWith(...Array.from(list.childNodes));
    });
    // Eliminar estilos en línea residuales
    preview.querySelectorAll('p, span, b, i, u, s, strike, font, mark, strong, em, li, div, h1, h2, h3, h4, h5, h6, blockquote').forEach(el => el.removeAttribute('style'));
    // Justificar todo
    const all = document.createRange();
    all.selectNodeContents(preview);
    sel.removeAllRanges();
    sel.addRange(all);
    try { document.execCommand('styleWithCSS', false, true); } catch(e) {}
    document.execCommand('justifyFull', false, null);
    // Interlineado normal
    preview.querySelectorAll('p, li, div, h1, h2, h3, h4, h5, h6, blockquote').forEach(el => { el.style.lineHeight = 'normal'; });
    sel.removeAllRanges();
    guardarCaminataFormateo();
  }

  function caminataMarcarSeleccion() {
    const select = document.getElementById('caminataColorMarcador');
    if (!select) return;
    caminataRestaurarSeleccion();
    caminataHighlight(select.value);
  }
