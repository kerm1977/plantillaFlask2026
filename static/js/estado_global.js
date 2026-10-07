// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
// Filtro de búsqueda de la tabla "Estado de cuenta de todas las
// personas" (programa de fidelidad, Mis puntos). Oculta la fila de
// cada persona y sus filas de detalle de caminatas.
(function() {
    function armarEstadoGlobal() {
        var input = document.getElementById('egBuscar');
        var tabla = document.getElementById('egTabla');
        if (!input || !tabla) return;
        var vacio = document.getElementById('egVacio');
        input.addEventListener('input', function() {
            var terms = input.value.toLowerCase().trim().split(/\s+/).filter(Boolean);
            var visibles = 0;
            tabla.querySelectorAll('.eg-fila').forEach(function(fila) {
                var show = terms.every(function(t) {
                    return (fila.getAttribute('data-search') || '').indexOf(t) !== -1;
                });
                fila.classList.toggle('d-none', !show);
                tabla.querySelectorAll('.eg-detalle[data-owner="' + fila.dataset.owner + '"]').forEach(function(det) {
                    det.classList.toggle('d-none', !show);
                });
                if (show) visibles++;
            });
            if (vacio) vacio.classList.toggle('d-none', visibles > 0);
        });
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', armarEstadoGlobal);
    } else {
        armarEstadoGlobal();
    }
})();
