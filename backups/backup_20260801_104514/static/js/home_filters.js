// Archivo: static/js/home_filters.js
// Funciones de filtrado y vista

let currentViewMode = 'grid';
let expandedMonths = new Set();
let allMonthsList = [];

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
