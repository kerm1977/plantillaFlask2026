// Archivo: static/js/home.js

let allEvents = [];
let currentViewMode = 'grid'; 
let localDB; 

let expandedMonths = new Set(); 
let allMonthsList = []; 

// Leemos la variable inyectada desde Flask en el HTML
const isSuperUser = window.IS_SUPER_USER || false;
const DB_NAME = "EventosLocalDB";
const DB_VERSION = 3; 

let deleteHomeEventId = null;
let deleteHomeClicks = 0;

document.addEventListener("DOMContentLoaded", async () => {
    await initDB();
    
    currentViewMode = await loadSetting('userViewMode', 'grid');
    updateViewButtons(currentViewMode);
    
    loadEvents();

    const filtersCollapse = document.getElementById('filtersCollapse');
    const btnToggle = document.getElementById('btnToggleOpciones');
    
    if(filtersCollapse && btnToggle) {
        filtersCollapse.addEventListener('show.bs.collapse', () => {
            btnToggle.innerHTML = '<i class="bi bi-x-lg fs-5"></i>';
            btnToggle.classList.add('bg-white');
        });
        filtersCollapse.addEventListener('hide.bs.collapse', () => {
            btnToggle.innerHTML = '<i class="bi bi-search fs-5"></i>';
            btnToggle.classList.remove('bg-white');
        });
    }

    // LÓGICA DE LA FLECHITA DE LA NOTA
    const collapseNotaTribu = document.getElementById('collapseNotaTribu');
    const notaChevron = document.getElementById('notaChevron');
    if (collapseNotaTribu && notaChevron) {
        collapseNotaTribu.addEventListener('show.bs.collapse', () => {
            notaChevron.style.transform = 'rotate(180deg)';
        });
        collapseNotaTribu.addEventListener('hide.bs.collapse', () => {
            notaChevron.style.transform = 'rotate(0deg)';
        });
    }
});

// NUEVO: Función para mostrar el modal de "Sin Espacio"
function showSoldOutModal() {
    const modalEl = document.getElementById('soldOutModal');
    if (modalEl) {
        const modal = new bootstrap.Modal(modalEl);
        modal.show();
    }
}

// NUEVO Y REFORZADO: Detectar si el usuario regresó con el botón "Atrás" en todos los navegadores
window.addEventListener('pageshow', (event) => {
    // Detecta BFCache (Safari/iOS) o navegación histórica estándar
    const isBackNavigation = event.persisted || 
        (typeof performance !== 'undefined' && performance.navigation.type === 2);
        
    if (isBackNavigation) {
        console.log("Regreso detectado. Refrescando eventos silenciosamente...");
        loadEvents();
    }
});

function initDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, DB_VERSION);
        request.onupgradeneeded = (e) => {
            const db = e.target.result;
            if (!db.objectStoreNames.contains("eventos")) db.createObjectStore("eventos", { keyPath: "id", autoIncrement: true });
            if (!db.objectStoreNames.contains("settings")) db.createObjectStore("settings", { keyPath: "id" });
        };
        request.onsuccess = (e) => {
            localDB = e.target.result;
            resolve(localDB);
        };
        request.onerror = (e) => reject(e.target.error);
    });
}

function saveSetting(key, value) {
    if (!localDB) return;
    localDB.transaction("settings", "readwrite").objectStore("settings").put({ id: key, value: value });
}

function loadSetting(key, defaultValue) {
    return new Promise((resolve) => {
        if (!localDB) resolve(defaultValue);
        const request = localDB.transaction("settings", "readonly").objectStore("settings").get(key);
        request.onsuccess = () => resolve(request.result ? request.result.value : defaultValue);
        request.onerror = () => resolve(defaultValue);
    });
}

async function loadEvents() {
    const container = document.getElementById('eventosContainer');
    try {
        const response = await fetch('/api/get_events');
        if (!response.ok) throw new Error("Server error");
        
        const fetchedEvents = await response.json();
        allEvents = fetchedEvents;
        
        if (allEvents && allEvents.length > 0) {
            renderEvents(allEvents, false);
            syncEventsToIndexedDB(allEvents);
        } else {
            if(container) container.innerHTML = `<div class="col-12 text-center py-5 text-muted"><i class="bi bi-calendar-x opacity-25" style="font-size: 4rem;"></i><p class="mt-3 fs-5">No hay eventos publicados actualmente.</p></div>`;
        }
    } catch (err) {
        console.warn("Fallo de conexión. Cargando modo Offline.");
        loadEventsFromIndexedDB();
    }
}

// ----------------------------------------------------------------------------------
// ACTUALIZACIÓN OPTIMISTA SIN COLAPSAR (Se cambió a false el filtro)
// ----------------------------------------------------------------------------------

