/* ══ BITÁCORA — exportar / compartir / pulsación larga ══
   Independiente. Depende de bitacora.js (btEntryId, _btPayload). */
/* global btEntryId, _btPayload, _btAutoSave, btPages, btToggleCompartir,
          _btRenderPagesUI, btSelPagina */

function _btEnlace() {
  return btEntryId ? location.origin + '/bitacora/' + btEntryId : null;
}

function btCopiarEnlace(url) {
  const u = url || _btEnlace();
  if (!u) { alert('Guardá la entrada primero para tener enlace.'); return; }
  navigator.clipboard.writeText(u).then(
    () => alert('Enlace copiado:\n' + u),
    () => prompt('Copiá el enlace:', u));
}

/* Compartir el enlace por WhatsApp (a quien sea) */
function btCompartirWA() {
  const u = _btEnlace();
  if (!u) { alert('Guardá la entrada primero para poder compartirla.'); return; }
  const titulo = (document.getElementById('btTitulo') || {}).value || 'Bitácora';
  window.open('https://wa.me/?text=' +
    encodeURIComponent(titulo + ' — ' + u), '_blank');
}

/* Compartir con un usuario del menú de selección */
function btCompartirUsuario() {
  const sel = document.getElementById('btShareUser');
  if (!sel || !sel.value) { alert('Elegí un usuario primero.'); return; }
  const vis = document.getElementById('btVisibilidad');
  if (vis) vis.value = 'seleccion';
  btToggleCompartir();
  const chk = document.querySelector(
    '.bt-share-check[value="' + sel.value + '"]');
  if (chk) chk.checked = true;
  _btAutoSave();
  const nombre = sel.options[sel.selectedIndex].text.trim();
  alert('La entrada se compartirá con ' + nombre + '.');
}

/* Exportar la entrada completa a un archivo .json */
function btExportarJSON() {
  const data = _btPayload();
  data.exportado = new Date().toISOString();
  data.tipo = 'bitacora-entry';
  const blob = new Blob([JSON.stringify(data, null, 2)],
    {type: 'application/json'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'bitacora-' + (btEntryId || 'nueva') + '.json';
  a.click();
  URL.revokeObjectURL(a.href);
}

/* Importar entrada desde un archivo .json */
function btImportarJSON(input) {
  const f = input.files && input.files[0];
  if (!f) return;
  const rd = new FileReader();
  rd.onload = () => {
    try {
      const d = JSON.parse(rd.result);
      if (d.titulo !== undefined) {
        document.getElementById('btTitulo').value = d.titulo || '';
      }
      if (d.descripcion !== undefined) {
        document.getElementById('btDescripcion').value = d.descripcion || '';
      }
      const vis = document.getElementById('btVisibilidad');
      if (vis && d.visibilidad) { vis.value = d.visibilidad; btToggleCompartir(); }
      btPages = Array.isArray(d.paginas) && d.paginas.length
        ? d.paginas : [d.contenido || ''];
      btPageIdx = 0;
      document.getElementById('btEditor').innerHTML = btPages[0];
      _btRenderPagesUI();
      _btAutoSave();
      alert('Entrada importada.');
    } catch (e) {
      alert('Archivo JSON no válido.');
    }
    input.value = '';
  };
  rd.readAsText(f);
}

/* Pulsación larga sobre "Editar entrada" → copia el enlace de la entrada */
let _btLpTimer = null, _btLpFired = false;
document.addEventListener('DOMContentLoaded', () => {
  const h = document.getElementById('btAcEditarBtn');
  if (!h) return;
  const start = () => {
    _btLpTimer = setTimeout(() => {
      _btLpFired = true;
      btCopiarEnlace();
    }, 600);
  };
  const stop = () => clearTimeout(_btLpTimer);
  h.addEventListener('mousedown', start);
  h.addEventListener('mouseup', stop);
  h.addEventListener('mouseleave', stop);
  h.addEventListener('touchstart', start, {passive: true});
  h.addEventListener('touchend', stop);
  h.addEventListener('touchmove', stop);
  h.addEventListener('click', (e) => {
    if (_btLpFired) {
      e.preventDefault();
      e.stopImmediatePropagation();
      _btLpFired = false;
    }
  }, true);
});
