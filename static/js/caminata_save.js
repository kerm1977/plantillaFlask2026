// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
  function mostrarEstadoGuardadoCaminata(state, message) {
    const button = document.getElementById('caminataSaveButton');
    const icon = document.getElementById('caminataSaveIcon');
    const label = document.getElementById('caminataSaveLabel');
    const status = document.getElementById('caminataSaveStatus');
    if (!button || !icon || !label) return;
    button.classList.remove('btn-outline-orange', 'btn-outline-success', 'btn-success', 'btn-outline-danger');
    if (state === 'listening') {
      button.classList.add('btn-outline-success');
      icon.className = 'bi bi-circle-fill text-success me-1 animate__animated animate__pulse animate__infinite';
      label.textContent = 'Escuchando';
    } else if (state === 'saving') {
      button.classList.add('btn-outline-success');
      icon.className = 'spinner-border spinner-border-sm text-success me-1';
      label.textContent = 'Guardando';
    } else if (state === 'saved') {
      button.classList.add('btn-success');
      icon.className = 'bi bi-check-lg me-1';
      label.textContent = 'Guardado';
    } else if (state === 'error') {
      button.classList.add('btn-outline-danger');
      icon.className = 'bi bi-exclamation-triangle me-1';
      label.textContent = 'Error';
    } else {
      button.classList.add('btn-outline-orange');
      icon.className = 'bi bi-save me-1';
      label.textContent = 'Guardar';
    }
    button.title = message || label.textContent;
    if (status) status.textContent = message || '';
  }

  function programarGuardadoCaminata(delay) {
    registrarHistorialCaminata();
    mostrarEstadoGuardadoCaminata('listening', 'Cambios detectados. Preparando autoguardado…');
    if (_guardarCaminataTimer) clearTimeout(_guardarCaminataTimer);
    if (_guardarCaminataFormateoTimer) clearTimeout(_guardarCaminataFormateoTimer);
    _guardarCaminataTimer = setTimeout(() => {
      _guardarCaminataTimer = null;
      _guardarCaminataFormateoTimer = null;
      caminataSave(true);
    }, delay);
  }

  function guardarCaminata() {
    programarGuardadoCaminata(700);
  }

  function guardarCaminataFormateo() {
    programarGuardadoCaminata(250);
  }

  function guardarCaminataAhora() {
    if (_guardarCaminataTimer) clearTimeout(_guardarCaminataTimer);
    if (_guardarCaminataFormateoTimer) clearTimeout(_guardarCaminataFormateoTimer);
    _guardarCaminataTimer = null;
    _guardarCaminataFormateoTimer = null;
    return caminataSave(true);
  }


  function caminataFormatBlock(tag) {
    const preview = document.getElementById('caminataPreview');
    if (!preview || !tag) return;
    caminataRestaurarSeleccion();
    const bloques = caminataBloquesSeleccionados();
    if (bloques.length === 0) return;
    preview.focus();
    const t = tag.toLowerCase();
    bloques.forEach(el => {
      if (el.tagName.toLowerCase() === t) return;
      const nuevo = document.createElement(t);
      nuevo.innerHTML = el.innerHTML;
      nuevo.className = el.className;
      nuevo.style.cssText = el.style.cssText;
      el.replaceWith(nuevo);
    });
    guardarCaminataFormateo();
  }

  function caminataCita() {
    caminataRestaurarSeleccion();
    const bloques = caminataBloquesSeleccionados();
    if (bloques.length === 0) return;
    const preview = document.getElementById('caminataPreview');
    if (!preview) return;
    preview.focus();
    bloques.forEach(el => {
      if (el.tagName === 'BLOCKQUOTE') {
        const p = document.createElement('p');
        p.innerHTML = el.innerHTML;
        p.className = el.className;
        p.style.cssText = el.style.cssText;
        el.replaceWith(p);
      } else {
        const bq = document.createElement('blockquote');
        bq.innerHTML = el.innerHTML;
        bq.className = el.className;
        bq.style.cssText = el.style.cssText;
        el.replaceWith(bq);
      }
    });
    guardarCaminataFormateo();
  }

  async function caminataSave(silent=false) {
    const statusEl = document.getElementById('caminataSaveStatus');
    registrarHistorialCaminata();
    if (_caminataStale && silent) {
      mostrarEstadoGuardadoCaminata('error', 'Contenido desactualizado. Recargá la página.');
      return;
    }
    if (_caminataSaveInProgress) {
      _caminataPendingSilent = _caminataSavePending ? (_caminataPendingSilent && silent) : silent;
      _caminataSavePending = true;
      return;
    }
    _caminataSaveInProgress = true;
    mostrarEstadoGuardadoCaminata('saving', silent ? 'Autoguardando…' : 'Guardando…');
    try {
      const preview = document.getElementById('caminataPreview');
      const content = preview ? caminataContenidoLimpio() : '';
      if (content === originalItinerario) {
        if (!silent) reiniciarHistorialCaminata(content);
        mostrarEstadoGuardadoCaminata('saved', 'Todo está guardado');
      } else {
        const r = await fetch(`/api/caminatas-2027/${CAMINATA_ID}/save-itinerario`, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({itinerario: content, hash: ITINERARIO_HASH})
        });
        const data = await r.json();
        if (data.ok) {
          originalItinerario = content;
          if (data.hash) ITINERARIO_HASH = data.hash;
          if (silent) guardarHistorialCaminata();
          else reiniciarHistorialCaminata(content);
          mostrarEstadoGuardadoCaminata('saved', silent ? 'Todos los cambios se autoguardaron' : 'Todos los cambios se guardaron');
        } else if (data.stale) {
          _caminataStale = true;
          mostrarEstadoGuardadoCaminata('error', 'El contenido cambió en otro dispositivo. Recargá la página.');
          if (!silent) alert(data.error || 'El contenido cambió en otro dispositivo. Recargá la página.');
        } else {
          mostrarEstadoGuardadoCaminata('error', data.error || 'Error al guardar');
          if (!silent) alert(data.error || 'Error al guardar');
        }
      }
    } catch(e) {
      mostrarEstadoGuardadoCaminata('error', 'Error de conexión al guardar');
      if (!silent) alert('Error de conexión al guardar');
    } finally {
      _caminataSaveInProgress = false;
      if (_caminataSavePending) {
        _caminataSavePending = false;
        const nextSilent = _caminataPendingSilent;
        _caminataPendingSilent = false;
        await caminataSave(nextSilent);
      }
    }
  }

