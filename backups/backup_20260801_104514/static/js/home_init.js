// Archivo: static/js/home_init.js
// Inicialización y configuración

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

function showSoldOutModal() {
    const modalEl = document.getElementById('soldOutModal');
    if (modalEl) {
        const modal = new bootstrap.Modal(modalEl);
        modal.show();
    }
}

window.addEventListener('pageshow', (event) => {
    const isBackNavigation = event.persisted || 
        (typeof performance !== 'undefined' && performance.navigation.type === 2);
        
    if (isBackNavigation) {
        console.log("Regreso detectado. Refrescando eventos silenciosamente...");
        loadEvents();
    }
});
