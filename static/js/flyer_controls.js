// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
document.addEventListener("DOMContentLoaded", () => {
    if (!window.FLYER_STORE_KEY) return;
    const C = window._fc = {};
    C.FLYER_STORE_KEY = window.FLYER_STORE_KEY;
    C.toggleSwitches = document.querySelectorAll('.flyer-toggle');
    
    C.img = document.getElementById('flyerBgImg');
    C.imgClone = document.getElementById('flyerBgImgClone');
    C.blurContainer = document.getElementById('flyerBgBlurContainer');
    C.overlay = document.getElementById('flyerOverlay');

    function scalePreview() {
        const wrapper = document.getElementById('flyerPreviewWrapper');
        const area = document.getElementById('flyerCaptureArea');
        if(!wrapper || !area) return;
        const scale = Math.min((wrapper.clientWidth - 20) / 360, (wrapper.clientHeight - 20) / 640);
        area.style.transform = `scale(${scale})`;
    }
    window.addEventListener('resize', scalePreview);
    scalePreview();
    
    C.scScale = document.getElementById('flyerScale');
    C.scRot = document.getElementById('flyerRot');
    C.scX = document.getElementById('flyerPosX');
    C.scY = document.getElementById('flyerPosY');
    C.scBlur = document.getElementById('flyerBlur');
    C.scOp = document.getElementById('flyerOpacity');

    C.ovScale = document.getElementById('overlayScale');
    C.ovWidth = document.getElementById('overlayWidth');
    C.ovX = document.getElementById('overlayPosX');
    C.ovY = document.getElementById('overlayPosY');
    C.ovBlur = document.getElementById('overlayBlur');
    C.ovOp = document.getElementById('overlayOpacity');
    C.ovFontSize = document.getElementById('overlayFontSize');

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
            // Guardar valor inicial por defecto
            if (!input.dataset.default) input.dataset.default = input.value;
            // Asegurar paso más controlado
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
                    C.updateFlyer();
                }
            });
        });
    }
    setupSliderControls();

    function loadFlyerState() {
        try {
            const saved = localStorage.getItem(C.FLYER_STORE_KEY);
            if (!saved) return;
            const state = JSON.parse(saved);
            if(state.bgScale !== undefined) C.scScale.value = state.bgScale;
            if(state.bgRot !== undefined) C.scRot.value = state.bgRot;
            if(state.bgX !== undefined) C.scX.value = state.bgX;
            if(state.bgY !== undefined) C.scY.value = state.bgY;
            if(state.bgBlur !== undefined) C.scBlur.value = state.bgBlur;
            if(state.bgOp !== undefined) C.scOp.value = state.bgOp;
            if(state.ovScale !== undefined) C.ovScale.value = state.ovScale;
            if(state.ovWidth !== undefined) C.ovWidth.value = state.ovWidth;
            if(state.ovX !== undefined) C.ovX.value = state.ovX;
            if(state.ovY !== undefined) C.ovY.value = state.ovY;
            if(state.ovBlur !== undefined) C.ovBlur.value = state.ovBlur;
            if(state.ovOp !== undefined) C.ovOp.value = state.ovOp;
            if(state.ovFontSize !== undefined && C.ovFontSize) C.ovFontSize.value = state.ovFontSize;
            if(state.toggles) {
                C.toggleSwitches.forEach(t => {
                    if(state.toggles[t.id] !== undefined) t.checked = state.toggles[t.id];
                });
            }
        } catch(e) { console.error("Error cargando caché", e); }
    }

    function saveFlyerState() {
        const state = {
            bgScale: getVal('flyerScale'), bgRot: getVal('flyerRot'), 
            bgX: getVal('flyerPosX'), bgY: getVal('flyerPosY'),
            bgBlur: getVal('flyerBlur'), bgOp: getVal('flyerOpacity'),
            ovScale: getVal('overlayScale'), ovWidth: getVal('overlayWidth'), 
            ovX: getVal('overlayPosX'), ovY: getVal('overlayPosY'),
            ovBlur: getVal('overlayBlur'), ovOp: getVal('overlayOpacity'),
            ovFontSize: getVal('overlayFontSize'),
            toggles: {}
        };
        C.toggleSwitches.forEach(t => { state.toggles[t.id] = t.checked; });
        localStorage.setItem(C.FLYER_STORE_KEY, JSON.stringify(state));
    }

    function syncBlurMask() {
        const captureArea = document.getElementById('flyerCaptureArea');
        if(!captureArea || !C.overlay || !C.blurContainer) return;
        const currentOvBlur = Math.max(0, 15 + (getVal('overlayBlur') * 0.15));
        if (currentOvBlur === 0) {
            C.blurContainer.style.display = 'none';
            return;
        } else {
            C.blurContainer.style.display = 'block';
        }
        const cBox = captureArea.getBoundingClientRect();
        const oBox = C.overlay.getBoundingClientRect();
        const globalScale = cBox.width / 360; 
        const top = Math.max(0, (oBox.top - cBox.top) / globalScale);
        const left = Math.max(0, (oBox.left - cBox.left) / globalScale);
        const right = Math.max(0, (cBox.right - oBox.right) / globalScale);
        const bottom = Math.max(0, (cBox.bottom - oBox.bottom) / globalScale);
        const tScale = Math.max(0.1, 1 + (getVal('overlayScale') / 100));
        const radius = 1.0 * 16 * tScale; 
        const clipPathVal = `inset(${top}px ${right}px ${bottom}px ${left}px round ${radius}px)`;
        C.blurContainer.style.clipPath = clipPathVal;
        C.blurContainer.style.webkitClipPath = clipPathVal;
    }

    Object.assign(C, { getVal, setLabel, setupSliderControls,
        loadFlyerState, saveFlyerState, syncBlurMask });
});

