// ==========================================
// FUNCIONES DE FORMULARIO DE PUBLICACIONES
// ==========================================

function _resetForm() {
    ['pubNombre','pubDireccion','pubUrl','pubLugar','pubPuntoSalida',
     'pubHora','pubRecomendaciones','pubDescCaminata',
     'pubTelefono','pubWhatsapp','pubFacebook','pubInstagram','pubTiktok','pubYoutube',
     'pubColaborarDetalle'].forEach(id => {
        const el = document.getElementById(id); if (el) el.value = '';
    });
    if (window._quillDesc) window._quillDesc.setText('');
    document.getElementById('pubFechaInicio').value = '';
    document.getElementById('pubFechaFin').value = '';
    document.getElementById('pubTipo').value = '';
    document.getElementById('pubAudio').value = '';
    document.getElementById('pubRifaUrl').value = '';
    document.getElementById('pubRifaUrl2').value = '';
    document.getElementById('pubSinpe').value = '';
    document.getElementById('pubCuenta').value = '';
    document.getElementById('pubLogo').value = '';
    document.getElementById('pubFlyer').value = '';
    document.getElementById('prevLogo').classList.add('d-none');
    document.getElementById('prevFlyer').classList.add('d-none');
    document.querySelectorAll('#mostrarChecks input[type=checkbox]').forEach(cb => cb.checked = true);
    toggleTipoFields();
}

async function editEvento(id) {
    _editingPubId = id;
    const res = await fetch(`/api/publicaciones/${id}`);
    const d = await res.json();
    if (d.error) { alert(d.error); return; }
    document.getElementById('pubNombre').value       = d.nombre || '';
    document.getElementById('pubFechaInicio').value  = d.fecha_inicio || '';
    document.getElementById('pubFechaFin').value     = d.fecha_fin || '';
    if (window._quillDesc) { window._quillDesc.root.innerHTML = d.descripcion || ''; }
    document.getElementById('pubAudio').value        = d.audio_filename || '';
    document.getElementById('pubTipo').value         = d.tipo_evento || '';
    document.getElementById('pubRifaUrl').value      = d.rifa_url || '';
    document.getElementById('pubRifaUrl2').value     = d.rifa_url_2 || '';
    document.getElementById('pubLugar').value        = d.lugar || '';
    document.getElementById('pubPuntoSalida').value  = d.punto_salida || '';
    document.getElementById('pubHora').value         = d.hora_encuentro || '';
    document.getElementById('pubRecomendaciones').value = d.recomendaciones || '';
    document.getElementById('pubDescCaminata').value = d.desc_caminata || '';
    document.getElementById('pubDireccion').value    = d.direccion || '';
    document.getElementById('pubUrl').value          = d.url_externa || '';
    
    const sinpeValues = [d.sinpe_info, d.sinpe_info_2, d.sinpe_info_3, d.sinpe_info_4];
    for (let i = 0; i < 4; i++) {
        const cb = document.getElementById(`sinpe${i + 1}`);
        if (cb) {
            cb.checked = !!sinpeValues[i];
            if (i === 3 && sinpeValues[i]) {
                document.getElementById('pubSinpe4Custom').value = sinpeValues[i];
                document.getElementById('pubSinpe4Custom').classList.remove('d-none');
            }
        }
    }
    
    const cuentaValues = [d.cuenta_info, d.cuenta_info_2, d.cuenta_info_3, d.cuenta_info_4];
    for (let i = 1; i <= 6; i++) {
        const cb = document.getElementById(`cuenta${i}`);
        if (cb) {
            cb.checked = cuentaValues.includes(cb.value);
        }
    }
    
    if (cuentaValues.length > 4 && cuentaValues[4]) {
        const cb6 = document.getElementById('cuenta6');
        if (cb6) {
            cb6.checked = true;
            document.getElementById('pubCuenta6Custom').value = cuentaValues[4];
            document.getElementById('pubCuenta6Custom').classList.remove('d-none');
        }
    }
    
    document.getElementById('pubColaborarDetalle').value = d.colaborar_detalle || '';
    document.getElementById('pubTelefono').value     = d.telefono || '';
    document.getElementById('pubWhatsapp').value     = d.whatsapp || '';
    document.getElementById('pubFacebook').value     = d.facebook || '';
    document.getElementById('pubInstagram').value    = d.instagram || '';
    document.getElementById('pubTiktok').value       = d.tiktok || '';
    document.getElementById('pubYoutube').value      = d.youtube || '';
    toggleTipoFields();
    let mostrar = [];
    try { mostrar = JSON.parse(d.mostrar || '[]'); } catch {}
    document.querySelectorAll('#mostrarChecks input[type=checkbox]').forEach(cb => {
        cb.checked = mostrar.includes(cb.value);
    });
    if (d.logo_filename) {
        const l = document.getElementById('prevLogo');
        l.src = `/static/uploads/publicaciones/${d.logo_filename}`; l.classList.remove('d-none');
    }
    if (d.flyer_filename) {
        const f = document.getElementById('prevFlyer');
        f.src = `/static/uploads/publicaciones/${d.flyer_filename}`; f.classList.remove('d-none');
    }
    document.getElementById('pubModalTitle').innerHTML = '<i class="bi bi-pencil-fill me-2 text-orange"></i>Editar Evento';
    document.getElementById('pubSubmitTxt').textContent = 'Actualizar';
    document.getElementById('pubFormMsg').innerHTML = '';
    _getPubModal().show();
}
