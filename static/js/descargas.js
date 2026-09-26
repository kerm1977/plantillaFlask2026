/* ══ BLINDADO — DESCARGAS ══
   Multi-enlace, cola con concurrencia, barras de progreso,
   opciones avanzadas y actualización de yt-dlp. */

let _dlLote = null;
let _dlTimer = null;
let _dlUpTimer = null;

async function dlPegar() {
  try {
    const t = await navigator.clipboard.readText();
    const ta = document.getElementById('dlUrl');
    if (t) ta.value = (ta.value ? ta.value + '\n' : '') + t.trim();
  } catch (e) {
    document.getElementById('dlUrl').focus();
  }
}

function _dlCard(job) {
  const pct = job.pct || 0;
  const color = job.status === 'error' ? '#dc3545'
    : job.status === 'listo' ? '#198754' : '#f58c1f';
  return '<div class="mb-3 p-3 rounded-4 shadow-sm" ' +
    'style="background:rgba(255,255,255,0.6);">' +
    '<p class="small fw-bold text-dark mb-1 text-break">' +
    '<i class="bi bi-link-45deg"></i> ' + job.url + '</p>' +
    '<div class="progress" style="height:0.7rem;border-radius:1rem;">' +
    '<div class="progress-bar" role="progressbar" ' +
    'style="width:' + pct + '%;background:' + color + ';"></div></div>' +
    '<div class="d-flex justify-content-between align-items-center mt-1">' +
    '<span class="small" style="color:' + color + ';">' + job.msg + '</span>' +
    (job.status === 'listo'
      ? '<a class="btn btn-sm btn-success rounded-pill px-3 fw-bold" ' +
        'href="/api/descargas/archivo/' + job.id + '">' +
        '<i class="bi bi-save me-1"></i>Guardar</a>'
      : '<span class="small fw-bold" style="color:' + color + ';">' +
        pct + '%</span>') +
    '</div></div>';
}

async function _dlPoll() {
  if (!_dlLote) return;
  try {
    const r = await fetch('/api/descargas/lote/' + _dlLote,
                          {cache: 'no-store'});
    const d = await r.json();
    if (!d.ok) return;
    const lista = document.getElementById('dlLista');
    lista.innerHTML = d.jobs.map(_dlCard).join('');
    const activo = d.jobs.some(j =>
      j.status === 'pendiente' || j.status === 'descargando' ||
      j.status === 'convirtiendo');
    if (activo) {
      _dlTimer = setTimeout(_dlPoll, 1200);
    } else {
      document.getElementById('dlBtn').disabled = false;
      _dlLote = null;
    }
  } catch (e) {
    _dlTimer = setTimeout(_dlPoll, 3000);  // reintenta si la red falla
  }
}

async function dlIniciar() {
  const urls = document.getElementById('dlUrl').value
    .split('\n').map(u => u.trim()).filter(u => u);
  if (!urls.length) { alert('Pegá al menos un enlace.'); return; }
  const fmt = document.querySelector('input[name="dlFmt"]:checked');
  document.getElementById('dlBtn').disabled = true;
  try {
    const r = await fetch('/api/descargas/iniciar', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        urls: urls,
        formato: fmt ? fmt.value : 'mp4',
        extra: document.getElementById('dlExtra').value,
        max_par: document.getElementById('dlMaxPar').value
      })
    });
    const d = await r.json();
    if (!d.ok) throw new Error(d.error || 'Error al iniciar');
    _dlLote = d.lote;
    _dlPoll();
  } catch (e) {
    document.getElementById('dlBtn').disabled = false;
    alert(e.message);
  }
}

/* ── Actualización de yt-dlp ── */
async function dlCheckVersion() {
  const el = document.getElementById('dlVerDisp');
  el.textContent = 'Consultando PyPI…';
  try {
    const r = await fetch('/api/descargas/version', {cache: 'no-store'});
    const d = await r.json();
    if (!d.ok || !d.disponible) {
      el.textContent = d.disponible ? '' : 'Sin conexión a PyPI.';
      return;
    }
    el.textContent = d.disponible === d.actual
      ? 'Ya tenés la última versión (' + d.actual + ').'
      : 'Hay una nueva versión disponible: ' + d.disponible;
  } catch (e) {
    el.textContent = 'No se pudo consultar.';
  }
}

async function dlActualizar() {
  const el = document.getElementById('dlUpMsg');
  el.textContent = 'Actualizando yt-dlp…';
  try {
    const r = await fetch('/api/descargas/actualizar', {method: 'POST'});
    const d = await r.json();
    if (!d.ok) throw new Error(d.error);
    _dlUpTimer = setInterval(async () => {
      try {
        const s = await fetch('/api/descargas/update-estado',
                              {cache: 'no-store'});
        const u = await s.json();
        el.textContent = u.running ? 'Actualizando…' : (u.salida || '');
        if (!u.running) {
          clearInterval(_dlUpTimer);
          if (u.version) document.getElementById('dlVer').textContent = u.version;
        }
      } catch (e) { clearInterval(_dlUpTimer); }
    }, 2000);
  } catch (e) {
    el.textContent = 'No se pudo actualizar: ' + e.message;
  }
}
