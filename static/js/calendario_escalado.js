// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
// ==========================================
// ESCALADO Y RESPONSIVE
// ==========================================

function ajustarEscalaWrapperCalendario() {
    const calWrapper = document.getElementById('flyer-wrapper');
    const calLienzoArte = document.getElementById('lienzo-arte');
    const holder = document.getElementById('cal-flyer-holder');
    if(!calWrapper || !calLienzoArte) return;

    const fSelect = document.getElementById('calFormatoArte');
    const formato = fSelect ? fSelect.value : 'horizontal';

    const baseWidth = formato === 'horizontal' ? 1920 : 1080;
    const baseHeight = formato === 'horizontal' ? 1080 : 1920;

    calLienzoArte.style.width = baseWidth + 'px';
    calLienzoArte.style.height = baseHeight + 'px';

    // El flyer cabe COMPLETO en la mitad inferior: escala por ancho Y alto
    const box = holder || calWrapper.parentElement;
    const availW = box ? box.clientWidth : calWrapper.clientWidth;
    const availH = box ? box.clientHeight : 0;
    if(availW === 0) return;

    const scale = availH > 0
        ? Math.min(availW / baseWidth, availH / baseHeight)
        : (availW / baseWidth);

    calWrapper.style.width = Math.round(baseWidth * scale) + 'px';
    calWrapper.style.height = Math.round(baseHeight * scale) + 'px';
    calWrapper.style.margin = '0 auto';
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
