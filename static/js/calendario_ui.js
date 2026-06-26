// ==========================================
// INTERFAZ DE USUARIO Y LOCAL STORAGE
// ==========================================

function cargarTextosLocales() {
    const tTitulo = document.getElementById('calInputTitulo');
    const tNota = document.getElementById('calInputNota');
    const tPhone = document.getElementById('calInputPhone');
    const tSinpe = document.getElementById('calInputSinpe');
    const sSize = document.getElementById('calSliderCardSize');
    const tPrecio = document.getElementById('calTogglePrecio');

    if(tTitulo) tTitulo.value = localStorage.getItem('cal_titulo') || 'CALENDARIO DE AVENTURAS';
    if(tNota) tNota.value = localStorage.getItem('cal_nota') || '';
    if(tPhone) tPhone.value = localStorage.getItem('cal_phone') || '8622-7500';
    if(tSinpe) tSinpe.value = localStorage.getItem('cal_sinpe') || '';
    if(sSize) sSize.value = localStorage.getItem('cal_card_size') || '1';
    if(tPrecio) tPrecio.checked = localStorage.getItem('cal_show_price') !== 'false'; 

    actualizarTextosCalendario();
}

function actualizarTextosCalendario() {
    const tituloEl = document.getElementById('cal-flyer-titulo');
    const notaEl = document.getElementById('cal-flyer-nota');
    const contactoEl = document.getElementById('cal-flyer-contacto');
    const tPrecio = document.getElementById('calTogglePrecio');
    
    const inTitulo = document.getElementById('calInputTitulo')?.value || '';
    const inNota = document.getElementById('calInputNota')?.value || '';
    const inPhone = document.getElementById('calInputPhone')?.value || '';
    const inSinpe = document.getElementById('calInputSinpe')?.value || '';

    localStorage.setItem('cal_titulo', inTitulo);
    localStorage.setItem('cal_nota', inNota);
    localStorage.setItem('cal_phone', inPhone);
    localStorage.setItem('cal_sinpe', inSinpe);
    if(tPrecio) localStorage.setItem('cal_show_price', tPrecio.checked);

    if(tituloEl) tituloEl.innerText = inTitulo;
    if(notaEl) notaEl.innerText = inNota;
    
    if(contactoEl) {
        let textoFooter = `Reservas: ${inPhone}`;
        if(inSinpe.trim() !== '') {
            textoFooter += ` | SINPE: ${inSinpe}`;
        }
        textoFooter += ` | www.latribu.top`;
        contactoEl.innerText = textoFooter;
    }
}

function actualizarTamanoTarjetas() {
    const scale = document.getElementById('calSliderCardSize')?.value || 1;
    const valText = document.getElementById('calValCardSize');
    if(valText) valText.innerText = Math.round(scale * 100) + '%';
    
    localStorage.setItem('cal_card_size', scale);

    const grid = document.getElementById('cal-grid-meses');
    const formato = document.getElementById('calFormatoArte')?.value || 'horizontal';
    
    if(grid) {
        grid.style.display = 'grid';
        grid.style.gap = '1.5rem';
        grid.style.fontSize = `${scale}rem`;
        const baseMinW = formato === 'horizontal' ? 380 : 300;
        grid.style.gridTemplateColumns = `repeat(auto-fit, minmax(calc(${baseMinW}px * ${scale}), 1fr))`;
    }
}
