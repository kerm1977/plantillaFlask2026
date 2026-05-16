// ==========================================
// LÓGICA DEL GENERADOR DE CALENDARIO HD
// ==========================================

let eventosDBCalendario = [];
let calBgImageObj = new Image();

// Asignamos una imagen en blanco por defecto para que no haya error 404
const fallbackImage = window.APP_VARS ? window.APP_VARS.emptyImageBase64 : "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=";
calBgImageObj.src = typeof cleanImage !== 'undefined' ? cleanImage : fallbackImage;
calBgImageObj.onload = renderizarFondoCanvas;

async function cargarEventosCalendario() {
    try {
        const response = await fetch('/api/get_events');
        const eventosRaw = await response.json();

        const meses_es = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];

        eventosDBCalendario = eventosRaw.map(ev => {
            let fechaCorta = ev.fecha ? ev.fecha.split(' ')[0] : '';
            let mesTxt = "S/M";
            let diaTxt = "--";
            let ms = 0;
            
            if (fechaCorta && fechaCorta.includes('-')) {
                let partes = fechaCorta.split('-'); 
                let d = new Date(partes[0], partes[1] - 1, partes[2]);
                mesTxt = meses_es[d.getMonth()];
                diaTxt = d.getDate().toString();
                ms = d.getTime();
            }

            return {
                mes: mesTxt,
                dia: diaTxt,
                nombre: ev.nombreLugar,
                categoria: ev.actividad || 'Caminata',
                dificultad: ev.dificultad || 'Moderada',
                precio: ev.precio || 'PENDIENTE', // Capturamos el precio de la base de datos
                _timestamp: ms
            };
        });

        eventosDBCalendario.sort((a, b) => a._timestamp - b._timestamp);
        renderizarCalendario();
    } catch(e) {
        console.error("Error al cargar caminatas:", e);
    }
}

const calWrapper = document.getElementById('flyer-wrapper');
const calLienzoArte = document.getElementById('lienzo-arte');

function ajustarEscalaWrapperCalendario() {
    if(!calWrapper || !calLienzoArte) return;
    const currentWidth = calWrapper.clientWidth;
    if(currentWidth === 0) return; 
    
    const fSelect = document.getElementById('calFormatoArte');
    const formato = fSelect ? fSelect.value : 'horizontal';
    
    const baseWidth = formato === 'horizontal' ? 1920 : 1080;
    const baseHeight = formato === 'horizontal' ? 1080 : 1920;

    calLienzoArte.style.width = baseWidth + 'px';
    calLienzoArte.style.height = baseHeight + 'px';

    const ratio = baseHeight / baseWidth;
    calWrapper.style.height = (currentWidth * ratio) + 'px';

    const scale = currentWidth / baseWidth;
    calLienzoArte.style.transform = `scale(${scale})`;
    
    renderizarFondoCanvas(); 
}

window.addEventListener('resize', ajustarEscalaWrapperCalendario);

const modalCal = document.getElementById('calendarioModal');
if(modalCal) {
    modalCal.addEventListener('shown.bs.modal', function () {
        ajustarEscalaWrapperCalendario();
        cargarEventosCalendario();
        actualizarOpacidadOverlay(); 
        
        // Cargar los valores guardados localmente (Textos, Tamaño y Toggle Precio)
        cargarTextosLocales();
        actualizarTamanoTarjetas();
    });
}

function cambiarFormatoArte() {
    ajustarEscalaWrapperCalendario();
    renderizarCalendario();
    actualizarTamanoTarjetas(); // Re-acomoda la cascada según el nuevo formato
}

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

// -------------------------------------------------------------------
// FUNCIONES DE LOCAL STORAGE Y TAMAÑO RESPONSIVO (GRID CASCADA)
// -------------------------------------------------------------------

function cargarTextosLocales() {
    const tTitulo = document.getElementById('calInputTitulo');
    const tNota = document.getElementById('calInputNota');
    const tPhone = document.getElementById('calInputPhone');
    const tSinpe = document.getElementById('calInputSinpe');
    const sSize = document.getElementById('calSliderCardSize');
    const tPrecio = document.getElementById('calTogglePrecio');

    // Recupera la data o usa valores por defecto
    if(tTitulo) tTitulo.value = localStorage.getItem('cal_titulo') || 'CALENDARIO DE AVENTURAS';
    if(tNota) tNota.value = localStorage.getItem('cal_nota') || '';
    if(tPhone) tPhone.value = localStorage.getItem('cal_phone') || '8622-7500';
    if(tSinpe) tSinpe.value = localStorage.getItem('cal_sinpe') || '';
    if(sSize) sSize.value = localStorage.getItem('cal_card_size') || '1';
    
    // Recuperar toggle de precios (Por defecto activado si no existe)
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

    // GUARDADO LOCAL (Sobrevive a F5 sin tocar la BD)
    localStorage.setItem('cal_titulo', inTitulo);
    localStorage.setItem('cal_nota', inNota);
    localStorage.setItem('cal_phone', inPhone);
    localStorage.setItem('cal_sinpe', inSinpe);
    if(tPrecio) localStorage.setItem('cal_show_price', tPrecio.checked);

    if(tituloEl) tituloEl.innerText = inTitulo;
    if(notaEl) notaEl.innerText = inNota;
    
    // Armado inteligente del Botón Píldora
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
        // Aseguramos que es un CSS Grid
        grid.style.display = 'grid';
        grid.style.gap = '1.5rem';
        
        // Magia Relativa: Al cambiar el font-size raíz de la Grid, 
        // TODOS los elementos internos (diseñados en 'em') crecen o se achican perfectos.
        grid.style.fontSize = `${scale}rem`;
        
        // Cascading Grid: Calculamos la anchura mínima de ruptura
        const baseMinW = formato === 'horizontal' ? 380 : 300;
        grid.style.gridTemplateColumns = `repeat(auto-fit, minmax(calc(${baseMinW}px * ${scale}), 1fr))`;
    }
}

