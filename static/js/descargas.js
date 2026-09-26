/* ══ BLINDADO — DESCARGAS ══
   Pega el enlace, elige formato y descarga. Independiente. */

let _dlJob = null;
let _dlTimer = null;

function _dlMsg(txt, color) {
  const m = document.getElementById('dlMsg');
  m.textContent = txt;
  m.style.color = color || '#212529';
}

async function dlPegar() {
  try {
    const t = await navigator.clipboard.readText();
    if (t) document.getElementById('dlUrl').value = t.trim();
  } catch (e) {
    document.getElementById('dlUrl').focus();
  }
}

async function dlIniciar() {
  const url = document.getElementById('dlUrl').value.trim();
  const fmt = document.querySelector('input[name="dlFmt"]:checked');
  if (!url) { alert('Pegá el enlace del video primero.'); return; }
  const est = document.getElementById('dlEstado');
  const spn = document.getElementById('dlSpinner');
  const lnk = document.getElementById('dlArchivo');
  document.getElementById('dlBtn').disabled = true;
  est.style.display = 'block';
  spn.style.display = 'inline-block';
  lnk.style.display = 'none';
  _dlMsg('Iniciando…');
  try {
    const r = await fetch('/api/descargas/iniciar', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({url: url, formato: fmt ? fmt.value : 'mp4'})
    });
    const d = await r.json();
    if (!d.ok) throw new Error(d.error || 'Error al iniciar');
    _dlJob = d.job;
    _dlPoll();
  } catch (e) {
    spn.style.display = 'none';
    document.getElementById('dlBtn').disabled = false;
    _dlMsg(e.message, '#dc3545');
  }
}

async function _dlPoll() {
  try {
    const r = await fetch('/api/descargas/estado/' + _dlJob);
    const d = await r.json();
    if (!d.ok) throw new Error(d.error || 'Error');
    _dlMsg(d.msg, d.status === 'error' ? '#dc3545' : '#212529');
    if (d.status === 'listo') {
      document.getElementById('dlSpinner').style.display = 'none';
      document.getElementById('dlBtn').disabled = false;
      const lnk = document.getElementById('dlArchivo');
      lnk.href = '/api/descargas/archivo/' + _dlJob;
      lnk.style.display = 'inline-block';
      return;
    }
    if (d.status === 'error') {
      document.getElementById('dlSpinner').style.display = 'none';
      document.getElementById('dlBtn').disabled = false;
      return;
    }
  } catch (e) {
    _dlMsg(e.message, '#dc3545');
  }
  _dlTimer = setTimeout(_dlPoll, 1500);
}
