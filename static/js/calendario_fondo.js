// ==========================================
// RENDERIZADO DE FONDO CANVAS
// ==========================================

function actualizarOpacidadOverlay() {
    const sOsc = document.getElementById('calSliderOscuridad');
    if(!sOsc) return;
    const opacidad = sOsc.value;
    
    const valOsc = document.getElementById('calValOscuridad');
    if(valOsc) valOsc.innerText = Math.round(opacidad * 100) + '%';
    
    const overlay = document.getElementById('cal-overlay-oscuro');
    if(overlay) {
        overlay.style.backgroundColor = `rgba(0, 0, 0, ${opacidad})`;
    }
}

function renderizarFondoCanvas() {
    const canvas = document.getElementById('cal-flyer-bg-canvas');
    if(!canvas || !calBgImageObj.src) return;
    
    const fSelect = document.getElementById('calFormatoArte');
    const formato = fSelect ? fSelect.value : 'horizontal';
    const w = formato === 'horizontal' ? 1920 : 1080;
    const h = formato === 'horizontal' ? 1080 : 1920;
    
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext('2d');
    
    ctx.fillStyle = "#111111";
    ctx.fillRect(0, 0, w, h);

    const sScale = document.getElementById('calSliderScale');
    const sX = document.getElementById('calSliderX');
    const sY = document.getElementById('calSliderY');
    const sBlur = document.getElementById('calSliderBlur');

    const scale = sScale ? parseFloat(sScale.value) : 1;
    const tx = sX ? parseFloat(sX.value) : 0;
    const ty = sY ? parseFloat(sY.value) : 0;
    const blur = sBlur ? parseInt(sBlur.value) : 0;

    const vScale = document.getElementById('calValScale');
    const vX = document.getElementById('calValX');
    const vY = document.getElementById('calValY');
    const vBlur = document.getElementById('calValBlur');
    
    if(vScale) vScale.innerText = scale.toFixed(1);
    if(vX) vX.innerText = tx + 'px';
    if(vY) vY.innerText = ty + 'px';
    if(vBlur) vBlur.innerText = blur + 'px';

    ctx.save();
    
    if(blur > 0) {
        ctx.filter = `blur(${blur}px)`;
    }

    if (calBgImageObj.width > 1) { 
        const imgRatio = calBgImageObj.width / calBgImageObj.height;
        const canvasRatio = w / h;
        let drawW = w;
        let drawH = h;

        if (imgRatio > canvasRatio) {
            drawW = h * imgRatio;
            drawH = h;
        } else {
            drawW = w;
            drawH = w / imgRatio;
        }

        ctx.translate(w/2 + tx, h/2 + ty);
        ctx.scale(scale, scale);
        ctx.drawImage(calBgImageObj, -drawW/2, -drawH/2, drawW, drawH);
    }
    
    ctx.restore();
}

const calUpload = document.getElementById('calBgImageUpload');
if(calUpload) {
    calUpload.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(event) {
                calBgImageObj.src = event.target.result;
                const sS = document.getElementById('calSliderScale');
                const sX = document.getElementById('calSliderX');
                const sY = document.getElementById('calSliderY');
                const sB = document.getElementById('calSliderBlur');
                if(sS) sS.value = 1; 
                if(sX) sX.value = 0; 
                if(sY) sY.value = 0;
                if(sB) sB.value = 8;
                actualizarOpacidadOverlay();
            };
            reader.readAsDataURL(file);
        }
    });
}
