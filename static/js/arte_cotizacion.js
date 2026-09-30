// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
let cotizacionesData = [];
let cotizadorInfo = {};

// Cargar datos del cotizador
async function cargarCotizacion() {
    try {
        const res = await fetch('/cotizadores/lista');
        const text = await res.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(text, 'text/html');
        
        // Extraer datos del cotizador desde el HTML
        const nombreElement = doc.getElementById('nombre');
        const tituloElement = doc.getElementById('titulo');
        const descripcionElement = doc.getElementById('descripcion');
        
        if(nombreElement) {
            cotizadorInfo.nombre = nombreElement.value;
            cotizadorInfo.titulo = tituloElement ? tituloElement.value : '';
            cotizadorInfo.descripcion = descripcionElement ? descripcionElement.value : '';
        }
        
        // Actualizar título si existe
        if(cotizadorInfo.titulo) {
            document.getElementById('inputTitulo').value = cotizadorInfo.titulo;
            actualizarTextos();
        }
        
        // Extraer lugares del script embedded
        const scriptElements = doc.querySelectorAll('script');
        scriptElements.forEach(script => {
            const content = script.textContent;
            if(content.includes('lugares.push')) {
                // Parsear los lugares del script
                const matches = content.matchAll(/lugares\.push\(\{([^}]+)\}\)/g);
                cotizacionesData = [];
                for(const match of matches) {
                    try {
                        const lugarStr = '{' + match[1] + '}';
                        const lugar = eval('(' + lugarStr + ')');
                        cotizacionesData.push(lugar);
                    } catch(e) {
                        console.error('Error parsing lugar:', e);
                    }
                }
            }
        });
        
        renderizarCotizacion();
        
    } catch(e) {
        console.error('Error cargando cotización:', e);
        renderizarCotizacion();
    }
}

function renderizarCotizacion() {
    const filtro = document.getElementById('filtroProvincia').value;
    const subtitulo = filtro === 'Todas' ? 'Todas las Provincias' : filtro;
    document.getElementById('flyer-subtitulo').textContent = subtitulo;
    
    // Usar datos reales del cotizador o datos de ejemplo
    const lugares = cotizacionesData.length > 0 ? cotizacionesData : [
        {nombre: 'Volcán Barva', provincia: 'Heredia', precio: 15000, moneda: 'colones'},
        {nombre: 'Cerro Chiripó', provincia: 'Cartago', precio: 20000, moneda: 'colones'},
        {nombre: 'Playa Manuel Antonio', provincia: 'Puntarenas', precio: 25000, moneda: 'colones'},
        {nombre: 'Volcán Arenal', provincia: 'Alajuela', precio: 18000, moneda: 'colones'},
        {nombre: 'Monteverde', provincia: 'Puntarenas', precio: 22000, moneda: 'colones'},
        {nombre: 'Irazú', provincia: 'Cartago', precio: 12000, moneda: 'colones'}
    ];
    
    const lugaresFiltrados = filtro === 'Todas' ? lugares : lugares.filter(l => l.provincia === filtro);
    
    const html = lugaresFiltrados.map(l => {
        const moneda = l.moneda || 'colones';
        const precio = l.precio || 0;
        return `
        <div class="col-6 col-md-4">
            <div class="lugar-card">
                <div class="provincia">${l.provincia || 'Sin provincia'}</div>
                <h5>${l.nombre}</h5>
                <div class="precio">${moneda === 'colones' ? '₡' : '$'}${Number(precio).toLocaleString(undefined, {maximumFractionDigits: 0})}</div>
            </div>
        </div>
    `;
    }).join('');
    
    document.getElementById('grid-lugares').innerHTML = html;
}

function actualizarTextos() {
    const titulo = document.getElementById('inputTitulo').value;
    document.getElementById('flyer-titulo').textContent = titulo;
}

// Controles de imagen
document.getElementById('bgImageUpload').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if(file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('flyer-bg-img').src = e.target.result;
        };
        reader.readAsDataURL(file);
    }
});

document.getElementById('sliderScale').addEventListener('input', function(e) {
    const scale = e.target.value;
    document.getElementById('valScale').textContent = scale;
    document.getElementById('flyer-bg-img').style.transform = `scale(${scale}) translateX(${document.getElementById('sliderX').value}px) translateY(${document.getElementById('sliderY').value}px)`;
});

document.getElementById('sliderX').addEventListener('input', function(e) {
    const x = e.target.value;
    document.getElementById('valX').textContent = x;
    const scale = document.getElementById('sliderScale').value;
    document.getElementById('flyer-bg-img').style.transform = `scale(${scale}) translateX(${x}px) translateY(${document.getElementById('sliderY').value}px)`;
});

document.getElementById('sliderY').addEventListener('input', function(e) {
    const y = e.target.value;
    document.getElementById('valY').textContent = y;
    const scale = document.getElementById('sliderScale').value;
    document.getElementById('flyer-bg-img').style.transform = `scale(${scale}) translateX(${document.getElementById('sliderX').value}px) translateY(${y}px)`;
});

function descargarArte() {
    const lienzo = document.getElementById('lienzo-16-9');
    html2canvas(lienzo, {
        scale: 2,
        useCORS: true,
        allowTaint: true
    }).then(canvas => {
        const link = document.createElement('a');
        link.download = 'arte-cotizacion.png';
        link.href = canvas.toDataURL('image/png');
        link.click();
    });
}

// Inicializar
document.addEventListener('DOMContentLoaded', function() {
    cargarCotizacion();
});
