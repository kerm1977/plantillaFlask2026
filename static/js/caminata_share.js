// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
  async function copyTextToClipboard(text) {
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
      }
      alert('Enlace copiado al portapapeles');
    } catch(e) {
      alert('No se pudo copiar el enlace');
    }
  }

  let shareCaminataModalInstance = null;

  function abrirModalCompartirCaminata() {
    const modalEl = document.getElementById('shareCaminataModal');
    if (!modalEl) return;
    if (!shareCaminataModalInstance) shareCaminataModalInstance = new bootstrap.Modal(modalEl);
    const enlace = window.location.origin + window.location.pathname + '?share=1';
    document.getElementById('shareCaminataEnlace').textContent = enlace;
    shareCaminataModalInstance.show();
  }

  async function compartirCaminataPorWhatsApp() {
    const mensajeInput = document.getElementById('shareCaminataMensaje');
    const enlace = window.location.origin + window.location.pathname + '?share=1';
    const texto = (mensajeInput.value || '').trim();
    const fullText = texto ? (texto + '\n\n' + enlace) : enlace;
    await copyTextToClipboard(fullText);
    window.open('https://wa.me/?text=' + encodeURIComponent(fullText), '_blank');
    if (shareCaminataModalInstance) shareCaminataModalInstance.hide();
  }

  function setupCaminataDetalleLongPress() {
    const title = document.getElementById('caminataDetalleTitle');
    if (!title) return;
    let timer = null;
    const start = (e) => {
      timer = setTimeout(() => {
        abrirModalCompartirCaminata();
        title.style.transform = 'scale(0.98)';
        setTimeout(() => { title.style.transform = ''; }, 150);
      }, 600);
    };
    const cancel = () => { if (timer) { clearTimeout(timer); timer = null; } };
    title.addEventListener('mousedown', start);
    title.addEventListener('touchstart', start, {passive: true});
    title.addEventListener('mouseup', cancel);
    title.addEventListener('mouseleave', cancel);
    title.addEventListener('touchend', cancel);
    title.addEventListener('touchcancel', cancel);
    title.addEventListener('contextmenu', (e) => e.preventDefault());
  }

  document.addEventListener('DOMContentLoaded', function() {
    setupCaminataDetalleLongPress();
    Wysiwyg.setupUploadListeners('caminataPreview', `/api/caminatas-2027/${CAMINATA_ID}/upload-image`, () => caminataSave(true));
    const preview = document.getElementById('caminataPreview');
    if (preview) {
      originalItinerario = caminataContenidoLimpio();
      iniciarHistorialCaminata();
      const observer = new MutationObserver(() => {
        if (!_caminataMarcandoSeleccion && document.activeElement === preview) guardarCaminata();
      });
      observer.observe(preview, { childList: true, subtree: true, characterData: true });
      preview.addEventListener('input', function(event) {
        if (event.inputType === 'insertParagraph' || event.inputType === 'insertLineBreak' || (event.inputType === 'insertText' && /\s/.test(event.data || ''))) {
          caminataConvertirEnlaces();
        }
        guardarCaminata();
      });
      preview.addEventListener('paste', function() {
        setTimeout(caminataConvertirEnlaces, 0);
      });
      preview.addEventListener('mouseup', caminataAgregarRangoMultiseleccion);
      preview.addEventListener('touchend', function() {
        if (_caminataMultiseleccionActiva) setTimeout(caminataAgregarRangoMultiseleccion, 50);
      });
      preview.addEventListener('click', function(event) {
        if (!_caminataMultiseleccionActiva) return;
        const media = event.target.closest('img, video, .caminata-embed');
        if (media && preview.contains(media)) {
          event.preventDefault();
          media.dataset.caminataMultiselect = media.dataset.caminataMultiselect === 'true' ? 'false' : 'true';
          if (media.dataset.caminataMultiselect === 'false') media.removeAttribute('data-caminata-multiselect');
          actualizarEstadoMultiseleccion(`${caminataElementosMultiseleccionados().length} elemento(s) agregado(s). Seleccioná otro o aplicá una acción.`);
          actualizarBotonesAlineacion(false);
        }
      });
      preview.addEventListener('keydown', function(event) {
        const modifier = event.ctrlKey || event.metaKey;
        if (!modifier || event.altKey || event.key.toLowerCase() !== 'z') return;
        event.preventDefault();
        navegarHistorialCaminata(event.shiftKey ? 1 : -1);
      });
      preview.addEventListener('blur', function() {
        const sel = window.getSelection();
        if (sel && sel.rangeCount && !sel.getRangeAt(0).collapsed) {
          const r = sel.getRangeAt(0);
          if (preview.contains(r.commonAncestorContainer)) caminataRange = r.cloneRange();
        }
        caminataConvertirEnlaces();
        guardarCaminataAhora();
      });
      document.addEventListener('visibilitychange', function() {
        if (document.visibilityState === 'hidden') guardarCaminataAhora();
      });
      preview.addEventListener('contextmenu', function(e) {
        let node = e.target;
        while (node && node.id !== 'caminataPreview') {
          if (node.tagName === 'VIDEO' || (node.classList && node.classList.contains('caminata-embed'))) {
            e.preventDefault();
            _videoSeleccionadoContexto = node;
            const menu = crearMenuContextualVideo();
            menu.style.display = 'block';
            menu.style.left = (e.clientX + 8) + 'px';
            menu.style.top = (e.clientY + 8) + 'px';
            return;
          }
          node = node.parentElement;
        }
      });
    }
  });

  async function caminataExport(format) {
    if (format === 'pdf') {
      window.print();
      return;
    }
    const preview = document.getElementById('caminataPreview');
    if (typeof html2canvas === 'undefined') {
      alert('Espere a que cargue html2canvas o recargue la pÃ¡gina.');
      return;
    }
    try {
      const canvas = await html2canvas(preview, {scale: 2, useCORS: true});
      if (format === 'png') {
        const link = document.createElement('a');
        link.download = `caminata_${CAMINATA_ID}_${CAMINATA_NOMBRE_FILE}.png`;
        link.href = canvas.toDataURL('image/png');
        link.click();
      } else if (format === 'jpg') {
        const link = document.createElement('a');
        link.download = `caminata_${CAMINATA_ID}_${CAMINATA_NOMBRE_FILE}.jpg`;
        link.href = canvas.toDataURL('image/jpeg', 0.9);
        link.click();
      } else if (format === 'pdf') {
        if (typeof jspdf === 'undefined' || !jspdf.jsPDF) {
          alert('Espere a que cargue jsPDF o recargue la página.');
          return;
        }
        const { jsPDF } = jspdf;
        const pdf = new jsPDF('p', 'mm', 'a4');
        const imgData = canvas.toDataURL('image/png');
        const pdfWidth = pdf.internal.pageSize.getWidth();
        const pdfHeight = (canvas.height * pdfWidth) / canvas.width;
        const pageHeight = pdf.internal.pageSize.getHeight();
        let heightLeft = pdfHeight;
        let position = 0;
        pdf.addImage(imgData, 'PNG', 0, position, pdfWidth, pdfHeight);
        heightLeft -= pageHeight;
        while (heightLeft > 0) {
          position = heightLeft - pdfHeight;
          pdf.addPage();
          pdf.addImage(imgData, 'PNG', 0, position, pdfWidth, pdfHeight);
          heightLeft -= pageHeight;
        }
        pdf.save(`caminata_${CAMINATA_ID}_${CAMINATA_NOMBRE_FILE}.pdf`);
      }
    } catch(e) {
      console.error(e);
      alert('Error al exportar');
    }
  }

  function reservarCaminataWhatsApp() {
    const nombreEvento = CAMINATA_NOMBRE;
    const precio = CAMINATA_PRECIO_TXT;
    const sinpeString = CAMINATA_SINPE;

    let numeroAdmin = "50686529837";
    if(sinpeString.includes("87984232")) numeroAdmin = "50687984232";
    if(sinpeString.includes("86227500")) numeroAdmin = "50686227500";

    const mensaje = `¡Hola! Me gustaría reservar un cupo para el evento *${nombreEvento}* (${precio}). ¿Aún hay espacio disponible?`;
    window.open(`https://api.whatsapp.com/send?phone=${numeroAdmin}&text=${encodeURIComponent(mensaje)}`, '_blank');
  }

