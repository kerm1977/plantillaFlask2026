// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
document.addEventListener("DOMContentLoaded", () => {
    const C = window._fc;
    if (!C) return;
    function updateFlyer() {
        const vBgScale = C.getVal('flyerScale');
        const bgScaleReal = Math.max(0.1, 1 + (vBgScale / 100));
        C.setLabel('flyerScale', vBgScale > 0 ? '+' + vBgScale + '%' : vBgScale + '%');
        const vBgRot = C.getVal('flyerRot');
        const bgRotReal = vBgRot * 1.8; 
        C.setLabel('flyerRot', Math.round(bgRotReal) + '°');
        const bgXReal = C.getVal('flyerPosX'); C.setLabel('flyerPosX', bgXReal > 0 ? '+' + bgXReal + '%' : bgXReal + '%');
        const bgYReal = C.getVal('flyerPosY'); C.setLabel('flyerPosY', bgYReal > 0 ? '+' + bgYReal + '%' : bgYReal + '%');
        const vBgBlur = C.getVal('flyerBlur');
        const bgBlurReal = Math.max(0, 15 + (vBgBlur * 0.15)); 
        C.setLabel('flyerBlur', vBgBlur > 0 ? '+' + vBgBlur + '%' : vBgBlur + '%');
        const vBgOp = C.getVal('flyerOpacity');
        const bgOpReal = Math.max(0, Math.min(1, 0.5 + (vBgOp * 0.005)));
        C.setLabel('flyerOpacity', vBgOp > 0 ? '+' + vBgOp + '%' : vBgOp + '%');
        const vOvScale = C.getVal('overlayScale');
        const ovScaleReal = Math.max(0.1, 1 + (vOvScale / 100));
        C.setLabel('overlayScale', vOvScale > 0 ? '+' + vOvScale + '%' : vOvScale + '%');
        const vOvWidth = C.getVal('overlayWidth');
        const ovWidthReal = vOvWidth < 0 ? 90 - (Math.abs(vOvWidth)/100 * 40) : Math.min(100, 90 + (vOvWidth/100 * 10));
        C.setLabel('overlayWidth', vOvWidth > 0 ? '+' + vOvWidth + '%' : vOvWidth + '%');
        const vOvX = C.getVal('overlayPosX');
        const ovXReal = vOvX * 1.5; 
        C.setLabel('overlayPosX', vOvX > 0 ? '+' + vOvX + '%' : vOvX + '%');
        const vOvY = C.getVal('overlayPosY');
        const ovYReal = vOvY * 2.5; 
        C.setLabel('overlayPosY', vOvY > 0 ? '+' + vOvY + '%' : vOvY + '%');
        const vOvBlur = C.getVal('overlayBlur');
        const ovBlurReal = Math.max(0, 15 + (vOvBlur * 0.15)); 
        C.setLabel('overlayBlur', vOvBlur > 0 ? '+' + vOvBlur + '%' : vOvBlur + '%');
        const vOvOp = C.getVal('overlayOpacity');
        const ovOpReal = Math.max(0, Math.min(0.95, 0.4 + (vOvOp * 0.005)));
        C.setLabel('overlayOpacity', vOvOp > 0 ? '+' + vOvOp + '%' : vOvOp + '%');
        const vOvFontSize = C.getVal('overlayFontSize');
        const ovFontSizeReal = Math.max(0.5, 1 + (vOvFontSize / 100));
        C.setLabel('overlayFontSize', vOvFontSize > 0 ? '+' + vOvFontSize + '%' : vOvFontSize + '%');

        if (C.img) {
            const tf = `translate(${bgXReal}%, ${bgYReal}%) scale(${bgScaleReal}) rotate(${bgRotReal}deg)`;
            C.img.style.transform = tf;
            C.img.style.filter = `blur(${bgBlurReal}px) opacity(${bgOpReal})`;
            if(C.imgClone) {
                C.imgClone.style.transform = tf;
                C.imgClone.style.filter = `blur(${bgBlurReal + ovBlurReal}px) opacity(${bgOpReal})`;
            }
        }
        if (C.overlay) {
            C.overlay.style.width = `${ovWidthReal}%`;
            C.overlay.style.transform = `translate(${ovXReal}px, ${ovYReal}px) scale(${ovScaleReal})`;
            C.overlay.style.backgroundColor = `rgba(0, 0, 0, ${ovOpReal})`;
            C.overlay.style.setProperty('--text-scale', ovFontSizeReal);
            C.syncBlurMask();
        }
        C.saveFlyerState();
    }

    C.updateFlyer = updateFlyer;
    C.loadFlyerState();
    C.toggleSwitches.forEach(toggle => {
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
    [C.scScale, C.scX, C.scY, C.scRot, C.scBlur, C.scOp, C.ovScale, C.ovWidth, C.ovX, C.ovY, C.ovBlur, C.ovOp, C.ovFontSize].forEach(el => {
        if(el) el.addEventListener('input', updateFlyer);
    });
    updateFlyer();

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
});

