// ==========================================
// RENDERIZADO DE TARJETAS DE EVENTOS
// ==========================================

function renderGridCard(ev, currentMonthId, isExpanded, imgPath, badgeClass, destinoDisplay, timeDisplay, dateDisplay, isSoldOut, cardClass, overlay, cardAction, superUserBtns, btnHacerPublico) {
    const visibilityClass = isExpanded ? '' : 'd-none';
    const googleCalendarBtn = ev.google_calendar_link ? 
        `<a href="${ev.google_calendar_link}" target="_blank" class="btn btn-sm rounded-pill px-3 py-1 fw-bold text-white w-100 mb-2" 
           style="background:#4285F4;border:none;" onclick="event.stopPropagation()">
          <i class="bi bi-google me-1"></i>Agregar a G.Calendar
        </a>` : '';
    
    return `
        <div class="col-12 col-xxs-6 col-sm-6 col-lg-4 col-xl-3 animate__animated animate__zoomIn month-item-${currentMonthId} ${visibilityClass}">
            <div class="glass-panel event-card rounded-4 h-100 d-flex flex-column overflow-hidden shadow-sm ${cardClass}" onclick="${cardAction}" style="cursor: pointer; position: relative;">
                ${superUserBtns}
                <div class="event-img-container border-bottom border-white border-2 position-relative">
                    ${overlay}
                    <img src="${imgPath}" onerror="this.src='https://via.placeholder.com/270x480?text=Error+Imagen'">
                    <span class="badge-dificultad ${badgeClass}">${ev.dificultad}</span>
                </div>
                <div class="p-3 d-flex flex-column flex-grow-1">
                    <span class="badge bg-dark rounded-pill align-self-start mb-2 px-2 py-1 shadow-sm" style="font-size: 0.65rem; white-space: normal; text-align: center; max-width: 100%; line-height: 1.2;">${ev.actividad}</span>
                    <h5 class="fw-bold text-dark mb-1 text-truncate-multiline lh-sm">${ev.nombreLugar}</h5>
                    <p class="text-secondary small mb-1 text-truncate" title="Punto de Salida">${destinoDisplay}</p>
                    <p class="text-secondary small mb-3 text-truncate" title="Hora de Salida">${timeDisplay}</p>
                    ${googleCalendarBtn}
                    <div class="event-details-box mt-auto d-flex justify-content-between align-items-center">
                        <div class="d-flex flex-column">
                            <span class="text-muted" style="font-size: 0.65rem; font-weight: 800; text-transform: uppercase;">Precio</span>
                            <span class="fw-bold text-orange fs-6">${ev.precio}</span>
                        </div>
                        <div class="text-end d-flex flex-column text-end-mobile">
                            <span class="text-muted" style="font-size: 0.65rem; font-weight: 800; text-transform: uppercase;">Día Exacto</span>
                            <span class="fw-semibold text-dark small" style="font-size: 0.75rem;">
                                <i class="bi bi-calendar-check text-orange me-1"></i>${dateDisplay}
                            </span>
                        </div>
                    </div>
                    ${btnHacerPublico}
                </div>
            </div>
        </div>
    `;
}

function renderListCard(ev, currentMonthId, isExpanded, badgeClass, destinoDisplay, timeDisplay, dateDisplay, isSoldOut, cardClass, overlay, cardAction, superUserBtns, btnHacerPublico) {
    const visibilityClass = isExpanded ? '' : 'd-none';
    const googleCalendarBtn = ev.google_calendar_link ? 
        `<a href="${ev.google_calendar_link}" target="_blank" class="btn btn-sm rounded-pill px-3 py-1 fw-bold text-white w-100 mb-2" 
           style="background:#4285F4;border:none;" onclick="event.stopPropagation()">
          <i class="bi bi-google me-1"></i>Agregar a G.Calendar
        </a>` : '';
    
    return `
        <div class="col-12 col-md-6 col-lg-4 animate__animated animate__fadeInUp month-item-${currentMonthId} ${visibilityClass}">
            <div class="glass-panel p-3 rounded-4 list-card-hover bg-white bg-opacity-50 ${cardClass}" onclick="${cardAction}" style="cursor: pointer; position: relative; overflow: hidden;">
                ${superUserBtns}
                ${overlay}
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <div class="pe-2 overflow-hidden">
                        <span class="badge bg-dark rounded-pill mb-1 d-inline-block" style="font-size: 0.6rem; white-space: normal; text-align: left; max-width: 100%; line-height: 1.2;">${ev.actividad}</span>
                        <h6 class="fw-bold text-dark mb-0 text-truncate lh-sm" style="font-size: 1rem; max-width: 100%;">${ev.nombreLugar}</h6>
                    </div>
                    <span class="badge-dificultad-list ${badgeClass} flex-shrink-0 shadow-sm mt-1">${ev.dificultad}</span>
                </div>
                <div class="text-secondary small mb-2" style="font-size: 0.8rem;">
                    <div class="text-truncate mb-1">${destinoDisplay}</div>
                    <div class="text-truncate mb-1">${timeDisplay}</div>
                    <div class="fw-bold text-dark text-truncate">
                        <i class="bi bi-calendar-check text-orange me-1"></i>${dateDisplay}
                    </div>
                </div>
                ${googleCalendarBtn}
                <div class="d-flex justify-content-between align-items-end border-top border-white border-opacity-75 pt-2">
                    <div class="text-end flex-shrink-0">
                        <span class="text-muted d-block lh-1" style="font-size: 0.6rem; text-transform: uppercase; font-weight: 800;">Precio</span>
                        <span class="fw-bold text-orange fs-5 lh-1">${ev.precio}</span>
                    </div>
                </div>
                ${btnHacerPublico}
                <div class="mt-2"></div>
            </div>
        </div>
    `;
}
