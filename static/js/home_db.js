// Archivo: static/js/home_db.js
// Funciones de IndexedDB para almacenamiento local

let localDB;
const DB_NAME = "EventosLocalDB";
const DB_VERSION = 3;

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
