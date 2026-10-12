// ==============================================================
//   PÁGINA CREAR USUARIO — hoja única (sin modal)
//   Editor de avatar + envío a /api/admin/create_user
//   Misma lógica que tenía el formulario dentro del dashboard.
// ==============================================================
document.addEventListener("DOMContentLoaded", () => {

    // ---- Editor visual de avatar (zoom + posición) ----
    const cuAvatarUpload     = document.getElementById('cuAvatarUpload');
    const cuAvatarPreviewImg = document.getElementById('cuAvatarPreviewImg');
    const cuScaleSlider      = document.getElementById('cuScaleSlider');
    const cuPosXSlider       = document.getElementById('cuPosXSlider');
    const cuPosYSlider       = document.getElementById('cuPosYSlider');

    function resetCuAvatar() {
        if (cuAvatarPreviewImg) {
            cuAvatarPreviewImg.src = '/static/default.png';
            cuAvatarPreviewImg.style.transform = '';
        }
        if (cuScaleSlider) cuScaleSlider.value = 1;
        if (cuPosXSlider)  cuPosXSlider.value = 0;
        if (cuPosYSlider)  cuPosYSlider.value = 0;
    }

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

    // Bloqueo de campos hasta ingresar cédula (solo aplica a no-superusuarios)
    toggleCedulaLock('crearUsuarioForm', 'cuCedula');

    const crearUsuarioForm = document.getElementById('crearUsuarioForm');
    if (!crearUsuarioForm) return;

    // Quitar borde rojo de advertencia mientras el usuario completa un campo
    crearUsuarioForm.addEventListener('input', function(e) { if (e.target.classList) e.target.classList.remove('is-danger'); });
    crearUsuarioForm.addEventListener('change', function(e) { if (e.target.classList) e.target.classList.remove('is-danger'); });

    // Limpia los campos dinámicos y contactos extra tras crear (queda lista para el siguiente)
    function limpiarFormulario() {
        crearUsuarioForm.reset();
        resetCuAvatar();
        const dynSelect = document.getElementById('cuDynamicSelect');
        const dynContainer = document.getElementById('cuDynamicContainer');
        if (dynSelect) dynSelect.value = '';
        if (dynContainer) dynContainer.innerHTML = '';
        const emg = document.getElementById('cuEmergencyContainer');
        if (emg) {
            const rows = emg.querySelectorAll('.cu-emergency-row');
            rows.forEach(function(row, i) { if (i > 0) row.remove(); });
        }
    }

    // ---- Envío del formulario ----
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
                limpiarFormulario();
                if (d.card) {
                    mostrarCardUsuario(d);
                } else {
                    mostrarAlerta('Usuario creado correctamente.', 'success');
                }
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
});
