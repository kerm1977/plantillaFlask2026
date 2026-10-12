// ==============================================================
//   PÁGINA EDITAR USUARIO — hoja única (sin modal)
//   Editor de avatar + envío a /api/admin/update_user/<id>
//   Misma lógica que tenía el formulario dentro del dashboard.
// ==============================================================

// Selector de "Información Adicional": si el campo ya existe en la hoja
// (precargado o el teléfono directo), se enfoca en vez de duplicarlo.
function handleEditDynamicSelectPage() {
    const select = document.getElementById('editDynamicSelect');
    const form = document.getElementById('adminEditUserForm');
    if (!select || !form) return;
    const map = {
        'Telefono': 'phone', 'Whatsapp': 'phone',
        'Facebook': 'facebook', 'Instagram': 'instagram', 'Direccion': 'address',
        'Institucion': 'institution', 'Otro': 'other_info'
    };
    const name = map[select.value];
    if (name) {
        const existing = form.querySelector('input[name="' + name + '"], textarea[name="' + name + '"]');
        if (existing) {
            existing.focus();
            select.value = '';
            mostrarAlerta('Ese campo ya está en la hoja, edítelo directamente.', 'warning');
            return;
        }
    }
    handleEditDynamicSelect();
}

document.addEventListener("DOMContentLoaded", () => {

    // ---- Editor visual de avatar (zoom + posición) ----
    const editAvatarUpload     = document.getElementById('editAvatarUpload');
    const editAvatarPreviewImg = document.getElementById('editAvatarPreviewImg');
    const editScaleSlider      = document.getElementById('editScaleSlider');
    const editPosXSlider       = document.getElementById('editPosXSlider');
    const editPosYSlider       = document.getElementById('editPosYSlider');
    if (editScaleSlider && editPosXSlider && editPosYSlider && editAvatarPreviewImg) {
        function updateEditImageTransform() {
            editAvatarPreviewImg.style.transform =
                `scale(${editScaleSlider.value}) translate(${editPosXSlider.value}px, ${editPosYSlider.value}px)`;
        }
        editScaleSlider.addEventListener('input', updateEditImageTransform);
        editPosXSlider.addEventListener('input', updateEditImageTransform);
        editPosYSlider.addEventListener('input', updateEditImageTransform);
        if (editAvatarUpload) {
            editAvatarUpload.addEventListener('change', function(e) {
                if (e.target.files && e.target.files[0]) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        editAvatarPreviewImg.src = e.target.result;
                        editScaleSlider.value = 1; editPosXSlider.value = 0; editPosYSlider.value = 0;
                        updateEditImageTransform();
                    }
                    reader.readAsDataURL(e.target.files[0]);
                }
            });
        }
    }

    // Bloqueo de campos hasta ingresar cédula (solo aplica a no-superusuarios)
    toggleCedulaLock('adminEditUserForm', 'editCedula');

    const form = document.getElementById('adminEditUserForm');
    if (!form) return;

    // Quitar borde rojo de advertencia mientras el usuario completa un campo
    form.addEventListener('input', function(e) { if (e.target.classList) e.target.classList.remove('is-danger'); });
    form.addEventListener('change', function(e) { if (e.target.classList) e.target.classList.remove('is-danger'); });

    // ---- Envío del formulario ----
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        const dia = document.getElementById('editDia').value;
        const mes = document.getElementById('editMes').value;
        const anio = document.getElementById('editAnio').value;
        const fechaHidden = document.getElementById('editFechaNacHidden');
        const dobHidden = document.getElementById('editDobHidden');
        if (dia && mes && anio) {
            const fecha = `${anio}-${mes}-${dia}`;
            fechaHidden.value = fecha;
            dobHidden.value = fecha;
        } else {
            fechaHidden.value = '';
            dobHidden.value = '';
        }
        const btn = document.getElementById('btnGuardarUsuario');
        const originalHTML = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Guardando...';

        const formData = new FormData(this);
        const userId = this.dataset.userId;
        try {
            const response = await fetch(`/api/admin/update_user/${userId}`, { method: 'POST', body: formData });
            const result = await response.json();
            if (response.ok && result.success) {
                mostrarAlerta('Los datos del usuario han sido actualizados correctamente.', 'success');
                setTimeout(() => { window.location.href = '/dashboard'; }, 1500);
            } else {
                mostrarAlerta('Error al actualizar: ' + (result.error || 'Desconocido'), 'error');
                btn.disabled = false;
                btn.innerHTML = originalHTML;
            }
        } catch (err) {
            mostrarAlerta('Error de conexión al guardar los datos.', 'error');
            btn.disabled = false;
            btn.innerHTML = originalHTML;
        }
    });
});
