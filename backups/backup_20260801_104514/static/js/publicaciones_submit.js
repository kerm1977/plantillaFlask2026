// ==========================================
// FUNCIONES DE ENVÍO DE PUBLICACIONES
// ==========================================

async function submitEvento() {
    const nombre = document.getElementById('pubNombre').value.trim();
    const fecha  = document.getElementById('pubFechaInicio').value;
    if (!nombre || !fecha) {
        document.getElementById('pubFormMsg').innerHTML =
            '<div class="alert alert-warning py-2 small">Nombre y fecha son obligatorios.</div>';
        return;
    }
    const mostrar = Array.from(document.querySelectorAll('#mostrarChecks input:checked')).map(c => c.value);
    
    const sinpeSelected = [];
    for (let i = 1; i <= 4; i++) {
        const cb = document.getElementById(`sinpe${i}`);
        if (cb && cb.checked) {
            if (i === 4) {
                const custom = document.getElementById('pubSinpe4Custom').value;
                sinpeSelected.push(custom || '');
            } else {
                sinpeSelected.push(cb.value);
            }
        }
    }
    
    const cuentaSelected = [];
    for (let i = 1; i <= 6; i++) {
        const cb = document.getElementById(`cuenta${i}`);
        if (cb && cb.checked) {
            if (i === 6) {
                const custom = document.getElementById('pubCuenta6Custom').value;
                if (custom) cuentaSelected.push(custom);
            } else if (cb.value) {
                cuentaSelected.push(cb.value);
            }
        }
    }
    
    const fd = new FormData();
    fd.append('nombre',          nombre);
    fd.append('fecha_inicio',    fecha);
    fd.append('fecha_fin',       document.getElementById('pubFechaFin').value);
    fd.append('descripcion',     window._quillDesc ? window._quillDesc.root.innerHTML : '');
    fd.append('audio_filename',  document.getElementById('pubAudio').value);
    fd.append('tipo_evento',     document.getElementById('pubTipo').value);
    fd.append('rifa_url',        document.getElementById('pubRifaUrl').value);
    fd.append('rifa_url_2',      document.getElementById('pubRifaUrl2').value);
    fd.append('lugar',           document.getElementById('pubLugar').value);
    fd.append('punto_salida',    document.getElementById('pubPuntoSalida').value);
    fd.append('hora_encuentro',  document.getElementById('pubHora').value);
    fd.append('recomendaciones', document.getElementById('pubRecomendaciones').value);
    fd.append('desc_caminata',   document.getElementById('pubDescCaminata').value);
    fd.append('direccion',       document.getElementById('pubDireccion').value);
    fd.append('url_externa',     document.getElementById('pubUrl').value);
    fd.append('sinpe_info',      sinpeSelected[0] || '');
    fd.append('sinpe_info_2',    sinpeSelected[1] || '');
    fd.append('sinpe_info_3',    sinpeSelected[2] || '');
    fd.append('sinpe_info_4',    sinpeSelected[3] || '');
    fd.append('cuenta_info',     cuentaSelected[0] || '');
    fd.append('cuenta_info_2',   cuentaSelected[1] || '');
    fd.append('cuenta_info_3',   cuentaSelected[2] || '');
    fd.append('cuenta_info_4',   cuentaSelected[3] || '');
    fd.append('colaborar_detalle', document.getElementById('pubColaborarDetalle').value);
    fd.append('telefono',          document.getElementById('pubTelefono').value);
    fd.append('whatsapp',        document.getElementById('pubWhatsapp').value);
    fd.append('facebook',        document.getElementById('pubFacebook').value);
    fd.append('instagram',       document.getElementById('pubInstagram').value);
    fd.append('tiktok',          document.getElementById('pubTiktok').value);
    fd.append('youtube',         document.getElementById('pubYoutube').value);
    fd.append('mostrar',         JSON.stringify(mostrar));
    const logo  = document.getElementById('pubLogo').files[0];
    const flyer = document.getElementById('pubFlyer').files[0];
    if (logo)  fd.append('logo',  logo);
    if (flyer) fd.append('flyer', flyer);

    const url    = _editingPubId ? `/api/publicaciones/${_editingPubId}` : '/api/publicaciones';
    const method = _editingPubId ? 'PUT' : 'POST';
    const res    = await fetch(url, { method, body: fd });
    const data   = await res.json();
    if (data.ok) {
        bootstrap.Modal.getInstance(document.getElementById('pubModal'))?.hide();
        window.location.reload();
    } else {
        document.getElementById('pubFormMsg').innerHTML =
            `<div class="alert alert-danger py-2 small">${data.error}</div>`;
    }
}
