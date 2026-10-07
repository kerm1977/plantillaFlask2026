// static/js/fidelidad_admin.js - Programa de fidelidad (solo superusuario)
(function () {
  'use strict';
  function $(id) { return document.getElementById(id); }
  var selPersona = $('fidPersona'), estado = $('fidEstado'), msg = $('fidMsg');
  var lista = $('fidLista'), historial = $('fidHistorial'), contador = $('fidContador');
  if (!selPersona || !lista) return;

  function aviso(texto, ok) {
    msg.className = 'small mb-2 alert py-2 ' + (ok ? 'alert-success' : 'alert-danger');
    msg.textContent = texto;
  }

  function fmtNivel(nivel, label, manual) {
    if (nivel === 'exclusivo') return '<span class="badge text-dark" style="background:#ffe082">💎 Exclusivo VIP ×1.5</span>' + (manual ? ' <span class="badge bg-secondary">manual</span>' : '');
    if (nivel === 'activo') return '<span class="badge" style="background:#b3e5fc">⭐ Activo VIP ×1.2</span>' + (manual ? ' <span class="badge bg-secondary">manual</span>' : '');
    return '<span class="badge bg-light text-dark border">Sin nivel VIP</span>';
  }

  function cargarLista() {
    fetch('/api/fidelidad/lista').then(function (r) { return r.json(); }).then(function (d) {
      if (!d.ok) { lista.textContent = d.error || 'Error'; return; }
      contador.textContent = d.items.length;
      if (!d.items.length) { lista.innerHTML = '<p class="text-muted mb-0">Nadie tiene nivel VIP todavía.</p>'; return; }
      lista.innerHTML = '<ul class="list-group list-group-flush">' + d.items.map(function (p) {
        return '<li class="list-group-item px-0 py-1 d-flex justify-content-between align-items-center flex-wrap">' +
          '<span><strong>' + p.nombre + '</strong> <span class="text-muted">(' + p.cedula + ')</span>' +
          (p.nota ? ' <span class="text-muted fst-italic">· ' + p.nota + '</span>' : '') + '</span>' +
          '<span class="text-nowrap">' + fmtNivel(p.nivel, p.nivel_label, p.manual) +
          ' <span class="text-muted">' + p.participaciones + ' cam.</span></span></li>';
      }).join('') + '</ul>';
    }).catch(function () { lista.textContent = 'Error de conexión.'; });
  }

  function cargarHistorial() {
    fetch('/api/fidelidad/historial/todos').then(function (r) { return r.json(); }).then(function (d) {
      if (!d.ok || !d.items.length) { historial.innerHTML = '<p class="mb-0">Sin cambios manuales registrados.</p>'; return; }
      historial.innerHTML = d.items.map(function (h) {
        return '<p class="mb-1 border-bottom pb-1"><strong>' + h.fecha + '</strong> · ' + h.cedula +
          ': ' + h.de + ' → <strong>' + h.a + '</strong> (por ' + (h.por || '—') + ')' +
          (h.nota ? '<br><em>Motivo: ' + h.nota + '</em>' : '') + '</p>';
      }).join('');
    }).catch(function () {});
  }

  selPersona.addEventListener('change', function () {
    estado.classList.add('d-none');
    fetch('/api/fidelidad/info/' + selPersona.value).then(function (r) { return r.json(); }).then(function (d) {
      if (!d.ok) { aviso(d.error || 'Error', false); return; }
      estado.classList.remove('d-none');
      estado.innerHTML = '<strong>' + d.nombre + '</strong>: ' + fmtNivel(d.nivel, d.nivel_label, d.manual) +
        ' · ' + d.participaciones + ' caminatas · nivel automático: ' +
        (d.nivel_auto === 'exclusivo' ? 'Exclusivo' : d.nivel_auto === 'activo' ? 'Activo' : 'ninguno') +
        (d.nota ? '<br><em>Nota: ' + d.nota + '</em>' : '');
    });
  });

  $('fidGuardar').addEventListener('click', function () {
    var cedula = selPersona.value;
    if (!cedula) { aviso('Seleccioná una persona.', false); return; }
    var nivel = $('fidNivel').value, nota = $('fidNota').value.trim();
    if ((nivel === 'activo' || nivel === 'auto') && !nota) {
      var cur = estado.textContent || '';
      if (cur.indexOf('Exclusivo') >= 0) { aviso('Para degradar de Exclusivo VIP tenés que escribir el motivo en la nota.', false); return; }
    }
    fetch('/api/fidelidad/nivel', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cedula: cedula, nivel: nivel, nota: nota })
    }).then(function (r) { return r.json(); }).then(function (d) {
      aviso(d.ok ? (d.nombre + ': ahora es ' + d.nivel_label + '.') : (d.error || 'Error'), d.ok);
      if (d.ok) { selPersona.dispatchEvent(new Event('change')); cargarLista(); cargarHistorial(); }
    }).catch(function () { aviso('Error de conexión.', false); });
  });

  $('fidObsequiar').addEventListener('click', function () {
    var cedula = selPersona.value, monto = parseInt($('fidObsequio').value, 10);
    if (!cedula) { aviso('Seleccioná una persona.', false); return; }
    if (!monto || monto <= 0) { aviso('Indicá los puntos a obsequiar.', false); return; }
    fetch('/api/fidelidad/obsequio', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cedula: cedula, monto: monto, motivo: 'puntos por fidelidad al grupo' })
    }).then(function (r) { return r.json(); }).then(function (d) {
      aviso(d.ok ? ('Obsequiados ' + monto + ' puntos a ' + (d.nombre || cedula) + '. Total: ' + d.total) : (d.error || 'Error'), d.ok);
    }).catch(function () { aviso('Error de conexión.', false); });
  });

  function demoInsignia(nivel) {
    var viejo = document.getElementById('fidDemoBadge');
    var mismo = viejo && viejo.dataset.nivel === nivel;
    if (viejo) viejo.remove();
    var caja = $('fidDemoBox');
    if (mismo) { if (caja) caja.classList.add('d-none'); return; }
    var b = document.createElement('span');
    b.id = 'fidDemoBadge';
    b.dataset.nivel = nivel;
    b.className = 'vip-badge' + (nivel === 'exclusivo' ? ' vip-gold' : '');
    b.textContent = nivel === 'exclusivo' ? 'GOLD' : 'VIP-1';
    b.title = 'Muestra de la insignia ' + (nivel === 'exclusivo' ? 'Exclusivo VIP' : 'Activo VIP');
    var h2 = document.getElementById('puntosTotal');
    if (h2) { h2.appendChild(b); return; }
    if (caja) {
      caja.classList.remove('d-none');
      caja.innerHTML = '<span class="text-muted small d-block mb-1">Así se vería junto a los puntos:</span>' +
        '<span class="fw-bold" style="font-size:1.6rem">1 250 puntos</span> ';
      caja.appendChild(b);
    }
  }

  document.querySelectorAll('.fid-demo-nivel').forEach(function (el) {
    el.addEventListener('click', function () { demoInsignia(el.dataset.nivel); });
  });

  document.getElementById('accFidelidad').addEventListener('shown.bs.collapse', function () {
    cargarLista(); cargarHistorial();
  });
})();
