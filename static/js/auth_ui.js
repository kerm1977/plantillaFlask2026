// ✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️
// ✂️ INICIO DE CORTE: auth_ui.js ✂️
// ✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️

// ==========================================
// AUTENTICACIÓN Y EDITOR DE AVATAR
// ==========================================

function togglePasswordVisibility(inputId, iconElement) {
    const input = document.getElementById(inputId);
    if (input && input.type === 'password') {
        input.type = 'text';
        iconElement.classList.replace('bi-eye-slash', 'bi-eye');
        iconElement.style.color = 'var(--primary-orange, #ff8c00)';
    } else if(input) {
        input.type = 'password';
        iconElement.classList.replace('bi-eye', 'bi-eye-slash');
        iconElement.style.color = '#6c757d';
    }
}

const avatarUpload = document.getElementById('avatarUpload');
const avatarPreviewImg = document.getElementById('avatarPreviewImg');
const scaleSlider = document.getElementById('scaleSlider');
const posXSlider = document.getElementById('posXSlider');
const posYSlider = document.getElementById('posYSlider');

if(scaleSlider && posXSlider && posYSlider && avatarPreviewImg) {
    function updateImageTransform() {
        avatarPreviewImg.style.transform = `scale(${scaleSlider.value}) translate(${posXSlider.value}px, ${posYSlider.value}px)`;
    }
    scaleSlider.addEventListener('input', updateImageTransform);
    posXSlider.addEventListener('input', updateImageTransform);
    posYSlider.addEventListener('input', updateImageTransform);
    if(avatarUpload) {
        avatarUpload.addEventListener('change', function(e) {
            if (e.target.files && e.target.files[0]) {
                const reader = new FileReader();
                reader.onload = function(evt) {
                    avatarPreviewImg.src = evt.target.result;
                    scaleSlider.value = 1; posXSlider.value = 0; posYSlider.value = 0; updateImageTransform();
                }
                reader.readAsDataURL(e.target.files[0]);
            }
        });
    }
}

const showMessage = (containerId, text, type = 'danger') => {
    const container = document.getElementById(containerId);
    if(container) {
        container.innerHTML = `
            <div class="alert alert-${type} modal-alert alert-dismissible fade show" role="alert" style="background: rgba(${type === 'danger' ? '220,53,69' : '25,135,84'}, 0.2); color: ${type === 'danger' ? '#842029' : '#0f5132'};">
                ${text}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>`;
    }
};

document.getElementById('loginForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
        const response = await fetch('/api/login', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: document.getElementById('logEmail').value, password: document.getElementById('logPass').value })
        });
        const result = await response.json();
        if (response.ok) window.location.reload();
        else showMessage('loginMessage', result.error || 'Error al iniciar sesión');
    } catch (err) { showMessage('loginMessage', 'Error de conexión'); }
});

document.getElementById('registerForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const pass = document.getElementById('regPass').value;
    if (pass !== document.getElementById('regPassVerify').value) {
        showMessage('registerMessage', 'Las contraseñas no coinciden');
        return;
    }
    const userData = {
        name: document.getElementById('regName').value, last_name_1: document.getElementById('regLastName1').value,
        last_name_2: document.getElementById('regLastName2').value, email: document.getElementById('regEmail').value, password: pass
    };
    try {
        const response = await fetch('/api/register', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(userData) });
        const result = await response.json();
        if (response.ok) {
            showMessage('registerMessage', '¡Registro exitoso! Ya puedes iniciar sesión.', 'success');
            document.getElementById('registerForm').reset();
            if(avatarPreviewImg) { 
                avatarPreviewImg.src = cleanImage; 
                scaleSlider.value = 1; posXSlider.value = 0; posYSlider.value = 0; 
                updateImageTransform(); 
            }
        } else showMessage('registerMessage', result.error || 'Error al registrarse');
    } catch (err) { showMessage('registerMessage', 'Error de conexión'); }
});

async function submitForgotPassword() {
    const email = document.getElementById('forgotEmail')?.value?.trim();
    const msgEl = document.getElementById('forgotMsg');
    if (!email) { msgEl.innerHTML = '<div class="alert alert-warning py-2 small">Ingresa tu correo.</div>'; return; }
    msgEl.innerHTML = '<div class="text-secondary small">Buscando cuenta...</div>';
    try {
        const res = await fetch('/api/forgot_password', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });
        const data = await res.json();
        if (data.ok) {
            msgEl.innerHTML = '';
            document.getElementById('forgotForm').classList.add('d-none');
            document.getElementById('forgotResult').classList.remove('d-none');
            document.getElementById('forgotLink').value = data.reset_url;
            const waBtn = document.getElementById('forgotWA');
            if (data.whatsapp_url) { waBtn.href = data.whatsapp_url; waBtn.classList.remove('d-none'); }
        } else {
            msgEl.innerHTML = `<div class="alert alert-danger py-2 small">${data.error}</div>`;
        }
    } catch (e) { msgEl.innerHTML = '<div class="alert alert-danger py-2 small">Error de conexión.</div>'; }
}

function copyResetLink() {
    const link = document.getElementById('forgotLink');
    if (link) { link.select(); navigator.clipboard?.writeText(link.value); }
}

// ✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️
// ✂️ FIN DE CORTE: auth_ui.js ✂️
// ✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️

