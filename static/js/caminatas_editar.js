// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
async function editarEvento(id) {
    try {
        const res = await fetch(`/api/get_event/${id}`);
        if (!res.ok) { alert('No autorizado o error al cargar.'); return; }
        const e = await res.json();
        eventoEditando = e.id;
        document.getElementById('caminata2027Title').innerHTML = '<i class="bi bi-pencil-square text-orange me-2"></i>Editar Caminata';
        document.getElementById('submitEventBtn').innerHTML = '<i class="bi bi-save me-2"></i>Guardar Cambios';

        document.getElementById('nombreLugar').value = e.nombre_lugar || '';
        document.getElementById('provincia').value = e.provincia || 'San José';
        let estadoEdit = e.visitado || 'Pendiente';
        if (estadoEdit === 'Sí' || estadoEdit === 'Visitado') estadoEdit = 'Visitados';
        if (estadoEdit === 'No') estadoEdit = 'Pendiente';
        if (estadoEdit === 'Por programar') estadoEdit = 'Programados';
        if (/^\d{4}$/.test(estadoEdit)) {
            document.getElementById('anio').value = estadoEdit;
            estadoEdit = 'Año';
        }
        document.getElementById('visitado').value = ['Pendiente','Visitados','Año','Programados','Cotización'].includes(estadoEdit) ? estadoEdit : 'Pendiente';
        toggleAnio(document.getElementById('visitado').value);
        toggleEstadoCampos(document.getElementById('visitado').value);
        toggleCotizacionFields(document.getElementById('visitado').value);

        document.getElementById('dificultad').value = e.dificultad || 'Paseo';
        document.getElementById('tipoTerreno').value = e.tipo_terreno || 'Lastre';
        document.getElementById('tipoCaminata').value = e.tipo_caminata || 'Circular';
        document.getElementById('actividad').value = e.actividad || 'Caminata';
        toggleActividad();
        document.getElementById('moneda').value = e.moneda || '¢';
        document.getElementById('precio').value = e.precio || 0;
        document.getElementById('reserva').value = e.reserva || 0;
        document.getElementById('kilometros').value = e.kilometros != null ? e.kilometros : '';
        document.getElementById('capacidad').value = (e.capacidad || '').replace('AGOTADO_', '') || '14-17';
        document.getElementById('sinpe').value = e.sinpe || '86529837 - Jenny Ceciliano Cordoba';
        document.getElementById('cuenta').value = e.cuenta || 'Ninguna';
        document.getElementById('enlaceExtra').value = e.enlace_extra || '';
        document.getElementById('puntos').value = e.puntos || 0;
        document.getElementById('textoReferencia').value = e.texto_referencia || '';
        document.getElementById('altoRiesgoToggle').checked = !!e.zona_alto_riesgo;
        document.getElementById('eventImagePreview').src = e.poster ? `/static/uploads/${e.poster}` : '/static/default.png';

        // Fechas
        const setDateFields = (dateStr, dId, mId, yId) => {
            if (!dateStr || dateStr === "None") return;
            const pts = dateStr.split('-');
            if (pts.length === 3) {
                document.getElementById(yId).value = pts[0];
                document.getElementById(mId).value = pts[1];
                document.getElementById(dId).value = parseInt(pts[2], 10);
            }
        };
        document.getElementById('dias').value = e.dias || 1;
        toggleDateInputs();
        setDateFields(e.fecha_unica, 'dayUnica', 'monthUnica', 'yearUnica');
        setDateFields(e.fecha_inicio, 'dayInicio', 'monthInicio', 'yearInicio');
        setDateFields(e.fecha_regreso, 'dayRegreso', 'monthRegreso', 'yearRegreso');
        if (e.actividad === 'Internacional' && e.fecha_unica) {
            document.getElementById('fechaIda').value = e.fecha_unica;
        }

        // Logística
        document.getElementById('diaSeguroToggle').checked = !!e.solo_chat;
        toggleDiaSeguro();
        const isSecureLog = !!e.logistica_segura;
        document.getElementById('logisticaSeguraToggle').checked = isSecureLog;
        toggleLogisticaSegura();
        let lugarSalidaVal = e.lugar_salida || '';
        if (lugarSalidaVal.startsWith('SEGURO_')) lugarSalidaVal = lugarSalidaVal.replace('SEGURO_', '');
        if (e.actividad === 'Internacional') {
            document.getElementById('destinoInternacional').value = lugarSalidaVal;
        } else {
            document.getElementById('lugarSalida').value = lugarSalidaVal || 'Parque de Tres Ríos - Escuela';
        }
        document.getElementById('horaSalida').value = e.hora_salida || '';
        updateTimePreview();
        document.getElementById('puntosRecogidaInput').value = e.puntos_recogida || '';

        // Incluye
        const includesGuardados = (e.incluye || '').split(',').map(s => s.trim()).filter(Boolean);
        document.querySelectorAll('#incluyeWrapper input[name="incluye_check"]').forEach(cb => cb.checked = false);
        document.querySelectorAll('#incluyeWrapper input[name="incluye_check"]').forEach(cb => {
            if (cb.value !== "Otros" && includesGuardados.includes(cb.value)) {
                cb.checked = true;
                const idx = includesGuardados.indexOf(cb.value);
                if (idx > -1) includesGuardados.splice(idx, 1);
            }
        });
        const filteredOtros = includesGuardados.filter(item => item !== "Otros" && item !== "");
        document.getElementById('otrosDescripcion').value = '';
        document.getElementById('otrosDescContainer').classList.add('d-none');
        document.getElementById('modalCheckOtros').checked = false;
        if (filteredOtros.length > 0) {
            document.getElementById('modalCheckOtros').checked = true;
            document.getElementById('otrosDescripcion').value = filteredOtros.join(', ');
            document.getElementById('otrosDescContainer').classList.remove('d-none');
        }

        // Información Especial
        Wysiwyg.setContent('itinerarioEditor', e.itinerario || '');

        colapsarAcordeonEvento();
        if (window.loadFlyerStateForId) loadFlyerStateForId(e.id);
        if (window.actualizarPreviewFlyer) actualizarPreviewFlyer();
        if (modalEvento) modalEvento.show();
    } catch (err) {
        console.error(err);
        alert('Error al cargar la caminata para editar.');
    }
}

function eliminarEvento(id) {
    eventoAEliminar = id;
    if (modalEliminarEvento1) modalEliminarEvento1.show();
}

function mostrarConfirmarEliminarEvento(paso) {
    if (paso === 2) {
        if (modalEliminarEvento1) modalEliminarEvento1.hide();
        if (modalEliminarEvento2) modalEliminarEvento2.show();
    }
}

async function confirmarEliminarEvento() {
    if (!eventoAEliminar) return;
    try {
        const res = await fetch(`/api/delete_event/${eventoAEliminar}`, { method: 'DELETE' });
        const result = await res.json();
        if (modalEliminarEvento2) modalEliminarEvento2.hide();
        if (res.ok && result.success) {
            window.location.reload();
        } else {
            alert('Error al eliminar: ' + (result.error || 'Desconocido'));
        }
    } catch (err) {
        console.error(err);
        alert('Error de conexión al eliminar.');
    } finally {
        eventoAEliminar = null;
    }
}

