// static/js/ver_evento_puntos.js - Long-press sobre los puntos que parpadean:
// abre un modal para editar los puntos del evento y guardarlos en la BD
// (solo superusuario; el elemento lleva data-puntos-edit solo para ese rol).
(function () {
  'use strict';
  var script = document.currentScript;
  var eventId = script.getAttribute('data-event-id');
  var modalEl = document.getElementById('modalEditarPuntos');
  var input = document.getElementById('epInput');
  var msg = document.getElementById('epMsg');
  var btnGuardar = document.getElementById('epGuardar');
  var target = document.querySelector('[data-puntos-edit]');
  if (!eventId || !modalEl || !input || !target || typeof bootstrap === 'undefined') return;

  var modal = new bootstrap.Modal(modalEl);
  var LONG_PRESS_MS = 600;
  var MOVE_TOLERANCE = 12;
  var timer = null;
  var startX = 0, startY = 0;

  function abrir() {
    var val = document.getElementById('hbPuntosVal');
    input.value = val ? parseInt(val.innerText, 10) || 0 : (script.getAttribute('data-puntos') || 0);
    msg.textContent = '';
    msg.className = 'small mt-2';
    modal.show();
    setTimeout(function () { input.focus(); input.select(); }, 350);
  }
  function cancelar() { if (timer) { clearTimeout(timer); timer = null; } }

  target.addEventListener('pointerdown', function (e) {
    cancelar();
    startX = e.clientX; startY = e.clientY;
    timer = setTimeout(function () { timer = null; abrir(); }, LONG_PRESS_MS);
  });
  target.addEventListener('pointermove', function (e) {
    if (timer && Math.hypot(e.clientX - startX, e.clientY - startY) > MOVE_TOLERANCE) cancelar();
  });
  ['pointerup', 'pointerleave', 'pointercancel'].forEach(function (ev) {
    target.addEventListener(ev, cancelar);
  });
  // Evita el menú contextual del long-press en móviles sobre ese elemento
  target.addEventListener('contextmenu', function (e) { e.preventDefault(); });

  btnGuardar.addEventListener('click', function () {
    var v = Math.max(0, Math.min(99999, parseInt(input.value, 10) || 0));
    btnGuardar.disabled = true;
    fetch('/api/eventos/' + eventId + '/puntos', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ puntos: v })
    }).then(function (r) {
      if (!r.ok) throw new Error();
      return r.json();
    }).then(function (d) {
      var nuevos = d.puntos != null ? d.puntos : v;
      [['hbPuntosVal', 'hbPuntos'], ['cardPuntosVal', 'cardPuntosBadge'], ['fl_puntosVal', 'fl_puntos']]
        .forEach(function (ids) {
          var el = document.getElementById(ids[0]);
          var box = document.getElementById(ids[1]);
          if (el) el.innerText = nuevos;
          if (box) box.classList.toggle('d-none', nuevos <= 0);
        });
      var flyerInput = document.getElementById('flyerPuntos');
      if (flyerInput) flyerInput.value = nuevos;
      script.setAttribute('data-puntos', nuevos);
      msg.className = 'small mt-2 text-success';
      msg.textContent = 'Guardado: ' + nuevos + ' puntos';
      setTimeout(function () { modal.hide(); }, 700);
    }).catch(function () {
      msg.className = 'small mt-2 text-danger';
      msg.textContent = 'Error al guardar. Revisá tu conexión e intentá de nuevo.';
    }).finally(function () { btnGuardar.disabled = false; });
  });
})();
