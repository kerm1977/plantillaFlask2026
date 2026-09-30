// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
  let _videoSeleccionadoContexto = null;
  let _guardarCaminataTimer = null;
  let _guardarCaminataFormateoTimer = null;
  let originalItinerario = '';
  let caminataRange = null;
  let _caminataStale = false;
  let _caminataSaveInProgress = false;
  let _caminataSavePending = false;
  let _caminataPendingSilent = false;
  const CAMINATA_HISTORY_KEY = `caminata-history-${CAMINATA_ID}`;
  const CAMINATA_HISTORY_LIMIT = 100;
  let _caminataHistory = [];
  let _caminataHistoryIndex = -1;
  let _caminataApplyingHistory = false;

  function guardarHistorialCaminata() {
    try {
      sessionStorage.setItem(CAMINATA_HISTORY_KEY, JSON.stringify({
        hash: ITINERARIO_HASH,
        states: _caminataHistory,
        index: _caminataHistoryIndex
      }));
    } catch (e) {}
  }

  function registrarHistorialCaminata() {
    if (_caminataApplyingHistory) return;
    const preview = document.getElementById('caminataPreview');
    if (!preview) return;
    const content = caminataContenidoLimpio();
    if (_caminataHistory[_caminataHistoryIndex] === content) return;
    _caminataHistory = _caminataHistory.slice(0, _caminataHistoryIndex + 1);
    _caminataHistory.push(content);
    if (_caminataHistory.length > CAMINATA_HISTORY_LIMIT) _caminataHistory.shift();
    _caminataHistoryIndex = _caminataHistory.length - 1;
    guardarHistorialCaminata();
  }

  function iniciarHistorialCaminata() {
    const preview = document.getElementById('caminataPreview');
    if (!preview) return;
    try {
      const saved = JSON.parse(sessionStorage.getItem(CAMINATA_HISTORY_KEY) || 'null');
      if (saved && saved.hash === ITINERARIO_HASH && Array.isArray(saved.states) && saved.states.length) {
        _caminataHistory = saved.states.slice(-CAMINATA_HISTORY_LIMIT);
        _caminataHistoryIndex = Math.min(Math.max(Number(saved.index) || 0, 0), _caminataHistory.length - 1);
        _caminataHistory[_caminataHistoryIndex] = preview.innerHTML;
        guardarHistorialCaminata();
        return;
      }
    } catch (e) {}
    _caminataHistory = [preview.innerHTML];
    _caminataHistoryIndex = 0;
    guardarHistorialCaminata();
  }

  function reiniciarHistorialCaminata(savedContent) {
    const preview = document.getElementById('caminataPreview');
    const currentContent = preview ? preview.innerHTML : savedContent;
    _caminataHistory = [savedContent];
    _caminataHistoryIndex = 0;
    if (currentContent !== savedContent) {
      _caminataHistory.push(currentContent);
      _caminataHistoryIndex = 1;
    }
    guardarHistorialCaminata();
  }

  function navegarHistorialCaminata(direction) {
    const nextIndex = _caminataHistoryIndex + direction;
    if (nextIndex < 0 || nextIndex >= _caminataHistory.length) return;
    const preview = document.getElementById('caminataPreview');
    if (!preview) return;
    _caminataApplyingHistory = true;
    _caminataHistoryIndex = nextIndex;
    preview.innerHTML = _caminataHistory[_caminataHistoryIndex];
    _caminataApplyingHistory = false;
    guardarHistorialCaminata();
    preview.focus();
    guardarCaminataFormateo();
  }

  function actualizarBotonesAlineacion(enabled) {
    const hasMulti = caminataElementosMultiseleccionados().length > 0;
    document.querySelectorAll('.caminata-align-button').forEach(button => {
      button.disabled = !(enabled || hasMulti);
    });
  }

  document.addEventListener('selectionchange', function() {
    const preview = document.getElementById('caminataPreview');
    const sel = window.getSelection();
    if (!preview || !sel.rangeCount) return;
    const r = sel.getRangeAt(0);
    if (preview.contains(r.commonAncestorContainer)) {
      caminataRange = r.cloneRange();
      actualizarBotonesAlineacion(!r.collapsed);
    }
  });

  function caminataRestaurarSeleccion() {
    if (!caminataRange) return;
    const preview = document.getElementById('caminataPreview');
    if (!preview) return;
    const sel = window.getSelection();
    try {
      const start = caminataRange.startContainer;
      const end = caminataRange.endContainer;
      if (preview.contains(start) && preview.contains(end)) {
        preview.focus();
        sel.removeAllRanges();
        sel.addRange(caminataRange);
      }
    } catch(e) {}
  }
