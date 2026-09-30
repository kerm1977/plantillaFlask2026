// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
(function() {
    function armarDropdownBusqueda() {
        document.querySelectorAll('select[data-searchable]').forEach(function(select) {
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
                item.setAttribute('data-search', (opt.getAttribute('data-search') || opt.textContent).toLowerCase());
                item.addEventListener('click', function() {
                    select.value = opt.value;
                    options.forEach(function(o) { o.selected = (o.value === opt.value); });
                    btn.textContent = opt.textContent;
                    menu.style.display = 'none';
                });
                list.appendChild(item);
            });
            input.addEventListener('input', function() {
                var q = input.value.toLowerCase().trim();
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
