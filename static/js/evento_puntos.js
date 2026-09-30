// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
  const cantidadCompra = document.getElementById('cantidadCompra');
  const costoCompra = document.getElementById('costoCompra');
  const detalleCompra = document.getElementById('detalleCompra');
  function calcularCosto() {
    let n = parseInt(cantidadCompra.value || 0, 10);
    if (n < 500) { costoCompra.textContent = 'Mínimo 500 puntos'; detalleCompra.textContent = ''; return; }
    let fee = n <= 1000 ? 150 : 250;
    let total = n + fee;
    costoCompra.textContent = `Pagás ${total} colones. Recibís ${n} puntos.`;
    detalleCompra.textContent = `Excedente: ${fee} colones (50 para actividades La Tribu, ${fee - 50} administrativos).`;
  }
  if (cantidadCompra) { cantidadCompra.addEventListener('input', calcularCosto); calcularCosto(); }

  const cantidadRedencion = document.getElementById('cantidadRedencion');
  const tipoRedencion = document.getElementById('tipoRedencion');
  const valorRedencion = document.getElementById('valorRedencion');
  function calcularRedencion() {
    let n = parseInt(cantidadRedencion.value || 0, 10);
    let tipo = tipoRedencion ? tipoRedencion.value : 'caminata';
    let valor = tipo === 'dinero' ? Math.floor(n * 0.8) : n;
    valorRedencion.textContent = `Valor aplicado: ${valor} puntos.`;
  }
  if (cantidadRedencion) { cantidadRedencion.addEventListener('input', calcularRedencion); }
  if (tipoRedencion) { tipoRedencion.addEventListener('change', calcularRedencion); }
  calcularRedencion();

  document.addEventListener('DOMContentLoaded', function() {
    var el = document.getElementById('noRegistradoModal');
    if (el && typeof bootstrap !== 'undefined') {
      new bootstrap.Modal(el).show();
    }
  });
