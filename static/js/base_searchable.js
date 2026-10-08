// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
(function() {
    var PICKER_PAGE_SIZE = 10;
    var pickerCount = 0;

    // Búsqueda insensible a tildes: "astua" encuentra "Astúa"
    function norm(s) {
        return (s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
    }

    function armarModalPicker(select) {
        if (select.dataset.dropdownInit === '1') return;
        select.dataset.dropdownInit = '1';
        select.style.display = 'none';
        var wrapper = document.createElement('div');
        wrapper.className = 'custom-search-dropdown';
        select.parentNode.insertBefore(wrapper, select);
        wrapper.appendChild(select);
        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btn btn-outline-secondary w-100 text-start text-truncate';
        var allOpts = Array.from(select.options);
        var placeholder = allOpts.find(function(o) { return o.value === ''; });
        var defaultText = placeholder ? placeholder.textContent : 'Seleccionar...';
        btn.textContent = defaultText;
        var options = allOpts.filter(function(o) { return o.value !== ''; });
        wrapper.appendChild(btn);

        var modalId = 'pickerModal' + (++pickerCount);
        var modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = modalId;
        modal.tabIndex = -1;
        modal.setAttribute('aria-hidden', 'true');
        modal.innerHTML =
            '<div class="modal-dialog modal-dialog-centered modal-dialog-scrollable">' +
              '<div class="modal-content border-0 shadow-lg rounded-4">' +
                '<div class="modal-header border-0 pb-0">' +
                  '<h5 class="modal-title fw-bold"><i class="bi bi-people me-2"></i>' + defaultText + '</h5>' +
                  '<button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button>' +
                '</div>' +
                '<div class="modal-body px-3 pt-3">' +
                  '<input type="search" class="form-control mb-3" placeholder="Buscar por nombre o cédula..." autocomplete="off">' +
                  '<div class="list-group picker-list mb-2"></div>' +
                  '<p class="small text-muted text-center d-none mb-2 picker-empty">Sin resultados.</p>' +
                '</div>' +
                '<div class="modal-footer border-0 justify-content-between pt-0 pb-3 px-3">' +
                  '<span class="small text-muted picker-info"></span>' +
                  '<div>' +
                    '<button type="button" class="btn btn-outline-secondary btn-sm rounded-pill picker-prev"><i class="bi bi-chevron-left"></i></button> ' +
                    '<button type="button" class="btn btn-outline-secondary btn-sm rounded-pill picker-next"><i class="bi bi-chevron-right"></i></button>' +
                  '</div>' +
                '</div>' +
              '</div>' +
            '</div>';
        document.body.appendChild(modal);

        var input = modal.querySelector('input[type="search"]');
        var list = modal.querySelector('.picker-list');
        var empty = modal.querySelector('.picker-empty');
        var info = modal.querySelector('.picker-info');
        var prev = modal.querySelector('.picker-prev');
        var next = modal.querySelector('.picker-next');
        var page = 0;
        var filtered = options;

        function render() {
            var pages = Math.max(1, Math.ceil(filtered.length / PICKER_PAGE_SIZE));
            if (page >= pages) page = pages - 1;
            var slice = filtered.slice(page * PICKER_PAGE_SIZE, (page + 1) * PICKER_PAGE_SIZE);
            list.innerHTML = '';
            slice.forEach(function(opt) {
                var item = document.createElement('button');
                item.type = 'button';
                item.className = 'list-group-item list-group-item-action py-2';
                item.textContent = opt.textContent;
                item.addEventListener('click', function() {
                    select.value = opt.value;
                    options.forEach(function(o) { o.selected = (o.value === opt.value); });
                    select.dispatchEvent(new Event('change', { bubbles: true }));
                    btn.textContent = opt.textContent;
                    window.bootstrap.Modal.getOrCreateInstance(modal).hide();
                });
                list.appendChild(item);
            });
            empty.classList.toggle('d-none', filtered.length > 0);
            info.textContent = filtered.length ? ('Página ' + (page + 1) + ' de ' + pages + ' · ' + filtered.length + ' usuarios') : '';
            prev.disabled = page <= 0;
            next.disabled = page >= pages - 1;
        }

        input.addEventListener('input', function() {
            var terms = norm(input.value).trim().split(/\s+/).filter(Boolean);
            filtered = options.filter(function(o) {
                var text = norm(o.getAttribute('data-search') || o.textContent);
                return terms.every(function(t) { return text.indexOf(t) !== -1; });
            });
            page = 0;
            render();
        });
        prev.addEventListener('click', function() { page--; render(); });
        next.addEventListener('click', function() { page++; render(); });
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            input.value = '';
            filtered = options;
            page = 0;
            render();
            window.bootstrap.Modal.getOrCreateInstance(modal).show();
        });
        modal.addEventListener('shown.bs.modal', function() { input.focus(); });
    }

    function armarDropdownBusqueda() {
        document.querySelectorAll('select[data-searchable]').forEach(function(select) {
            if (select.hasAttribute('data-modal-picker')) { armarModalPicker(select); return; }
            if (select.dataset.dropdownInit === '1') return;
            select.dataset.dropdownInit = '1';
            select.style.display = 'none';
            var wrapper = document.createElement('div');
            wrapper.className = 'custom-search-dropdown';
            select.parentNode.insertBefore(wrapper, select);
            wrapper.appendChild(select);
            var btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'btn btn-outline-secondary w-100 text-start';
            var menu = document.createElement('div');
            menu.className = 'custom-search-dropdown-menu';
            var input = document.createElement('input');
            input.type = 'search';
            input.className = 'form-control form-control-sm';
            input.placeholder = 'Escribí para buscar por nombre, cédula, pasaporte, sangre, contacto...';
            input.setAttribute('autocomplete', 'off');
            var list = document.createElement('div');
            list.className = 'dropdown-list';
            var allOpts = Array.from(select.options);
            var placeholder = allOpts.find(function(o) { return o.value === ''; });
            var defaultText = placeholder ? placeholder.textContent : 'Seleccionar...';
            btn.textContent = defaultText;
            var options = allOpts.filter(function(o) { return o.value !== ''; });
            options.forEach(function(opt) {
                var item = document.createElement('button');
                item.type = 'button';
                item.className = 'dropdown-item small';
                item.textContent = opt.textContent;
                item.setAttribute('data-value', opt.value);
                item.setAttribute('data-search', norm(opt.getAttribute('data-search') || opt.textContent));
                item.addEventListener('click', function() {
                    select.value = opt.value;
                    options.forEach(function(o) { o.selected = (o.value === opt.value); });
                    btn.textContent = opt.textContent;
                    menu.style.display = 'none';
                });
                list.appendChild(item);
            });
            input.addEventListener('input', function() {
                var q = norm(input.value).trim();
                var terms = q.split(/\s+/).filter(Boolean);
                list.querySelectorAll('.dropdown-item').forEach(function(item) {
                    var text = item.getAttribute('data-search');
                    var match = terms.every(function(t) { return text.indexOf(t) !== -1; });
                    item.classList.toggle('d-none', !match);
                });
            });
            input.addEventListener('keydown', function(e) { e.stopPropagation(); });
            menu.addEventListener('click', function(e) { e.stopPropagation(); });
            menu.appendChild(input);
            menu.appendChild(list);
            wrapper.appendChild(btn);
            wrapper.appendChild(menu);
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                var abierto = menu.style.display === 'block';
                document.querySelectorAll('.custom-search-dropdown-menu').forEach(function(m) { m.style.display = 'none'; });
                if (!abierto) {
                    menu.style.display = 'block';
                    input.value = '';
                    list.querySelectorAll('.dropdown-item').forEach(function(item) { item.classList.remove('d-none'); });
                    input.focus();
                }
            });
            document.addEventListener('click', function() { menu.style.display = 'none'; });
        });
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', armarDropdownBusqueda);
    } else {
        armarDropdownBusqueda();
    }
})();
