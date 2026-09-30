// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
function _abreviaturaProvincia(nombre) {
    const limpio = (nombre || 'XX').toString().toUpperCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^A-Z0-9\s]/g, '').trim();
    const partes = limpio.split(/\s+/).filter(p => p);
    if(partes.length >= 2) {
        return partes.slice(0, 2).map(p => p[0]).join('');
    }
    return (partes[0] || 'XX').substring(0, 2);
}

function _prepararCodigos() {
    const indices = {};
    lugaresData.forEach(l => {
        const provincia = l.provincia || 'Sin provincia';
        if(!indices[provincia]) indices[provincia] = 0;
        indices[provincia]++;
        l.codigo = _abreviaturaProvincia(provincia) + '-' + String(indices[provincia]).padStart(2, '0');
    });
}

function _textoLugar(l, prefijo = '') {
    const precio = l.precio || '';
    const moneda = l.moneda == 'colones' ? '₡' : '$';
    const tipo = l.tipo_caminata || 'circular';
    const duracion = l.duracion == '1_dia' ? '1 dia' : 'Multiples dias';
    let texto = `- Nombre: ${l.nombre}\n`;
    if(prefijo) texto += `- Codigo: ${prefijo}\n`;
    texto += `- Provincia: ${l.provincia || 'Pendiente'}\n`;
    texto += `- Duracion: ${duracion}\n`;
    texto += `- Tipo: ${tipo == 'lineal' ? 'Lineal' : 'Circular'}\n`;
    texto += `- Salida: ${l.fecha_ida || 'Pendiente'}\n`;
    if(l.duracion === 'multiples_dias') {
        texto += `- Regreso: ${l.fecha_regreso || 'Pendiente'}\n`;
    }
    texto += `- Hora: ${l.hora || 'Pendiente'}\n`;
    if(precio) texto += `- Precio: ${moneda}${precio}\n`;
    if(tipo === 'lineal') {
        texto += `- Mapa de inicio: ${l.maps_ida || 'Pendiente'}\n`;
        texto += `- Mapa de recogida: ${l.maps_regreso || 'Pendiente'}\n`;
    } else {
        texto += `- Mapa: ${l.maps_ida || 'Pendiente'}\n`;
    }
    return texto;
}

function _cabeceraWhatsApp() {
    let texto = '';
    if(cotizadorTitulo) texto += `*${cotizadorTitulo}*\n\n`;
    if(cotizadorNombre) texto += `*${cotizadorNombre}*\n`;
    if(cotizadorDescripcion) texto += `${cotizadorDescripcion}\n\n`;
    return texto;
}

function exportarWhatsApp() {
    // Agrupar lugares por provincia
    const grupos = {};
    lugaresData.forEach(l => {
        const provincia = l.provincia || 'Sin provincia';
        if(!grupos[provincia]) grupos[provincia] = [];
        grupos[provincia].push(l);
    });
    
    let texto = _cabeceraWhatsApp();
    
    for(const [provincia, lugares] of Object.entries(grupos)) {
        texto += `*${provincia}*\n`;
        texto += '--------------------\n';
        lugares.forEach((l, i) => {
            const prefijo = _abreviaturaProvincia(provincia) + '-' + String(i + 1).padStart(2, '0');
            texto += _textoLugar(l, prefijo);
            texto += '\n';
        });
    }
    
    // Agregar enlace público al final
    const enlacePublico = window.location.href;
    texto += `\nEnlace publico para ver el detalle completo:\n${enlacePublico}`;
    
    document.getElementById('whatsappText').value = texto;
    whatsappModal.show();
}

function exportarLugarWhatsApp(id) {
    const l = lugaresData.find(x => x.id === id);
    if(!l) return;
    const provincia = l.provincia || 'Sin provincia';
    const index = lugaresData.filter(x => (x.provincia || 'Sin provincia') === provincia).findIndex(x => x.id === l.id) + 1;
    const prefijo = _abreviaturaProvincia(provincia) + '-' + String(index).padStart(2, '0');
    let texto = _cabeceraWhatsApp();
    texto += `*${l.nombre}*\n`;
    texto += '--------------------\n';
    texto += _textoLugar(l, prefijo);
    texto += '\nEnlace publico para ver el detalle completo:\n' + window.location.href;
    document.getElementById('whatsappText').value = texto;
    whatsappModal.show();
}

function exportarProvinciaWhatsApp(provincia) {
    const filtrados = lugaresData.filter(l => (l.provincia || 'Sin provincia') === provincia);
    if(filtrados.length === 0) return;
    let texto = _cabeceraWhatsApp();
    texto += `*${provincia}*\n`;
    texto += '--------------------\n';
    filtrados.forEach((l, i) => {
        const prefijo = _abreviaturaProvincia(provincia) + '-' + String(i + 1).padStart(2, '0');
        texto += _textoLugar(l, prefijo);
        texto += '\n';
    });
    texto += '\nEnlace publico para ver el detalle completo:\n' + window.location.href;
    document.getElementById('whatsappText').value = texto;
    whatsappModal.show();
}
function copiarWhatsApp() {
    const texto = document.getElementById('whatsappText');
    texto.select();
    document.execCommand('copy');
    alert('Texto copiado al portapapeles');
}
function enviarWhatsApp() {
    const texto = encodeURIComponent(document.getElementById('whatsappText').value);
    window.open(`https://wa.me/?text=${texto}`, '_blank');
}
