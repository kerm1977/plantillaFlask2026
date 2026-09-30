// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
(function() {
    const KEY = 'rifas_analisis_collapse';
    const btn = document.getElementById('btnToggleAnalisis');
    const body = document.getElementById('rifasAnalisisBody');
    const icon = document.getElementById('iconToggleAnalisis');
    if (!btn || !body || !icon) return;

    function applyState(collapsed) {
        if (collapsed) {
            body.classList.remove('show');
            btn.setAttribute('aria-expanded', 'false');
            icon.classList.remove('bi-chevron-up');
            icon.classList.add('bi-chevron-down');
        } else {
            body.classList.add('show');
            btn.setAttribute('aria-expanded', 'true');
            icon.classList.remove('bi-chevron-down');
            icon.classList.add('bi-chevron-up');
        }
    }

    const saved = sessionStorage.getItem(KEY);
    let collapsed = false;
    if (saved !== null) {
        collapsed = saved === '1';
    } else {
        sessionStorage.setItem(KEY, '0');
    }
    applyState(collapsed);

    btn.addEventListener('click', function() {
        const nowCollapsed = body.classList.contains('show');
        applyState(nowCollapsed);
        sessionStorage.setItem(KEY, nowCollapsed ? '1' : '0');
    });
})();
