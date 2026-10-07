// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
// compras_admin.js - Modal para aprobar o rechazar compras de puntos (superusuario)
(function () {
  var modalEl = document.getElementById('modalCompraAdmin');
  if (!modalEl) return;
  document.body.appendChild(modalEl);
  var form = document.getElementById('caForm');
  var titulo = document.getElementById('caTitulo');
  var texto = document.getElementById('caTexto');
  var check = document.getElementById('caCheck');
  var checkBox = document.getElementById('caCheckBox');
  var enviar = document.getElementById('caEnviar');
  var aprobar = false;

  var validar = function () { enviar.disabled = aprobar && !check.checked; };
  check.addEventListener('change', validar);
  modalEl.addEventListener('hidden.bs.modal', function () { check.checked = false; });

  document.querySelectorAll('.btn-compra-accion').forEach(function (b) {
    b.addEventListener('click', function () {
      aprobar = b.dataset.accion === 'aprobar';
      form.action = b.dataset.action;
      check.checked = false;
      checkBox.classList.toggle('d-none', !aprobar);
      if (aprobar) {
        titulo.innerHTML = '<i class="bi bi-check-circle-fill text-success me-2"></i>Aprobar pago';
        texto.innerHTML = '¿Recibiste <strong>₡' + b.dataset.pagar + '</strong> de <strong class="ca-nombre"></strong>?<br>Se acreditarán <strong>' +
          b.dataset.puntos + '</strong> puntos a la cédula ' + b.dataset.cedula + '.';
        enviar.className = 'btn btn-success rounded-pill px-4 fw-bold';
        enviar.textContent = 'Aprobar y acreditar';
      } else {
        titulo.innerHTML = '<i class="bi bi-x-circle-fill text-danger me-2"></i>Rechazar solicitud';
        texto.innerHTML = '¿Rechazar la compra de <strong>' + b.dataset.puntos + '</strong> puntos de <strong class="ca-nombre"></strong>?<br>No se acreditará ningún punto.';
        enviar.className = 'btn btn-danger rounded-pill px-4 fw-bold';
        enviar.textContent = 'Rechazar solicitud';
      }
      texto.querySelector('.ca-nombre').textContent = b.dataset.nombre;
      validar();
      bootstrap.Modal.getOrCreateInstance(modalEl).show();
    });
  });
})();
