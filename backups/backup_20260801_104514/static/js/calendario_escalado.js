// ==========================================
// ESCALADO Y RESPONSIVE
// ==========================================

function ajustarEscalaWrapperCalendario() {
    const calWrapper = document.getElementById('flyer-wrapper');
    const calLienzoArte = document.getElementById('lienzo-arte');
    if(!calWrapper || !calLienzoArte) return;
    const currentWidth = calWrapper.clientWidth;
    if(currentWidth === 0) return;

    const fSelect = document.getElementById('calFormatoArte');
    const formato = fSelect ? fSelect.value : 'horizontal';

    const baseWidth = formato === 'horizontal' ? 1920 : 1080;
    const baseHeight = formato === 'horizontal' ? 1080 : 1920;

    calLienzoArte.style.width = baseWidth + 'px';
    calLienzoArte.style.height = baseHeight + 'px';

    const ratio = baseHeight / baseWidth;
    calWrapper.style.height = (currentWidth * ratio) + 'px';

    const scale = currentWidth / baseWidth;
    calLienzoArte.style.transform = `scale(${scale})`;

    if(typeof renderizarFondoCanvas === 'function') {
        renderizarFondoCanvas();
    }
}

window.addEventListener('resize', ajustarEscalaWrapperCalendario);

// Esperar a que el DOM esté completamente cargado
document.addEventListener('DOMContentLoaded', function() {
    const modalCal = document.getElementById('calendarioModal');
    if(modalCal) {
        modalCal.addEventListener('shown.bs.modal', function () {
            ajustarEscalaWrapperCalendario();
            if(typeof cargarEventosCalendario === 'function') cargarEventosCalendario();
            if(typeof actualizarOpacidadOverlay === 'function') actualizarOpacidadOverlay();
            if(typeof cargarTextosLocales === 'function') cargarTextosLocales();
            if(typeof actualizarTamanoTarjetas === 'function') actualizarTamanoTarjetas();
        });
    }
});

function cambiarFormatoArte() {
    ajustarEscalaWrapperCalendario();
    if(typeof renderizarCalendario === 'function') renderizarCalendario();
    if(typeof actualizarTamanoTarjetas === 'function') actualizarTamanoTarjetas();
}