function renderizarCalendario() {
    const filtroEl = document.getElementById('calFiltroCategoria');
    const subTituloEl = document.getElementById('cal-flyer-subtitulo');
    const grid = document.getElementById('cal-grid-meses');
    const tPrecio = document.getElementById('calTogglePrecio');
    
    if(!filtroEl || !subTituloEl || !grid) return;
    
    const categoriaSeleccionada = filtroEl.value;
    const mostrarPrecios = tPrecio ? tPrecio.checked : true;
    
    subTituloEl.innerText = categoriaSeleccionada === 'Todas' ? 'Todas las Actividades' : `Especial: ${categoriaSeleccionada}`;

    const filtrados = eventosDBCalendario.filter(ev => categoriaSeleccionada === 'Todas' || ev.categoria === categoriaSeleccionada);

    const agrupados = {};
    filtrados.forEach(ev => {
        if (!agrupados[ev.mes]) agrupados[ev.mes] = [];
        agrupados[ev.mes].push(ev);
    });

    grid.innerHTML = '';

    for (const [mes, eventos] of Object.entries(agrupados)) {
        // En lugar de Pixeles o Rem, usamos 'em' en TODOS los tamaños y paddings de las tarjetas.
        // Así dependen 100% de la barra de escala que controla el Grid.
        let eventosHTML = eventos.map(ev => {
            // HTML para el precio condicional
            let precioHtml = mostrarPrecios ? ` <span style="margin-left: 0.5em;"><i class="bi bi-tag-fill text-orange"></i> ${ev.precio}</span>` : '';
            
            return `
            <div class="evento-item d-flex justify-content-between align-items-center mb-2" style="background: rgba(255, 255, 255, 0.05); border-left: 0.3em solid #ff8c00; padding: 0.6em 0.8em; border-radius: 0 0.5em 0.5em 0;">
                <div class="pe-2">
                    <h4 class="fw-bold mb-0 text-white" style="font-size: 1.1em;">${ev.nombre}</h4>
                    <small class="text-white-50" style="font-size: 0.85em;">
                        <i class="bi bi-geo-alt-fill text-orange"></i> Dif: ${ev.dificultad} 
                        ${precioHtml}
                    </small>
                </div>
                <div class="bg-darker text-orange fw-bold rounded border border-secondary" style="font-size: 1.2em; padding: 0.3em 0.6em; white-space: nowrap;">
                    ${ev.dia}
                </div>
            </div>
            `;
        }).join('');

        // Se inyectan las tarjetas puras, la CSS Grid se encarga de ordenarlas y envolverlas en cascada.
        grid.innerHTML += `
            <div style="background: rgba(30, 30, 30, 0.7); border: 1px solid rgba(255, 140, 0, 0.3); border-radius: 1em; padding: 1.2em; display: flex; flex-direction: column; height: 100%;">
                <h2 style="color: #ff8c00; border-bottom: 0.15em solid #ff8c00; padding-bottom: 0.3em; margin-bottom: 0.8em; font-weight: 900; text-transform: uppercase; letter-spacing: 0.1em; font-size: 1.5em;">${mes}</h2>
                <div class="eventos-lista">
                    ${eventosHTML}
                </div>
            </div>
        `;
    }
    
    // Invocamos el redimensionamiento después de inyectar los elementos
    actualizarTamanoTarjetas();
}

function descargarArteCalendario() {
    if(typeof html2canvas === 'undefined') {
        alert("La librería de captura aún está cargando. Por favor, intenta de nuevo en unos segundos.");
        return;
    }
    
    if(!calLienzoArte || !calWrapper) return;

    calLienzoArte.style.transform = 'scale(1)';
    calWrapper.style.overflow = 'visible';
    
    const btnDescarga = document.querySelector('#calendarioModal .btn-primary');
    let btnOriginalText = 'Descargar';
    if(btnDescarga) {
        btnOriginalText = btnDescarga.innerHTML;
        btnDescarga.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Generando Alta Resolución...';
        btnDescarga.disabled = true;
    }
    
    html2canvas(calLienzoArte, { 
        scale: 1,
        useCORS: true,
        allowTaint: true,
        backgroundColor: null,
        logging: false,
        width: calLienzoArte.offsetWidth,
        height: calLienzoArte.offsetHeight
    }).then(canvas => {
        const link = document.createElement('a');
        const fechaTxt = new Date().toISOString().slice(0,10);
        const fSelect = document.getElementById('calFormatoArte');
        const formato = fSelect ? fSelect.value : 'horizontal';
        const cSelect = document.getElementById('calFiltroCategoria');
        const cate = cSelect ? cSelect.value : 'Todas';
        
        link.download = `Arte_${formato}_${cate}_${fechaTxt}.png`;
        link.href = canvas.toDataURL('image/png', 1.0);
        link.click();
        
        calWrapper.style.overflow = 'hidden';
        ajustarEscalaWrapperCalendario();
        if(btnDescarga) {
            btnDescarga.innerHTML = btnOriginalText;
            btnDescarga.disabled = false;
        }
    }).catch(err => {
        console.error("Error capturando lienzo:", err);
        alert("Hubo un error de lectura de imagen. Sube una foto de tu galería e inténtalo de nuevo.");
        calWrapper.style.overflow = 'hidden';
        ajustarEscalaWrapperCalendario();
        if(btnDescarga) {
            btnDescarga.innerHTML = btnOriginalText;
            btnDescarga.disabled = false;
        }
    });
}