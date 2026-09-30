// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
async function agregarFormaPago(tipo) {
    let payload = { tipo: tipo };
    if (tipo === 'sinpe') {
        payload.numero = document.getElementById('nuevoSinpeNumero').value.trim();
        payload.titular = document.getElementById('nuevoSinpeTitular').value.trim();
        if (!payload.numero || !payload.titular) { alert('Complete el número SINPE y el titular.'); return; }
    } else {
        payload.numero = document.getElementById('nuevaCuentaNumero').value.trim();
        payload.titular = document.getElementById('nuevaCuentaTitular').value.trim();
        payload.detalle = document.getElementById('nuevaCuentaDetalle').value.trim();
        if (!payload.numero || !payload.titular) { alert('Complete el número de cuenta y el titular.'); return; }
    }

    try {
        const res = await fetch('/api/payment_methods', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok || !data.ok) {
            alert(data.error || 'Error al guardar la forma de pago.');
            return;
        }

        if (tipo === 'sinpe') {
            const select = document.getElementById('sinpe');
            const opt = document.createElement('option'); opt.value = data.display; opt.textContent = data.display; select.appendChild(opt);
            document.getElementById('listaSinpes').insertAdjacentHTML('beforeend', `<li class="mb-1">${data.display}</li>`);
            document.getElementById('nuevoSinpeNumero').value = '';
            document.getElementById('nuevoSinpeTitular').value = '';
        } else {
            const select = document.getElementById('cuenta');
            const opt = document.createElement('option'); opt.value = data.display; opt.textContent = data.display; select.appendChild(opt);
            document.getElementById('listaCuentas').insertAdjacentHTML('beforeend', `<li class="mb-1 text-break">${data.display}</li>`);
            document.getElementById('nuevaCuentaNumero').value = '';
            document.getElementById('nuevaCuentaTitular').value = '';
            document.getElementById('nuevaCuentaDetalle').value = '';
        }
    } catch (err) {
        console.error(err);
        alert('Error de conexión al guardar la forma de pago.');
    }
}

function exportarFormasPagoWhatsApp() {
    const sinpeItems = Array.from(document.querySelectorAll('#sinpe option')).map(o => '- ' + o.value).filter(v => v.length > 2);
    const cuentaItems = Array.from(document.querySelectorAll('#cuenta option'))
        .filter(o => o.value !== 'Ninguna')
        .map(o => '- ' + o.value)
        .filter(v => v.length > 2);
    const sinpeText = sinpeItems.length ? sinpeItems.join('\n') : 'No hay SINPE registrado';
    const cuentaText = cuentaItems.length ? cuentaItems.join('\n') : 'No aplica / Solo usar SINPE';
    const mensaje = `Estas son las formas de pago del grupo La Tribu de los Libres.\n\nSINPE:\n${sinpeText}\n\nCuentas:\n${cuentaText}`;
    window.open('https://wa.me/?text=' + encodeURIComponent(mensaje), '_blank');
}
