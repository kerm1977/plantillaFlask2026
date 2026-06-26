// ==========================================
// UTILIDADES DE RENDERIZADO DE EVENTOS
// ==========================================

const isSuperUser = window.IS_SUPER_USER || false;

function getBadgeClass(dificultad) {
    if (dificultad === 'Intermedio') return "bg-warning text-dark";
    if (dificultad === 'Dificil' || dificultad === 'Técnico' || dificultad === 'Avanzado') return "bg-danger";
    return "bg-success";
}

function formatDateDisplay(ev, mesesNombres) {
    let dateDisplay = ev.fecha || "Por definir";
    const dateMatch = ev.fecha && ev.fecha.match(/(\d{4})-(\d{2})-(\d{2})/);
    if (dateMatch) {
        const day = parseInt(dateMatch[3], 10);
        const month = mesesNombres[parseInt(dateMatch[2], 10) - 1];
        const yearShort = dateMatch[1];
        dateDisplay = `${day} de ${month} del ${yearShort}`;
        if (ev.fecha.includes('al')) dateDisplay += " (varios días)";
    }
    return { dateDisplay, dateMatch };
}

function getPrivateDisplay(ev, isPrivate) {
    let destinoDisplay = "";
    let timeDisplay = "";
    
    if (isPrivate) {
        if (isSuperUser) {
            destinoDisplay = `<i class="bi bi-geo-alt-fill text-orange me-1"></i>${ev.destino} <span class="badge bg-danger rounded-pill ms-1" style="font-size:0.55rem;">Oculto</span>`;
            timeDisplay = `<i class="bi bi-clock-fill text-orange me-1"></i>${ev.hora_salida || 'Por definir'} <span class="badge bg-danger rounded-pill ms-1" style="font-size:0.55rem;">Oculto</span>`;
        } else {
            destinoDisplay = `<span class="text-danger fw-bold"><i class="bi bi-shield-lock-fill me-1"></i>Info en chat</span>`;
            timeDisplay = `<span class="text-danger fw-bold"><i class="bi bi-shield-lock-fill me-1"></i>Info en chat</span>`;
        }
    } else {
        destinoDisplay = `<i class="bi bi-geo-alt-fill text-orange me-1"></i>${ev.destino}`;
        timeDisplay = `<i class="bi bi-clock-fill text-orange me-1"></i>${ev.hora_salida || 'Por definir'}`;
    }
    
    return { destinoDisplay, timeDisplay };
}
