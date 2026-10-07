// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
// donacion_admin.js - Finalidades de donación: lista de donantes y eliminación con triple confirmación
(function () {
  var mDon = document.getElementById('modalDonantes');
  var mEli = document.getElementById('modalEliminarFinalidad');
  if (!mDon || !mEli) return;
  document.body.appendChild(mDon);
  document.body.appendChild(mEli);
  var fmt = function (n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, '.'); };
  var celda = function (tr, texto, cls) {
    var td = document.createElement('td');
    td.textContent = texto;
    if (cls) td.className = cls;
    tr.appendChild(td);
  };

  document.querySelectorAll('.btn-ver-donantes').forEach(function (a) {
    a.addEventListener('click', function (e) {
      e.preventDefault();
      var lista = document.getElementById('dnLista');
      document.getElementById('dnTitulo').textContent = a.textContent;
      document.getElementById('dnResumen').textContent = 'Cargando...';
      lista.textContent = '';
      bootstrap.Modal.getOrCreateInstance(mDon).show();
      fetch(a.dataset.url, { credentials: 'same-origin' })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          if (!d.ok) { document.getElementById('dnResumen').textContent = d.error || 'No se pudo cargar.'; return; }
          document.getElementById('dnResumen').textContent = d.donantes.length
            ? d.donantes.length + ' persona(s) · ' + fmt(d.total) + ' puntos donados'
            : 'Aún nadie ha donado a esta finalidad.';
          d.donantes.forEach(function (p) {
            var tr = document.createElement('tr');
            celda(tr, p.nombre);
            celda(tr, p.cedula);
            celda(tr, fmt(p.puntos), 'text-end fw-bold');
            lista.appendChild(tr);
          });
        })
        .catch(function () { document.getElementById('dnResumen').textContent = 'No se pudo cargar la lista.'; });
    });
  });

  var form = document.getElementById('efForm');
  var texto = document.getElementById('efTexto');
  var enviar = document.getElementById('efEnviar');
  var checks = mEli.querySelectorAll('.ef-check');
  var nombreActual = '';
  var validar = function () {
    var ok = Array.prototype.every.call(checks, function (c) { return c.checked; }) && texto.value.trim() === nombreActual.trim();
    enviar.disabled = !ok;
  };
  checks.forEach(function (c) { c.addEventListener('change', validar); });
  texto.addEventListener('input', validar);
  mEli.addEventListener('hidden.bs.modal', function () {
    checks.forEach(function (c) { c.checked = false; });
    texto.value = '';
    enviar.disabled = true;
  });

  document.querySelectorAll('.btn-eliminar-finalidad').forEach(function (b) {
    b.addEventListener('click', function () {
      nombreActual = b.dataset.nombre;
      form.action = b.dataset.action;
      document.getElementById('efNombre').textContent = nombreActual;
      var aviso = document.getElementById('efAviso');
      var donado = parseInt(b.dataset.donado, 10) || 0;
      if (donado > 0) {
        aviso.classList.remove('d-none');
        aviso.textContent = 'Esta finalidad ya recibió ' + fmt(donado) + ' puntos de ' + b.dataset.donantes +
          ' persona(s). Los movimientos seguirán en el historial de cada persona, pero se perderá la lista de donantes de esta finalidad.';
      } else {
        aviso.classList.add('d-none');
      }
      validar();
      bootstrap.Modal.getOrCreateInstance(mEli).show();
    });
  });
})();
