// BLINDADO: confirmación de retos de "Ganar puntos desde casa".
// Registra la solicitud pendiente y abre WhatsApp para avisar a los coordinadores.
(function () {
  'use strict';
  document.querySelectorAll('.btn-reto').forEach(function (btn) {
    btn.addEventListener('click', function () {
      if (btn.disabled) return;
      btn.disabled = true;
      var body = new URLSearchParams();
      body.set('cedula', btn.dataset.cedula || '');
      fetch(btn.dataset.action, {
        method: 'POST',
        headers: { 'X-Requested-With': 'fetch' },
        body: body,
        credentials: 'same-origin'
      }).then(function (r) { return r.json(); }).then(function (res) {
        if (res.ok) {
          if (res.wa) window.open(res.wa, '_blank');
          window.location.reload();
        } else {
          alert(res.error || 'No se pudo registrar el reto.');
          btn.disabled = false;
        }
      }).catch(function () {
        alert('Sin conexión. Revisá tu internet e intentá de nuevo.');
        btn.disabled = false;
      });
    });
  });
})();
