// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
// Filtro de búsqueda del modal "Estado de cuenta de todas las
// personas" (programa de fidelidad, Mis puntos).
(function() {
    function armarEstadoGlobal() {
        var input = document.getElementById('egBuscar');
        var lista = document.getElementById('egLista');
        if (!input || !lista) return;
        var vacio = document.getElementById('egVacio');
        input.addEventListener('input', function() {
            var terms = input.value.toLowerCase().trim().split(/\s+/).filter(Boolean);
            var visibles = 0;
            lista.querySelectorAll('.eg-item').forEach(function(item) {
                var show = terms.every(function(t) {
                    return (item.getAttribute('data-search') || '').indexOf(t) !== -1;
                });
                item.classList.toggle('d-none', !show);
                if (show) visibles++;
            });
            if (vacio) vacio.classList.toggle('d-none', visibles > 0);
        });
        var modal = document.getElementById('modalEstadoGlobal');
        if (modal) {
            modal.addEventListener('shown.bs.modal', function() { input.focus(); });
        }
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', armarEstadoGlobal);
    } else {
        armarEstadoGlobal();
    }
})();
