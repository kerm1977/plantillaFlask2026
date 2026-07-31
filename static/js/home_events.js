// Archivo: static/js/home_events.js
// Funciones de carga y gestión de eventos

let allEvents = [];

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
    abrirModalBorrarUnificado({
        titulo: 'Eliminar Publicación',
        mensaje: 'Esta acción borrará permanentemente la publicación y no se puede deshacer.',
        nombre: eventName || 'esta publicación',
        onConfirmar: async () => {
            try {
                const response = await fetch(`/api/delete_event/${eventId}`, { method: 'DELETE' });
                const result = await response.json();
                if (response.ok && result.success) {
                    try {
                        indexedDB.open(DB_NAME, DB_VERSION).onsuccess = (e) => e.target.result.transaction("eventos", "readwrite").objectStore("eventos").delete(eventId);
                    } catch(e) {}
                    loadEvents();
                } else {
                    alert("Error al eliminar el evento: " + (result.error || "Desconocido"));
                }
            } catch (err) {
                alert("Error de conexión al intentar eliminar el evento.");
            }
        }
    });
}
