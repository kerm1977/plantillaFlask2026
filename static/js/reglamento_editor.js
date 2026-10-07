// ==============================================================
//   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
//   Explicar antes de editar. Contenido sagrado protegido.
// ==============================================================
// reglamento_editor.js - Edición en vivo del reglamento de puntos (solo superusuario)
(function () {
  var cont = document.getElementById('reglamentoContenido');
  var barra = document.getElementById('rgBarra');
  var btnEditar = document.getElementById('rgEditar');
  if (!cont || !barra || !btnEditar) return;
  var msg = document.getElementById('rgMsg');
  var original = '';

  function modo(editando) {
    cont.contentEditable = editando ? 'true' : 'false';
    cont.classList.toggle('editando', editando);
    barra.classList.toggle('d-none', !editando);
    btnEditar.classList.toggle('d-none', editando);
    document.getElementById('rgCompartir').classList.toggle('d-none', editando);
    if (editando) {
      document.execCommand('defaultParagraphSeparator', false, 'p');
      document.execCommand('styleWithCSS', false, false);
      cont.focus();
    }
  }

  function bloqueActual() {
    var sel = window.getSelection();
    var n = sel && sel.anchorNode;
    while (n && n.parentNode !== cont) n = n.parentNode;
    return n && n.nodeType === 1 ? n : null;
  }

  function romano(n) {
    var m = [[10, 'X'], [9, 'IX'], [5, 'V'], [4, 'IV'], [1, 'I']], r = '';
    m.forEach(function (p) { while (n >= p[0]) { r += p[1]; n -= p[0]; } });
    return r;
  }

  function insertar(html) {
    var ref = bloqueActual();
    var tmp = document.createElement('div');
    tmp.innerHTML = html;
    var nuevo = tmp.firstChild;
    if (ref && ref.nextSibling) cont.insertBefore(nuevo, ref.nextSibling); else cont.appendChild(nuevo);
    var r = document.createRange();
    r.selectNodeContents(nuevo);
    r.collapse(false);
    var sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(r);
    nuevo.scrollIntoView({ block: 'center' });
  }

  var ACCIONES = {
    titulo: function () {
      var actual = (document.queryCommandValue('formatBlock') || '').toLowerCase();
      document.execCommand('formatBlock', false, actual === 'h6' ? 'p' : 'h6');
    },
    capitulo: function () {
      var n = Array.prototype.filter.call(cont.querySelectorAll('h6'), function (h) { return /^cap[ií]tulo/i.test(h.textContent.trim()); }).length + 1;
      insertar('<h6>Capítulo ' + romano(n) + ': </h6>');
    },
    articulo: function () {
      var n = 0;
      cont.querySelectorAll('p').forEach(function (p) {
        var m = /^art[ií]culo\s+(\d+)/i.exec(p.textContent.trim());
        if (m) n = Math.max(n, parseInt(m[1], 10));
      });
      insertar('<p><strong>Artículo ' + (n + 1) + '. Título.</strong> Texto del artículo.</p>');
    }
  };

  barra.querySelectorAll('.rg-cmd').forEach(function (b) {
    b.addEventListener('mousedown', function (e) { e.preventDefault(); });
    b.addEventListener('click', function () {
      cont.focus();
      var cmd = b.dataset.cmd;
      if (ACCIONES[cmd]) ACCIONES[cmd](); else document.execCommand(cmd, false, null);
    });
  });

  btnEditar.addEventListener('click', function () { original = cont.innerHTML; msg.textContent = ''; modo(true); });
  document.getElementById('rgCancelar').addEventListener('click', function () { cont.innerHTML = original; modo(false); });
  document.getElementById('rgGuardar').addEventListener('click', function () {
    var b = this;
    b.disabled = true;
    fetch(cont.dataset.guardar, { method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'same-origin', body: JSON.stringify({ html: cont.innerHTML }) })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (!d.ok) throw new Error(d.error || 'Error');
        cont.innerHTML = d.html;
        modo(false);
        var aviso = document.createElement('div');
        aviso.className = 'alert alert-success small rounded-pill py-1 text-center';
        aviso.textContent = d.restaurado ? 'Reglamento restaurado al texto original.' : 'Reglamento guardado.';
        cont.parentNode.insertBefore(aviso, cont);
        setTimeout(function () { aviso.remove(); }, 3500);
      })
      .catch(function (e) { msg.className = 'small text-danger me-auto'; msg.textContent = 'No se pudo guardar: ' + e.message; })
      .finally(function () { b.disabled = false; });
  });
})();