async function toggleEspacio(eventId) {
    // 1. ACTUALIZACIÓN INSTANTÁNEA EN LA PANTALLA
    const eventIndex = allEvents.findIndex(ev => ev.id === eventId);
    if (eventIndex !== -1) {
        // Invertimos el valor al instante
        allEvents[eventIndex].is_sold_out = !allEvents[eventIndex].is_sold_out;
        // False evita que se borre el historial de meses expandidos (¡Ya no colapsa!)
        filterEventsLive(false); 
        // Guardamos en la base de datos local para que se mantenga si el usuario navega rápido
        syncEventsToIndexedDB(allEvents);
    }

    // 2. PETICIÓN REAL AL SERVIDOR (En segundo plano)
    try {
        const response = await fetch(`/api/toggle_espacio/${eventId}`, { method: 'POST' });
        const result = await response.json();
        
        if (!response.ok || !result.success) {
            throw new Error(result.error || "Error del servidor al guardar.");
        }
    } catch(err) {
        // Si falló el internet o el servidor, deshacemos el cambio visual
        if (eventIndex !== -1) {
            allEvents[eventIndex].is_sold_out = !allEvents[eventIndex].is_sold_out;
            filterEventsLive(false);
        }
        alert("Error de conexión: No se pudo guardar el cambio.");
    }
}

async function makePublic(eventId) {
    // ACTUALIZACIÓN INSTANTÁNEA EN LA PANTALLA
    const eventIndex = allEvents.findIndex(ev => ev.id === eventId);
    if (eventIndex !== -1) {
        allEvents[eventIndex].solo_chat = false;
        allEvents[eventIndex].logistica_segura = false;
        filterEventsLive(false); // Evita el colapso del acordeón de meses
        syncEventsToIndexedDB(allEvents);
    }

    // PETICIÓN REAL AL SERVIDOR
    try {
        const response = await fetch(`/api/make_public/${eventId}`, { method: 'POST' });
        const result = await response.json();
        if (!response.ok || !result.success) {
             throw new Error("Error del servidor.");
        }
    } catch(err) {
        alert("Error de conexión al intentar hacer público.");
        loadEvents(); 
    }
}
// ----------------------------------------------------------------------------------

function initiateDeleteEvent(eventId, eventName) {
    deleteHomeEventId = eventId;
    deleteHomeClicks = 0;
    const nameEl = document.getElementById('deleteEventHomeName');
    if(nameEl) nameEl.innerHTML = `Esta acción borrará permanentemente la publicación "<strong>${eventName}</strong>" y no se puede deshacer.`;
    resetDeleteBtn();
    new bootstrap.Modal(document.getElementById('deleteEventHomeModal')).show();
}

function processDeleteEventHome() {
    const btn = document.getElementById('btnConfirmDeleteHome');
    deleteHomeClicks++;
    if (deleteHomeClicks === 1) {
        btn.innerHTML = '<i class="bi bi-exclamation-triangle-fill me-2"></i>¿Está seguro?';
        btn.className = 'btn btn-warning fw-bold rounded-pill px-4 shadow-sm w-100 text-dark';
    } else if (deleteHomeClicks === 2) {
        btn.innerHTML = '<i class="bi bi-exclamation-octagon-fill me-2"></i>¿Completamente seguro?';
        btn.className = 'btn btn-dark fw-bold rounded-pill px-4 shadow-sm w-100 text-white';
    } else {
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Borrando...';
        btn.disabled = true;
        executeDeleteEventHome(deleteHomeEventId);
    }
    setTimeout(() => { if (deleteHomeClicks > 0 && deleteHomeClicks < 3) resetDeleteBtn(); }, 4000);
}

async function executeDeleteEventHome(eventId) {
    try {
        const response = await fetch(`/api/delete_event/${eventId}`, { method: 'DELETE' });
        const result = await response.json();
        if (response.ok && result.success) {
            try {
                indexedDB.open(DB_NAME, DB_VERSION).onsuccess = (e) => e.target.result.transaction("eventos", "readwrite").objectStore("eventos").delete(eventId);
            } catch(e) {}
            const modalEl = document.getElementById('deleteEventHomeModal');
            if (modalEl) bootstrap.Modal.getInstance(modalEl)?.hide();
            loadEvents();
        } else {
            alert("Error al eliminar el evento: " + (result.error || "Desconocido"));
            resetDeleteBtn();
        }
    } catch (err) {
        alert("Error de conexión al intentar eliminar el evento.");
        resetDeleteBtn();
    }
}

function resetDeleteBtn() {
    const btn = document.getElementById('btnConfirmDeleteHome');
    if(btn) {
        btn.disabled = false;
        deleteHomeClicks = 0;
        btn.innerHTML = 'Sí, eliminar evento';
        btn.className = 'btn btn-danger fw-bold rounded-pill px-4 shadow-sm w-100 text-white';
    }
}

