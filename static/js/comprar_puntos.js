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
  var modalEl = document.getElementById('modalCompraPuntos');
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
    e.preventDefault();
    document.getElementById('cmPuntos').textContent = '₡' + fmt(p);
    document.getElementById('cmTotal').textContent = '₡' + fmt(p + fee);
    document.getElementById('cmTitulo').textContent = fmt(p) + ' puntos';
    bootstrap.Modal.getOrCreateInstance(modalEl).show();
  });
  if (modalEl) {
    document.body.appendChild(modalEl);
    document.getElementById('cmConfirmar').addEventListener('click', function () {
      this.disabled = true;
      var w = window.open('', '_blank');  // se abre dentro del toque del usuario para que no lo bloquee el navegador
      var volver = function () { location.hash = '#accComprar'; location.reload(); };
      fetch(form.action, { method: 'POST', body: new FormData(form), headers: { 'X-Requested-With': 'fetch' }, credentials: 'same-origin' })
        .then(function (r) { return r.json(); })
        .then(function (d) { if (w) { if (d.ok && d.wa) w.location.href = d.wa; else w.close(); } volver(); })
        .catch(function () { if (w) w.close(); volver(); });
    });
    modalEl.addEventListener('hidden.bs.modal', function () { document.getElementById('cmConfirmar').disabled = false; });
  }
  input.addEventListener('input', function () { input.setCustomValidity(''); });
  if (location.hash === '#accComprar') {
    var el = document.getElementById('accComprar');
    if (el) bootstrap.Collapse.getOrCreateInstance(el, { toggle: false }).show();
  }
})();
