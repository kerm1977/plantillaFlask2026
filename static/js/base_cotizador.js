// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
let cotizadorBusModal;
let cotizadorBusSlug = null;

function abrirCotizadorBus() {
    if(!cotizadorBusModal) cotizadorBusModal = new bootstrap.Modal(document.getElementById('cotizadorBusModal'));
    cotizadorBusModal.show();
}

function showCotizadorBusError(mensaje) {
    if(typeof mostrarAlerta === 'function') mostrarAlerta(mensaje, 'error', 1100);
    else alert(mensaje);
}

function toggleClaveCotizadorBusVisibilidad() {
    const input = document.getElementById('claveCotizadorBus');
    const icon = document.getElementById('toggleClaveCotizadorBus');
    if(input.type === 'password') {
        input.type = 'text';
        icon.classList.replace('bi-eye-slash', 'bi-eye');
    } else {
        input.type = 'password';
        icon.classList.replace('bi-eye', 'bi-eye-slash');
    }
}

async function ingresarCotizadorBus() {
    const clave = document.getElementById('claveCotizadorBus').value.trim();
    if(!clave) {
        showCotizadorBusError('Ingrese la clave de acceso.');
        return;
    }
    if(!cotizadorBusSlug) {
        try {
            const res = await fetch('/api/cotizadores/unico');
            const d = await res.json().catch(() => ({}));
            if(!d.slug) {
                showCotizadorBusError('No hay un cotizador activo.');
                return;
            }
            cotizadorBusSlug = d.slug;
        } catch(e) {
            showCotizadorBusError('Error al obtener el cotizador.');
            return;
        }
    }
    try {
        const res = await fetch('/cotizadores/' + cotizadorBusSlug + '/verificar', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({clave})});
        const d = await res.json().catch(() => ({error:'Error del servidor'}));
        if(d.ok) {
            sessionStorage.setItem('transaviClave', clave);
            cotizadorBusModal.hide();
            window.location.href = '/cotizadores/' + cotizadorBusSlug;
        } else {
            showCotizadorBusError(d.error || 'Clave incorrecta. Por favor, verifique e intente de nuevo.');
        }
    } catch(e) {
        showCotizadorBusError('Error al verificar la clave.');
    }
}
