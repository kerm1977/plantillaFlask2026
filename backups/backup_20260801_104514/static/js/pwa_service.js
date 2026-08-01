// ==========================================
// PWA: REGISTRO DEL SERVICE WORKER
// ==========================================

// Registro del Service Worker
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
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
