// ==========================================
// CONFIGURACIÓN Y ESTADO GLOBAL
// ==========================================

let eventosDBCalendario = [];
let calBgImageObj = new Image();

const fallbackImage = window.APP_VARS ? window.APP_VARS.emptyImageBase64 : "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=";
calBgImageObj.src = typeof cleanImage !== 'undefined' ? cleanImage : fallbackImage;
calBgImageObj.onload = renderizarFondoCanvas;

const calWrapper = document.getElementById('flyer-wrapper');
const calLienzoArte = document.getElementById('lienzo-arte');
const modalCal = document.getElementById('calendarioModal');
