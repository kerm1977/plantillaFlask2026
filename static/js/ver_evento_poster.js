// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
// ver_evento_poster.js - Póster del detalle del evento: clic para ampliar, descargar y compartir
(function () {
  var modalEl = document.getElementById('posterModal');
  var poster = document.querySelector('.event-poster');
  if (!modalEl || !poster) return;
  document.body.appendChild(modalEl);
  var big = document.getElementById('posterModalImg');
  var msg = document.getElementById('posterModalMsg');
  var dl = document.getElementById('posterDescargar');
  var nombre = modalEl.dataset.nombre || 'Evento';
  var archivo = null, src = '';

  poster.style.cursor = 'zoom-in';
  poster.title = 'Tocar para ampliar, descargar o compartir';

  function nombreArchivo(url) {
    var ext = ((url.split('?')[0].match(/\.([a-zA-Z0-9]+)$/) || [])[1] || 'png').toLowerCase();
    return 'Poster_' + nombre.normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-zA-Z0-9]+/g, '_').replace(/^_|_$/g, '') + '.' + ext;
  }

  poster.addEventListener('click', function () {
    src = poster.currentSrc || poster.src;
    big.src = src;
    dl.href = src;
    dl.download = nombreArchivo(src);
    msg.textContent = '';
    archivo = null;
    // Se precarga el archivo para que "Compartir" responda dentro del toque del usuario.
    fetch(src).then(function (r) { return r.blob(); }).then(function (b) {
      archivo = new File([b], nombreArchivo(src), { type: b.type || 'image/png' });
    }).catch(function () { archivo = null; });
    bootstrap.Modal.getOrCreateInstance(modalEl).show();
  });

  document.getElementById('posterCompartir').addEventListener('click', function () {
    var url = window.location.href;
    var texto = nombre + '\n' + url;
    var abortado = function (e) { return e && e.name === 'AbortError'; };
    var respaldo = function () { window.open('https://wa.me/?text=' + encodeURIComponent(texto), '_blank'); };
    if (archivo && navigator.canShare && navigator.canShare({ files: [archivo] })) {
      navigator.share({ files: [archivo], title: nombre, text: texto })
        .catch(function (e) { if (!abortado(e)) respaldo(); });
    } else if (navigator.share) {
      navigator.share({ title: nombre, text: nombre, url: url })
        .catch(function (e) { if (!abortado(e)) respaldo(); });
    } else {
      respaldo();
    }
  });
})();
