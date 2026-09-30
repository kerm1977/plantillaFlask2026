// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
// Mantener presionado el enlace "Mis puntos" del footer abre un modal para
// compartir por WhatsApp (mensaje personalizable + enlace). Un toque normal
// (clic corto) sigue navegando a la página como siempre.

async function _footerShareCopyText(text) {
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
  } catch (e) { /* copiar es una mejora opcional, no bloquea el envío */ }
}

let shareMisPuntosModalInstance = null;

function abrirModalCompartirMisPuntos(enlace) {
  const modalEl = document.getElementById('shareMisPuntosModal');
  if (!modalEl) return;
  if (!shareMisPuntosModalInstance) shareMisPuntosModalInstance = new bootstrap.Modal(modalEl);
  document.getElementById('shareMisPuntosEnlace').textContent = enlace;
  modalEl.dataset.enlace = enlace;
  shareMisPuntosModalInstance.show();
}

async function compartirMisPuntosPorWhatsApp() {
  const modalEl = document.getElementById('shareMisPuntosModal');
  const mensajeInput = document.getElementById('shareMisPuntosMensaje');
  const enlace = (modalEl && modalEl.dataset.enlace) || (window.location.origin + '/mis-puntos');
  const texto = (mensajeInput.value || '').trim();
  const fullText = texto ? (texto + '\n\n' + enlace) : enlace;
  await _footerShareCopyText(fullText);
  window.open('https://wa.me/?text=' + encodeURIComponent(fullText), '_blank');
  if (shareMisPuntosModalInstance) shareMisPuntosModalInstance.hide();
}

function setupFooterMisPuntosLongPress() {
  const links = document.querySelectorAll('.ft-mis-puntos-link');
  if (!links.length) return;
  links.forEach(function (link) {
    let timer = null;
    let triggered = false;
    const start = () => {
      triggered = false;
      timer = setTimeout(() => {
        triggered = true;
        const enlace = link.href;
        abrirModalCompartirMisPuntos(enlace);
        link.style.opacity = '0.6';
        setTimeout(() => { link.style.opacity = ''; }, 150);
      }, 600);
    };
    const cancel = () => { if (timer) { clearTimeout(timer); timer = null; } };
    link.addEventListener('mousedown', start);
    link.addEventListener('touchstart', start, { passive: true });
    link.addEventListener('mouseup', cancel);
    link.addEventListener('mouseleave', cancel);
    link.addEventListener('touchend', cancel);
    link.addEventListener('touchcancel', cancel);
    link.addEventListener('contextmenu', (e) => e.preventDefault());
    link.addEventListener('click', function (e) {
      if (triggered) { e.preventDefault(); triggered = false; }
    });
  });
}

document.addEventListener('DOMContentLoaded', setupFooterMisPuntosLongPress);
