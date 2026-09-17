// WYSIWYG reutilizable para La Tribu
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

  function dataURLtoBlob(dataurl) {
    const arr = dataurl.split(',');
    const mime = arr[0].match(/:(.*?);/)[1];
    const bstr = atob(arr[1]);
    let n = bstr.length;
    const u8arr = new Uint8Array(n);
    while (n--) u8arr[n] = bstr.charCodeAt(n);
    return new Blob([u8arr], { type: mime });
  }

  async function uploadFile(editorId, file, uploadUrl, onUpload) {
    const formData = new FormData();
    formData.append('media', file);
    try {
      const r = await fetch(uploadUrl, {method: 'POST', body: formData});
      const data = await r.json();
      const preview = _editor(editorId);
      if (preview) preview.focus();
      if (data.ok) {
        const kind = data.kind || (file.type && file.type.startsWith('video/') ? 'video' : 'image');
        let html = '';
        if (kind === 'video') {
          html = `<video src="${data.url}" controls playsinline style="max-width:100%; border-radius:0.5rem; display:block; margin:1rem auto;" preload="metadata"></video>`;
        } else {
          html = `<img src="${data.url}" class="img-fluid rounded-3" style="max-width:100%;" alt="Imagen">`;
        }
        try { document.execCommand('styleWithCSS', false, true); } catch(e) {}
        document.execCommand('insertHTML', false, html);
        if (typeof onUpload === 'function') onUpload();
      } else {
        alert(data.error || 'Error al subir archivo');
      }
    } catch(e) {
      alert('Error de conexión al subir archivo');
    }
  }

  async function uploadImage(editorId, input, uploadUrl, onUpload) {
    if (!input || !input.files || !input.files[0]) return;
    uploadUrl = uploadUrl || input.dataset.uploadUrl;
    if (!uploadUrl) { alert('Falta URL de subida'); return; }
    await uploadFile(editorId, input.files[0], uploadUrl, onUpload);
    input.value = '';
  }

  async function processBase64Images(editorId, uploadUrl, onUpload) {
    const editor = _editor(editorId);
    if (!editor || !uploadUrl) return;
    let changed = false;
    for (const img of Array.from(editor.querySelectorAll('img'))) {
      const src = img.getAttribute('src') || img.src;
      if (!src || (!src.startsWith('data:') && !src.startsWith('blob:'))) continue;
      try {
        let blob;
        if (src.startsWith('data:')) {
          blob = dataURLtoBlob(src);
        } else {
          const resp = await fetch(src);
          blob = await resp.blob();
        }
        const ext = (blob.type.split('/')[1] || 'png').replace(/[^a-z0-9]/gi, '').toLowerCase() || 'png';
        const fakeFile = new File([blob], `pegado.${ext}`, {type: blob.type});
        const formData = new FormData();
        formData.append('media', fakeFile);
        const r = await fetch(uploadUrl, {method: 'POST', body: formData});
        const data = await r.json();
        if (data.ok) {
          img.src = data.url;
          changed = true;
        }
      } catch(e) { console.error('Error convirtiendo imagen pegada:', e); }
    }
    for (const v of Array.from(editor.querySelectorAll('video source, video'))) {
      const src = v.getAttribute('src') || v.src;
      if (!src || (!src.startsWith('data:') && !src.startsWith('blob:'))) continue;
      try {
        let blob;
        if (src.startsWith('data:')) blob = dataURLtoBlob(src);
        else { const resp = await fetch(src); blob = await resp.blob(); }
        const ext = (blob.type.split('/')[1] || 'mp4').replace(/[^a-z0-9]/gi, '').toLowerCase() || 'mp4';
        const fakeFile = new File([blob], `pegado.${ext}`, {type: blob.type});
        const formData = new FormData();
        formData.append('media', fakeFile);
        const r = await fetch(uploadUrl, {method: 'POST', body: formData});
        const data = await r.json();
        if (data.ok) { v.src = data.url; changed = true; }
      } catch(e) { console.error('Error convirtiendo video pegado:', e); }
    }
    if (changed && typeof onUpload === 'function') onUpload();
  }

  function handlePaste(e, editorId, uploadUrl, onUpload) {
    const cd = e.clipboardData || window.clipboardData;
    if (!cd) return;
    const files = Array.from(cd.files || []);
    if (files.length > 0) {
      e.preventDefault();
      files.forEach(file => uploadFile(editorId, file, uploadUrl, onUpload));
      return;
    }
    if (Array.from(cd.types || []).includes('text/html')) {
      e.preventDefault();
      const html = cd.getData('text/html');
      try { document.execCommand('styleWithCSS', false, true); } catch(err) {}
      document.execCommand('insertHTML', false, html);
      setTimeout(() => processBase64Images(editorId, uploadUrl, onUpload), 100);
      return;
    }
  }

  function handleDrop(e, editorId, uploadUrl, onUpload) {
    e.preventDefault();
    const dt = e.dataTransfer;
    if (!dt) return;
    if (dt.files && dt.files.length > 0) {
      Array.from(dt.files).forEach(file => uploadFile(editorId, file, uploadUrl, onUpload));
      return;
    }
    const html = dt.getData('text/html');
    if (html) {
      try { document.execCommand('styleWithCSS', false, true); } catch(err) {}
      document.execCommand('insertHTML', false, html);
      setTimeout(() => processBase64Images(editorId, uploadUrl, onUpload), 100);
      return;
    }
    const text = dt.getData('text/plain');
    if (text) document.execCommand('insertText', false, text);
  }

  function setupUploadListeners(editorId, uploadUrl, onUpload) {
    const editor = _editor(editorId);
    if (!editor) return;
    editor.addEventListener('dragover', e => e.preventDefault());
    editor.addEventListener('dragenter', e => e.preventDefault());
    editor.addEventListener('paste', e => handlePaste(e, editorId, uploadUrl, onUpload));
    editor.addEventListener('drop', e => handleDrop(e, editorId, uploadUrl, onUpload));
  }

  function imageAlign(editorId, position) {
    const sel = window.getSelection();
    if (!sel.rangeCount) return;
    let node = sel.getRangeAt(0).commonAncestorContainer;
    if (node.nodeType === Node.TEXT_NODE) node = node.parentElement;
    let img = node;
    if (img && img.tagName !== 'IMG') img = node.querySelector('img');
    if (!img || img.tagName !== 'IMG') return;
    if (position === 'left') {
      img.style.float = 'left'; img.style.margin = '0 1rem 1rem 0'; img.style.display = 'inline';
    } else if (position === 'right') {
      img.style.float = 'right'; img.style.margin = '0 0 1rem 1rem'; img.style.display = 'inline';
    } else {
      img.style.float = 'none'; img.style.display = 'block'; img.style.margin = '0 auto 1rem auto';
    }
  }

  function insertarVideo(editorId, modalPrefix) {
    const modalEl = document.getElementById(modalPrefix + 'InsertarVideoModal');
    if (!modalEl) return;
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    const urlInput = document.getElementById(modalPrefix + 'InsertarVideoUrl');
    const feedback = document.getElementById(modalPrefix + 'InsertarVideoFeedback');
    if (urlInput) urlInput.value = '';
    if (feedback) { feedback.textContent = ''; feedback.style.display = 'none'; }
    modal.show();
  }

  function insertarVideoDesdeModal(editorId, urlInputId, feedbackId, modalId) {
    const urlInput = document.getElementById(urlInputId);
    const feedback = document.getElementById(feedbackId);
    const u = (urlInput && urlInput.value || '').trim();
    if (!u) {
      if (feedback) { feedback.textContent = 'Por favor pega un enlace.'; feedback.style.display = 'block'; }
      return;
    }
    let html = '';
    const ytMatch = u.match(/(?:youtube\.com\/(?:[^\/]+\/.+\/(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/|youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})/);
    if (ytMatch && ytMatch[1]) {
      html = `<div class="caminata-embed" style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:0.5rem;max-width:100%;margin:1rem 0;"><iframe style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;" src="https://www.youtube.com/embed/${ytMatch[1]}" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen loading="lazy" referrerpolicy="strict-origin-when-cross-origin"></iframe></div>`;
    } else if (u.includes('facebook.com') || u.includes('fb.watch')) {
      html = `<div class="caminata-embed" style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:0.5rem;max-width:100%;margin:1rem 0;"><iframe style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;" src="https://www.facebook.com/plugins/video.php?href=${encodeURIComponent(u)}&show_text=0&width=560" allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share" allowfullscreen loading="lazy" scrolling="no" frameborder="0"></iframe></div>`;
    } else {
      if (feedback) { feedback.textContent = 'Enlace no soportado. Por ahora solo YouTube y Facebook.'; feedback.style.display = 'block'; }
      return;
    }
    const preview = _editor(editorId);
    if (preview) preview.focus();
    try { document.execCommand('styleWithCSS', false, true); } catch(e) {}
    document.execCommand('insertHTML', false, html);
    const modalEl = document.getElementById(modalId);
    const modal = bootstrap.Modal.getInstance(modalEl) || bootstrap.Modal.getOrCreateInstance(modalEl);
    modal.hide();
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

  async function save(editorId, url, bodyKey, statusId, silent) {
    const statusEl = statusId ? document.getElementById(statusId) : null;
    if (statusEl && !silent) statusEl.textContent = 'Guardando...';
    const preview = _editor(editorId);
    const content = preview ? preview.innerHTML : '';
    try {
      const body = {};
      body[bodyKey] = content;
      const r = await fetch(url, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});
      const data = await r.json();
      if (data.ok && statusEl && !silent) {
        statusEl.innerHTML = '<i class="bi bi-check-circle text-success me-1"></i>Guardado';
        setTimeout(() => { if (statusEl) statusEl.textContent = ''; }, 2000);
      } else if (!data.ok && !silent) {
        alert(data.error || 'Error al guardar');
        if (statusEl) statusEl.textContent = '';
      }
    } catch(e) {
      if (!silent) {
        alert('Error de conexión al guardar');
        if (statusEl) statusEl.textContent = '';
      }
    }
  }

  function getContent(editorId) {
    const preview = _editor(editorId);
    return preview ? preview.innerHTML : '';
  }

  function setContent(editorId, html) {
    const preview = _editor(editorId);
    if (preview) preview.innerHTML = html || '';
  }

  return {
    execCmd, clearFormat, highlight, marcarSeleccion, cambiarFuente, wrapTag,
    transformarTexto, bloquesSeleccionados, interlineado, capitular, cita,
    formatBlock, uploadImage, uploadFile, processBase64Images, setupUploadListeners,
    imageAlign, insertarVideo, insertarVideoDesdeModal,
    eliminarSeleccion, save, getContent, setContent,
    guardarSeleccion, restaurarSeleccion
  };
})();
