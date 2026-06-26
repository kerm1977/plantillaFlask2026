// Archivo: static/js/home_events.js
// Funciones de carga y gestión de eventos

let allEvents = [];
let deleteHomeEventId = null;
let deleteHomeClicks = 0;

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

// Limpiar IndexedDB al cargar la página para evitar datos corruptos
async function clearIndexedDB() {
    try {
        if (!localDB) {
            localDB = await initDB();
        }
        const tx = localDB.transaction("eventos", "readwrite");
        const store = tx.objectStore("eventos");
        store.clear();
        console.log("IndexedDB limpiado correctamente");
    } catch (err) {
        console.warn("Error limpiando IndexedDB:", err);
    }
}

async function toggleEspacio(eventId) {
    const eventIndex = allEvents.findIndex(ev => ev.id === eventId);
    if (eventIndex !== -1) {
        allEvents[eventIndex].is_sold_out = !allEvents[eventIndex].is_sold_out;
        filterEventsLive(false);
        syncEventsToIndexedDB(allEvents);
    }

    try {
        const response = await fetch(`/api/toggle_espacio/${eventId}`, { method: 'POST' });
        const result = await response.json();
        
        if (!response.ok || !result.success) {
            throw new Error(result.error || "Error del servidor al guardar.");
        }
    } catch(err) {
        if (eventIndex !== -1) {
            allEvents[eventIndex].is_sold_out = !allEvents[eventIndex].is_sold_out;
            filterEventsLive(false);
        }
        alert("Error de conexión: No se pudo guardar el cambio.");
    }
}

async function makePublic(eventId) {
    const eventIndex = allEvents.findIndex(ev => ev.id === eventId);
    if (eventIndex !== -1) {
        allEvents[eventIndex].solo_chat = false;
        allEvents[eventIndex].logistica_segura = false;
        filterEventsLive(false);
        syncEventsToIndexedDB(allEvents);
    }

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