function setViewMode(mode) {
    currentViewMode = mode;
    saveSetting('userViewMode', mode);
    updateViewButtons(mode);
    filterEventsLive(false); 
}

function updateViewButtons(mode) {
    const btnGrid = document.getElementById('btnViewGrid');
    const btnList = document.getElementById('btnViewList');
    if(!btnGrid || !btnList) return;
    
    if (mode === 'grid') {
        btnGrid.className = 'btn btn-orange rounded-pill px-3 fw-bold shadow-sm';
        btnList.className = 'btn bg-transparent text-secondary rounded-pill px-3 fw-bold';
    } else {
        btnList.className = 'btn btn-orange rounded-pill px-3 fw-bold shadow-sm';
        btnGrid.className = 'btn bg-transparent text-secondary rounded-pill px-3 fw-bold';
    }
}

function setQuickFilter(term) {
    const searchInput = document.getElementById('globalSearchInput');
    if(searchInput) searchInput.value = term;
    filterEventsLive(true); 
}

function filterEventsLive(isUserInput = false) {
    const query = document.getElementById('globalSearchInput')?.value.toLowerCase() || '';
    const monthQuery = document.getElementById('monthFilter')?.value || ''; 
    const isSearching = (query.length > 0 || monthQuery !== "");

    if (isUserInput) {
        expandedMonths.clear();
    }

    const filteredEvents = allEvents.filter(ev => {
        const searchPool = `${ev.nombreLugar} ${ev.dificultad} ${ev.actividad} ${ev.precio} ${ev.destino} ${ev.fecha}`.toLowerCase();
        const matchesText = searchPool.includes(query);
        let matchesMonth = true;
        if (monthQuery !== "") {
            matchesMonth = ev.fecha && ev.fecha.includes(monthQuery);
        }
        return matchesText && matchesMonth;
    });

    renderEvents(filteredEvents, isUserInput && isSearching);
}

function toggleMonthCards(monthId, targetState = null, isGlobalAction = false) {
    const isNowExpanded = expandedMonths.has(monthId);
    let nextState = targetState !== null ? targetState : !isNowExpanded;

    if (nextState && !isGlobalAction) {
        expandedMonths.forEach(otherId => {
            if (otherId !== monthId) applyMonthState(otherId, false);
        });
    }

    applyMonthState(monthId, nextState);
    updateGlobalToggleBtn();
}

function applyMonthState(monthId, expand) {
    const items = document.querySelectorAll(`.month-item-${monthId}`);
    const headerTitle = document.getElementById(`header-title-${monthId}`);
    const badge = document.getElementById(`badge-${monthId}`);
    const chevron = document.getElementById(`chevron-${monthId}`);
    const hint = document.getElementById(`hint-${monthId}`);

    if (expand) {
        expandedMonths.add(monthId);
        items.forEach(i => i.classList.remove('d-none'));
        if (headerTitle) headerTitle.style.opacity = '1';
        if (badge) { badge.classList.remove('d-inline-flex'); badge.classList.add('d-none'); }
        if (chevron) chevron.style.transform = 'rotate(180deg)';
        if (hint) hint.classList.add('d-none');
    } else {
        expandedMonths.delete(monthId);
        items.forEach(i => i.classList.add('d-none'));
        if (headerTitle) headerTitle.style.opacity = '0.6';
        if (badge) { badge.classList.remove('d-none'); badge.classList.add('d-inline-flex'); }
        if (chevron) chevron.style.transform = 'rotate(0deg)';
        if (hint) hint.classList.remove('d-none');
    }
}

function toggleAllMonths() {
    const isExpandingAll = expandedMonths.size < allMonthsList.length;
    allMonthsList.forEach(monthId => { applyMonthState(monthId, isExpandingAll); });
    updateGlobalToggleBtn();
}

