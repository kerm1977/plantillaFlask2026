// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
// ==========================================// PWA: footer de version, updates Android y estado offline nativo

async function renderAppFooterVersion() {
    const element = document.getElementById('appFooterVersion');
    if (!element) return;
    try {
        if (window.LaTribuAndroid && typeof window.LaTribuAndroid.getVersionName === 'function') {
            element.className = 'small text-success fw-bold mt-1';
            element.textContent = `Aplicación Android · versión ${window.LaTribuAndroid.getVersionName()}`;
            return;
        }
        const response = await fetch('/api/app/version', { cache: 'no-store' });
        if (!response.ok) throw new Error();
        const data = await response.json();
        element.className = 'small text-secondary fw-semibold mt-1';
        element.textContent = `Sitio web · APK disponible ${data.versionName}`;
    } catch (error) {
        element.className = 'small text-secondary fw-semibold mt-1';
        element.textContent = 'Sitio web';
    }
}

document.addEventListener('DOMContentLoaded', renderAppFooterVersion);

let latestAndroidAppUpdate = null;

function downloadAppUpdate() {
    const status = document.getElementById('appUpdateStatus');
    if (!latestAndroidAppUpdate || !latestAndroidAppUpdate.url) {
        if (status) status.textContent = 'Primero buscá una actualización disponible.';
        return;
    }
    try {
        if (window.LaTribuAndroid && typeof window.LaTribuAndroid.downloadUpdate === 'function') {
            if (status) status.textContent = 'Iniciando descarga con Android…';
            window.LaTribuAndroid.downloadUpdate(latestAndroidAppUpdate.url);
        } else {
            window.location.assign(latestAndroidAppUpdate.url);
        }
    } catch (error) {
        if (status) status.textContent = `No se pudo iniciar la descarga: ${error.message}`;
    }
}

async function checkAppUpdate() {
    const status = document.getElementById('appUpdateStatus');
    try {
        const response = await fetch('/api/app/version', { cache: 'no-store' });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        latestAndroidAppUpdate = data;
        const installedCode = window.LaTribuAndroid && typeof window.LaTribuAndroid.getVersionCode === 'function' ? Number(window.LaTribuAndroid.getVersionCode()) : null;
        const installedName = window.LaTribuAndroid && typeof window.LaTribuAndroid.getVersionName === 'function' ? String(window.LaTribuAndroid.getVersionName()) : 'navegador web';
        const link = document.getElementById('appUpdateDownload');
        if (installedCode !== null && installedCode >= data.versionCode) {
            if (status) status.textContent = `La aplicación está actualizada (${installedName}).`;
            if (link) link.classList.add('d-none');
        } else {
            if (status) status.textContent = `Instalada: ${installedName}. Disponible: ${data.versionName} · ${formatOfflineBytes(data.size)}.`;
            if (link) link.classList.remove('d-none');
        }
    } catch (error) {
        if (status) status.textContent = `No se pudo comprobar la actualización: ${error.message}`;
    }
}

function handleNativeOfflineEvent(data) {
    const button = document.getElementById('btnDownloadAllOffline');
    const progress = document.getElementById('offlineDownloadProgress');
    const status = document.getElementById('offlineDownloadStatus');
    if (data.type === 'OFFLINE_DOWNLOAD_LOG') appendOfflineLog(data.message, data.level);
    if (data.type === 'OFFLINE_DOWNLOAD_START' && status) status.textContent = `Descargando ${data.total} elementos (${formatOfflineBytes(data.totalBytes)}) en Android…`;
    if (data.type === 'OFFLINE_DOWNLOAD_PROGRESS') {
        if (progress) progress.value = data.total ? data.completed * 100 / data.total : 0;
        if (status) status.textContent = `${data.completed}/${data.total} · ${formatOfflineBytes(data.downloadedBytes)} de ${formatOfflineBytes(data.totalBytes)} · reutilizados: ${data.reused || 0} · errores: ${Array.isArray(data.failures) ? data.failures.length : 0}`;
    }
    if (data.type === 'OFFLINE_DOWNLOAD_COMPLETE') {
        if (button) button.disabled = false;
        if (status) status.textContent = data.failures.length ? `Descarga finalizada con ${data.failures.length} errores.` : 'Toda la información está disponible offline en Android.';
    }
    if (data.type === 'OFFLINE_DOWNLOAD_ERROR') {
        if (button) button.disabled = false;
        if (status) status.textContent = `No se pudo continuar: ${data.error}`;
        appendOfflineLog(`No se pudo continuar: ${data.error}`, 'error');
    }
}

