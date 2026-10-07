// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
// donar_puntos.js - Modal de confirmación de donación con fin benéfico
(function () {
  var form = document.getElementById('formDonarCausa');
  var modalEl = document.getElementById('modalDonarCausa');
  if (!form || !modalEl) return;
  document.body.appendChild(modalEl);
  var monto = document.getElementById('donarMonto');
  var sel = document.getElementById('donarFinalidad');
  var desc = document.getElementById('donarDesc');
  var confirma = document.getElementById('dcConfirma');
  var enviar = document.getElementById('dcEnviar');
  var aviso = document.getElementById('dcAviso');
  var total = parseInt(form.dataset.total, 10) || 0;
  var modo = form.dataset.modo;
  var tope = parseInt(form.dataset.max, 10) || 0;
  var fmt = function (n) { return Number(n).toLocaleString('es-CR'); };

  sel.addEventListener('change', function () {
    var o = sel.options[sel.selectedIndex];
    desc.textContent = (o && o.dataset.desc) || '';
  });
  confirma.addEventListener('change', function () { enviar.disabled = !confirma.checked; });
  modalEl.addEventListener('hidden.bs.modal', function () { confirma.checked = false; enviar.disabled = true; });

  document.getElementById('btnAbrirDonar').addEventListener('click', function () {
    var m = parseInt(monto.value, 10);
    if (!sel.value) { sel.reportValidity(); return; }
    if (isNaN(m) || m < 1) { monto.setCustomValidity('Ingresá los puntos a donar'); monto.reportValidity(); return; }
    if (modo === 'parcial' && m > tope) {
      monto.setCustomValidity('Podés donar hasta ' + fmt(tope) + ' puntos (80%)');
      monto.reportValidity();
      return;
    }
    monto.setCustomValidity('');
    var resto = total - m;
    document.getElementById('dcMonto').textContent = fmt(m);
    document.getElementById('dcFinalidad').textContent = sel.options[sel.selectedIndex].text;
    if (modo === 'total') {
      aviso.className = 'alert alert-warning small rounded-4 mb-3';
      aviso.innerHTML = '<strong>Donarás la totalidad de tus puntos.</strong> Tenés ' + fmt(total) +
        ' puntos (menos de 5.000), y con un fin benéfico solo se puede donar el total. Te quedarás con <strong>0</strong> puntos.';
    } else {
      aviso.className = 'alert alert-info small rounded-4 mb-3';
      aviso.innerHTML = 'Tenés ' + fmt(total) + ' puntos. Después de donar te quedarán <strong>' + fmt(resto) + '</strong> puntos.';
    }
    bootstrap.Modal.getOrCreateInstance(modalEl).show();
  });
  monto.addEventListener('input', function () { monto.setCustomValidity(''); });
})();
