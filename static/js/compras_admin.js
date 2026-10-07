// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
// compras_admin.js - Aprobar / rechazar / confirmar compras de puntos con confirmaciones en pasos
(function () {
  var modalEl = document.getElementById('modalCompraAdmin');
  if (!modalEl) return;
  document.body.appendChild(modalEl);
  var $ = function (id) { return document.getElementById(id); };
  var form = $('caForm'), siguiente = $('caSiguiente'), enviar = $('caEnviar'), alerta = $('caAlerta');
  var pasos = [], paso = 0, datos = null;

  var FLUJOS = {
    aprobar: {
      titulo: '<i class="bi bi-check-circle-fill text-success me-2"></i>Aprobar pago', btn: 'btn-success', final: 'Continuar y acreditar los puntos',
      pasos: [
        ['alert-info', '¿Confirmás realmente que <strong class="ca-nombre"></strong> canceló la cantidad de <strong>₡{pagar}</strong>?'],
        ['alert-warning', '¿Estás seguro de que deseás proseguir? Revisá el comprobante y que el monto coincida exactamente con <strong>₡{pagar}</strong>.'],
        ['alert-danger', '<strong>Atención:</strong> puede que sumes dinero que no ha ingresado a tu cuenta. Revisá bien. Si das continuar, aceptás las condiciones y se sumarán <strong>{puntos}</strong> puntos a la cédula {cedula}.']
      ]
    },
    rechazar: {
      titulo: '<i class="bi bi-x-circle-fill text-danger me-2"></i>Rechazar pago', btn: 'btn-danger', final: 'Sí, el pago no fue realizado',
      pasos: [
        ['alert-info', '¿Estás seguro de que <strong class="ca-nombre"></strong> <strong>no hizo el depósito</strong> de <strong>₡{pagar}</strong>?'],
        ['alert-warning', '¿Revisaste bien tu cuenta y tus notificaciones del banco? Puede haber un error de depósito o una transferencia que aún está en proceso.'],
        ['alert-danger', '<strong>Última confirmación:</strong> ¿estás completamente seguro? La solicitud no se elimina: queda pendiente, esperando que se confirme el pago nuevamente.']
      ]
    },
    eliminar: {
      titulo: '<i class="bi bi-trash-fill text-danger me-2"></i>Eliminar pago pendiente', btn: 'btn-danger', final: 'Sí, eliminar definitivamente',
      pasos: [
        ['alert-info', '¿Eliminar la solicitud de <strong>{puntos}</strong> puntos (₡{pagar}) de <strong class="ca-nombre"></strong>? El pago ya fue rechazado una vez.'],
        ['alert-warning', 'Esta acción <strong>borra la solicitud por completo</strong>: desaparece de la lista y la persona tendrá que hacer una compra nueva si quiere puntos.'],
        ['alert-danger', '<strong>Última confirmación:</strong> la solicitud de la cédula {cedula} se eliminará definitivamente y no se puede recuperar. ¿Continuar?']
      ]
    },
    confirmar: {
      titulo: '<i class="bi bi-patch-check-fill text-primary me-2"></i>Confirmado', btn: 'btn-primary', final: 'Sí, realmente confirmado',
      pasos: [
        ['alert-success', '¿Confirmás que el dinero de <strong>₡{pagar}</strong> de <strong class="ca-nombre"></strong> ya ingresó definitivamente a tu cuenta? Al confirmar, esta solicitud desaparece de «Compras pendientes de pago».']
      ]
    }
  };

  function pintar() {
    var f = FLUJOS[datos.accion], p = pasos[paso];
    $('caTitulo').innerHTML = f.titulo;
    $('caPaso').textContent = pasos.length > 1 ? 'Confirmación ' + (paso + 1) + ' de ' + pasos.length : 'Confirmación final';
    $('caBarra').style.width = ((paso + 1) / pasos.length * 100) + '%';
    $('caBarra').className = 'progress-bar bg-' + (paso === pasos.length - 1 && datos.accion !== 'confirmar' ? 'danger' : 'success');
    alerta.className = 'alert rounded-4 mb-0 ' + p[0];
    alerta.innerHTML = p[1].replace('{pagar}', datos.pagar).replace('{puntos}', datos.puntos).replace('{cedula}', datos.cedula);
    var n = alerta.querySelector('.ca-nombre');
    if (n) n.textContent = datos.nombre;
    var ultimo = paso === pasos.length - 1;
    siguiente.classList.toggle('d-none', ultimo);
    enviar.classList.toggle('d-none', !ultimo);
    siguiente.className = 'btn rounded-pill px-4 fw-bold ' + f.btn + (ultimo ? ' d-none' : '');
    enviar.className = 'btn rounded-pill px-4 fw-bold ' + f.btn + (ultimo ? '' : ' d-none');
    enviar.textContent = f.final;
  }

  siguiente.addEventListener('click', function () { if (paso < pasos.length - 1) { paso++; pintar(); } });

  document.querySelectorAll('.btn-compra-accion').forEach(function (b) {
    b.addEventListener('click', function () {
      datos = { accion: b.dataset.accion, nombre: b.dataset.nombre, cedula: b.dataset.cedula, puntos: b.dataset.puntos, pagar: b.dataset.pagar };
      pasos = FLUJOS[datos.accion].pasos;
      paso = 0;
      form.action = b.dataset.action;
      pintar();
      bootstrap.Modal.getOrCreateInstance(modalEl).show();
    });
  });
})();
