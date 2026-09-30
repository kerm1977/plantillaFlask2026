// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
let modalInstance = null;
let nuevoModalInstance = null;

function mostrarMensaje(texto, ok) {
    const el = document.getElementById('mensaje');
    el.textContent = texto;
    el.className = 'alert ' + (ok ? 'alert-success' : 'alert-danger');
    el.classList.remove('d-none');
    setTimeout(() => el.classList.add('d-none'), 3000);
}

function renderIcono(val) {
    if (!val) return '';
    val = String(val).trim();
    if (val.startsWith('bi-') || val.startsWith('bi ')) {
        return '<i class="' + val + '"></i>';
    }
    return '<span>' + val + '</span>';
}

function mostrarVista(vista) {
    const text = document.getElementById('triggers-text');
    const cards = document.getElementById('triggers-view');
    const music = document.getElementById('music-view');
    if (vista === 'music') {
        text.classList.add('d-none');
        cards.classList.add('d-none');
        music.classList.remove('d-none');
    } else {
        text.classList.remove('d-none');
        cards.classList.remove('d-none');
        music.classList.add('d-none');
    }
}

function abrirModal(id) {
    const h = HOLIDAYS.find(x => x.id === id);
    if (!h) return;
    document.getElementById('modal-id').value = h.id;
    document.getElementById('modal-custom').value = h.custom ? '1' : '';
    document.getElementById('modal-nombre').textContent = h.id;
    document.getElementById('modal-fecha').textContent = h.day
        ? ('0' + h.month).slice(-2) + '/' + ('0' + h.day).slice(-2)
        : (h.nth_weekday ? h.nth_weekday[0] + 'º domingo de ' + h.month : '');
    document.getElementById('modal-titulo').value = h.title || '';
    document.getElementById('modal-subtitulo').value = h.subtitle || '';
    const icono = h.icon || h.emoji || '🎉';
    document.getElementById('modal-icono').value = icono;
    document.getElementById('modal-preview').innerHTML = renderIcono(icono);
    document.getElementById('modal-activo').checked = h.enabled;
    document.getElementById('modal-autoplay').checked = h.autoplay;
    document.getElementById('modal-confeti').checked = h.show_confetti !== false;
    document.getElementById('modal-mensaje').value = h.custom_message || '';
    document.getElementById('modal-reproductor').checked = h.show_player !== false;
    document.getElementById('modal-superuser').checked = h.superuser_only === true;
    document.getElementById('modal-link-activo').checked = h.link_enabled === true;
    document.getElementById('modal-link').value = h.link_url || '';

    const fechaGrupo = document.getElementById('modal-fecha-grupo');
    if (h.custom) {
        fechaGrupo.classList.remove('d-none');
        document.getElementById('modal-mes').value = h.month;
        document.getElementById('modal-dia').value = h.day;
        document.getElementById('modal-fin-mes').value = h.end_month || '';
        document.getElementById('modal-fin-dia').value = h.end_day || '';
    } else {
        fechaGrupo.classList.add('d-none');
    }

    const select = document.getElementById('modal-cancion');
    select.value = h.song || '';
    if (h.song && !select.querySelector('option[value="' + h.song.replace(/"/g, '\\"') + '"]')) {
        const opt = document.createElement('option');
        opt.value = h.song;
        opt.textContent = h.song;
        select.appendChild(opt);
        select.value = h.song;
    }
    document.getElementById('modal-cancion-file').value = '';
    modalInstance = new bootstrap.Modal(document.getElementById('holidayModal'));
    modalInstance.show();
}

function abrirModalNuevo() {
    document.getElementById('nuevo-titulo').value = '';
    document.getElementById('nuevo-subtitulo').value = '';
    document.getElementById('nuevo-icono').value = '🎉';
    document.getElementById('nuevo-mes').value = new Date().getMonth() + 1;
    document.getElementById('nuevo-dia').value = new Date().getDate();
    document.getElementById('nuevo-fin-mes').value = '';
    document.getElementById('nuevo-fin-dia').value = '';
    document.getElementById('nuevo-activo').checked = true;
    document.getElementById('nuevo-autoplay').checked = false;
    document.getElementById('nuevo-confeti').checked = true;
    document.getElementById('nuevo-mensaje').value = '';
    document.getElementById('nuevo-reproductor').checked = true;
    document.getElementById('nuevo-superuser').checked = false;
    document.getElementById('nuevo-link-activo').checked = false;
    document.getElementById('nuevo-link').value = '';
    document.getElementById('nuevo-cancion').value = '';
    document.getElementById('nuevo-cancion-file').value = '';
    nuevoModalInstance = new bootstrap.Modal(document.getElementById('newHolidayModal'));
    nuevoModalInstance.show();
}

function armarFormData(idPrefix) {
    const formData = new FormData();
    formData.append('title', document.getElementById(idPrefix + 'titulo').value);
    formData.append('subtitle', document.getElementById(idPrefix + 'subtitulo').value);
    formData.append('icon', document.getElementById(idPrefix + 'icono').value);
    formData.append('enabled', document.getElementById(idPrefix + 'activo').checked ? 'true' : 'false');
    formData.append('autoplay', document.getElementById(idPrefix + 'autoplay').checked ? 'true' : 'false');
    formData.append('show_confetti', document.getElementById(idPrefix + 'confeti').checked ? 'true' : 'false');
    formData.append('custom_message', document.getElementById(idPrefix + 'mensaje').value);
    formData.append('show_player', document.getElementById(idPrefix + 'reproductor').checked ? 'true' : 'false');
    formData.append('superuser_only', document.getElementById(idPrefix + 'superuser').checked ? 'true' : 'false');
    formData.append('link_enabled', document.getElementById(idPrefix + 'link-activo').checked ? 'true' : 'false');
    formData.append('link_url', document.getElementById(idPrefix + 'link').value);
    formData.append('song', document.getElementById(idPrefix + 'cancion').value);
    const fileInput = document.getElementById(idPrefix + 'cancion-file');
    if (fileInput.files[0]) formData.append('song_file', fileInput.files[0]);
    return formData;
}


document.getElementById('modal-icono').addEventListener('input', function() {
    document.getElementById('modal-preview').innerHTML = renderIcono(this.value);
});
document.getElementById('modal-icono-preset').addEventListener('change', function() {
    document.getElementById('modal-icono').value = this.value;
    document.getElementById('modal-preview').innerHTML = renderIcono(this.value);
    this.value = '';
});
document.getElementById('nuevo-icono-preset').addEventListener('change', function() {
    document.getElementById('nuevo-icono').value = this.value;
    this.value = '';
});
