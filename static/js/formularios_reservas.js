// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
let reservationNumbers = '';

async function openReservationModal() {
    if (!currentResponsesFormId) return;
    const modal = new bootstrap.Modal(document.getElementById('reservationModal'));
    document.getElementById('reservationModalLabel').textContent = `Números de Reserva - Formulario #${currentResponsesFormId}`;
    try {
        const res = await fetch(`/api/forms/${currentResponsesFormId}/reservation-numbers`);
        const data = await res.json();
        reservationNumbers = data.reservation_numbers || '';
        document.getElementById('reservationNumbersInput').value = reservationNumbers;
    } catch (e) {
        console.error('Error cargando números de reserva:', e);
    }
    modal.show();
}

async function saveReservationNumbers() {
    if (!currentResponsesFormId) return;
    reservationNumbers = document.getElementById('reservationNumbersInput').value.trim();
    try {
        const res = await fetch(`/api/forms/${currentResponsesFormId}/reservation-numbers`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reservation_numbers: reservationNumbers })
        });
        const data = await res.json();
        if (data.success) {
            bootstrap.Modal.getInstance(document.getElementById('reservationModal')).hide();
            alert('Números de reserva guardados');
            if (reservationNumbers) viewResponses(currentResponsesFormId);
        }
    } catch (e) {
        console.error('Error guardando números de reserva:', e);
        alert('Error al guardar números de reserva');
    }
}

function clearReservationNumbers() {
    document.getElementById('reservationNumbersInput').value = '';
}

function editReservationNumbers(formId) {
    currentResponsesFormId = formId;
    openReservationModal();
}

function copyReservationNumbers(text) {
    const numbers = (text || '').split(/\r?\n|\r|,/).map(n => n.trim()).filter(n => n).sort((a,b) => a.localeCompare(b, undefined, {numeric:true})).join(', ');
    if (!numbers) return;
    navigator.clipboard.writeText(numbers).then(() => alert('Números de reserva copiados')).catch(() => alert('No se pudo copiar'));
}

async function assignReservationNumber(responseId, reservationNumber) {
    try {
        const res = await fetch(`/api/responses/${responseId}/reservation-number`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reservation_number: reservationNumber })
        });
        const data = await res.json();
        if (data.success) {
            // Recargar la tabla para mostrar el cambio
            if (currentResponsesFormId) {
                viewResponses(currentResponsesFormId);
            }
        } else {
            alert('Error al asignar número de reserva');
        }
    } catch (e) {
        console.error('Error asignando número de reserva:', e);
        alert('Error al asignar número de reserva');
    }
}

