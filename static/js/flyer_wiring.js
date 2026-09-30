// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
document.addEventListener("DOMContentLoaded", () => {
    const _F = window._flyer || {};
    if (!_F.loadFlyerState) return;
    const { loadFlyerState, actualizarPreviewFlyer, scalePreview, captureArea } = _F;
    const toggleSwitches = document.querySelectorAll('.flyer-toggle');
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
    // Inicializacion
    loadFlyerState();
    toggleSwitches.forEach(toggle => {
        toggle.addEventListener('change', function() {
            const targetElement = document.getElementById(this.getAttribute('data-target'));
            if (targetElement) {
                if (this.checked) targetElement.classList.remove('d-none');
                else targetElement.classList.add('d-none');
            }
            setTimeout(updateFlyer, 50);
        });
        toggle.dispatchEvent(new Event('change'));
    });
    [scScale, scX, scY, scRot, scBlur, scOp, ovScale, ovWidth, ovX, ovY, ovBlur, ovOp, ovFontSize].forEach(el => {
        if(el) el.addEventListener('input', updateFlyer);
    });
    updateFlyer();
    actualizarPreviewFlyer();
    document.getElementById('accFlyer')?.addEventListener('shown.bs.collapse', () => {
        actualizarPreviewFlyer();
        scalePreview();
    });
    ['nombreLugar','precio','reserva','horaSalida','lugarSalida'].forEach(id => {
        document.getElementById(id)?.addEventListener('input', actualizarPreviewFlyer);
    });
    ['dificultad','actividad','moneda','capacidad','sinpe','cuenta','dias'].forEach(id => {
        document.getElementById(id)?.addEventListener('change', actualizarPreviewFlyer);
    });
    document.getElementById('incluyeWrapper')?.addEventListener('change', actualizarPreviewFlyer);
    document.getElementById('otrosDescripcion')?.addEventListener('input', actualizarPreviewFlyer);
    ['dayUnica','monthUnica','yearUnica','dayInicio','monthInicio','yearInicio','dayRegreso','monthRegreso','yearRegreso','diaSeguroToggle','altoRiesgoToggle'].forEach(id => {
        document.getElementById(id)?.addEventListener('change', actualizarPreviewFlyer);
    });

    // PULSACIÓN LARGA PARA RESET DE AJUSTES
    const resetFlyerValuesModalEl = document.getElementById('resetFlyerValuesModal');
    const resetFlyerValuesModal = resetFlyerValuesModalEl ? new bootstrap.Modal(resetFlyerValuesModalEl) : null;
    const resetFlyerMessage = document.getElementById('resetFlyerMessage');
    const confirmResetFlyer = document.getElementById('confirmResetFlyer');
    const btnConfirmResetFlyer = document.getElementById('btnConfirmResetFlyer');
    let currentResetScope = null;

    if (resetFlyerValuesModal && confirmResetFlyer && btnConfirmResetFlyer) {
        confirmResetFlyer.addEventListener('change', () => {
            btnConfirmResetFlyer.disabled = !confirmResetFlyer.checked;
        });

        btnConfirmResetFlyer.addEventListener('click', () => {
            if (!currentResetScope) return;
            const ids = currentResetScope === 'fondo'
                ? ['flyerScale', 'flyerRot', 'flyerPosX', 'flyerPosY', 'flyerBlur', 'flyerOpacity']
                : ['overlayScale', 'overlayWidth', 'overlayPosX', 'overlayPosY', 'overlayBlur', 'overlayOpacity', 'overlayFontSize'];
            ids.forEach(id => {
                const el = document.getElementById(id);
                if (el) el.value = 0;
            });
            updateFlyer();
            confirmResetFlyer.checked = false;
            btnConfirmResetFlyer.disabled = true;
            resetFlyerValuesModal.hide();
            currentResetScope = null;
        });

        document.querySelectorAll('[data-reset-target]').forEach(header => {
            let pressTimer = null;
            let isLongPress = false;
            const scopeName = header.dataset.resetTarget === 'fondo' ? 'Ajustes de Fondo' : 'Ajustes del Texto';

            function startPress(e) {
                if (e.type === 'mousedown' && e.button !== 0) return;
                isLongPress = false;
                pressTimer = setTimeout(() => {
                    isLongPress = true;
                    currentResetScope = header.dataset.resetTarget;
                    if (resetFlyerMessage) resetFlyerMessage.textContent = `¿Restablecer todos los valores de ${scopeName} a cero? Esta acción no se puede deshacer.`;
                    confirmResetFlyer.checked = false;
                    btnConfirmResetFlyer.disabled = true;
                    resetFlyerValuesModal.show();
                }, 800);
            }

            function cancelPress() {
                if (pressTimer) { clearTimeout(pressTimer); pressTimer = null; }
            }

            header.addEventListener('mousedown', startPress);
            header.addEventListener('touchstart', startPress, {passive: true});
            header.addEventListener('mouseup', cancelPress);
            header.addEventListener('mouseleave', cancelPress);
            header.addEventListener('touchend', cancelPress);
            header.addEventListener('click', (e) => {
                if (isLongPress) {
                    e.preventDefault();
                    e.stopPropagation();
                    isLongPress = false;
                }
            }, true);
        });
    }

    // EXPORTAR FLYER
    const btnExportFlyer = document.getElementById('btnExportFlyer');
    if (btnExportFlyer) {
        btnExportFlyer.addEventListener('click', async function() {
            if (typeof htmlToImage === 'undefined') {
                alert("La librería de exportación no se ha cargado. Verifica tu conexión a internet.");
                return;
            }
            const originalText = this.innerHTML;
            this.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Generando Alta Resolución...';
            this.disabled = true;
            actualizarPreviewFlyer();
            try {
                const currentTransform = captureArea.style.transform;
                captureArea.style.transform = 'none';
                const dataUrl = await htmlToImage.toPng(captureArea, {
                    pixelRatio: 4,
                    backgroundColor: 'transparent',
                    style: { transform: 'none' }
                });
                captureArea.style.transform = currentTransform;
                const link = document.createElement('a');
                const safeName = (document.getElementById('nombreLugar')?.value || 'Evento').replace(/[^a-zA-Z0-9\s]/g, '').replace(/\s+/g, '_');
                link.download = `Flyer_${safeName}.png`;
                link.href = dataUrl;
                link.click();
            } catch(e) {
                console.error(e);
                alert("Error al generar el flyer. Intenta de nuevo.");
            } finally {
                this.innerHTML = originalText;
                this.disabled = false;
            }
        });
    }
});
