/* ══ BITÁCORA — vista de entrada: páginas + lightbox ══ */

/* Cambia de página sin recargar */
function btVerPagina(i) {
  document.querySelectorAll('.bt-pagina').forEach(d => {
    d.style.display = (d.dataset.pag === String(i)) ? 'block' : 'none';
  });
}

/* Lightbox: clic en imagen del contenido → vista completa + descargar */
document.addEventListener('DOMContentLoaded', () => {
  const modal = document.getElementById('btImgModal');
  if (!modal) return;
  document.querySelectorAll('.bt-contenido img').forEach(img => {
    img.style.cursor = 'zoom-in';
    img.addEventListener('click', () => {
      document.getElementById('btImgFull').src = img.src;
      const dl = document.getElementById('btImgDownload');
      dl.href = img.src;
      dl.setAttribute('download', img.src.split('/').pop() || 'imagen');
      bootstrap.Modal.getOrCreateInstance(modal).show();
    });
  });
});
