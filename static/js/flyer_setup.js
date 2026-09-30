// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
document.addEventListener("DOMContentLoaded", () => {
    const captureArea = document.getElementById('flyerCaptureArea');
    if (!captureArea) return;

    const FLYER_STORE_KEY = () => 'flyer_prefs_v2_' + (captureArea.dataset.eventId || 'new');
    const toggleSwitches = document.querySelectorAll('.flyer-toggle');

    const img = document.getElementById('flyerBgImg');
    const imgClone = document.getElementById('flyerBgImgClone');
    const blurContainer = document.getElementById('flyerBgBlurContainer');
    const overlay = document.getElementById('flyerOverlay');

    function scalePreview() {
        const wrapper = document.getElementById('flyerPreviewWrapper');
        const area = document.getElementById('flyerCaptureArea');
        if(!wrapper || !area) return;
        const scale = Math.min((wrapper.clientWidth - 20) / 360, (wrapper.clientHeight - 20) / 640);
        area.style.transform = `scale(${scale})`;
    }
    window.addEventListener('resize', scalePreview);
    scalePreview();

    const scScale = document.getElementById('flyerScale');
    const scRot = document.getElementById('flyerRot');
    const scX = document.getElementById('flyerPosX');
    const scY = document.getElementById('flyerPosY');
    const scBlur = document.getElementById('flyerBlur');
    const scOp = document.getElementById('flyerOpacity');

    const ovScale = document.getElementById('overlayScale');
    const ovWidth = document.getElementById('overlayWidth');
    const ovX = document.getElementById('overlayPosX');
    const ovY = document.getElementById('overlayPosY');
    const ovBlur = document.getElementById('overlayBlur');
    const ovOp = document.getElementById('overlayOpacity');
    const ovFontSize = document.getElementById('overlayFontSize');

    function getVal(id) {
        const el = document.getElementById(id);
        return el ? parseFloat(el.value) : 0;
    }
    function setLabel(id, text) {
        const label = document.getElementById('val_' + id);
        if(!label) return;
        const val = label.querySelector('.slider-val');
        if(val) val.innerText = text;
        else label.innerText = text;
    }

    function setupSliderControls() {
        document.querySelectorAll('input[type="range"]').forEach(input => {
            if (!input.dataset.default) input.dataset.default = input.value;
            if (input.step === '1') input.step = '5';
            const label = input.previousElementSibling;
            if (!label || label.tagName !== 'LABEL') return;
            const valSpan = label.querySelector('.float-end.text-orange');
            if (!valSpan || valSpan.querySelector('.slider-val')) return;
            const currentText = valSpan.innerText.trim();
            valSpan.innerHTML = '<span class="slider-val">' + currentText + '</span> <button type="button" class="btn btn-link text-orange p-0 ms-1 reset-slider-btn" style="font-size:0.75rem; text-decoration:none; line-height:1;" title="Restablecer"><i class="bi bi-arrow-counterclockwise"></i></button>';
            const btn = valSpan.querySelector('.reset-slider-btn');
            if (btn) btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                if (input.dataset.default !== undefined) {
                    input.value = input.dataset.default;
                    updateFlyer();
                }
            });
        });
    }
    setupSliderControls();

    window.actualizarPreviewFlyer = function() {
        const nombre = document.getElementById('nombreLugar')?.value || 'Nombre del Lugar';
        const actividad = document.getElementById('actividad')?.value || 'Caminata';
        const dificultad = document.getElementById('dificultad')?.value || 'Paseo';
        const precio = parseInt(document.getElementById('precio')?.value || 0) || 0;
        const reserva = parseInt(document.getElementById('reserva')?.value || 0) || 0;
        const moneda = document.getElementById('moneda')?.value || '¢';
        const capacidad = (document.getElementById('capacidad')?.value || '').replace('AGOTADO_', '');
        const sinpe = document.getElementById('sinpe')?.value || 'Por definir';
        const cuenta = document.getElementById('cuenta')?.value || 'Por definir';
        const incluyeChecks = document.querySelectorAll('#incluyeWrapper input[name="incluye_check"]:checked');
        const incluyeArr = [];
        incluyeChecks.forEach(cb => {
            if (cb.value === 'Otros') {
                const desc = document.getElementById('otrosDescripcion')?.value.trim();
                if (desc) incluyeArr.push(desc);
            } else {
                incluyeArr.push(cb.value);
            }
        });
        const incluye = incluyeArr.join(', ');
        const dias = parseInt(document.getElementById('dias')?.value || 1) || 1;

        const diaSeguro = document.getElementById('diaSeguroToggle')?.checked;
        const horaSalida = document.getElementById('horaSalida')?.value || '';
        const lugarSalida = document.getElementById('lugarSalida')?.value || '';

        let fechaTexto = 'Por definir';
        if (dias == 1) {
            const day = document.getElementById('dayUnica')?.value || '';
            const month = document.getElementById('monthUnica')?.value || '';
            const year = document.getElementById('yearUnica')?.value || '';
            if (day && month && year) {
                const meses = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'];
                fechaTexto = `${day} de ${meses[parseInt(month)-1]} del ${year}`;
                if (diaSeguro) fechaTexto = 'Por confirmar en Chat';
            }
        } else {
            const dayI = document.getElementById('dayInicio')?.value || '';
            const monthI = document.getElementById('monthInicio')?.value || '';
            const yearI = document.getElementById('yearInicio')?.value || '';
            const dayR = document.getElementById('dayRegreso')?.value || '';
            const monthR = document.getElementById('monthRegreso')?.value || '';
            const yearR = document.getElementById('yearRegreso')?.value || '';
            const meses = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'];
            if (dayI && monthI && yearI) {
                fechaTexto = `${dayI} de ${meses[parseInt(monthI)-1]} del ${yearI}`;
                if (dias > 1 && dayR && monthR && yearR) {
                    fechaTexto += ` al ${dayR} de ${meses[parseInt(monthR)-1]} del ${yearR}`;
                }
                if (diaSeguro) fechaTexto = 'Por confirmar en Chat';
            }
        }

        const posterPreview = document.getElementById('eventImagePreview');
        if (posterPreview && img && imgClone) {
            img.src = posterPreview.src;
            imgClone.src = posterPreview.src;
        }

        const tTitulo = document.getElementById('flyerTitulo');
        if(tTitulo) tTitulo.innerText = nombre;
        const tActividad = document.getElementById('fl_actividad');
        if(tActividad) tActividad.innerText = actividad;
        const tDificultad = document.getElementById('fl_dificultad');
        if(tDificultad) tDificultad.innerText = dificultad;
        const tAlto = document.getElementById('fl_altoRiesgo');
        if(tAlto) tAlto.classList.toggle('d-none', !(document.getElementById('altoRiesgoToggle')?.checked));
        const tFecha = document.getElementById('flyerFechaText');
        if(tFecha) tFecha.innerText = fechaTexto;
        const tSalida = document.getElementById('flyerSalidaText');
        if(tSalida) tSalida.innerText = (lugarSalida || 'Por definir') + (horaSalida ? ' (' + horaSalida + ')' : '');
        const tPrecio = document.getElementById('flyerPrecioText');
        if(tPrecio) tPrecio.innerText = precio > 0 ? moneda + precio : 'PENDIENTE';
        const tReserva = document.getElementById('flyerReservaText');
        if(tReserva) tReserva.innerText = reserva > 0 ? moneda + reserva : 'PENDIENTE';
        const tCap = document.getElementById('flyerCapacidadText');
        if(tCap) tCap.innerText = capacidad;
        const tSinpe = document.getElementById('flyerSinpeText');
        if(tSinpe) tSinpe.innerText = sinpe;
        const tCuenta = document.getElementById('flyerCuentaText');
        if(tCuenta) tCuenta.innerText = cuenta === 'Ninguna' ? 'Solo SINPE' : cuenta;

        const flIncluye = document.getElementById('fl_incluye');
        const tags = document.getElementById('flyerIncluyeTags');
        if (flIncluye && tags) {
            if (incluye) {
                tags.innerHTML = '';
                incluye.split(',').forEach(item => {
                    const t = item.trim();
                    if (t) {
                        tags.insertAdjacentHTML('beforeend', '<span class="badge border border-white border-opacity-50 text-white shadow-sm" style="font-size: calc(0.55rem * var(--text-scale)); background: rgba(255,255,255,0.15);">' + t + '</span>');
                    }
                });
            } else {
                flIncluye.classList.add('d-none');
                document.getElementById('t_incluye').checked = false;
            }
        }
    };

    window._flyer = { captureArea, FLYER_STORE_KEY, toggleSwitches, img, imgClone,
        blurContainer, overlay, getVal, setLabel, scalePreview, actualizarPreviewFlyer,
        sliders: [scScale, scRot, scX, scY, scBlur, scOp, ovScale, ovWidth, ovX, ovY, ovBlur, ovOp, ovFontSize] };
});