function updateGlobalToggleBtn() {
    const btn = document.getElementById('btnToggleAllMonths');
    if (!btn) return;
    if (expandedMonths.size === allMonthsList.length && allMonthsList.length > 0) {
        btn.innerHTML = '<i class="bi bi-arrows-collapse me-1"></i>Ocultar Todo';
    } else {
        btn.innerHTML = '<i class="bi bi-arrows-expand me-1"></i>Mostrar Todo';
    }
}

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
                            <h4 id="header-title-${currentMonthId}" class="${colorClass} fw-bold text-uppercase mb-0 pb-1 border-bottom border-2 d-inline-flex align-items-center month-header-title" style="letter-spacing: 1px; opacity: ${headerOpacity};">
                                <i class="bi bi-calendar3 me-2"></i>${monthGroup}
                                <i class="bi bi-chevron-down ms-2 fs-5" id="chevron-${currentMonthId}" style="transform: ${chevronRotation}; transition: transform 0.3s ease;"></i>
                                <span id="badge-${currentMonthId}" class="badge bg-white text-dark ms-3 shadow-sm border ${badgeDisplay} align-items-center" style="font-size: 0.85rem; border-radius: 12px;">
                                    <i class="bi bi-droplet-fill text-info me-1"></i> ${count}
                                </span>
                            </h4>
                            <hr class="flex-grow-1 border-secondary opacity-25 ms-3 my-0 d-none d-sm-block">
                        </div>
                        <small id="hint-${currentMonthId}" class="text-muted mt-1 ${hintClass} text-center text-sm-start w-100" style="font-size: 0.75rem;">
                            <i class="bi bi-hand-index-thumb me-1"></i>Toca para expandir el mes
                        </small>
                    </div>
                </div>
            `;
            currentMonthLabel = monthGroup;
        }

        let badgeClass = "bg-success";
        if(ev.dificultad === 'Intermedio') badgeClass = "bg-warning text-dark";
        if(ev.dificultad === 'Dificil' || ev.dificultad === 'Técnico' || ev.dificultad === 'Avanzado') badgeClass = "bg-danger";

        const imgPath = ev.poster || ev.imagen || 'https://via.placeholder.com/270x480?text=Sin+Imagen';
        
        let dateDisplay = ev.fecha || "Por definir";
        if (dateMatch) {
            const day = parseInt(dateMatch[3], 10);
            const month = mesesNombres[parseInt(dateMatch[2], 10) - 1];
            const yearShort = dateMatch[1];
            dateDisplay = `${day} de ${month} del ${yearShort}`;
            if (ev.fecha.includes('al')) dateDisplay += " (varios días)"; 
        }

        let isPrivate = ev.solo_chat || ev.logistica_segura;
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

        const isSoldOut = ev.is_sold_out === true;
        const cardClass = isSoldOut ? 'sold-out-card' : '';
        const overlay = isSoldOut ? '<div class="sold-out-overlay">SIN ESPACIO</div>' : '';
        
        // LÓGICA DE CLICK: Activa el Modal si está agotado y no es admin
        const cardAction = (isSoldOut && !isSuperUser) 
            ? `showSoldOutModal()` 
            : `window.location.href='/detalles_evento/${ev.id}'`;

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

        const btnHacerPublico = (isSuperUser && isPrivate)
            ? `<button class="btn btn-outline-info w-100 rounded-pill mt-2 fw-bold shadow-sm py-1" style="font-size: 0.8rem; border-width: 2px;" onclick="event.stopPropagation(); makePublic(${ev.id})"><i class="bi bi-unlock-fill me-1"></i>Hacerlo Público</button>`
            : '';

        const isExpanded = expandedMonths.has(currentMonthId);
        const visibilityClass = isExpanded ? '' : 'd-none';

        if (currentViewMode === 'grid') {
            container.innerHTML += `
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
                            
                            <p class="text-secondary small mb-1 text-truncate" title="Punto de Salida">
                                ${destinoDisplay}
                            </p>
                            <p class="text-secondary small mb-3 text-truncate" title="Hora de Salida">
                                ${timeDisplay}
                            </p>

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
        } else {
            container.innerHTML += `
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
                        
                        <div class="d-flex justify-content-between align-items-end mt-3 border-top border-white border-opacity-75 pt-2">
                            <div class="text-secondary small" style="font-size: 0.8rem; flex-grow: 1; min-width: 0; padding-right: 10px;">
                                <div class="text-truncate mb-1">
                                    ${destinoDisplay}
                                </div>
                                <div class="text-truncate mb-1">
                                    ${timeDisplay}
                                </div>
                                <div class="fw-bold text-dark text-truncate">
                                    <i class="bi bi-calendar-check text-orange me-1"></i>${dateDisplay}
                                </div>
                            </div>
                            
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
    });

    updateGlobalToggleBtn();
}

function syncEventsToIndexedDB(events) {
    if (!localDB) return;
    try {
        const tx = localDB.transaction("eventos", "readwrite");
        const store = tx.objectStore("eventos");
        store.clear(); 
        events.forEach(ev => store.put(ev));
    } catch (err) {}
}

function loadEventsFromIndexedDB() {
    if (!localDB) return;
    try {
        const tx = localDB.transaction("eventos", "readonly");
        const store = tx.objectStore("eventos");
        const getAll = store.getAll();
        getAll.onsuccess = () => {
            if (getAll.result && getAll.result.length > 0) {
                allEvents = getAll.result;
                renderEvents(allEvents, false);
            } else {
                const container = document.getElementById('eventosContainer');
                if(container) container.innerHTML = `<div class="col-12 text-center py-5">Sin conexión y sin datos locales.</div>`;
            }
        };
    } catch (err) {}
}