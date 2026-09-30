// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
  function toggleOtroDetalle(select) {
    var otro = document.getElementById('detalleOtro');
    var texto = document.getElementById('detalleOtroText');
    var monto = document.getElementById('montoRedimir');
    var precioInfo = document.getElementById('precioCaminata');
    if (select.value === 'otro') {
      otro.style.display = 'block';
      if (texto) texto.setAttribute('required', 'required');
      if (monto) {
        monto.value = '';
        monto.readOnly = false;
      }
      if (precioInfo) precioInfo.classList.add('d-none');
    } else if (select.value && select.value.startsWith('caminata_')) {
      otro.style.display = 'none';
      if (texto) {
        texto.removeAttribute('required');
        texto.value = '';
      }
      var opt = select.options[select.selectedIndex];
      var precio = parseInt(opt.getAttribute('data-precio') || '0', 10);
      var max = monto ? parseInt(monto.getAttribute('max') || '0', 10) : 0;
      if (monto) {
        if (precio > 0) {
          monto.value = (max && precio > max) ? max : precio;
        }
      }
      if (precioInfo) {
        if (precio > 0) {
          if (max >= precio) {
            var restantes = max - precio;
            precioInfo.textContent = 'Precio: ' + precio.toLocaleString() + ' puntos. Te quedan ' + restantes.toLocaleString() + ' puntos a favor.';
            precioInfo.className = 'small fw-bold text-success mt-1';
          } else {
            var faltan = precio - max;
            precioInfo.textContent = 'Precio: ' + precio.toLocaleString() + ' puntos. Te faltan ' + faltan.toLocaleString() + ' puntos (' + faltan.toLocaleString() + ' en efectivo). Usá la cantidad de puntos que tengas.';
            precioInfo.className = 'small fw-bold text-danger mt-1';
          }
          precioInfo.classList.remove('d-none');
        } else {
          precioInfo.classList.add('d-none');
        }
      }
    } else {
      otro.style.display = 'none';
      if (texto) {
        texto.removeAttribute('required');
        texto.value = '';
      }
      if (monto) monto.value = '';
      if (precioInfo) precioInfo.classList.add('d-none');
    }
  }

  setTimeout(function() {
    document.querySelectorAll('.flash-msg').forEach(function(el) {
      el.style.transition = 'opacity 0.5s ease';
      el.style.opacity = '0';
      setTimeout(function() { el.style.display = 'none'; }, 500);
    });
  }, 3000);
