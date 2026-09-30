// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
// WYSIWYG reutilizable para La Tribu — parte media (subida, paste/drop, video, save)
window.Wysiwyg = Object.assign(window.Wysiwyg || {}, (function() {
  'use strict';

  function _editor(editorId) { return document.getElementById(editorId); }

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

  return {
    dataURLtoBlob, uploadFile, uploadImage, processBase64Images,
    handlePaste, handleDrop, setupUploadListeners,
    imageAlign, insertarVideo, insertarVideoDesdeModal, save
  };
})());
