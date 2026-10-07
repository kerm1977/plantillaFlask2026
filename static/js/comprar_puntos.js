// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
// comprar_puntos.js - Comprar puntos: monto por select o manual, siempre + 200 colones
(function () {
  var form = document.getElementById('formComprar');
  if (!form) return;
  var fee = parseInt(form.dataset.fee, 10) || 200;
  var minimo = parseInt(form.dataset.minimo, 10) || 1000;
  var sel = document.getElementById('compraSelect');
  var input = document.getElementById('compraPuntos');
  var resumen = document.getElementById('compraResumen');
  var fmt = function (n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, '.'); };

  function pintar() {
    var p = parseInt(input.value, 10);
    if (isNaN(p) || p < minimo) { resumen.classList.add('d-none'); return; }
    resumen.classList.remove('d-none');
    resumen.innerHTML = 'Comprás <strong>' + fmt(p) + '</strong> puntos · Total a transferir: <strong class="fs-6">₡' + fmt(p + fee) +
      '</strong><br><span class="text-muted">₡' + fmt(p) + ' para tu uso + ₡' + fee + ' para donaciones, administración y hosting</span>';
  }
  sel.addEventListener('change', function () { if (sel.value) input.value = sel.value; pintar(); });
  input.addEventListener('input', function () {
    var coincide = Array.prototype.some.call(sel.options, function (o) { return o.value && o.value === input.value; });
    sel.value = coincide ? input.value : '';
    pintar();
  });
  form.addEventListener('submit', function (e) {
    var p = parseInt(input.value, 10);
    if (isNaN(p) || p < minimo) { e.preventDefault(); input.setCustomValidity('La compra mínima es de ' + fmt(minimo) + ' puntos'); input.reportValidity(); return; }
    input.setCustomValidity('');
    if (!confirm('Vas a comprar ' + fmt(p) + ' puntos y transferir ₡' + fmt(p + fee) + ' (incluye ₡' + fee + ' para donaciones, administración y hosting). ¿Continuar?')) e.preventDefault();
  });
  input.addEventListener('input', function () { input.setCustomValidity(''); });
  if (location.hash === '#accComprar') {
    var el = document.getElementById('accComprar');
    if (el) bootstrap.Collapse.getOrCreateInstance(el, { toggle: false }).show();
  }
})();
