// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('createEventForm');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            // Validación explícita: el navegador no puede mostrar errores
            // de campos required dentro de accordions colapsados.
            if (!validarEventoForm()) return;

            const submitBtn = document.getElementById('submitEventBtn');
            const originalBtnText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Guardando...';

            const formData = new FormData(form);

            // Estados de seguridad
            const isSecureDia = document.getElementById('diaSeguroToggle').checked;
            formData.set('solo_chat', isSecureDia);

            const isSecureLog = document.getElementById('logisticaSeguraToggle').checked;
            formData.set('logistica_segura', isSecureLog);
            if (isSecureLog) {
                const lugar = formData.get('lugarSalida');
                formData.set('lugarSalida', 'SEGURO_' + lugar);
            }

            const isAltoRiesgo = document.getElementById('altoRiesgoToggle').checked;
            formData.set('zona_alto_riesgo', isAltoRiesgo);

            // Checkboxes de "Incluye"
            const incluyeArr = [];
            document.querySelectorAll('#incluyeWrapper input[name="incluye_check"]:checked').forEach(cb => {
                if (cb.value === "Otros") {
                    const desc = document.getElementById('otrosDescripcion').value;
                    if (desc) incluyeArr.push(desc);
                } else {
                    incluyeArr.push(cb.value);
                }
            });
            formData.set('incluye', incluyeArr.join(', '));

            // Información Especial (WYSIWYG) -> campo itinerario
            formData.set('itinerario', Wysiwyg.getContent('itinerarioEditor'));

            // Lógica inteligente de fechas: se serializa siempre que la fecha
            // esté completa; si el estado era Pendiente, el evento pasa a
            // Programados (mismo comportamiento que el selector rápido).
            const pad = (n) => { let v = parseInt(n, 10); return (isNaN(v) ? '01' : (v < 10 ? '0' + v : v)); };
            const visitadoSel = document.getElementById('visitado');
            let fechaCompleta = false;

            if (document.getElementById('actividad').value === 'Internacional') {
                const f = document.getElementById('fechaIda').value;
                if (f) {
                    formData.set('fechaUnica', f);
                    fechaCompleta = true;
                }
            } else {
                const dias = parseInt(document.getElementById('dias').value) || 1;
                if (dias === 1) {
                    const y = document.getElementById('yearUnica').value;
                    const m = document.getElementById('monthUnica').value;
                    const dRaw = document.getElementById('dayUnica').value;
                    if (y && m && (dRaw || isSecureDia)) {
                        formData.set('fechaUnica', `${y}-${m}-${isSecureDia ? '01' : pad(dRaw)}`);
                        fechaCompleta = true;
                    }
                } else {
                    const yI = document.getElementById('yearInicio').value;
                    const mI = document.getElementById('monthInicio').value;
                    const dRawI = document.getElementById('dayInicio').value;
                    const yR = document.getElementById('yearRegreso').value;
                    const mR = document.getElementById('monthRegreso').value;
                    const dRawR = document.getElementById('dayRegreso').value;
                    if (yI && mI && (dRawI || isSecureDia) && yR && mR && (dRawR || isSecureDia)) {
                        formData.set('fechaInicio', `${yI}-${mI}-${isSecureDia ? '01' : pad(dRawI)}`);
                        formData.set('fechaRegreso', `${yR}-${mR}-${isSecureDia ? '01' : pad(dRawR)}`);
                        fechaCompleta = true;
                    }
                }
            }

            if (fechaCompleta && ['Pendiente', 'No', ''].includes(visitadoSel.value)) {
                visitadoSel.value = 'Programados';
                formData.set('visitado', 'Programados');
            }

            const endpoint = eventoEditando ? `/api/update_event/${eventoEditando}` : '/api/create_event';

            try {
                const response = await fetch(endpoint, { method: 'POST', body: formData });
                const result = await response.json();
                if (response.ok && result.success) {
                    mostrarAlerta(eventoEditando ? 'Caminata actualizada correctamente.' : 'Caminata creada correctamente.', 'success');
                    if (document.getElementById('visitado').value === 'Cotización' && !eventoEditando) {
                        window.open(COTIZACIONES_BUSETA_URL, '_blank');
                        setTimeout(() => { window.location.reload(); }, 800);
                    } else {
                        setTimeout(() => { window.location.reload(); }, 1200);
                    }
                } else {
                    alert('Error al guardar: ' + (result.error || 'Desconocido'));
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalBtnText;
                }
            } catch (err) {
                console.error(err);
                alert('Error de conexión al guardar.');
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;
            }
        });

        // Limpiar marca roja al corregir el campo
        form.addEventListener('input', ev => ev.target.classList.remove('is-invalid'));
        form.addEventListener('change', ev => ev.target.classList.remove('is-invalid'));
    }

    const upload = document.getElementById('eventImageUpload');
    if (upload) {
        upload.addEventListener('change', function(e) {
            if (e.target.files && e.target.files[0]) {
                const reader = new FileReader();
                reader.onload = function(evt) {
                    document.getElementById('eventImagePreview').src = evt.target.result;
                }
                reader.readAsDataURL(e.target.files[0]);
            }
        });
    }

    if (document.getElementById('itinerarioEditor')) {
        Wysiwyg.setupUploadListeners('itinerarioEditor', CAMINATA_UPLOAD_URL);
    }

    const elModal = document.getElementById('eventoModal');
    if (elModal) modalEvento = new bootstrap.Modal(elModal);

    const modal1 = document.getElementById('confirmDeleteEventModal1');
    if (modal1) modalEliminarEvento1 = new bootstrap.Modal(modal1);
    const modal2 = document.getElementById('confirmDeleteEventModal2');
    if (modal2) modalEliminarEvento2 = new bootstrap.Modal(modal2);

    // Abrir automáticamente el formulario de creación si se llega con ?crear=1
    // (usado por el enlace "Crear Caminata" del menú de Herramientas de Admin)
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('crear') === '1') {
        abrirCrear();
        urlParams.delete('crear');
        const newUrl = window.location.pathname + (urlParams.toString() ? '?' + urlParams.toString() : '');
        window.history.replaceState({}, '', newUrl);
    }
});

// BLINDADO: validación visible del formulario de evento.
// Devuelve true si todo está completo; si falta algo, muestra qué,
// abre el accordion que lo contiene y enfoca el campo en rojo.
