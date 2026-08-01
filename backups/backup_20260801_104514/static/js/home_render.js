// Archivo: static/js/home_render.js
// Funciones de renderizado de eventos

function renderEvents(eventsToRender, autoExpandAllSearch = false) {
    const container = document.getElementById('eventosContainer');
    if(!container) return;

    container.innerHTML = ''; 
    allMonthsList = [];

    if (eventsToRender.length === 0) {
        container.innerHTML = `
            <div class="col-12 text-center py-5 text-muted animate__animated animate__fadeIn">
                <i class="bi bi-search opacity-25" style="font-size: 4rem;"></i>
                <p class="mt-3 fs-5 fw-bold">No encontramos aventuras con esos criterios.</p>
                <button class="btn btn-outline-secondary rounded-pill mt-2 fw-bold" onclick="setQuickFilter('')">Limpiar Filtros</button>
            </div>`;
        return;
    }

    const sortedEvents = [...eventsToRender].sort((a, b) => {
        const matchA = a.fecha && a.fecha.match(/(\d{4}-\d{2}-\d{2})/);
        const matchB = b.fecha && b.fecha.match(/(\d{4}-\d{2}-\d{2})/);
        const dateA = matchA ? matchA[1] : '9999-99-99'; 
        const dateB = matchB ? matchB[1] : '9999-99-99';
        return dateA.localeCompare(dateB);
    });

    const mesesNombres = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"];
    
    const monthCounts = {};
    sortedEvents.forEach(ev => {
        let monthGroup = "Próximamente / Fechas por Definir";
        const dateMatch = ev.fecha && ev.fecha.match(/(\d{4})-(\d{2})-(\d{2})/);
        if (dateMatch) {
            const year = dateMatch[1];
            const monthIndex = parseInt(dateMatch[2], 10) - 1;
            monthGroup = `${mesesNombres[monthIndex]} ${year}`;
        }
        monthCounts[monthGroup] = (monthCounts[monthGroup] || 0) + 1;
    });

    let currentMonthLabel = "";
    let currentMonthId = "";
    let monthIndexCounter = 0;

    sortedEvents.forEach(ev => {
        let monthGroup = "Próximamente / Fechas por Definir";
        const dateMatch = ev.fecha && ev.fecha.match(/(\d{4})-(\d{2})-(\d{2})/);
        if (dateMatch) {
            const year = dateMatch[1];
            const monthIndex = parseInt(dateMatch[2], 10) - 1;
            monthGroup = `${mesesNombres[monthIndex]} ${year}`;
        }

        if (monthGroup !== currentMonthLabel) {
            currentMonthId = monthGroup.replace(/[^a-zA-Z0-9]/g, '-');
            allMonthsList.push(currentMonthId);
            const count = monthCounts[monthGroup];
            const colorClass = (monthIndexCounter % 2 === 0) ? 'month-black' : 'month-gray';
            monthIndexCounter++;

            if (autoExpandAllSearch) expandedMonths.add(currentMonthId);
            
            const isExpanded = expandedMonths.has(currentMonthId);
            const headerOpacity = isExpanded ? '1' : '0.6';
            const badgeDisplay = isExpanded ? 'd-none' : 'd-inline-flex';
            const chevronRotation = isExpanded ? 'rotate(180deg)' : 'rotate(0deg)';
            const hintClass = isExpanded ? 'd-none' : '';

            container.innerHTML += `
                <div class="col-12 mt-4 mb-2 animate__animated animate__fadeIn w-100 text-center text-sm-start">
                    <div class="d-flex flex-column align-items-center justify-content-center justify-content-sm-start" onclick="toggleMonthCards('${currentMonthId}')" style="cursor: pointer;" title="Presiona una vez para expandir o colapsar">
                        <div class="d-flex align-items-center w-100 justify-content-center justify-content-sm-start">
                            <h4 id="header-title-${currentMonthId}" class="${colorClass} fw-bold text-uppercase mb-0 pb-1 border-bottom border-2 d-flex align-items-center justify-content-between w-100 month-header-title" style="letter-spacing: 1px; opacity: ${headerOpacity};">
                                <span class="d-flex align-items-center">
                                    <i class="bi bi-calendar3 me-2"></i>${monthGroup}
                                    <i class="bi bi-chevron-down ms-2 fs-5" id="chevron-${currentMonthId}" style="transform: ${chevronRotation}; transition: transform 0.3s ease;"></i>
                                </span>
                                <span id="badge-${currentMonthId}" class="badge bg-white text-dark ms-3 shadow-sm border ${badgeDisplay} align-items-center" style="font-size: 0.85rem; border-radius: 12px;">
                                    <i class="bi bi-person-walking me-1" style="color:#0dcaf0 !important;"></i> ${count}
                                </span>
                            </h4>
                        </div>
                        <small id="hint-${currentMonthId}" class="text-muted mt-1 ${hintClass} text-center text-sm-start w-100" style="font-size: 0.75rem;">
                            <i class="bi bi-hand-index-thumb me-1"></i>Toca para expandir el mes
                        </small>
                        <hr class="flex-grow-1 border-secondary opacity-25 ms-3 my-0">
                    </div>
                </div>
            `;
            currentMonthLabel = monthGroup;
        }

        const badgeClass = getBadgeClass(ev.dificultad);
        const imgPath = ev.poster || ev.imagen || 'https://via.placeholder.com/270x480?text=Sin+Imagen';
        const { dateDisplay } = formatDateDisplay(ev, mesesNombres);
        const isPrivate = ev.solo_chat || ev.logistica_segura;
        const { destinoDisplay, timeDisplay } = getPrivateDisplay(ev, isPrivate);
        const isSoldOut = ev.is_sold_out === true;
        const cardClass = isSoldOut ? 'sold-out-card' : '';
        const overlay = isSoldOut ? '<div class="sold-out-overlay">SIN ESPACIO</div>' : '';
        const cardAction = (isSoldOut && !isSuperUser) ? `showSoldOutModal()` : `window.location.href='/detalles_evento/${ev.id}'`;
        const superUserBtns = isSuperUser ? `
            <div class="position-absolute top-0 start-0 m-2 d-flex gap-2" style="z-index: 20;">
                <button class="btn btn-sm ${isSoldOut ? 'btn-success' : 'btn-danger'} shadow-sm rounded-circle d-flex align-items-center justify-content-center" style="width: 35px; height: 35px;" onclick="event.stopPropagation(); toggleEspacio(${ev.id})" title="${isSoldOut ? 'Habilitar Espacio' : 'Marcar Sin Espacio'}">
                    <i class="bi ${isSoldOut ? 'bi-check-lg' : 'bi-x-lg'} fs-6"></i>
                </button>
                <button class="btn btn-sm btn-dark shadow-sm rounded-circle d-flex align-items-center justify-content-center" style="width: 35px; height: 35px;" onclick="event.stopPropagation(); initiateDeleteEvent(${ev.id}, '${ev.nombreLugar.replace(/'/g, "\\'").replace(/"/g, "&quot;")}')" title="Eliminar Publicación">
                    <i class="bi bi-trash-fill fs-6 text-white"></i>
                </button>
            </div>
        ` : '';
        const btnHacerPublico = (isSuperUser && isPrivate) ? `<button class="btn btn-outline-info w-100 rounded-pill mt-2 fw-bold shadow-sm py-1" style="font-size: 0.8rem; border-width: 2px;" onclick="event.stopPropagation(); makePublic(${ev.id})"><i class="bi bi-unlock-fill me-1"></i>Hacerlo Público</button>` : '';
        const isExpanded = expandedMonths.has(currentMonthId);

        if (currentViewMode === 'grid') {
            container.innerHTML += renderGridCard(ev, currentMonthId, isExpanded, imgPath, badgeClass, destinoDisplay, timeDisplay, dateDisplay, isSoldOut, cardClass, overlay, cardAction, superUserBtns, btnHacerPublico);
        } else {
            container.innerHTML += renderListCard(ev, currentMonthId, isExpanded, badgeClass, destinoDisplay, timeDisplay, dateDisplay, isSoldOut, cardClass, overlay, cardAction, superUserBtns, btnHacerPublico);
        }
    });

    updateGlobalToggleBtn();
}
