// BLINDADO: paginacion de "Retos cumplidos" en el estado de cuenta
// individual — 10 retos por pagina, botones < > y contador.
(function () {
  'use strict';
  var lista = document.getElementById('listaRetos');
  var paginador = document.getElementById('paginadorRetos');
  if (!lista || !paginador) return;
  var items = lista.querySelectorAll('li');
  var POR_PAGINA = 10;
  var paginas = Math.ceil(items.length / POR_PAGINA);
  if (paginas <= 1) return;
  var actual = 1;
  var lbl = document.getElementById('retosPagina');
  var prev = document.getElementById('retosPrev');
  var next = document.getElementById('retosNext');
  function mostrar() {
    items.forEach(function (li, i) {
      li.style.display = (i >= (actual - 1) * POR_PAGINA && i < actual * POR_PAGINA) ? '' : 'none';
    });
    lbl.textContent = 'Página ' + actual + ' de ' + paginas + ' · ' + items.length + ' retos';
    prev.disabled = actual === 1;
    next.disabled = actual === paginas;
  }
  prev.addEventListener('click', function () { if (actual > 1) { actual--; mostrar(); } });
  next.addEventListener('click', function () { if (actual < paginas) { actual++; mostrar(); } });
  paginador.classList.remove('d-none');
  mostrar();
})();
