/* ══ BITÁCORA — gestión de páginas del editor ══
   Dropdown con ↑↓ y drag&drop; numeración automática;
   eliminar con modal de doble confirmación. */

let btPages = [];       // HTML de cada página, en orden
let btPageIdx = 0;      // página que se está editando
let btDragIdx = null;   // índice arrastrado en el dropdown
let btDelPageIdx = null;

function _btPaginaNombre(i) { return 'Página ' + (i + 1); }

function _btSyncPagina() {
  const ed = document.getElementById('btEditor');
  if (ed) btPages[btPageIdx] = ed.innerHTML;
}

function _btRenderPagesUI() {
  const menu = document.getElementById('btPagesMenu');
  const lbl = document.getElementById('btPageLbl');
  if (lbl) lbl.textContent = _btPaginaNombre(btPageIdx);
  if (!menu) return;
  menu.innerHTML = '';
  btPages.forEach((_, i) => {
    const li = document.createElement('li');
    const it = document.createElement('div');
    it.className = 'dropdown-item d-flex align-items-center gap-2 bt-page-item'
      + (i === btPageIdx ? ' active' : '');
    it.draggable = true;
    it.innerHTML = '<i class="bi bi-grip-vertical text-muted"></i>' +
      '<span class="flex-grow-1">' + _btPaginaNombre(i) + '</span>' +
      '<button class="btn btn-sm btn-light rounded-circle py-0 px-1" title="Subir"><i class="bi bi-arrow-up"></i></button>' +
      '<button class="btn btn-sm btn-light rounded-circle py-0 px-1" title="Bajar"><i class="bi bi-arrow-down"></i></button>';
    const [btnUp, btnDown] = it.querySelectorAll('button');
    btnUp.onclick = (e) => { e.stopPropagation(); btMoverPagina(i, -1); };
    btnDown.onclick = (e) => { e.stopPropagation(); btMoverPagina(i, 1); };
    it.onclick = () => btSelPagina(i);
    it.ondragstart = () => { btDragIdx = i; };
    it.ondragover = (e) => e.preventDefault();
    it.ondrop = (e) => { e.preventDefault(); btSoltarPagina(i); };
    li.appendChild(it);
    menu.appendChild(li);
  });
}

function btSelPagina(i) {
  _btSyncPagina();
  btPageIdx = i;
  document.getElementById('btEditor').innerHTML = btPages[i];
  btMediaSel = null;
  const tools = document.getElementById('btMediaTools');
  if (tools) tools.style.display = 'none';
  _btRenderPagesUI();
}

function btAgregarPagina() {
  _btSyncPagina();
  btPages.push('');
  btPageIdx = btPages.length - 1;
  document.getElementById('btEditor').innerHTML = '';
  _btRenderPagesUI();
}

function btMoverPagina(i, dir) {
  const j = i + dir;
  if (j < 0 || j >= btPages.length) return;
  _btSyncPagina();
  const tmp = btPages[i]; btPages[i] = btPages[j]; btPages[j] = tmp;
  if (btPageIdx === i) btPageIdx = j; else if (btPageIdx === j) btPageIdx = i;
  _btRenderPagesUI();
}

function btSoltarPagina(destino) {
  if (btDragIdx === null || btDragIdx === destino) return;
  _btSyncPagina();
  const actual = btPages[btPageIdx];
  const movida = btPages.splice(btDragIdx, 1)[0];
  btPages.splice(destino, 0, movida);
  btPageIdx = Math.max(0, btPages.indexOf(actual));
  btDragIdx = null;
  _btRenderPagesUI();
}

/* ── Eliminar página: modal del tema con doble confirmación ── */
function btEliminarPagina(i) {
  if (btPages.length <= 1) { alert('Debe quedar al menos una página.'); return; }
  btDelPageIdx = i;
  document.getElementById('btDelPageTxt1').textContent =
    '¿Eliminar la ' + _btPaginaNombre(i) + '?';
  btDelPagePaso(1);
  bootstrap.Modal.getOrCreateInstance(
    document.getElementById('btDelPageModal')).show();
}

function btDelPagePaso(paso) {
  const t1 = document.getElementById('btDelPageTxt1');
  const t2 = document.getElementById('btDelPageTxt2');
  const b1 = document.getElementById('btDelPageBtn1');
  const b2 = document.getElementById('btDelPageBtn2');
  t1.style.display = paso === 1 ? 'block' : 'none';
  t2.style.display = paso === 2 ? 'block' : 'none';
  b1.style.display = paso === 1 ? 'inline-block' : 'none';
  b2.style.display = paso === 2 ? 'inline-block' : 'none';
}

function btConfirmarDelPage() {
  const i = btDelPageIdx;
  if (i === null) return;
  btPages.splice(i, 1);
  if (btPageIdx >= btPages.length) btPageIdx = btPages.length - 1;
  document.getElementById('btEditor').innerHTML = btPages[btPageIdx];
  btDelPageIdx = null;
  bootstrap.Modal.getOrCreateInstance(
    document.getElementById('btDelPageModal')).hide();
  _btRenderPagesUI();
}
