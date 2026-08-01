
// ✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️
// ✂️ INICIO DE CORTE: calendario_export.js ✂️
// ✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️

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

// ✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️
// ✂️ FIN DE CORTE: calendario_export.js ✂️
// ✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️