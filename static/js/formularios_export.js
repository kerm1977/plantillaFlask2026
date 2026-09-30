// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
async function exportResponses(fmt) {
    if (!currentResponsesFormId) return;
    const addMembrete = document.getElementById('addMembrete')?.checked || false;
    const includeFecha = document.getElementById('includeFecha')?.checked || false;
    const includeFichaMedica = document.getElementById('includeFichaMedica')?.checked || false;
    if (fmt === 'whatsapp') {
        const url = `/api/forms/${currentResponsesFormId}/export/whatsapp?include_fecha=${includeFecha}&include_ficha_medica=${includeFichaMedica}`;
        const data = await (await fetch(url)).json();
        if (data.text) shareWhatsAppText(data.text);
    } else {
        const url = `/api/forms/${currentResponsesFormId}/export/${fmt}?membrete=${addMembrete}&include_fecha=${includeFecha}&include_ficha_medica=${includeFichaMedica}`;
        const fullUrl = reservationNumbers ? `${url}&reservation_numbers=${encodeURIComponent(reservationNumbers)}` : url;
        window.open(fullUrl, '_blank');
    }
}

function shareWhatsAppText(text) {
    if (navigator.share) {
        navigator.share({ title: document.getElementById('responsesTitle')?.textContent || 'Respuestas', text })
            .catch(() => {});
    } else {
        window.open('https://wa.me/?text=' + encodeURIComponent(text), '_blank');
    }
}

async function openSinglepageModal() {
    const sel = document.getElementById('singlepageEventSelect');
    sel.innerHTML = '<option value="">Cargando eventos...</option>';
    const modal = new bootstrap.Modal(document.getElementById('singlepageEventModal'));
    modal.show();
    try {
        const eventos = await (await fetch('/api/events/options')).json();
        sel.innerHTML = '<option value="">— Sin información de caminata —</option>' +
            eventos.map(e => `<option value="${e.id}">${e.nombre_lugar}${e.fecha ? ' (' + e.fecha + ')' : ''}</option>`).join('');
    } catch (e) {
        sel.innerHTML = '<option value="">Error cargando eventos</option>';
    }
}

function generateSinglepage(eventId) {
    if (!currentResponsesFormId) return;
    const params = new URLSearchParams();
    if (eventId) params.set('event_id', eventId);
    if (document.getElementById('spHistoria')?.checked) params.set('include_historia', '1');
    if (document.getElementById('spMision')?.checked) params.set('include_mision', '1');
    if (document.getElementById('spOracion')?.checked) params.set('include_oracion', '1');
    if (document.getElementById('spPuntos')?.checked) params.set('include_puntos', '1');
    const qs = params.toString();
    window.open(`/api/forms/${currentResponsesFormId}/export/singlepage${qs ? '?' + qs : ''}`, '_blank');
    const modal = bootstrap.Modal.getInstance(document.getElementById('singlepageEventModal'));
    if (modal) modal.hide();
}

async function shareResponsesBasico() {
    const data = window._responsesData;
    if (!data || !data.responses || !data.responses.length) return;
    const includeFecha = document.getElementById('includeFecha')?.checked || false;
    let text = `*${data.form_name || 'Respuestas'}* - Información básica`;
    if (includeFecha) text += `\n- Fecha: ${new Date().toLocaleDateString('es-CR')}`;
    text += `\n- Personas: ${data.responses.length}\n`;
    data.responses.forEach((r, i) => {
        text += `\n*${i + 1}. ${r.nombre_completo || 'Sin nombre'}*`;
        if (r.cedula) text += `\n- Cédula: ${r.cedula}`;
        if (r.pasaporte) text += `\n- Pasaporte: ${r.pasaporte}`;
        if (r.telefono) text += `\n- Teléfono: ${fmtTel506(r.telefono, data.show_pasaporte)}`;
        const emerg = (r.contacto_emergencia_nombre || '') + (r.contacto_emergencia_telefono ? ' - ' + fmtTel506(r.contacto_emergencia_telefono, data.show_pasaporte) : '');
        if (emerg.trim()) text += `\n- Emergencia: ${emerg.trim()}`;
        if (r.reservation_number) text += `\n- Reserva: ${r.reservation_number}`;
    });
    shareWhatsAppText(text);
}

loadForms();
