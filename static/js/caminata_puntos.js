// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
  document.addEventListener('DOMContentLoaded', function() {
    if (CAMINATA_PUNTOS > 0) {
      document.getElementById('puntosCaminataRow').style.display = 'flex';
      document.getElementById('puntosValorCaminata').textContent = CAMINATA_PUNTOS;
      cargarPuntosCaminata();
      if (IS_SUPER) document.getElementById('puntosAdmin').classList.remove('d-none');
    }
  });

  async function cargarPuntosCaminata() {
    try {
      const r = await fetch(`/api/puntos/evento/${CAMINATA_ID}`);
      const data = await r.json();
      if (!data.ok) return;
      const total = data.asignados.reduce((sum, a) => sum + a.puntos, 0);
      document.getElementById('puntosTotalCaminata').textContent = `Total acumulado en esta actividad: ${total}`;
      const cont = document.getElementById('puntosAsignadosCaminata');
      if (!data.asignados.length) {
        cont.innerHTML = '<p class="text-muted">Aún no se han asignado puntos.</p>';
      } else {
        cont.innerHTML = data.asignados.map(a => `<div class="d-flex justify-content-between border-bottom py-1"><span>${a.cedula}${a.retirado ? ' <span class="text-danger">(retirado)</span>' : ''}</span><span class="fw-bold">${a.puntos}</span></div>`).join('');
      }
    } catch (e) { console.error(e); }
  }

  async function asignarPuntosCaminata() {
    if (!confirm('¿Asignar ' + CAMINATA_PUNTOS + ' puntos a todos los registrados?')) return;
    try {
      const r = await fetch(`/api/puntos/asignar/${CAMINATA_ID}`, { method: 'POST' });
      const data = await r.json();
      alert(data.ok ? `Asignados: ${data.added} participantes` : data.error);
      if (data.ok) cargarPuntosCaminata();
    } catch (e) { console.error(e); }
  }

  async function retirarPuntosCaminata() {
    const cedula = document.getElementById('retirarCedula').value.trim();
    if (!cedula) return alert('Escribí la cédula.');
    if (!confirm('¿Retirar los puntos de ' + cedula + '?')) return;
    const mensaje = prompt('Si el retiro está justificado por lesión, escribí el mensaje. Dejalo vacío si no hay justificación.');
    if (mensaje === null) return;
    const justificado = mensaje.trim().length > 0;
    try {
      const r = await fetch(`/api/puntos/retirar/${CAMINATA_ID}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cedula, justificado, mensaje: mensaje.trim() })
      });
      const data = await r.json();
      alert(data.ok ? 'Retiro realizado. Deducido: ' + (data.points_deducted || 0) + ' puntos.' : data.error);
      if (data.ok) { document.getElementById('retirarCedula').value = ''; cargarPuntosCaminata(); }
    } catch (e) { console.error(e); }
  }
