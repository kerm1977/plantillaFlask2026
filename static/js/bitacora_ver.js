/* ══ BLINDADO — BITÁCORA — vista de entrada: paginación + lightbox ══ */

let btPagActual = 0;

/* Cambia de página sin recargar y marca el número activo */
function btVerPagina(i) {
  const paginas = document.querySelectorAll('.bt-pagina');
  if (i < 0 || i >= paginas.length) return;
  btPagActual = i;
  paginas.forEach(d => {
    d.style.display = (d.dataset.pag === String(i)) ? 'block' : 'none';
  });
  document.querySelectorAll('.bt-pg').forEach(b => {
    b.closest('.page-item').classList.toggle('active',
      b.dataset.pg === String(i));
  });
  const primero = document.querySelector('.bt-pagina');
  if (primero) primero.scrollIntoView({behavior: 'smooth', block: 'start'});
}

/* Anterior / Siguiente */
function btVerPaginaRel(dir) {
  btVerPagina(btPagActual + dir);
}

/* Lightbox: clic en imagen del contenido → vista completa + descargar */
document.addEventListener('DOMContentLoaded', () => {
  const modal = document.getElementById('btImgModal');
  if (modal) {
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
  }
  btVerPagina(0);
});
