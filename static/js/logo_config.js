// ==========================================
// CONFIGURACIÓN DEL LOGO DE SUEÑOS
// ==========================================

async function abrirConfigLogoSuenos() {
    try {
        const res = await fetch('/api/logo-config');
        const config = await res.json();
        document.getElementById('logoMostrarToggle').checked = config.mostrar;
        document.getElementById('logoEnlace').value = config.enlace || '';
        document.getElementById('logoTamañoPC').value = config.tamaño_pc || 150;
        document.getElementById('logoTamañoMobile').value = config.tamaño_mobile || 120;
        document.getElementById('logoPosicionLeft').value = config.posicion_left || 20;
        document.getElementById('logoPosicionBottom').value = config.posicion_bottom || 100;
        document.getElementById('logoNombreArchivo').value = config.nombre_archivo || 'logosueños.png';
    } catch (err) {
        console.error('Error al cargar configuración:', err);
    }
    cargarEventosActivos();
    const modal = new bootstrap.Modal(document.getElementById('configLogoSuenosModal'));
    modal.show();
}

async function cargarEventosActivos() {
    try {
        const res = await fetch('/api/eventos-activos');
        const eventos = await res.json();
        const select = document.getElementById('logoEventoSelect');
        select.innerHTML = '<option value="">-- Seleccionar evento --</option>';
        eventos.forEach(ev => {
            const option = document.createElement('option');
            option.value = ev.url;
            option.textContent = ev.nombre;
            select.appendChild(option);
        });
    } catch (err) {
        console.error('Error al cargar eventos:', err);
    }
}

function seleccionarEvento() {
    const select = document.getElementById('logoEventoSelect');
    const enlaceInput = document.getElementById('logoEnlace');
    if (select.value) {
        enlaceInput.value = select.value;
    }
}

async function guardarConfigLogoSuenos() {
    const config = {
        mostrar: document.getElementById('logoMostrarToggle').checked,
        enlace: document.getElementById('logoEnlace').value,
        tamaño_pc: parseInt(document.getElementById('logoTamañoPC').value),
        tamaño_mobile: parseInt(document.getElementById('logoTamañoMobile').value),
        posicion_left: parseInt(document.getElementById('logoPosicionLeft').value),
        posicion_bottom: parseInt(document.getElementById('logoPosicionBottom').value),
        nombre_archivo: document.getElementById('logoNombreArchivo').value
    };
    try {
        const res = await fetch('/api/logo-config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        const d = await res.json();
        if (d.ok) {
            aplicarConfigLogoSuenos(config);
            bootstrap.Modal.getInstance(document.getElementById('configLogoSuenosModal')).hide();
            alert('Configuración guardada correctamente');
        } else {
            alert('Error al guardar: ' + (d.error || 'Desconocido'));
        }
    } catch (err) {
        alert('Error de conexión');
    }
}

function aplicarConfigLogoSuenos(config) {
    const logoDesktopLink = document.getElementById('logoSuenosDesktopLink');
    const logoDesktopNoLink = document.getElementById('logoSuenosDesktopNoLink');
    const logoMobileLink = document.getElementById('logoSuenosMobileLink');
    const logoMobileNoLink = document.getElementById('logoSuenosMobileNoLink');
    const isMobile = window.innerWidth < 768;

    if (config.mostrar === false) {
        if (logoDesktopLink) logoDesktopLink.style.setProperty('display', 'none', 'important');
        if (logoDesktopNoLink) logoDesktopNoLink.style.setProperty('display', 'none', 'important');
        if (logoMobileLink) logoMobileLink.style.setProperty('display', 'none', 'important');
        if (logoMobileNoLink) logoMobileNoLink.style.setProperty('display', 'none', 'important');
    } else {
        if (config.enlace) {
            if (logoDesktopLink) logoDesktopLink.style.setProperty('display', isMobile ? 'none' : 'block', 'important');
            if (logoDesktopNoLink) logoDesktopNoLink.style.setProperty('display', 'none', 'important');
            if (logoMobileLink) logoMobileLink.style.setProperty('display', isMobile ? 'block' : 'none', 'important');
            if (logoMobileNoLink) logoMobileNoLink.style.setProperty('display', 'none', 'important');
        } else {
            if (logoDesktopLink) logoDesktopLink.style.setProperty('display', 'none', 'important');
            if (logoDesktopNoLink) logoDesktopNoLink.style.setProperty('display', isMobile ? 'none' : 'block', 'important');
            if (logoMobileLink) logoMobileLink.style.setProperty('display', 'none', 'important');
            if (logoMobileNoLink) logoMobileNoLink.style.setProperty('display', isMobile ? 'block' : 'none', 'important');
        }
    }

    if (config.nombre_archivo) {
        const imgUrl = '/static/uploads/' + config.nombre_archivo;
        const logoDesktopImg = document.getElementById('logoSuenosDesktop');
        const logoMobileImg = document.getElementById('logoSuenosMobile');
        if (logoDesktopImg) logoDesktopImg.src = imgUrl;
        if (logoMobileImg) logoMobileImg.src = imgUrl;
    }

    if (config.enlace) {
        if (logoDesktopLink) logoDesktopLink.href = config.enlace;
        if (logoMobileLink) logoMobileLink.href = config.enlace;
    }

    const logoDesktopImg = document.getElementById('logoSuenosDesktop');
    const logoMobileImg = document.getElementById('logoSuenosMobile');
    if (logoDesktopImg) {
        logoDesktopImg.style.height = config.tamaño_pc + 'px';
        logoDesktopImg.style.left = config.posicion_left + 'px';
        logoDesktopImg.style.bottom = config.posicion_bottom + 'px';
    }
    if (logoMobileImg) {
        logoMobileImg.style.height = config.tamaño_mobile + 'px';
    }
}

document.addEventListener('DOMContentLoaded', async function() {
    try {
        const res = await fetch('/api/logo-config');
        const config = await res.json();
        aplicarConfigLogoSuenos(config);
    } catch (err) {
        console.error('Error al cargar configuración del logo:', err);
    }
});

async function limpiarCachéChrome() {
    abrirModalBorrarUnificado({
        titulo: 'Limpiar Caché',
        mensaje: '¿Limpiar la caché de Chrome? Esto recargará la aplicación PWA.',
        onConfirmar: async () => {
            try {
                if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
                    const registrations = await navigator.serviceWorker.getRegistrations();
                    for (const registration of registrations) {
                        await registration.unregister();
                    }
                }
                if ('caches' in window) {
                    const cacheNames = await caches.keys();
                    await Promise.all(cacheNames.map(cacheName => caches.delete(cacheName)));
                }
                alert('Caché limpiada correctamente. La aplicación se recargará.');
                window.location.reload();
            } catch (error) {
                console.error('Error al limpiar caché:', error);
                alert('Error al limpiar la caché: ' + error.message);
            }
        }
    });
}
