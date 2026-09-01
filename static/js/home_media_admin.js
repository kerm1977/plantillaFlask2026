// static/js/home_media_admin.js
(function () {
  let items = [];
  let editingId = null;

  const modalEl = document.getElementById('homeMediaAdminModal');
  const listContainer = document.getElementById('homeMediaList');
  const form = document.getElementById('homeMediaForm');
  const typeSelect = document.getElementById('hmType');
  const urlGroup = document.getElementById('hmUrlGroup');
  const fileGroup = document.getElementById('hmFileGroup');
  const previewContainer = document.getElementById('hmPreview');

  function toggleFields() {
    const type = typeSelect.value;
    if (type === 'image') {
      urlGroup.classList.add('d-none');
      fileGroup.classList.remove('d-none');
      document.getElementById('hmUrl').removeAttribute('required');
    } else {
      urlGroup.classList.remove('d-none');
      fileGroup.classList.add('d-none');
      document.getElementById('hmUrl').setAttribute('required', 'required');
    }
  }

  if (typeSelect) {
    typeSelect.addEventListener('change', toggleFields);
  }

  async function loadItems() {
    if (!listContainer) return;
    listContainer.innerHTML = '<div class="text-center py-3"><span class="spinner-border spinner-border-sm text-orange"></span></div>';
    try {
      const res = await fetch('/api/home-media/all');
      if (!res.ok) throw new Error('No autorizado');
      items = await res.json();
      renderItems();
    } catch (e) {
      listContainer.innerHTML = `<div class="alert alert-danger">${e.message}</div>`;
    }
  }

  function typeLabel(type) {
    const map = { image: 'Imagen', youtube: 'YouTube', facebook: 'Facebook', link: 'Enlace' };
    return map[type] || type;
  }

  function renderItems() {
    if (!items.length) {
      listContainer.innerHTML = '<p class="text-muted text-center py-3">No hay elementos en el carrusel.</p>';
      return;
    }
    let html = '<div class="list-group list-group-flush rounded-4">';
    items.forEach((item, idx) => {
      const thumb = item.type === 'image'
        ? `<img src="/static/uploads/home_media/${item.filename}" class="rounded-3" style="width:64px;height:48px;object-fit:cover;">`
        : `<span class="badge bg-secondary">${typeLabel(item.type)}</span>`;
      html += `
        <div class="list-group-item d-flex align-items-center gap-3 py-2 px-2 bg-white bg-opacity-50">
          <div>${thumb}</div>
          <div class="flex-grow-1 minw-0">
            <div class="fw-bold text-truncate">${item.title || '(sin título)'}</div>
            <small class="text-muted">${typeLabel(item.type)} · Orden ${item.sort_order}</small>
          </div>
          <div class="d-flex gap-1 flex-wrap align-items-center">
            <button class="btn btn-sm btn-outline-secondary border-0" onclick="moveHomeMedia(${item.id}, -1)" title="Subir" ${idx === 0 ? 'disabled' : ''}><i class="bi bi-arrow-up"></i></button>
            <button class="btn btn-sm btn-outline-secondary border-0" onclick="moveHomeMedia(${item.id}, 1)" title="Bajar" ${idx === items.length - 1 ? 'disabled' : ''}><i class="bi bi-arrow-down"></i></button>
            <button class="btn btn-sm ${item.is_active ? 'btn-success' : 'btn-outline-secondary'}" onclick="toggleHomeMedia(${item.id})" title="Activo/Inactivo">
              <i class="bi ${item.is_active ? 'bi-eye' : 'bi-eye-slash'}"></i>
            </button>
            <button class="btn btn-sm btn-outline-primary border-0" onclick="editHomeMedia(${item.id})" title="Editar"><i class="bi bi-pencil"></i></button>
            <button class="btn btn-sm btn-outline-danger border-0" onclick="deleteHomeMedia(${item.id})" title="Eliminar"><i class="bi bi-trash"></i></button>
          </div>
        </div>`;
    });
    html += '</div>';
    listContainer.innerHTML = html;
  }

  window.moveHomeMedia = async function (id, dir) {
    const idx = items.findIndex(i => i.id === id);
    if (idx < 0) return;
    const otherIdx = idx + dir;
    if (otherIdx < 0 || otherIdx >= items.length) return;
    const a = items[idx];
    const b = items[otherIdx];
    const temp = a.sort_order;
    a.sort_order = b.sort_order;
    b.sort_order = temp;
    try {
      await fetch(`/api/home-media/${a.id}`, { method: 'PUT', body: new URLSearchParams({ sort_order: a.sort_order }) });
      await fetch(`/api/home-media/${b.id}`, { method: 'PUT', body: new URLSearchParams({ sort_order: b.sort_order }) });
      loadItems();
    } catch (e) {
      alert('Error reordenando');
    }
  };

  window.toggleHomeMedia = async function (id) {
    const item = items.find(i => i.id === id);
    if (!item) return;
    const formData = new FormData();
    formData.append('is_active', (!item.is_active).toString());
    formData.append('type', item.type);
    formData.append('sort_order', item.sort_order);
    try {
      const res = await fetch(`/api/home-media/${id}`, { method: 'PUT', body: formData });
      if (!res.ok) throw new Error('Error');
      loadItems();
    } catch (e) {
      alert('Error cambiando estado');
    }
  };

  window.editHomeMedia = function (id) {
    const item = items.find(i => i.id === id);
    if (!item) return;
    editingId = id;
    document.getElementById('hmTitle').value = item.title || '';
    document.getElementById('hmUrl').value = item.url || '';
    document.getElementById('hmOrder').value = item.sort_order;
    document.getElementById('hmActive').checked = item.is_active;
    typeSelect.value = item.type;
    toggleFields();
    previewContainer.innerHTML = '';
    if (item.type === 'image' && item.filename) {
      previewContainer.innerHTML = `<img src="/static/uploads/home_media/${item.filename}" class="rounded-3 shadow-sm" style="max-width:200px;max-height:120px;object-fit:cover;">`;
    }
    document.getElementById('homeMediaFormTitle').textContent = 'Editar elemento';
    const btn = document.getElementById('homeMediaSaveBtn');
    if (btn) btn.textContent = 'Actualizar';
  };

  window.deleteHomeMedia = async function (id) {
    if (!confirm('¿Eliminar este elemento del carrusel?')) return;
    try {
      const res = await fetch(`/api/home-media/${id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Error');
      loadItems();
    } catch (e) {
      alert('Error eliminando');
    }
  };

  function resetForm() {
    editingId = null;
    form.reset();
    typeSelect.value = 'image';
    toggleFields();
    previewContainer.innerHTML = '';
    document.getElementById('homeMediaFormTitle').textContent = 'Nuevo elemento';
    const btn = document.getElementById('homeMediaSaveBtn');
    if (btn) btn.textContent = 'Agregar';
  }

  if (form) {
    form.addEventListener('submit', async function (e) {
      e.preventDefault();
      const formData = new FormData(form);
      if (!formData.has('is_active')) {
        formData.append('is_active', 'false');
      }
      if (editingId) {
        formData.append('type', typeSelect.value);
        try {
          const res = await fetch(`/api/home-media/${editingId}`, { method: 'PUT', body: formData });
          const data = await res.json();
          if (!res.ok) throw new Error(data.error || 'Error');
          resetForm();
          loadItems();
        } catch (err) {
          alert(err.message);
        }
      } else {
        try {
          const res = await fetch('/api/home-media', { method: 'POST', body: formData });
          const data = await res.json();
          if (!res.ok) throw new Error(data.error || 'Error');
          resetForm();
          loadItems();
        } catch (err) {
          alert(err.message);
        }
      }
    });
  }

  const btnNew = document.getElementById('homeMediaNewBtn');
  if (btnNew) {
    btnNew.addEventListener('click', resetForm);
  }

  if (modalEl) {
    modalEl.addEventListener('shown.bs.modal', loadItems);
  }

  toggleFields();
})();