window.addEventListener('latribuNativeOffline', event => handleNativeOfflineEvent(event.detail || {}));
window.addEventListener('load', () => {
    if (!window.LaTribuAndroid || typeof window.LaTribuAndroid.getOfflineState !== 'function') return;
    try {
        const state = JSON.parse(window.LaTribuAndroid.getOfflineState() || 'null');
        if (state) renderOfflineDownloadState(state);
    } catch (error) {
        appendOfflineLog(`No se pudo leer el estado offline nativo: ${error.message}`, 'error');
    }
});

function renderOfflineDownloadState(state) {
    if (!state) return;
    const button = document.getElementById('btnDownloadAllOffline');
    const progress = document.getElementById('offlineDownloadProgress');
    const status = document.getElementById('offlineDownloadStatus');
    const failures = Array.isArray(state.failures) ? state.failures : [];
    if (progress) {
        progress.classList.remove('d-none');
        progress.value = state.total ? state.completed * 100 / state.total : 0;
    }
    if (button) button.disabled = state.status === 'running';
    if (status) status.textContent = `${state.completed || 0}/${state.total || 0} · ${formatOfflineBytes(state.downloadedBytes)} de ${formatOfflineBytes(state.totalBytes)} · reutilizados: ${state.reused || 0} · errores: ${failures.length}`;
    if (failures.length) failures.forEach(item => appendOfflineLog(`Error guardado ${item.error}: ${item.url}`, 'error'));
}

if ('serviceWorker' in navigator) {
    navigator.serviceWorker.addEventListener('message', event => {
        const data = event.data || {};
        const button = document.getElementById('btnDownloadAllOffline');
        const progress = document.getElementById('offlineDownloadProgress');
        const status = document.getElementById('offlineDownloadStatus');
        if (data.type === 'OFFLINE_DOWNLOAD_LOG') appendOfflineLog(data.message, data.level);
        if (data.type === 'OFFLINE_DOWNLOAD_START' && status) {
            status.textContent = `Descargando ${data.total} elementos (${formatOfflineBytes(data.totalBytes)})…`;
        }
        if (data.type === 'OFFLINE_DOWNLOAD_PROGRESS') {
            if (progress) progress.value = data.total ? data.completed * 100 / data.total : 0;
            if (status) status.textContent = `${data.completed}/${data.total} · ${formatOfflineBytes(data.downloadedBytes)} de ${formatOfflineBytes(data.totalBytes)} · reutilizados: ${data.reused || 0} · errores: ${Array.isArray(data.failures) ? data.failures.length : 0}`;
        }
        if (data.type === 'OFFLINE_DOWNLOAD_STATE') renderOfflineDownloadState(data.state);
        if (data.type === 'OFFLINE_DOWNLOAD_COMPLETE') {
            if (button) button.disabled = false;
            if (status) status.textContent = data.failures.length ? `Descarga finalizada con ${data.failures.length} errores.` : 'Toda la información está disponible offline.';
        }
        if (data.type === 'OFFLINE_DOWNLOAD_ERROR') {
            if (button) button.disabled = false;
            if (status) status.textContent = `Proceso interrumpido: ${data.error}. Podés reanudarlo sin repetir archivos completos.`;
            appendOfflineLog(`Proceso interrumpido: ${data.error}`, 'error');
        }
    });
    window.addEventListener('load', async () => {
        const registration = await navigator.serviceWorker.ready;
        if (registration.active) registration.active.postMessage({ type: 'GET_OFFLINE_DOWNLOAD_STATE' });
    });
}
