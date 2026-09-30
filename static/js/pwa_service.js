// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
// ==========================================
// PWA: REGISTRO DEL SERVICE WORKER
// ==========================================

// Registro del Service Worker
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js?v=10.18')
            .then(reg => console.log('[PWA] SW registrado:', reg.scope))
            .catch(err => console.warn('[PWA] SW falló:', err));
    });
}

// Capturar evento de instalación para el botón
window.deferredPWAPrompt = null;
window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    window.deferredPWAPrompt = e;
    const btn = document.getElementById('btnInstallPWA');
    if (btn) btn.classList.remove('d-none');
});

window.addEventListener('appinstalled', () => {
    window.deferredPWAPrompt = null;
    const btn = document.getElementById('btnInstallPWA');
    if (btn) btn.classList.add('d-none');
});

function installPWA() {
    if (!window.deferredPWAPrompt) return;
    window.deferredPWAPrompt.prompt();
    window.deferredPWAPrompt.userChoice.then(choice => {
        window.deferredPWAPrompt = null;
        const btn = document.getElementById('btnInstallPWA');
        if (btn) btn.classList.add('d-none');
    });
}

function formatOfflineBytes(bytes) {
    if (!Number.isFinite(bytes) || bytes <= 0) return '0 MB';
    const units = ['B', 'KB', 'MB', 'GB'];
    const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
    return `${(bytes / Math.pow(1024, index)).toFixed(index > 1 ? 1 : 0)} ${units[index]}`;
}

async function downloadAllOffline() {
    const button = document.getElementById('btnDownloadAllOffline');
    const progress = document.getElementById('offlineDownloadProgress');
    const status = document.getElementById('offlineDownloadStatus');
    ['offlineDownloadConsole', 'offlineDownloadConsoleModal'].forEach(id => {
        const consoleElement = document.getElementById(id);
        if (consoleElement) consoleElement.textContent = '';
    });
    if (window.LaTribuAndroid && typeof window.LaTribuAndroid.downloadAllOffline === 'function') {
        appendOfflineLog('Iniciando descarga en el almacenamiento nativo de Android.');
        if (button) button.disabled = true;
        if (progress) { progress.classList.remove('d-none'); progress.value = 0; }
        if (status) status.textContent = 'Preparando inventario offline en Android…';
        window.LaTribuAndroid.downloadAllOffline();
        return;
    }
    if (!navigator.serviceWorker) {
        if (status) status.textContent = 'Este navegador no admite el servicio de descarga offline.';
        return;
    }
    appendOfflineLog('Solicitud de descarga iniciada.');
    if (button) button.disabled = true;
    if (progress) { progress.classList.remove('d-none'); progress.value = 0; }
    if (status) status.textContent = 'Preparando inventario offline…';
    try {
        const inventoryResponse = await fetch('/api/offline/manifest', { credentials: 'include', cache: 'no-store' });
        if (!inventoryResponse.ok) throw new Error(`Inventario HTTP ${inventoryResponse.status}`);
        const inventory = await inventoryResponse.json();
        appendOfflineLog(`Inventario recibido: ${inventory.file_count} archivos, ${inventory.pages.length} páginas, ${formatOfflineBytes(inventory.total_bytes)}.`);
        if (status) status.textContent = 'Activando servicio de descarga…';
        if (navigator.storage && navigator.storage.persist) await navigator.storage.persist();
        const registration = await navigator.serviceWorker.register('/sw.js?v=10.18');
        await registration.update();
        if (registration.waiting) registration.waiting.postMessage({ type: 'SKIP_WAITING' });
        const worker = navigator.serviceWorker.controller || registration.active;
        if (!worker) throw new Error('El servicio offline todavía no controla esta pantalla. Recargá el perfil una vez.');
        worker.postMessage({ type: 'DOWNLOAD_ALL_OFFLINE' });
        window.setTimeout(() => {
            if (button && button.disabled && status && status.textContent.includes('Activando')) {
                button.disabled = false;
                status.textContent = 'El servicio no respondió. Recargá el perfil y volvé a intentarlo.';
                appendOfflineLog('Tiempo de espera agotado al activar el servicio offline.', 'error');
            }
        }, 15000);
    } catch (error) {
        if (button) button.disabled = false;
        if (status) status.textContent = `No se pudo iniciar: ${error.message}`;
        appendOfflineLog(`No se pudo iniciar: ${error.message}`, 'error');
    }
}

function appendOfflineLog(message, level = 'info') {
    const className = level === 'error' ? 'text-danger' : level === 'success' ? 'text-success' : 'text-light';
    const text = `[${new Date().toLocaleTimeString()}] ${message}`;
    ['offlineDownloadConsole', 'offlineDownloadConsoleModal'].forEach(id => {
        const consoleElement = document.getElementById(id);
        if (!consoleElement) return;
        const followTail = consoleElement.scrollHeight - consoleElement.scrollTop - consoleElement.clientHeight < 40;
        const line = document.createElement('div');
        line.className = className;
        line.dataset.level = level;
        line.textContent = text;
        consoleElement.appendChild(line);
        if (id === 'offlineDownloadConsole' || followTail) consoleElement.scrollTop = consoleElement.scrollHeight;
    });
}

function openOfflineConsoleModal() {
    const modalElement = document.getElementById('offlineConsoleModal');
    if (modalElement && window.bootstrap) bootstrap.Modal.getOrCreateInstance(modalElement).show();
}

async function copyOfflineErrors() {
    const source = document.getElementById('offlineDownloadConsoleModal') || document.getElementById('offlineDownloadConsole');
    const errors = source ? Array.from(source.querySelectorAll('[data-level="error"]')).map(line => line.textContent).join('\n') : '';
    const text = errors || 'No hay errores registrados en esta descarga.';
    try {
        await navigator.clipboard.writeText(text);
        appendOfflineLog(errors ? `${errors.split('\n').length} error(es) copiado(s) al portapapeles.` : text, errors ? 'success' : 'info');
    } catch (error) {
        window.prompt('Copiá los errores:', text);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const title = document.getElementById('offlineConsoleTitle');
    if (!title) return;
    let timer = null;
    let longPressed = false;
    const start = () => {
        longPressed = false;
        timer = window.setTimeout(async () => {
            longPressed = true;
            openOfflineConsoleModal();
            await copyOfflineErrors();
        }, 700);
    };
    const cancel = () => {
        if (timer) window.clearTimeout(timer);
        timer = null;
    };
    title.addEventListener('mousedown', start);
    title.addEventListener('touchstart', start, { passive: true });
    title.addEventListener('mouseup', cancel);
    title.addEventListener('mouseleave', cancel);
    title.addEventListener('touchend', cancel);
    title.addEventListener('touchcancel', cancel);
    title.addEventListener('click', event => {
        if (longPressed) {
            event.preventDefault();
            event.stopImmediatePropagation();
            longPressed = false;
        }
    }, true);
});
