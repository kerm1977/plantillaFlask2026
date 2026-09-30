// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
document.addEventListener("DOMContentLoaded", () => {
    loadAllUsers();
    document.getElementById('searchUserInput').addEventListener('input', function() {
        const term = this.value.toLowerCase();
        filteredContacts = term
            ? allContacts.filter(u =>
                u.display_name.toLowerCase().includes(term) ||
                (u.email      && u.email.toLowerCase().includes(term)) ||
                (u.crm_cedula && u.crm_cedula.toLowerCase().includes(term)) ||
                (u.phone      && u.phone.includes(term)))
            : [...allContacts];
        renderContactsPage(1);
    });
    const editAvatarUpload    = document.getElementById('editAvatarUpload');
    const editAvatarPreviewImg= document.getElementById('editAvatarPreviewImg');
    const editScaleSlider     = document.getElementById('editScaleSlider');
    const editPosXSlider      = document.getElementById('editPosXSlider');
    const editPosYSlider      = document.getElementById('editPosYSlider');
    if (editScaleSlider && editPosXSlider && editPosYSlider) {
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

    // Avatar preview para Crear Usuario
    const cuAvatarUpload     = document.getElementById('cuAvatarUpload');
    const cuAvatarPreviewImg = document.getElementById('cuAvatarPreviewImg');
    const cuScaleSlider      = document.getElementById('cuScaleSlider');
    const cuPosXSlider       = document.getElementById('cuPosXSlider');
    const cuPosYSlider       = document.getElementById('cuPosYSlider');
    if (cuScaleSlider && cuPosXSlider && cuPosYSlider && cuAvatarPreviewImg) {
        function updateCuImageTransform() {
            cuAvatarPreviewImg.style.transform =
                `scale(${cuScaleSlider.value}) translate(${cuPosXSlider.value}px, ${cuPosYSlider.value}px)`;
        }
        cuScaleSlider.addEventListener('input', updateCuImageTransform);
        cuPosXSlider.addEventListener('input', updateCuImageTransform);
        cuPosYSlider.addEventListener('input', updateCuImageTransform);
        if (cuAvatarUpload) {
            cuAvatarUpload.addEventListener('change', function(e) {
                if (e.target.files && e.target.files[0]) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        cuAvatarPreviewImg.src = e.target.result;
                        cuScaleSlider.value = 1; cuPosXSlider.value = 0; cuPosYSlider.value = 0;
                        updateCuImageTransform();
                    }
                    reader.readAsDataURL(e.target.files[0]);
                }
            });
        }
    }

    // Inicialmente bloquear todos los campos de Crear hasta ingresar cédula
    toggleCedulaLock('crearUsuarioForm', 'cuCedula');

    // Quitar borde rojo de advertencia mientras el usuario completa un campo
    ['crearUsuarioForm', 'adminEditUserForm'].forEach(function(fid) {
        const f = document.getElementById(fid);
        if (!f) return;
        f.addEventListener('input', function(e) { if (e.target.classList) e.target.classList.remove('is-danger'); });
        f.addEventListener('change', function(e) { if (e.target.classList) e.target.classList.remove('is-danger'); });
    });

    document.getElementById('adminEditUserForm').addEventListener('submit', async function(e) {
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
        const formData = new FormData(this);
        try {
            const btnSubmit = this.querySelector('button[type="submit"]');
            const originalHTML = btnSubmit.innerHTML;
            btnSubmit.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Guardando...';
            btnSubmit.disabled = true;
            const response = await fetch(`/api/admin/update_user/${currentSelectedUserId}`, {method:'POST', body:formData});
            const result   = await response.json();
            if (response.ok && result.success) {
                bootstrap.Modal.getInstance(document.getElementById('adminEditUserModal'))?.hide();
                mostrarAlerta('Los datos del usuario han sido actualizados correctamente.', 'success');
                showUsersList(); loadAllUsers();
            } else { mostrarAlerta("Error al actualizar: " + (result.error || 'Desconocido'), 'error'); }
            btnSubmit.innerHTML = originalHTML; btnSubmit.disabled = false;
        } catch(err) { mostrarAlerta("Error de conexión al guardar los datos.", 'error'); }
    });

    // Crear nuevo usuario (Cuenta + Caminante) desde el Dashboard
    const crearUsuarioForm = document.getElementById('crearUsuarioForm');
    const cuAvatarPreviewImgGlobal = document.getElementById('cuAvatarPreviewImg');
    if (crearUsuarioForm) {
        crearUsuarioForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const dia = document.getElementById('cuDia').value;
            const mes = document.getElementById('cuMes').value;
            const anio = document.getElementById('cuAnio').value;
            const fechaHidden = document.getElementById('cuFechaNacHidden');
            const dobHidden = document.getElementById('cuDobHidden');
            if (dia && mes && anio) {
                const fecha = `${anio}-${mes}-${dia}`;
                fechaHidden.value = fecha;
                dobHidden.value = fecha;
            } else {
                fechaHidden.value = '';
                dobHidden.value = '';
            }
            const btn = document.getElementById('btnCrearUsuario');
            const originalHTML = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Creando...';

            const formData = new FormData(this);
            try {
                const r = await fetch('/api/admin/create_user', { method: 'POST', body: formData });
                const d = await r.json();

                if (r.ok && d.success) {
                    bootstrap.Modal.getInstance(document.getElementById('crearUsuarioModal')).hide();
                    crearUsuarioForm.reset();
                    if (cuAvatarPreviewImgGlobal) cuAvatarPreviewImgGlobal.src = '/static/default.png';
                    if (d.card) {
                        mostrarCardUsuario(d);
                    } else {
                        mostrarAlerta('Usuario creado correctamente.', 'success');
                    }
                    loadAllUsers();
                } else {
                    mostrarAlerta(d.error || 'Error al crear usuario', 'error');
                }
            } catch (err) {
                mostrarAlerta('Error de conexión. Intenta nuevamente.', 'error');
            } finally {
                btn.disabled = false;
                btn.innerHTML = originalHTML;
            }
        });
    }
});

