// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
  const MAX_CAMINATA_UPLOAD_MB = 100;

  async function caminataUploadImage(input) {
    const file = input.files[0];
    if (!file) return;
    if (file.size > MAX_CAMINATA_UPLOAD_MB * 1024 * 1024) {
      alert('El archivo pesa ' + (file.size / 1024 / 1024).toFixed(1) + 'MB. El límite es ' + MAX_CAMINATA_UPLOAD_MB + 'MB.');
      input.value = '';
      return;
    }
    const formData = new FormData();
    formData.append('media', file);
    let r;
    try {
      r = await fetch(`/api/caminatas-2027/${CAMINATA_ID}/upload-image`, {method: 'POST', body: formData});
      if (!r.ok) {
        const text = await r.text();
        alert('Error del servidor al subir: ' + r.status + ' ' + text.slice(0, 100));
        input.value = '';
        return;
      }
      const data = await r.json();
      if (data.ok) {
        document.getElementById('caminataPreview').focus();
        const kind = data.kind === 'video' || file.type.startsWith('video/') ? 'video' : 'image';
        let html = '';
        if (kind === 'video') {
          html = `<video src="${data.url}" controls playsinline style="max-width:100%; border-radius:0.5rem; display:block; margin:1rem auto;" preload="metadata"></video>`;
        } else {
          html = `<img src="${data.url}" class="img-fluid rounded-3" style="max-width:100%;" alt="Imagen">`;
        }
        document.execCommand('insertHTML', false, html);
        await caminataSave(true);
      } else {
        alert(data.error || 'Error al subir archivo');
      }
    } catch(e) {
      console.error(e);
      alert('Error de conexión al subir archivo: ' + (e && e.message || ''));
    }
    input.value = '';
  }

  function crearMenuContextualVideo() {
    let menu = document.getElementById('caminataVideoContextMenu');
    if (menu) return menu;
    menu = document.createElement('div');
    menu.id = 'caminataVideoContextMenu';
    menu.style.position = 'fixed';
    menu.style.display = 'none';
    menu.style.zIndex = '9999';
    menu.style.background = '#fff';
    menu.style.border = '1px solid #ddd';
    menu.style.borderRadius = '0.5rem';
    menu.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
    menu.style.minWidth = '220px';
    menu.style.padding = '0.5rem';
    menu.innerHTML = `
      <div class="d-grid gap-1">
        <button type="button" class="btn btn-sm btn-light text-start" onclick="moverVideoCaminata('inicio')"><i class="bi bi-arrow-bar-up me-2"></i>Debajo del título</button>
        <button type="button" class="btn btn-sm btn-light text-start" onclick="moverVideoCaminata('finTexto')"><i class="bi bi-text-right me-2"></i>Al final del texto</button>
        <button type="button" class="btn btn-sm btn-light text-start" onclick="moverVideoCaminata('fin')"><i class="bi bi-arrow-bar-down me-2"></i>Al final de la sección</button>
        <div class="dropdown-divider"></div>
        <button type="button" class="btn btn-sm btn-light text-start text-danger" onclick="eliminarVideoCaminata()"><i class="bi bi-trash me-2"></i>Eliminar</button>
      </div>
    `;
    document.body.appendChild(menu);
    document.addEventListener('click', function(e) {
      if (menu && !menu.contains(e.target) && menu.style.display === 'block') {
        menu.style.display = 'none';
      }
    });
    return menu;
  }

  async function moverVideoCaminata(destino) {
    const menu = document.getElementById('caminataVideoContextMenu');
    const video = _videoSeleccionadoContexto;
    const preview = document.getElementById('caminataPreview');
    if (!video || !preview) return;
    if (destino === 'inicio') {
      const primero = preview.firstElementChild;
      if (primero && primero.nextElementSibling) {
        preview.insertBefore(video, primero.nextElementSibling);
      } else if (primero) {
        primero.after(video);
      } else {
        preview.appendChild(video);
      }
    } else if (destino === 'finTexto') {
      let bloqueTexto = null;
      for (let i = preview.children.length - 1; i >= 0; i--) {
        const el = preview.children[i];
        const esMedia = ['IMG', 'VIDEO', 'AUDIO', 'IFRAME'].includes(el.tagName) || (el.classList && el.classList.contains('caminata-embed'));
        if (!esMedia && el.innerText && el.innerText.trim().length > 0) {
          bloqueTexto = el;
          break;
        }
      }
      if (bloqueTexto) {
        bloqueTexto.after(video);
      } else if (preview.lastElementChild) {
        preview.lastElementChild.after(video);
      } else {
        preview.appendChild(video);
      }
    } else if (destino === 'fin') {
      preview.appendChild(video);
    }
    if (menu) menu.style.display = 'none';
    await caminataSave(true);
  }

  async function eliminarVideoCaminata() {
    const menu = document.getElementById('caminataVideoContextMenu');
    const video = _videoSeleccionadoContexto;
    if (video && video.parentElement) {
      video.parentElement.removeChild(video);
    }
    if (menu) menu.style.display = 'none';
    _videoSeleccionadoContexto = null;
    await caminataSave(true);
  }

  function caminataImageAlign(position) {
    caminataRestaurarSeleccion();
    const sel = window.getSelection();
    if (!sel.rangeCount) return;
    let node = sel.getRangeAt(0).commonAncestorContainer;
    if (node.nodeType === Node.TEXT_NODE) node = node.parentElement;
    const img = node && node.tagName === 'IMG' ? node : (node ? node.querySelector('img') : null);
    if (!img) return;
    if (position === 'left') {
      img.style.float = 'left'; img.style.margin = '0 1rem 1rem 0'; img.style.display = 'inline';
    } else if (position === 'right') {
      img.style.float = 'right'; img.style.margin = '0 0 1rem 1rem'; img.style.display = 'inline';
    } else {
      img.style.float = 'none'; img.style.display = 'block'; img.style.margin = '0 auto 1rem auto';
    }
    guardarCaminataFormateo();
  }

  function caminataInsertarVideo() {
    const modalEl = document.getElementById('insertarVideoModal');
    if (!modalEl) return;
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    const urlInput = document.getElementById('insertarVideoUrl');
    const feedback = document.getElementById('insertarVideoFeedback');
    if (urlInput) urlInput.value = '';
    if (feedback) { feedback.textContent = ''; feedback.style.display = 'none'; }
    modal.show();
  }

  function caminataEliminarSeleccion() {
    const multi = caminataElementosMultiseleccionados();
    if (multi.length) {
      multi.forEach(el => el.remove());
      _caminataMultiseleccionActiva = false;
      const button = document.getElementById('caminataMultiSelectButton');
      if (button) { button.classList.remove('btn-success'); button.classList.add('btn-light'); }
      guardarCaminataFormateo();
      return;
    }
    const sel = window.getSelection();
    if (!sel.rangeCount) return;
    if (!sel.getRangeAt(0).collapsed) {
      document.execCommand('delete');
      guardarCaminataFormateo();
      return;
    }
    let node = sel.getRangeAt(0).commonAncestorContainer;
    if (node.nodeType === Node.TEXT_NODE) node = node.parentElement;
    let el = node;
    while (el && el.id !== 'caminataPreview') {
      const esVideo = (el.classList && el.classList.contains('caminata-embed')) || (el.style && el.style.paddingBottom === '56.25%');
      if (esVideo) {
        const r = document.createRange();
        r.selectNode(el);
        sel.removeAllRanges();
        sel.addRange(r);
        try { document.execCommand('styleWithCSS', false, true); } catch(e) {}
        document.getElementById('caminataPreview').focus();
        document.execCommand('delete');
        guardarCaminataFormateo();
        return;
      }
      el = el.parentElement;
    }
  }

  function insertarVideoDesdeModal() {
    const urlInput = document.getElementById('insertarVideoUrl');
    const feedback = document.getElementById('insertarVideoFeedback');
    const u = (urlInput && urlInput.value || '').trim();
    if (!u) {
      feedback.textContent = 'Por favor pega un enlace.';
      feedback.style.display = 'block';
      return;
    }
    let html = '';
    const ytMatch = u.match(/(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/|youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})/);
    if (ytMatch && ytMatch[1]) {
      html = `<div class="caminata-embed" style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:0.5rem;max-width:100%;margin:1rem 0;"><iframe style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;" src="https://www.youtube.com/embed/${ytMatch[1]}" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen loading="lazy" referrerpolicy="strict-origin-when-cross-origin"></iframe></div>`;
    } else if (u.includes('facebook.com') || u.includes('fb.watch')) {
      html = `<div class="caminata-embed" style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:0.5rem;max-width:100%;margin:1rem 0;"><iframe style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;" src="https://www.facebook.com/plugins/video.php?href=${encodeURIComponent(u)}&show_text=0&width=560" allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share" allowfullscreen loading="lazy" scrolling="no" frameborder="0"></iframe></div>`;
    } else {
      feedback.textContent = 'Enlace no soportado. Por ahora solo YouTube y Facebook.';
      feedback.style.display = 'block';
      return;
    }
    caminataRestaurarSeleccion();
    document.getElementById('caminataPreview').focus();
    document.execCommand('insertHTML', false, html);
    guardarCaminataFormateo();
    const modalEl = document.getElementById('insertarVideoModal');
    const modal = bootstrap.Modal.getInstance(modalEl) || bootstrap.Modal.getOrCreateInstance(modalEl);
    modal.hide();
  }

